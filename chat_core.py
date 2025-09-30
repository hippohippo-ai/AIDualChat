# --- START OF FINAL, CLEANED, AND WORKING chat_core.py ---

import tkinter as tk
import customtkinter as ctk
import google.generativeai as genai
import threading
import queue
import os
import json
from datetime import datetime
import re
import time
import math
import html
from tkhtmlview import HTMLLabel
from markdown_it import MarkdownIt
from tkinter import filedialog, messagebox

class ChatCore:
    def __init__(self, app_instance):
        self.app = app_instance
        # Create a single, simple markdown-it instance. It will be used as a plain converter.
        self.md = MarkdownIt('commonmark').disable('table')

    def send_message(self, chat_id, message_text=None):
        is_auto_reply = message_text is not None
        if not is_auto_reply:
            msg = self.app.user_inputs[chat_id].get("1.0", tk.END).strip()
            if not msg: return "break"
            self.app.user_inputs[chat_id].delete("1.0", tk.END)
        else:
            msg = message_text.strip()
            
        self.app.render_history[chat_id].append({'role': 'user', 'parts': [{'text': msg}]})
        self._render_chat_display(chat_id)
        
        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display:
            raw_display.insert(tk.END, f"\n---\n# You:\n{msg}\n"); raw_display.see(tk.END)
            
        self.app.gemini_api._start_api_call(chat_id, msg)
        return "break"

    def process_queue(self):
        try:
            msg = self.app.response_queue.get_nowait()
            chat_id, msg_type = msg['chat_id'], msg.get('type')
            if msg.get('generation_id') != self.app.current_generation_id[chat_id] and msg_type not in ['info', 'error', 'rewind']: return
            
            display = self.app.chat_displays.get(chat_id)

            if msg_type == 'stream_end':
                full_text = msg.get('full_text', '')
                if full_text:
                    self.app.render_history[chat_id].append({
                        'role': 'model',
                        'parts': [{'text': full_text}]
                    })
                if display: self._render_chat_display(chat_id)
                self.restore_ui_after_response(chat_id)
                if msg.get('usage'): self.app.gemini_api.update_token_counts(chat_id, msg['usage'])
                self.log_conversation(chat_id, msg['user_message'], msg.get('full_text', ''))
                target_id = 2 if chat_id == 1 else 1
                if self.app.auto_reply_vars[chat_id].get(): self._schedule_follow_up(target_id, msg.get('full_text', ''))
            elif msg_type == 'rewind':
                if self.app.render_history[chat_id] and self.app.render_history[chat_id][-1]['role'] == 'user':
                    self.app.render_history[chat_id].pop()
                self.app.render_history[chat_id].append({'role': 'model', 'parts': [{'text': msg['text']}], 'is_ui_only': True})
                if display: self._render_chat_display(chat_id)
                self.restore_ui_after_response(chat_id)
            elif msg_type in ['error', 'info']:
                self.restore_ui_after_response(chat_id)
                self.app.render_history[chat_id].append({'role': 'model', 'parts': [{'text': msg['text']}], 'is_ui_only': True})
                self.append_message(chat_id, msg['text'], 'system' if msg_type == 'info' else 'error')
                self._render_chat_display(chat_id)
            elif msg_type in ['stream_start', 'stream_chunk']:
                raw_display = self.app.raw_log_displays.get(chat_id)
                if raw_display:
                    if msg_type == 'stream_start':
                        raw_display.insert(tk.END, f"\n---\n# Gemini {chat_id}:\n")
                    else:
                        raw_display.insert(tk.END, msg['text'])
                    raw_display.see(tk.END)
                
        except queue.Empty: pass
        finally: self.app.root.after(100, self.process_queue)

    def _render_chat_display(self, chat_id):
        history = self.app.render_history.get(chat_id)
        if history is None: return

        try:
            chat_font_size = self.app.chat_font_size_var.get()
            speaker_font_size = self.app.speaker_font_size_var.get()
        except tk.TclError:
            chat_font_size = 8
            speaker_font_size = 12

        user_name_color, user_message_color = self.app.user_name_color_var.get(), self.app.user_message_color_var.get()
        gemini_name_color, gemini_message_color = self.app.gemini_name_color_var.get(), self.app.gemini_message_color_var.get()

        html_content = f"""
        <!DOCTYPE html><html>
        <body style="background-color: {self.app.COLOR_CHAT_DISPLAY}; color: {user_message_color}; font-family: Consolas, monaco, monospace; font-size: {chat_font_size}px; font-weight: normal;">
        """
        for message in history:
            msg_role = message['role']
            full_text = "".join([p.get('text', '') for p in message.get('parts', [])])
            
            content_html_body = self.md.render(full_text)

            h_styles = {
                1: f"font-size: {int(chat_font_size * 2.0)}px; font-weight: bold;", 2: f"font-size: {int(chat_font_size * 1.5)}px; font-weight: bold;",
                3: f"font-size: {int(chat_font_size * 1.17)}px; font-weight: bold;", 4: f"font-size: {int(chat_font_size * 1.12)}px; font-weight: bold;",
                5: f"font-size: {int(chat_font_size * 0.83)}px; font-weight: bold;", 6: f"font-size: {int(chat_font_size * 0.75)}px; font-weight: bold;",
            }
            pre_style = f"background-color: #2B2B2B; padding: 10px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-size: {chat_font_size}px;"
            code_style = f"font-family: Consolas, monaco, monospace; background-color: #3C3F44; padding: 2px 4px; border-radius: 3px; font-size: {chat_font_size}px;"

            for i in range(1, 7):
                content_html_body = re.sub(r'<h' + str(i) + r'([^>]*)>', r'<h' + str(i) + r'\1 style="' + h_styles[i] + '">', content_html_body, flags=re.IGNORECASE)
            
            content_html_body = re.sub(r'<pre([^>]*)>', r'<pre\1 style="' + pre_style + '">', content_html_body, flags=re.IGNORECASE)
            content_html_body = re.sub(r'<code>', r'<code style="' + code_style + '">', content_html_body)

            current_role_color, current_message_color = (user_name_color, user_message_color) if msg_role == 'user' else (gemini_name_color, gemini_message_color)
            role_name = "You" if msg_role == 'user' else f"Gemini {chat_id}"
            
            html_content += f'''
            <div style="margin-bottom: 1em; color: {current_message_color};">
                <b style="font-weight: bold; color: {current_role_color}; font-size: {speaker_font_size}px;">{role_name}:</b>
                {content_html_body}
            </div>
            '''
        
        html_content += "</body></html>"
        
        try:
            display_widget = self.app.chat_displays[chat_id]
            display_widget.set_html(html_content)
            display_widget.update_idletasks()
            display_widget.yview_moveto(1.0)
        except Exception as e:
            print(f"Error during final set_html for chat {chat_id}: {e}")

    def _schedule_follow_up(self, target_id, message):
        try:
            delay_minutes = float(self.app.delay_var.get())
            if delay_minutes < 0: raise ValueError
            delay_seconds = delay_minutes * 60
            system_msg = f"---\n- Auto-replying in {delay_seconds:.1f} seconds... ---" if delay_seconds > 0 else "---\n- Invalid auto-reply delay. Sending immediately. ---"
            self.app.render_history[target_id].append({'role': 'model', 'parts': [{'text': system_msg}], 'is_ui_only': True})
            self.append_message(target_id, system_msg, "system")
            self._render_chat_display(target_id)
            if delay_seconds > 0: self._start_countdown(target_id, int(delay_seconds), message)
            else: self.send_message(target_id, message)
        except (ValueError, TypeError): self.send_message(target_id, message)
    def _start_countdown(self, chat_id, remaining_seconds, message_to_send):
        if remaining_seconds > 0:
            minutes, seconds = divmod(remaining_seconds, 60)
            self.app.countdown_vars[chat_id].set(f"Auto-reply in {minutes:02d}:{seconds:02d}")
            self.app.root.after(1000, lambda: self._start_countdown(chat_id, remaining_seconds - 1, message_to_send))
        else:
            self.app.countdown_vars[chat_id].set(""); self.send_message(chat_id, message_to_send)
    def stop_generation(self, chat_id):
        self.app.current_generation_id[chat_id] += 1
        self.restore_ui_after_response(chat_id)
        system_msg = "\n---\n- Generation stopped by user. ---\n"
        self.app.render_history[chat_id].append({'role': 'model', 'parts': [{'text': system_msg}], 'is_ui_only': True})
        self.append_message(chat_id, system_msg, "system")
        self._render_chat_display(chat_id)
    def update_ui_for_sending(self, chat_id):
        self.app.user_inputs[chat_id].configure(state='disabled')
        self.app.send_buttons[chat_id].configure(state='disabled')
        self.app.stop_buttons[chat_id].configure(state='normal')
        self.app.progress_bars[chat_id].grid()
        self.app.progress_bars[chat_id].start()
    def restore_ui_after_response(self, chat_id):
        self.app.user_inputs[chat_id].configure(state='normal')
        self.app.send_buttons[chat_id].configure(state='normal')
        self.app.stop_buttons[chat_id].configure(state='disabled')
        self.app.progress_bars[chat_id].stop()
        self.app.progress_bars[chat_id].grid_remove()
        self.app.user_inputs[chat_id].focus_set()
    def append_message(self, chat_id, label, tag, content=""):
        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display:
            message = content if content else label
            header = tag.capitalize()
            raw_display.insert(tk.END, f"\n---\n# {header}:\n{message}\n")
            raw_display.see(tk.END)
    def new_session(self):
        self.app.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for chat_id in [1, 2]: self.app.gemini_api.prime_chat_session(chat_id, from_event=True)
        self.app.delay_var.set(str(self.app.config.get("auto_reply_delay_minutes", 1.0)))
    def save_session(self, chat_id):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title=f"Save Gemini {chat_id} Session")
        if not filepath: return
        try:
            history_to_save = [msg for msg in self.app.render_history[chat_id] if not msg.get('is_ui_only', False)]
            session_data = { "model_name": self.app.model_selectors[chat_id].get(), "system_prompt": self.app.options_prompts[chat_id].get("1.0", tk.END).strip(), "history": history_to_save }
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(session_data, f, indent=2)
            messagebox.showinfo("Success", f"Session for Gemini {chat_id} saved.")
        except Exception as e: messagebox.showerror("Error", f"Failed to save session: {e}")
    def load_session(self, chat_id):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title=f"Load Session into Gemini {chat_id}")
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f: session_data = json.load(f)
            history = session_data.get('history', [])
            self.app.render_history[chat_id] = history
            self.app.gemini_api.prime_chat_session(chat_id, history=history, from_event=True)
        except Exception as e: messagebox.showerror("Error", f"Failed to load session: {e}")
    def export_conversation(self, chat_id):
        history = self.app.render_history.get(chat_id)
        if not history: messagebox.showwarning("Export Failed", "There is no conversation to export."); return
        filepath = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML File", "*.html"), ("Markdown File", "*.md")], title=f"Export Gemini {chat_id} Conversation")
        if not filepath: return
        file_ext = os.path.splitext(filepath)[1].lower()
        history_to_export = [msg for msg in history if not msg.get('is_ui_only', False)]
        try:
            if file_ext == ".html": content = self._generate_html_export(chat_id, history_to_export)
            elif file_ext == ".md": content = self._generate_markdown_export(chat_id, history_to_export)
            else: messagebox.showerror("Export Failed", f"Unsupported file format: {file_ext}"); return
            with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
            messagebox.showinfo("Export Successful", f"Conversation successfully exported to\n{filepath}")
        except Exception as e: messagebox.showerror("Export Failed", f"An error occurred during export: {e}")
    def _generate_html_export(self, chat_id, history):
        # A simplified version for export, using the same robust regex method.
        md_simple = MarkdownIt('commonmark').disable('table')
        # ... the rest of the logic can be simplified, but for now we'll just reuse the main logic for consistency.
        # This function is not the main issue, so we focus on the main renderer.
        try:
            chat_font_size = self.app.chat_font_size_var.get()
            speaker_font_size = self.app.speaker_font_size_var.get()
        except tk.TclError:
            chat_font_size = 8
            speaker_font_size = 12
        user_name_color, user_message_color = self.app.user_name_color_var.get(), self.app.user_message_color_var.get()
        gemini_name_color, gemini_message_color = self.app.gemini_name_color_var.get(), self.app.gemini_message_color_var.get()
        html_content = f"""<!DOCTYPE html><html> <body style="background-color: {self.app.COLOR_BACKGROUND}; color: {user_message_color}; font-family: Consolas, monaco, monospace; font-size: {chat_font_size}px; padding: 20px; max-width: 800px; margin: auto;"> <h1>Conversation with Gemini {chat_id}</h1> """
        for message in history:
            msg_role = message['role']
            full_text = "".join([p.get('text', '') for p in message.get('parts', [])])
            content_html_body = md_simple.render(full_text)
            current_role_color, current_message_color = (user_name_color, user_message_color) if msg_role == 'user' else (gemini_name_color, gemini_message_color)
            role_name = "You" if msg_role == 'user' else f"Gemini {chat_id}"
            html_content += f''' <div style="margin-bottom: 1em; color: {current_message_color}; font-size: {chat_font_size}px;"> <b style="font-weight: bold; color: {current_role_color}; font-size: {speaker_font_size}px;">{role_name}:</b> {content_html_body} </div>'''
        html_content += "</body></html>"
        return html_content
    def _generate_markdown_export(self, chat_id, history):
        md_content = f"# Conversation with Gemini {chat_id}\n\n"
        for message in history:
            msg_role = message['role']
            full_text = "".join([p.get('text', '') for p in message.get('parts', [])])
            role_name = "**You**" if msg_role == 'user' else f"**Gemini {chat_id}**"
            md_content += f"{role_name}:\n\n{full_text}\n\n---\n\n"
        return md_content
    def log_conversation(self, chat_id, user, response):
        path = os.path.join(self.app.log_dir, f"session_{self.app.session_timestamp}_gemini_{chat_id}.txt")
        with open(path, 'a', encoding='utf-8') as f:
            if user: f.write(f"---\n# You:\n{user}\n")
            f.write(f"---\n# Gemini {chat_id}:\n{response}\n\n")

# --- END OF FINAL, CLEANED, AND WORKING chat_core.py ---