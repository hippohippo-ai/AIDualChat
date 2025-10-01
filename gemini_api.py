# --- START OF REFACTORED gemini_api.py ---

import google.generativeai as genai
import customtkinter as ctk
from tkinter import messagebox
import threading
import queue
import os
import re
import math
import time

class GeminiAPI:
    def __init__(self, app_instance):
        self.app = app_instance

    def prompt_for_api_key(self):
        dialog = ctk.CTkInputDialog(text="Please enter your Gemini API Key:", title="API Key Required")
        key = dialog.get_input()
        if not key: return

        try:
            genai.configure(api_key=key)
            self.app.available_models = self.fetch_available_models()
            self.app.api_key = key
            self.app.config["api_key"] = key
            self.app.config_manager._save_config_to_file(self.app.config)
            messagebox.showinfo("Success", "API Key is valid. Re-initializing models.")
            self._update_model_dropdowns()
            for chat_id in [1, 2]: self.prime_chat_session(chat_id, from_event=True)
        except Exception as e:
            messagebox.showerror("Invalid API Key", f"The provided API key is invalid or a network error occurred.\nError: {e}")

    def _update_model_dropdowns(self):
        model_list = self._create_model_list_for_dropdown()
        if not model_list: return
        for selector in self.app.model_selectors.values(): selector.configure(values=model_list)
        
        active_config_index = self.app.config.get('active_config_index', 0)
        active_profile = self.app.config['configurations'][active_config_index]
        
        default1 = active_profile['gemini_1']['model']
        default2 = active_profile['gemini_2']['model']
        
        self.app.model_selectors[1].set(default1 if default1 in model_list else (model_list[0] if model_list else ""))
        self.app.model_selectors[2].set(default2 if default2 in model_list else (model_list[0] if model_list else ""))

    def fetch_available_models(self):
        models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models: raise Exception("No usable models found for your API key.")
        return sorted(models)

    def _create_model_list_for_dropdown(self):
        preferred = self.app.config.get("preferred_models", [])
        top_list = [m for m in preferred if m in self.app.available_models]
        other_list = sorted([m for m in self.app.available_models if m not in top_list])
        if top_list and other_list: return top_list + ["──────────"] + other_list
        return self.app.available_models or []

    def prime_chat_session(self, chat_id, from_event=False, history=None):
        pane = self.app.chat_panes[chat_id]
        if not self.app.available_models:
            if from_event: messagebox.showerror("No Models Loaded", "Cannot start chat. Please set a valid API key.")
            return
        try:
            model_name = self.app.model_selectors[chat_id].get()
            active_config_index = self.app.config.get('active_config_index', 0)
            agent_config = self.app.config['configurations'][active_config_index][f'gemini_{chat_id}']
            generation_config = genai.types.GenerationConfig(temperature=agent_config['temperature'])
            sys_prompt = self.app.options_prompts[chat_id].get("1.0", ctk.END).strip()
            
            model = genai.GenerativeModel(model_name, system_instruction=sys_prompt, generation_config=generation_config)
           
            self.app.chat_sessions[chat_id] = model.start_chat(history=history or [])
            
            if from_event:
                system_msg_text = f"--- Session reset with model: {model_name} ---" if not history else f"--- Loaded session with model: {model_name} ---"
                system_msg = {'role': 'model', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
                pane.render_history.append(system_msg)
                pane.render_message_incrementally(system_msg)
                self.app.ui_elements._remove_all_files(chat_id)

            self.update_token_counts(chat_id, None, reset=True)
            
        except Exception as e: 
            messagebox.showerror("Model Error", f"Failed to start chat for Gemini {chat_id}.\nError: {e}")

    def on_model_change(self, chat_id):
        if messagebox.askyesno("Confirm", f"Changing model for Gemini {chat_id} will reset its history. Continue?"):
            self.app.chat_panes[chat_id].clear_session()
            self.prime_chat_session(chat_id, from_event=True)

    def api_call_thread(self, session, msg, chat_id, files, generation_id):
        pane = self.app.chat_panes[chat_id]
        response = None
        full_text_accumulator = ""
        try:
            content = [msg]
            if files: content.extend([genai.upload_file(path=p) for p in files])
            
            self.app.response_queue.put({'type': 'stream_start', 'chat_id': chat_id, 'generation_id': generation_id})
            
            response = session.send_message(content, stream=True)
            for chunk in response:
                if pane.current_generation_id != generation_id: 
                    response.resolve()
                    return
                if chunk.text:
                    full_text_accumulator += chunk.text
                    self.app.response_queue.put({'type': 'stream_chunk', 'chat_id': chat_id, 'text': chunk.text, 'generation_id': generation_id})

        except Exception as e:
            error_str = str(e)
            if "429" in error_str and ("quota" in error_str.lower() or "rate limit" in error_str.lower()):
                match = re.search(r"retry in ([\d\.]+)s", error_str.lower())
                delay = math.ceil(float(match.group(1))) + 1 if match else 60
                self.app.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': f"\n--- Retrying Gemini {chat_id} in {delay}s... ---\n", 'generation_id': generation_id})
                time.sleep(delay)
                self.api_call_thread(session, msg, chat_id, files, generation_id)
                return
            else:
                self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"API Error: {e}", 'generation_id': generation_id})
        
        finally:
            if pane.current_generation_id == generation_id:
                usage_meta = response.usage_metadata if response else None
                usage_dict = {'prompt_token_count': usage_meta.prompt_token_count, 'candidates_token_count': usage_meta.candidates_token_count} if usage_meta else None
                
                is_ok = False
                reason = "UNKNOWN"
                if response and response.candidates:
                    finish_reason_enum = response.candidates[0].finish_reason
                    reason = finish_reason_enum.name
                    if reason == "STOP":
                        is_ok = True

                # Put a single 'rewind' message which contains the final text for rendering.
                self.app.response_queue.put({
                    'type': 'rewind', 
                    'chat_id': chat_id, 
                    'text': full_text_accumulator, 
                    'generation_id': generation_id
                })

                # Put a separate 'stream_end' for logging, auto-reply, etc.
                self.app.response_queue.put({
                    'type': 'stream_end',
                    'chat_id': chat_id,
                    'usage': usage_dict,
                    'user_message': msg,
                    'full_text': full_text_accumulator,
                    'generation_id': generation_id
                })
                
                if not is_ok:
                    try:
                        session.rewind()
                        error_text = f"--- Gemini {chat_id} response finished abnormally (Reason: {reason}). Chat history has been repaired. Automated reply chain is stopped. ---"
                        self.app.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': error_text, 'generation_id': generation_id})
                    except (ValueError, IndexError):
                        error_text = f"--- Gemini {chat_id} response finished abnormally (Reason: {reason}). Could not repair history. Starting a new session is recommended. ---"
                        self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': error_text, 'generation_id': generation_id})

    def _start_api_call(self, chat_id, message):
        pane = self.app.chat_panes[chat_id]
        files = pane.file_listbox_paths
        
        if files: 
            system_msg_text = f"Attached: {', '.join([os.path.basename(p) for p in files])}"
            system_msg = {'role': 'user', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
            pane.render_history.append(system_msg)
            pane.render_message_incrementally(system_msg)
            self.app.chat_core.append_message_to_raw_log(chat_id, system_msg_text, "system")

        pane.current_generation_id += 1
        pane.update_ui_for_sending()
        
        thread = threading.Thread(target=self.api_call_thread, args=(self.app.chat_sessions[chat_id], message, chat_id, files, pane.current_generation_id))
        thread.daemon = True
        thread.start()
        
        self.app.ui_elements._remove_all_files(chat_id)

    def update_token_counts(self, chat_id, usage_metadata, reset=False):
        pane = self.app.chat_panes[chat_id]
        if reset:
            pane.total_tokens = 0
            pane.token_info_var.set(f"Tokens: 0 | 0")
            return
            
        if not usage_metadata: return
        
        last = usage_metadata.get('prompt_token_count', 0) + usage_metadata.get('candidates_token_count', 0)
        pane.total_tokens += last
        pane.token_info_var.set(f"Tokens: {last} | {pane.total_tokens}")

# --- END OF REFACTORED gemini_api.py ---