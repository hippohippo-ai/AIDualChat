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

# --- START OF FIXED core/chat_core.py ---

import tkinter as tk
import queue
import os
import json
from datetime import datetime
import re
from markdown_it import MarkdownIt
from tkinter import filedialog, messagebox
import uuid
import threading

from services.providers.base_provider import ProviderError
from config.models import AIConfig

class ChatCore:
    def __init__(self, app_instance):
        self.app = app_instance
        self.md = MarkdownIt('commonmark', {'linkify': True}).enable('linkify')
        self.lang = app_instance.lang
        self.history_lock = threading.Lock()

    def send_message(self, chat_id, message_text=None):
        pane = self.app.chat_panes[chat_id]
        is_auto_reply = message_text is not None

        if not is_auto_reply:
            msg = pane.user_input.get("1.0", tk.END).strip()
            # Allow sending with only files
            if not msg and not pane.get_ready_files():
                return "break"
            pane.user_input.delete("1.0", tk.END)
        else:
            msg = message_text.strip()

        # Add user message to history, associating it with the current model
        if msg:
            user_message = {
                'role': 'user', 
                'parts': [{'text': msg}],
                'model_name': pane.current_model_display_name 
            }
            with self.history_lock:
                pane.render_history.append(user_message)
            pane.render_full_history(scroll_to_bottom=True)
        
        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display and msg:
            raw_display.insert(tk.END, f"\n---\n# {self.lang.get('you')}:\n{msg}\n"); raw_display.see(tk.END)
            
        trace_id = str(uuid.uuid4())
        self.app.main_window.right_sidebar.start_api_call(chat_id, msg, trace_id)
        return "break"

    def process_queue(self):
        try:
            msg = self.app.response_queue.get_nowait()
            chat_id = msg['chat_id']
            pane = self.app.chat_panes.get(chat_id)
            if not pane: return

            msg_type = msg.get('type')
            
            if msg.get('generation_id') != pane.current_generation_id and msg_type not in ['info', 'error', 'system', 'stream_end']:
                return

            raw_display = self.app.raw_log_displays.get(chat_id)

            if msg_type == 'stream_start':
                pane.reset_model_response_stream()
                if raw_display:
                    raw_display.insert(tk.END, f"\n---\n# AI {chat_id} ({pane.current_model_display_name}):\n")
            elif msg_type == 'stream_chunk':
                pane.append_model_response_stream(msg['text'])
                if raw_display:
                    raw_display.insert(tk.END, msg['text'])
                    raw_display.see(tk.END)
            elif msg_type == 'stream_end':
                pane.finalize_model_response_stream()
                if msg.get('usage'): self.update_token_counts(chat_id, msg['usage'])
                
                target_pane_id = 2 if chat_id == 1 else 1
                if pane.auto_reply_var.get() and msg.get('full_text', '').strip():
                    self._schedule_follow_up(target_pane_id, msg.get('full_text', ''))

            elif msg_type == 'status_update':
                pane.update_status_message(msg['text'])
            elif msg_type in ['error', 'info', 'system']:
                pane.restore_ui_after_response()
                system_message = {
                    'role': 'model', 
                    'parts': [{'text': msg['text']}], 
                    'is_ui_only': True,
                    'model_name': 'System'
                }
                with self.history_lock:
                    pane.render_history.append(system_message)
                self.append_message_to_raw_log(chat_id, msg['text'], msg_type)
                pane.render_full_history(scroll_to_bottom=True)
                
        except queue.Empty: pass
        finally: self.app.root.after(100, self.app.chat_core.process_queue)
    
    def regenerate_last_response(self, chat_id):
        with self.history_lock:
            pane = self.app.chat_panes[chat_id]
            
            last_user_message_index = -1
            for i in range(len(pane.render_history) - 1, -1, -1):
                if pane.render_history[i]['role'] == 'user' and not pane.render_history[i].get('is_ui_only', False):
                    last_user_message_index = i
                    break
            
            if last_user_message_index == -1:
                messagebox.showinfo(self.lang.get('info'), self.lang.get('info_no_previous_message'))
                return

            first_message_of_turn = last_user_message_index
            while first_message_of_turn > 0 and pane.render_history[first_message_of_turn - 1]['role'] == 'user':
                first_message_of_turn -= 1

            last_user_turn_messages = pane.render_history[first_message_of_turn : last_user_message_index + 1]
            last_user_prompt = "".join(p['parts'][0]['text'] for p in last_user_turn_messages if not p.get('is_ui_only'))

            pane.render_history = pane.render_history[:first_message_of_turn]
            
            for msg in last_user_turn_messages:
                pane.render_history.append(msg)
            pane.render_full_history(scroll_to_bottom=True)

        trace_id = str(uuid.uuid4())
        self.app.main_window.right_sidebar.start_api_call(chat_id, last_user_prompt, trace_id)

    def stop_generation(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        pane.current_generation_id += 1
        pane.restore_ui_after_response()
        system_msg_text = self.lang.get('generation_stopped')
        self.app.response_queue.put({'type': 'system', 'chat_id': chat_id, 'text': system_msg_text})

    def append_message_to_raw_log(self, chat_id, message, tag):
        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display:
            header = tag.capitalize()
            raw_display.insert(tk.END, f"\n---\n# {header}:\n{message}\n")
            raw_display.see(tk.END)

    def new_session(self):
        self.app.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for chat_id, pane in self.app.chat_panes.items():
            pane.clear_session()
            system_msg_text = self.lang.get('session_reset_msg')
            self.app.response_queue.put({'type': 'system', 'chat_id': chat_id, 'text': system_msg_text})
        self.app.delay_var.set(str(self.app.config_model.auto_reply_delay_minutes))

    def save_session(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title=f"Save AI {chat_id} Session")
        if not filepath: return
        try:
            with self.history_lock:
                history_to_save = [msg for msg in pane.render_history if not msg.get('is_ui_only', False)]
            
            active_config = self.app.main_window.right_sidebar._gather_ai_config_from_ui(chat_id)
            session_data = {
                "version": 1,
                "ai_config": active_config.dict(),
                "history": history_to_save
            }
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(session_data, f, indent=2)
            messagebox.showinfo(self.lang.get('success'), f"Session for AI {chat_id} saved.")
        except Exception as e:
            self.app.logger.error("Failed to save session", error=str(e), exc_info=True)
            messagebox.showerror(self.lang.get('error'), f"Failed to save session: {e}")

    def load_session(self, chat_id):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title=f"Load Session into AI {chat_id}")
        if not filepath: return
        try:
            pane = self.app.chat_panes[chat_id]
            with open(filepath, 'r', encoding='utf-8') as f: session_data = json.load(f)
            history = session_data.get('history', [])
            
            with self.history_lock:
                pane.clear_session()
                pane.render_history.extend(history)
            
            pane.render_full_history(scroll_to_bottom=True)
            
            ai_config_data = session_data.get("ai_config")
            if ai_config_data:
                ai_config = AIConfig(**ai_config_data)
                self.app.main_window.right_sidebar.apply_config_to_ui(ai_config, chat_id)

            messagebox.showinfo(self.lang.get('success'), self.lang.get('session_loaded_msg'))
        except Exception as e:
            self.app.logger.error("Failed to load session", error=str(e), exc_info=True)
            messagebox.showerror(self.lang.get('error'), f"Failed to load session: {e}")
    
    def rerender_all_panes(self):
        for pane in self.app.chat_panes.values():
            pane.render_full_history()

    def generate_message_html(self, chat_id, message):
        msg_role = message['role']
        is_user = msg_role == 'user'
        
        ai_name = message.get('model_name') or self.app.chat_panes[chat_id].current_model_display_name or self.lang.get('ai_unknown')

        name_color = self.app.user_name_color_var.get() if is_user else self.app.ai_name_color_var.get()
        message_color = self.app.user_message_color_var.get() if is_user else self.app.ai_message_color_var.get()
        role_name = self.lang.get('you') if is_user else ai_name

        full_text = "".join([p.get('text', '') for p in message.get('parts', [])])
        content_html_body = self.md.render(full_text)
        
        font_size = self.app.chat_font_size_var.get()
        speaker_font_size = self.app.speaker_font_size_var.get()

        return f'<div style="margin-bottom: 1em; color: {message_color}; font-size: {font_size}px; overflow-wrap: break-word;"><b style="font-weight: bold; color: {name_color}; font-size: {speaker_font_size}px;">{role_name}:</b>{content_html_body}</div>'

    def update_token_counts(self, chat_id, usage_metadata):
        pane = self.app.chat_panes.get(chat_id)
        if not pane or not usage_metadata: return
        last = usage_metadata.get('prompt_token_count', 0) + usage_metadata.get('candidates_token_count', 0)
        pane.total_tokens += last
        pane.token_info_var.set(f"Tokens: {last} | {pane.total_tokens}")

    def _start_countdown(self, target_pane, remaining_seconds, message_to_send):
        if remaining_seconds > 0:
            minutes, seconds = divmod(remaining_seconds, 60)
            target_pane.countdown_var.set(f"{minutes:02d}:{seconds:02d}")
            job_id = self.app.root.after(1000, 
                lambda: self._start_countdown(target_pane, remaining_seconds - 1, message_to_send))
            target_pane.set_scheduled_task_id(job_id)
        else:
            target_pane.countdown_var.set("")
            target_pane.set_scheduled_task_id(None)
            self.send_message(target_pane.chat_id, message_text=message_to_send)

    def _schedule_follow_up(self, target_id, message):
        target_pane = self.app.chat_panes.get(target_id)
        if not target_pane: return
        target_pane.cancel_scheduled_task()

        try:
            delay_minutes = float(self.app.delay_var.get())
            if delay_minutes <= 0:
                self.send_message(target_id, message_text=message)
                return
            delay_seconds = int(delay_minutes * 60)
            system_msg_text = self.lang.get('auto_reply_scheduled').format(delay_seconds)
            self.app.response_queue.put({'type': 'system', 'chat_id': target_id, 'text': system_msg_text})
            self._start_countdown(target_pane, delay_seconds, message)
        except (ValueError, TypeError):
            self.send_message(target_id, message_text=message)

    # --- START OF FIX for Export buttons ---
    def export_conversation(self, chat_id):
        with self.history_lock:
            history = self.app.chat_panes[chat_id].render_history
            if not history:
                messagebox.showwarning(self.lang.get('error'), self.lang.get('error_no_conversation_to_export'))
                return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML File", "*.html"), ("Markdown File", "*.md")],
            title=self.lang.get('export_title').format(chat_id)
        )
        if not filepath: return
        
        file_ext = os.path.splitext(filepath)[1].lower()
        history_to_export = [msg for msg in history if not msg.get('is_ui_only', False)]
        
        try:
            if file_ext == ".html":
                content = self._generate_html_export(chat_id, history_to_export)
            else:
                content = self._generate_markdown_export(chat_id, history_to_export)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo(self.lang.get('success'), self.lang.get('export_success_message').format(filepath))
        except Exception as e:
            self.app.logger.error("Export failed", error=str(e), exc_info=True)
            messagebox.showerror(self.lang.get('error'), self.lang.get('export_error_message').format(e))

    def smart_export(self, chat_id):
        with self.history_lock:
            pane = self.app.chat_panes[chat_id]
            if not pane.render_history:
                messagebox.showwarning(self.lang.get('error'), self.lang.get('error_no_conversation_to_export'))
                return
            full_text = "".join(
                p.get('text', '') 
                for msg in pane.render_history 
                if msg['role'] == 'model' and not msg.get('is_ui_only') 
                for p in msg.get('parts', [])
            )
            
        extracted_parts = re.findall(r'\[START_SCENE\](.*?)\[END_SCENE\]', full_text, re.DOTALL)
        if not extracted_parts:
            messagebox.showinfo(self.lang.get('info'), self.lang.get('smart_export_no_scenes'))
            return
            
        final_content = "\n\n---\n\n".join([part.strip() for part in extracted_parts])
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            filetypes=[("Text File", "*.txt"), ("Markdown File", "*.md")], 
            title=self.lang.get('smart_export_title').format(chat_id)
        )
        if not filepath: return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            messagebox.showinfo(self.lang.get('success'), self.lang.get('export_success_message').format(filepath))
        except Exception as e:
            self.app.logger.error("Smart export failed", error=str(e), exc_info=True)
            messagebox.showerror(self.lang.get('error'), self.lang.get('export_error_message').format(e))

    def _generate_html_export(self, chat_id, history):
        body_style = f"background-color: {self.app.COLOR_BACKGROUND}; color: {self.app.user_message_color_var.get()}; font-family: sans-serif; font-size: 16px; padding: 20px; max-width: 800px; margin: auto;"
        html_header = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Conversation with AI {chat_id}</title></head><body style='{body_style}'><h1>Conversation with AI {chat_id}</h1>"
        content = "".join([self.generate_message_html(chat_id, msg) for msg in history])
        return html_header + content + "</body></html>"

    def _generate_markdown_export(self, chat_id, history):
        md_content = f"# Conversation with AI {chat_id}\n\n"
        for message in history:
            full_text = "".join([p.get('text', '') for p in message.get('parts', [])])
            role_name = f"**{self.lang.get('you')}**" if message['role'] == 'user' else f"**{message.get('model_name', f'AI {chat_id}')}**"
            md_content += f"{role_name}:\n\n{full_text}\n\n---\n\n"
        return md_content
    # --- END OF FIX for Export buttons ---
    
# --- END OF FIXED core/chat_core.py ---