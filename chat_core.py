import tkinter as tk
import customtkinter as ctk
import google.generativeai as genai
import threading
import queue
import os
import json
from datetime import datetime
import re
import uuid
import time
import math
from tkhtmlview import HTMLLabel
from markdown_it import MarkdownIt

class ChatCore:
    def __init__(self, app_instance):
        self.app = app_instance

    def send_message(self, chat_id, message_text=None):
        is_auto_reply = message_text is not None
        if not is_auto_reply:
            msg = self.app.user_inputs[chat_id].get("1.0", tk.END).strip()
            if not msg: return "break"
            self.app.user_inputs[chat_id].delete("1.0", tk.END)
        else:
            msg = message_text.strip()

        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display:
            raw_display.insert(tk.END, f"\n---\n# You:\n{msg}\n")
            raw_display.see(tk.END)
        
        self.app.gemini_api._start_api_call(chat_id, msg)
        return "break"

    def process_queue(self):
        try:
            msg = self.app.response_queue.get_nowait()
            chat_id, msg_type = msg['chat_id'], msg.get('type')
            if msg.get('generation_id') != self.app.current_generation_id[chat_id] and msg_type not in ['info', 'error']: return
            
            display = self.app.chat_displays.get(chat_id)
            raw_display = self.app.raw_log_displays.get(chat_id)

            if msg_type == 'stream_start':
                label = f"Gemini {chat_id}:"
                if raw_display:
                    raw_display.insert(tk.END, f"\n---\n# {label}\n")
                    raw_display.see(tk.END)

            elif msg_type == 'stream_chunk':
                if raw_display:
                    raw_display.insert(tk.END, msg['text']); raw_display.see(tk.END)

            elif msg_type == 'stream_end':
                full_response_text = msg.get('full_text', '')
                if display:
                    self._render_chat_display(chat_id)
                
                self.restore_ui_after_response(chat_id)
                if msg.get('usage'): self.app.gemini_api.update_token_counts(chat_id, msg['usage'])
                self.log_conversation(chat_id, msg['user_message'], full_response_text)
                
                target_id = 2 if chat_id == 1 else 1
                if self.app.auto_reply_vars[chat_id].get():
                    self._schedule_follow_up(target_id, full_response_text)
            elif msg_type in ['error', 'info']:
                self.restore_ui_after_response(chat_id)
                role = 'model'
                self.app.chat_sessions[chat_id].history.append({'role': role, 'parts': [{'text': msg['text']}]})
                
                self.append_message(chat_id, msg['text'], 'system' if msg_type == 'info' else 'error')

                self._render_chat_display(chat_id)
        except queue.Empty: pass
        finally: self.app.root.after(100, self.process_queue)

    def _schedule_follow_up(self, target_id, message):
        try:
            delay_minutes = float(self.app.delay_var.get())
            if delay_minutes < 0: raise ValueError
            delay_seconds = delay_minutes * 60
            
            if delay_seconds > 0:
                system_msg = f"--- Auto-replying in {delay_seconds:.1f} seconds... ---"
                self.app.chat_sessions[target_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
                self.append_message(target_id, system_msg, "system")
                self._render_chat_display(target_id)
                
                # Start countdown
                self._start_countdown(target_id, int(delay_seconds), message)
            else:
                self.send_message(target_id, message)
        except (ValueError, TypeError):
            system_msg = "--- Invalid auto-reply delay. Sending immediately. ---"
            self.app.chat_sessions[target_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
            self.append_message(target_id, system_msg, "error")
            self._render_chat_display(target_id)
            self.send_message(target_id, message)

    def _start_countdown(self, chat_id, remaining_seconds, message_to_send):
        if remaining_seconds > 0:
            minutes, seconds = divmod(remaining_seconds, 60)
            self.app.countdown_vars[chat_id].set(f"Auto-reply in {minutes:02d}:{seconds:02d}")
            self.app.root.after(1000, lambda: self._start_countdown(chat_id, remaining_seconds - 1, message_to_send))
        else:
            self.app.countdown_vars[chat_id].set("") # Clear countdown
            self.send_message(chat_id, message_to_send)
        
    def stop_generation(self, chat_id):
        self.app.current_generation_id[chat_id] += 1
        self.restore_ui_after_response(chat_id)
        system_msg = "\n--- Generation stopped by user. ---\n"
        self.app.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
        self.append_message(chat_id, system_msg, "system")
        self._render_chat_display(chat_id)

    def update_ui_for_sending(self, chat_id):
        self.app.user_inputs[chat_id].configure(state='disabled'); self.app.send_buttons[chat_id].configure(state='disabled')
        self.app.stop_buttons[chat_id].configure(state='normal'); self.app.progress_bars[chat_id].grid(); self.app.progress_bars[chat_id].start()

    def restore_ui_after_response(self, chat_id):
        self.app.user_inputs[chat_id].configure(state='normal'); self.app.send_buttons[chat_id].configure(state='normal')
        self.app.stop_buttons[chat_id].configure(state='disabled'); self.app.progress_bars[chat_id].stop(); self.app.progress_bars[chat_id].grid_remove(); self.app.user_inputs[chat_id].focus_set()

    def append_message(self, chat_id, label, tag, content=""):
        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display:
            message = content if content else label
            header = tag.capitalize()
            raw_display.insert(tk.END, f"\n---\n# {header}:\n{message}\n")
            raw_display.see(tk.END)
    
    def new_session(self):
        for chat_id in [1, 2]:
            self.app.gemini_api.prime_chat_session(chat_id, from_event=True)
            system_msg = "--- New session started. ---"
            self.app.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
            self.append_message(chat_id, system_msg, "system")
            self._render_chat_display(chat_id)
        self.app.delay_var.set(str(self.app.config.get("auto_reply_delay_minutes", 1.0)))

    def _render_chat_display(self, chat_id):
        """Renders the entire chat history for a given chat_id to its HTMLLabel."""
        if self.app.is_streaming.get(chat_id):
            return
        if chat_id not in self.app.chat_sessions or not hasattr(self.app.chat_sessions[chat_id], 'history'):
            return

        display_widget = self.app.chat_displays[chat_id]
        display_widget.delete("1.0", tk.END) # Clear existing content

        history = self.app.chat_sessions[chat_id].history
        # Get current font sizes and colors
        chat_font_size = self.app.chat_font_size_var.get()
        speaker_font_size = self.app.speaker_font_size_var.get()
        user_name_color = self.app.user_name_color_var.get()
        user_message_color = self.app.user_message_color_var.get()
        gemini_name_color = self.app.gemini_name_color_var.get()
        gemini_message_color = self.app.gemini_message_color_var.get()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="background-color: {self.app.COLOR_BACKGROUND}; color: {user_message_color}; font-family: Consolas, monaco, monospace; font-size: {chat_font_size}px;">
        """
        for message in history:

            if isinstance(message, dict):
                msg_role = message['role']
                msg_parts = message['parts']
                full_text = "".join([p['text'] for p in msg_parts if 'text' in p])
            else:
                msg_role = message.role
                msg_parts = message.parts
                full_text = "".join([p.text for p in msg_parts if hasattr(p, 'text')])

            content_html = self.app.md.render(full_text)

            pre_style = f"background-color: #2B2B2B; padding: 10px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-size: {chat_font_size}px;"
            code_style = f"font-family: Consolas, monaco, monospace; font-size: {chat_font_size}px;"

            content_html = re.sub(r'<pre>(.*?)</pre>', r'<pre style="' + pre_style + r'">\1</pre>', content_html, flags=re.DOTALL)
            content_html = re.sub(r'<code>(.*?)</code>', r'<code style="' + code_style + r'">\1</code>', content_html, flags=re.DOTALL)

            # Apply colors based on role
            if msg_role == 'user':
                current_role_color = user_name_color
                current_message_color = user_message_color
            else: # model
                current_role_color = gemini_name_color
                current_message_color = gemini_message_color

            role_name = "You" if msg_role == 'user' else f"Gemini {chat_id}"
            
            html_content += f'''
            <div style="margin-bottom: 1em; color: {current_message_color}; font-size: {chat_font_size}px;">
                <b style="font-weight: bold; color: {current_role_color}; font-size: {speaker_font_size}px;">{role_name}:</b>
                {content_html}
            </div>
            '''

        
        html_content += "</body></html>"
        self.app.chat_displays[chat_id].set_html(html_content)
        self.app.chat_displays[chat_id].update_idletasks()
        self.app.chat_displays[chat_id].yview_moveto(1.0)

    def save_session(self, chat_id):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title=f"Save Gemini {chat_id} Session")
        if not filepath: return
        try:
            history = [{'role': c.role, 'parts': [p.text for p in c.parts if hasattr(p, 'text')]} for c in self.app.chat_sessions[chat_id].history]
            session_data = {"model_name": self.app.model_selectors[chat_id].get(), "system_prompt": self.app.options_prompts[chat_id].get("1.0", tk.END).strip(), "history": history}
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(session_data, f, indent=2)
            messagebox.showinfo("Success", f"Session for Gemini {chat_id} saved.")
        except Exception as e: messagebox.showerror("Error", f"Failed to save session: {e}")
        
    def load_session(self, chat_id):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title=f"Load Session into Gemini {chat_id}")
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            history = session_data.get('history', [])

            self.app.gemini_api.prime_chat_session(chat_id, history=history, from_event=True)

            if self.app.raw_log_displays.get(chat_id):
                self.app.raw_log_displays[chat_id].delete('1.0', tk.END)

            system_msg = f"--- Loaded session. History restored. ---"
            self.app.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
            self.append_message(chat_id, system_msg, "system")
            self._render_chat_display(chat_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load session: {e}")

    def log_conversation(self, chat_id, user, response):
        path = os.path.join(self.app.log_dir, f"session_{self.app.session_timestamp}_gemini_{chat_id}.txt")
        with open(path, 'a', encoding='utf-8') as f:
            if user:
                f.write(f"---\n# You:\n{user}\n")
            f.write(f"---\n# Gemini {chat_id}:\n{response}\n\n")
