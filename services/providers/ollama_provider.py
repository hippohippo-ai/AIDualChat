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

import requests
import json
import threading

from services.providers.base_provider import BaseProvider, ProviderError

class OllamaProvider(BaseProvider):
    def __init__(self, app_instance, state_manager):
        super().__init__(app_instance, state_manager)
        self.status = {"is_available": False, "models": [], "version": "Unknown"}
        self.lock = threading.Lock()

    def get_name(self):
        return "Ollama"

    def is_configured(self):
        return bool(self.state_manager.config_model.ollama_settings.host)

    def get_status(self):
        with self.lock:
            return self.status.copy()

    def get_models(self):
        with self.lock:
            return self.status.get("models", [])

    def _get_base_url(self):
        return self.state_manager.config_model.ollama_settings.host

    def refresh_status(self):
        if not self.is_configured():
            with self.lock:
                self.status = {"is_available": False, "models": [], "version": "Not Configured"}
            return

        base_url = self._get_base_url()
        new_status = {}
        try:
            # Check reachability
            response = requests.get(base_url, timeout=3)
            response.raise_for_status()
            new_status["is_available"] = True
            self.logger.info("Ollama host is reachable.", host=base_url)

            # Get version
            try:
                version_res = requests.get(f"{base_url}/api/version", timeout=3)
                new_status["version"] = version_res.json().get("version", "Unknown")
            except Exception:
                new_status["version"] = "Unknown"

            # Get models
            tags_res = requests.get(f"{base_url}/api/tags", timeout=10)
            tags_res.raise_for_status()
            models = [m['name'] for m in tags_res.json().get('models', [])]
            new_status["models"] = sorted(models)
            self.logger.info("Fetched Ollama models.", count=len(models))

        except requests.exceptions.RequestException as e:
            self.logger.warning("Failed to connect to Ollama host.", host=base_url, error=str(e))
            new_status = {"is_available": False, "models": [], "version": "Connection Error"}
        
        with self.lock:
            self.status = new_status

    def send_message(self, chat_id, model_config, message, trace_id):
        pane = self.app.chat_panes[chat_id]
        logger = self.logger.bind(trace_id=trace_id, chat_id=chat_id, generation_id=pane.current_generation_id)
        
        if not self.status.get("is_available"):
            raise ProviderError("Ollama is not available. Check host settings and ensure it's running.", is_fatal=True)

        base_url = self._get_base_url()
        endpoint = f"{base_url}/api/chat"
        
        persona_prompt = self.app.main_window.right_sidebar.persona_prompts[chat_id].get("1.0", "end-1c").strip()
        history = self.get_history_for_api(pane.render_history)
        
        # Format history for Ollama
        messages = []
        if persona_prompt:
            messages.append({"role": "system", "content": persona_prompt})
        
        for msg in history:
            messages.append({"role": msg['role'], "content": msg['parts'][0]['text']})
        
        if message:
            messages.append({"role": "user", "content": message})
        
        payload = {
            "model": model_config['model'],
            "messages": messages,
            "stream": True
        }

        try:
            logger.info("Sending request to Ollama.", model=model_config['model'])
            yield {'type': 'stream_start'}
            
            with requests.post(endpoint, json=payload, stream=True, timeout=300) as response:
                response.raise_for_status()
                full_text_accumulator = ""
                
                for line in response.iter_lines():
                    if pane.current_generation_id != model_config['generation_id']:
                        logger.warning("Generation cancelled by user.")
                        return

                    if line:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_text_accumulator += content
                            yield {'type': 'stream_chunk', 'text': content}
                        
                        if chunk.get("done"):
                            logger.info("Ollama stream finished.")
                            # Ollama provides token counts in the final chunk
                            usage_dict = {
                                'prompt_token_count': chunk.get('prompt_eval_count', 0),
                                'candidates_token_count': chunk.get('eval_count', 0)
                            }
                            yield {
                                'type': 'stream_end',
                                'usage': usage_dict,
                                'user_message': message,
                                'full_text': full_text_accumulator
                            }
                            break

        except requests.exceptions.RequestException as e:
            logger.error("Error during Ollama API call", error=str(e), exc_info=True)
            raise ProviderError(f"Ollama Connection Error: {e}", is_fatal=True)