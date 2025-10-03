# AIDualChat - A dual-pane chat application for AI models.
# Copyright (C) 2025 Hippohippo-AI
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# --- START OF UPDATED services/providers/google_provider.py ---

import google.generativeai as genai
from google.generativeai.types import generation_types, Tool, FunctionDeclaration
from google.generativeai.protos import FunctionResponse, Part
from google.api_core import exceptions as api_core_exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import threading
from ddgs import DDGS
from typing import Tuple  # --- FIX: Import Tuple for correct type hinting ---

from .base_provider import BaseProvider, ProviderError

RETRYABLE_EXCEPTIONS = (
    api_core_exceptions.DeadlineExceeded,
    api_core_exceptions.InternalServerError,
    api_core_exceptions.ServiceUnavailable,
    api_core_exceptions.ResourceExhausted,
)

class GoogleProvider(BaseProvider):
    def __init__(self, app_instance, state_manager):
        super().__init__(app_instance, state_manager)
        self.key_statuses = {}
        self.lock = threading.Lock()
        self.web_search_tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name='web_search',
                    description='Performs a web search to find up-to-date information on a given topic.',
                    parameters={
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'The search query to find information about.'
                            }
                        },
                        'required': ['query']
                    }
                )
            ]
        )

    @classmethod
    # --- FIX: Changed "-> (bool, str)" to the correct "-> Tuple[bool, str]" ---
    def validate_api_key(cls, api_key: str) -> Tuple[bool, str]:
        """
        Validates a Google API key by making a simple, low-cost API call.
        Returns a tuple: (is_valid: bool, message: str).
        """
        if not api_key.isascii():
            return False, "API Key must contain only ASCII characters."
        try:
            genai.configure(api_key=api_key)
            genai.list_models()
            return True, "API Key is valid."
        except Exception as e:
            error_str = str(e)
            if "API_KEY_INVALID" in error_str:
                return False, "The provided API Key is invalid."
            else:
                return False, f"Validation failed: {error_str}"

    def _perform_web_search(self, query: str) -> dict:
        self.logger.info("Performing web search", query=query)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            if not results:
                return {"results": "No results found."}
            
            formatted_results = []
            for i, res in enumerate(results, 1):
                formatted_results.append(f"Source [{i}]: {res['title']}\nSnippet: {res['body']}\nURL: {res['href']}\n---")
            
            return {"results": "\n".join(formatted_results)}
        except Exception as e:
            self.logger.error("Web search failed", error=str(e))
            return {"results": f"An error occurred during web search: {e}"}

    def get_name(self):
        return "Google"

    def is_configured(self):
        return bool(self.state_manager.get_google_keys())

    def get_key_status(self, key_id):
        with self.lock:
            return self.key_statuses.get(key_id, {"is_valid": None, "quota": "Unknown"})

    def get_models(self):
        with self.lock:
            for status in self.key_statuses.values():
                if status.get("is_valid") and status.get("models"):
                    return status["models"]
        return []

    def get_history_for_api(self, render_history):
        cleaned_history = []
        for msg in render_history:
            if not msg.get('is_ui_only', False):
                api_msg = {
                    'role': msg['role'],
                    'parts': msg['parts']
                }
                cleaned_history.append(api_msg)
        return cleaned_history

    def refresh_status(self):
        keys = self.state_manager.get_google_keys()
        for key in keys:
            self.logger.info("Refreshing status for Google Key", key_id=key.id, note=key.note)
            
            is_valid, _ = self.validate_api_key(key.api_key)
            
            if is_valid:
                try:
                    genai.configure(api_key=key.api_key)
                    models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    with self.lock:
                        self.key_statuses[key.id] = {
                            "is_valid": True, "quota": "OK", "reset_time": "N/A", "models": sorted(models)
                        }
                    self.logger.info("Google Key is valid.", key_id=key.id)
                except Exception as e:
                    with self.lock:
                        self.key_statuses[key.id] = {
                            "is_valid": False, "quota": "Permissions Error", "reset_time": "N/A", "models": []
                        }
                    self.logger.warning("Google Key is valid but failed to list models.", key_id=key.id, error=str(e))
            else:
                with self.lock:
                    self.key_statuses[key.id] = {
                        "is_valid": False, "quota": "Invalid", "reset_time": "N/A", "models": []
                    }
                self.logger.warning("Google Key is invalid.", key_id=key.id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS)
    )
    def _send_message_with_retry(self, session, content, logger, tools=None):
        logger.info("Attempting to send message to Google API...")
        return session.send_message(content, stream=True, tools=tools)

    def send_message(self, chat_id, model_config, message, trace_id):
        pane = self.app.chat_panes[chat_id]
        logger = self.logger.bind(trace_id=trace_id, chat_id=chat_id, generation_id=pane.current_generation_id)
        
        try:
            key_id = model_config.get("key_id")
            key = self.app.config_model.get_google_key_by_id(key_id)
            if not key:
                raise ProviderError(f"Google Key with ID '{key_id}' not found.", is_fatal=True)
            
            genai.configure(api_key=key.api_key)

            persona_prompt = self.app.main_window.right_sidebar.persona_prompts[chat_id].get("1.0", "end-1c").strip()
            web_search_enabled = self.app.main_window.right_sidebar.web_search_vars[chat_id].get()
            tools = [self.web_search_tool] if web_search_enabled else None
            
            model = genai.GenerativeModel(model_config['model'], system_instruction=persona_prompt)
            
            history = self.get_history_for_api(pane.render_history)
            
            session = model.start_chat(history=history)

            content_to_send = []
            files = pane.get_ready_files()
            if files: content_to_send.extend(files)
            if message: content_to_send.append(message)
            
            if not content_to_send:
                yield {'type': 'error', 'text': "No message or files to send."}
                return

            yield {'type': 'stream_start'}
            
            response = self._send_message_with_retry(session, content_to_send, logger, tools=tools)
            
            full_text_accumulator = ""
            for chunk in response:
                if pane.current_generation_id != model_config['generation_id']:
                    logger.warning("Generation cancelled by user.")
                    response.resolve()
                    return

                if chunk.parts:
                    for part in chunk.parts:
                        if part.function_call:
                            fc = part.function_call
                            if fc.name == 'web_search':
                                query = fc.args.get('query', 'No query specified')
                                yield {'type': 'status_update', 'text': self.app.lang.get('searching_web').format(query)}
                                
                                search_results = self._perform_web_search(query=query)
                                
                                yield {'type': 'status_update', 'text': self.app.lang.get('search_results_info')}
                                
                                response_for_tool = self._send_message_with_retry(
                                    session,
                                    Part(function_response=FunctionResponse(name='web_search', response=search_results)),
                                    logger
                                )
                                for final_chunk in response_for_tool:
                                     if final_chunk.text:
                                        full_text_accumulator += final_chunk.text
                                        yield {'type': 'stream_chunk', 'text': final_chunk.text}
                                break 
                        elif part.text:
                            full_text_accumulator += part.text
                            yield {'type': 'stream_chunk', 'text': part.text}

            usage_meta = response.usage_metadata if response else None
            usage_dict = {'prompt_token_count': usage_meta.prompt_token_count, 'candidates_token_count': usage_meta.candidates_token_count} if usage_meta else None
            
            yield {
                'type': 'stream_end',
                'usage': usage_dict,
                'user_message': message,
                'full_text': full_text_accumulator
            }

        except Exception as e:
            logger.error("Error during Google API call", error=str(e), exc_info=True)
            is_quota_error = isinstance(e, api_core_exceptions.ResourceExhausted)
            raise ProviderError(f"Google API Error: {e}", is_fatal=not is_quota_error)

# --- END OF UPDATED services/providers/google_provider.py ---