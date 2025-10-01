# --- START OF FINAL, ROBUST gemini_api.py ---

import google.generativeai as genai
import customtkinter as ctk
from tkinter import messagebox
import threading
import os
import re
import math
import time
from ddgs import DDGS

# This import combination is proven correct by your diagnostic script
from google.generativeai.types import Tool, FunctionDeclaration
from google.generativeai.protos import FunctionResponse, Part


class GeminiAPI:
    def __init__(self, app_instance):
        self.app = app_instance
        self.lang = app_instance.lang
        
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
                        }
                    }
                )
            ]
        )

    def _perform_web_search(self, query: str) -> dict:
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
            return {"results": f"An error occurred during web search: {e}"}

    def prompt_for_api_key(self):
        # ... (no changes in this method)
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
        # ... (no changes in this method)
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
        # ... (no changes in this method)
        models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models: raise Exception("No usable models found for your API key.")
        return sorted(models)

    def _create_model_list_for_dropdown(self):
        # ... (no changes in this method)
        preferred = self.app.config.get("preferred_models", [])
        top_list = [m for m in preferred if m in self.app.available_models]
        other_list = sorted([m for m in self.app.available_models if m not in top_list])
        if top_list and other_list: return top_list + ["──────────"] + other_list
        return self.app.available_models or []

    def prime_chat_session(self, chat_id, from_event=False, history=None):
        # ... (no changes in this method)
        if not self.app.available_models:
            if from_event: messagebox.showerror("No Models Loaded", "Cannot start chat. Please set a valid API key.")
            return
        try:
            model_name = self.app.model_selectors[chat_id].get()
            persona_prompt = self.app.options_prompts[chat_id].get("1.0", ctk.END).strip()
            
            tools_to_use = [self.web_search_tool] if self.app.web_search_vars[chat_id].get() else None
            model = genai.GenerativeModel(model_name, system_instruction=persona_prompt, tools=tools_to_use)
            
            self.app.chat_sessions[chat_id] = model.start_chat(history=history or [])
            
            if from_event:
                pane = self.app.chat_panes[chat_id]
                if not history: 
                    pane.clear_session()
                    system_msg_text = self.lang.get('session_reset_msg', model_name)
                    system_msg = {'role': 'model', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
                    pane.render_history.append(system_msg)
                    pane.render_message_incrementally(system_msg)
                    self.app.ui_elements._remove_all_files(chat_id)
                else: 
                    system_msg_text = self.lang.get('session_loaded_msg', model_name)
                    system_msg = {'role': 'model', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
                    pane.render_history.append(system_msg)
                
            if not history:
                self.update_token_counts(chat_id, None, reset=True)
            
        except Exception as e: 
            messagebox.showerror("Model Error", f"Failed to start chat for Gemini {chat_id}.\nError: {e}")

    def on_model_change(self, chat_id):
        # ... (no changes in this method)
        if messagebox.askyesno("Confirm", f"Changing model for Gemini {chat_id} will reset its history. Continue?"):
            self.prime_chat_session(chat_id, from_event=True, history=None)
            
    # --- START OF MODIFICATION ---
    def api_call_thread(self, session, msg, chat_id, files, generation_id, is_fallback_attempt=False):
        pane = self.app.chat_panes[chat_id]
        response = None
        full_text_accumulator = ""
        try:
            content_to_send = [msg]
            if files: content_to_send.extend([genai.upload_file(path=p) for p in files])
            
            self.app.response_queue.put({'type': 'stream_start', 'chat_id': chat_id, 'generation_id': generation_id})
            
            response = session.send_message(content_to_send, stream=True)

            for chunk in response:
                if pane.current_generation_id != generation_id: 
                    response.resolve(); return
                
                for part in chunk.parts:
                    if part.function_call:
                        fc = part.function_call
                        if fc.name == 'web_search':
                            query = fc.args['query']
                            
                            info_text = self.lang.get('searching_web', query)
                            self.app.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': info_text, 'generation_id': generation_id})
                            
                            search_results = self._perform_web_search(query=query)
                            
                            info_text_2 = self.lang.get('search_results_info')
                            self.app.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': info_text_2, 'generation_id': generation_id})

                            response = session.send_message(
                                Part(function_response=FunctionResponse(name='web_search', response=search_results)),
                                stream=True
                            )
                            
                            for final_chunk in response:
                                if pane.current_generation_id != generation_id: 
                                    response.resolve(); return
                                for final_part in final_chunk.parts:
                                    if final_part.text:
                                        full_text_accumulator += final_part.text
                                        self.app.response_queue.put({'type': 'stream_chunk', 'chat_id': chat_id, 'text': final_part.text, 'generation_id': generation_id})
                            break 
                    
                    elif part.text:
                        full_text_accumulator += part.text
                        self.app.response_queue.put({'type': 'stream_chunk', 'chat_id': chat_id, 'text': part.text, 'generation_id': generation_id})
                else: 
                    continue 
                break 

        except Exception as e:
            # --- THIS IS THE NEW ROBUSTNESS LOGIC ---
            # If search was enabled and this is the first try, attempt a fallback
            if self.app.web_search_vars[chat_id].get() and not is_fallback_attempt:
                print(f"Web search attempt failed: {e}. Falling back to normal mode.")
                
                # 1. Inform the user in the UI
                fallback_msg = self.lang.get('web_search_failed_fallback')
                self.app.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': fallback_msg, 'generation_id': generation_id})

                # 2. Create a temporary model session WITHOUT tools
                model_name = self.app.model_selectors[chat_id].get()
                persona_prompt = self.app.options_prompts[chat_id].get("1.0", ctk.END).strip()
                model_no_tools = genai.GenerativeModel(model_name, system_instruction=persona_prompt, tools=None)
                session_no_tools = model_no_tools.start_chat(history=session.history)

                # 3. Re-run this thread in fallback mode
                self.api_call_thread(session_no_tools, msg, chat_id, files, generation_id, is_fallback_attempt=True)
                return # Stop execution of this failed thread
            
            # --- Original error handling for all other cases ---
            else:
                import traceback
                print(f"Error in api_call_thread (is_fallback: {is_fallback_attempt}): {e}")
                traceback.print_exc()
                self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"API Error: {e}", 'generation_id': generation_id})
        
        finally:
            # ... (finally block remains the same)
            # --- END OF MODIFICATION ---
            if pane.current_generation_id == generation_id:
                is_ok, reason = False, "UNKNOWN"
                if response and response.candidates:
                    finish_reason_enum = response.candidates[0].finish_reason
                    reason = finish_reason_enum.name
                    if reason == "STOP": is_ok = True
                self.app.response_queue.put({'type': 'rewind', 'chat_id': chat_id, 'text': full_text_accumulator, 'generation_id': generation_id})
                usage_meta = response.usage_metadata if response else None
                usage_dict = {'prompt_token_count': usage_meta.prompt_token_count, 'candidates_token_count': usage_meta.candidates_token_count} if usage_meta else None
                self.app.response_queue.put({'type': 'stream_end', 'chat_id': chat_id, 'usage': usage_dict, 'user_message': msg, 'full_text': full_text_accumulator, 'generation_id': generation_id})
                if not is_ok:
                    try:
                        session.rewind(); session.rewind()
                        error_text = f"--- Gemini {chat_id} response finished abnormally (Reason: {reason}). Chat history has been repaired. Automated reply chain is stopped. ---"
                        self.app.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': error_text, 'generation_id': generation_id})
                    except (ValueError, IndexError):
                        error_text = f"--- Gemini {chat_id} response finished abnormally (Reason: {reason}). Could not repair history. Starting a new session is recommended. ---"
                        self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': error_text, 'generation_id': generation_id})

    def _start_api_call(self, chat_id, message, is_regenerate=False):
        # ... (no changes in this method)
        pane = self.app.chat_panes[chat_id]
        
        self.prime_chat_session(chat_id, from_event=False, history=self.app.chat_sessions[chat_id].history)
        
        context_text = self.app.context_prompts[chat_id].get("1.0", "end-1c").strip()
        final_message = f"{context_text}\n\n---\n\n{message}" if context_text else message

        files = pane.file_listbox_paths
        if files: 
            system_msg_text = f"Attached: {', '.join([os.path.basename(p) for p in files])}"
            system_msg = {'role': 'user', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
            pane.render_history.append(system_msg)
            pane.render_message_incrementally(system_msg)
            self.app.chat_core.append_message_to_raw_log(chat_id, system_msg_text, "system")

        pane.current_generation_id += 1
        pane.update_ui_for_sending()
        
        thread = threading.Thread(target=self.api_call_thread, args=(self.app.chat_sessions[chat_id], final_message, chat_id, files, pane.current_generation_id))
        thread.daemon = True
        thread.start()
        
        self.app.ui_elements._remove_all_files(chat_id)

    def update_token_counts(self, chat_id, usage_metadata, reset=False):
        # ... (no changes in this method)
        pane = self.app.chat_panes.get(chat_id)
        if not pane: return
        if reset:
            pane.total_tokens = 0
            pane.token_info_var.set(f"Tokens: 0 | 0")
            return
        if not usage_metadata: return
        last = usage_metadata.get('prompt_token_count', 0) + usage_metadata.get('candidates_token_count', 0)
        pane.total_tokens += last
        pane.token_info_var.set(f"Tokens: {last} | {pane.total_tokens}")

# --- END OF FINAL, ROBUST gemini_api.py ---