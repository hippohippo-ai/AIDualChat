import google.generativeai as genai
from google.generativeai.types import generation_types, Tool, FunctionDeclaration
from google.generativeai.protos import FunctionResponse, Part
from google.api_core import exceptions as api_core_exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import threading

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

    def refresh_status(self):
        keys = self.state_manager.get_google_keys()
        for key in keys:
            self.logger.info("Refreshing status for Google Key", key_id=key.id, note=key.note)
            try:
                genai.configure(api_key=key.api_key)
                models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                with self.lock:
                    self.key_statuses[key.id] = {
                        "is_valid": True,
                        "quota": "OK",
                        "reset_time": "N/A",
                        "models": sorted(models)
                    }
                self.logger.info("Google Key is valid.", key_id=key.id)
            except Exception as e:
                with self.lock:
                    self.key_statuses[key.id] = {
                        "is_valid": False,
                        "quota": "Error",
                        "reset_time": "N/A",
                        "models": []
                    }
                self.logger.warning("Google Key is invalid or failed to refresh.", key_id=key.id, error=str(e))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS)
    )
    def _send_message_with_retry(self, session, content, logger):
        logger.info("Attempting to send message to Google API...")
        return session.send_message(content, stream=True)

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

            response = self._send_message_with_retry(session, content_to_send, logger)
            
            full_text_accumulator = ""
            for chunk in response:
                if pane.current_generation_id != model_config['generation_id']:
                    logger.warning("Generation cancelled by user.")
                    response.resolve()
                    return

                if chunk.text:
                    full_text_accumulator += chunk.text
                    yield {'type': 'stream_chunk', 'text': chunk.text}

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