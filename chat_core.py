# --- START OF UPDATED chat_core.py ---

import tkinter as tk
import queue
import os
import json
from datetime import datetime
import re
from markdown_it import MarkdownIt
from tkinter import filedialog, messagebox

class ChatCore:
    def __init__(self, app_instance):
        self.app = app_instance
        self.md = MarkdownIt('commonmark').disable('table')
        self.lang = app_instance.lang

    def send_message(self, chat_id, message_text=None):
        pane = self.app.chat_panes[chat_id]
        is_auto_reply = message_text is not None
        
        if not is_auto_reply:
            msg = pane.user_input.get("1.0", tk.END).strip()
            if not msg: return "break"
            pane.user_input.delete("1.0", tk.END)
        else:
            msg = message_text.strip()
            
        user_message = {'role': 'user', 'parts': [{'text': msg}]}
        pane.render_history.append(user_message)
        pane.render_message_incrementally(user_message)
        
        raw_display = self.app.raw_log_displays.get(chat_id)
        if raw_display:
            raw_display.insert(tk.END, f"\n---\n# You:\n{msg}\n"); raw_display.see(tk.END)
            
        self.app.gemini_api._start_api_call(chat_id, msg)
        return "break"

    def process_queue(self):
        # ... (no changes in this method)
        try:
            msg = self.app.response_queue.get_nowait()
            chat_id = msg['chat_id']
            pane = self.app.chat_panes.get(chat_id)
            if not pane: return

            msg_type = msg.get('type')
            if msg.get('generation_id') != pane.current_generation_id and msg_type not in ['info', 'error', 'rewind', 'stream_end']: return

            if msg_type == 'stream_end':
                pane.restore_ui_after_response()
                if msg.get('usage'): self.app.gemini_api.update_token_counts(chat_id, msg['usage'])
                self.log_conversation(chat_id, msg['user_message'], msg.get('full_text', ''))
                
                target_pane_id = 2 if chat_id == 1 else 1
                if pane.auto_reply_var.get():
                    self._schedule_follow_up(target_pane_id, msg.get('full_text', ''))

            elif msg_type == 'rewind':
                final_text = msg.get('text', '')
                if final_text:
                    final_message = {'role': 'model', 'parts': [{'text': final_text}]}
                    pane.render_history.append(final_message)
                    pane.render_message_incrementally(final_message)

            elif msg_type in ['error', 'info']:
                pane.restore_ui_after_response()
                system_message = {'role': 'model', 'parts': [{'text': msg['text']}], 'is_ui_only': True}
                pane.render_history.append(system_message)
                self.append_message_to_raw_log(chat_id, msg['text'], 'system' if msg_type == 'info' else 'error')
                pane.render_message_incrementally(system_message)
                
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
    
    def regenerate_last_response(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        
        last_user_message_index = -1
        for i in range(len(pane.render_history) - 1, -1, -1):
            if pane.render_history[i]['role'] == 'user' and not pane.render_history[i].get('is_ui_only', False):
                last_user_message_index = i
                break
        
        if last_user_message_index == -1:
            messagebox.showinfo("Info", self.lang.get('info_no_previous_message'))
            return

        last_user_message = pane.render_history[last_user_message_index]
        # Trim history to *before* the last user message, as we will re-add it.
        pane.render_history = pane.render_history[:last_user_message_index]
        
        history_for_priming = [msg for msg in pane.render_history if not msg.get('is_ui_only')]

        self.app.gemini_api.prime_chat_session(chat_id, history=history_for_priming)
        
        # Visually re-render the now-trimmed history
        pane.render_full_history()

        # Re-send the last user message. The user message object itself is clean.
        # _start_api_call will handle adding the *current* context.
        last_user_prompt = last_user_message['parts'][0]['text']
        
        # Manually add the user message back to the UI before calling the API
        pane.render_history.append(last_user_message)
        pane.render_message_incrementally(last_user_message)

        self.app.gemini_api._start_api_call(chat_id, last_user_prompt)

    # ... (rest of the file is identical)
    def _schedule_follow_up(self, target_id, message):
        try:
            target_pane = self.app.chat_panes[target_id]
            delay_minutes = float(self.app.delay_var.get())
            if delay_minutes < 0: raise ValueError
            delay_seconds = delay_minutes * 60
            
            system_msg_text = f"---\n- Auto-replying in {delay_seconds:.1f} seconds... ---" if delay_seconds > 0 else "---\n- Invalid auto-reply delay. Sending immediately. ---"
            system_msg = {'role': 'model', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
            
            target_pane.render_history.append(system_msg)
            target_pane.render_message_incrementally(system_msg)
            self.append_message_to_raw_log(target_id, system_msg_text, "system")

            if delay_seconds > 0: self._start_countdown(target_id, int(delay_seconds), message)
            else: self.send_message(target_id, message)
        except (ValueError, TypeError): self.send_message(target_id, message)
    def _start_countdown(self, chat_id, remaining_seconds, message_to_send):
        pane = self.app.chat_panes[chat_id]
        if remaining_seconds > 0 and pane.auto_reply_var.get():
            minutes, seconds = divmod(remaining_seconds, 60)
            pane.countdown_var.set(f"Auto-reply in {minutes:02d}:{seconds:02d}")
            self.app.root.after(1000, lambda: self._start_countdown(chat_id, remaining_seconds - 1, message_to_send))
        else:
            pane.countdown_var.set("")
            if pane.auto_reply_var.get():
                self.send_message(chat_id, message_to_send)
    def stop_generation(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        pane.current_generation_id += 1
        pane.restore_ui_after_response()
        system_msg_text = self.lang.get('generation_stopped')
        system_msg = {'role': 'model', 'parts': [{'text': system_msg_text}], 'is_ui_only': True}
        pane.render_history.append(system_msg)
        pane.render_message_incrementally(system_msg)
        self.append_message_to_raw_log(chat_id, system_msg_text, "system")
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
            self.app.gemini_api.prime_chat_session(chat_id, from_event=True)
        self.app.delay_var.set(str(self.app.config.get("auto_reply_delay_minutes", 1.0)))
    def save_session(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title=f"Save Gemini {chat_id} Session")
        if not filepath: return
        try:
            history_to_save = [msg for msg in pane.render_history if not msg.get('is_ui_only', False)]
            session_data = { "model_name": self.app.model_selectors[chat_id].get(), "system_prompt": self.app.options_prompts[chat_id].get("1.0", tk.END).strip(), "history": history_to_save }
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(session_data, f, indent=2)
            messagebox.showinfo("Success", f"Session for Gemini {chat_id} saved.")
        except Exception as e: messagebox.showerror("Error", f"Failed to save session: {e}")
    def load_session(self, chat_id):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title=f"Load Session into Gemini {chat_id}")
        if not filepath: return
        try:
            pane = self.app.chat_panes[chat_id]
            with open(filepath, 'r', encoding='utf-8') as f: session_data = json.load(f)
            history = session_data.get('history', [])
            
            pane.clear_session()
            pane.render_history.extend(history)
            
            self.app.gemini_api.prime_chat_session(chat_id, history=history, from_event=True)
            pane.render_full_history()
            
        except Exception as e: messagebox.showerror("Error", f"Failed to load session: {e}")
    def rerender_all_panes(self):
        for pane in self.app.chat_panes.values():
            pane.render_full_history()
    def generate_message_html(self, chat_id, message):
        try:
            chat_font_size = self.app.chat_font_size_var.get()
            speaker_font_size = self.app.speaker_font_size_var.get()
        except tk.TclError:
            chat_font_size, speaker_font_size = 8, 12
        user_name_color, user_message_color = self.app.user_name_color_var.get(), self.app.user_message_color_var.get()
        gemini_name_color, gemini_message_color = self.app.gemini_name_color_var.get(), self.app.gemini_message_color_var.get()
        msg_role, full_text = message['role'], "".join([p.get('text', '') for p in message.get('parts', [])])
        content_html_body = self.md.render(full_text)
        h_styles = { i: f"font-size: {int(chat_font_size * (2.0 - (i-1)*0.25))}px; font-weight: bold;" for i in range(1, 7) }
        pre_style = f"background-color: #2B2B2B; padding: 10px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-size: {chat_font_size}px;"
        code_style = f"font-family: Consolas, monaco, monospace; background-color: #3C3F44; padding: 2px 4px; border-radius: 3px; font-size: {chat_font_size}px;"
        for i, style in h_styles.items():
            content_html_body = re.sub(r'<h' + str(i) + r'([^>]*)>', r'<h' + str(i) + r'\1 style="' + style + '">', content_html_body, flags=re.IGNORECASE)
        content_html_body = re.sub(r'<pre([^>]*)>', r'<pre\1 style="' + pre_style + '">', content_html_body, flags=re.IGNORECASE)
        content_html_body = re.sub(r'<code>', r'<code style="' + code_style + '">', content_html_body)
        current_role_color, current_message_color = (user_name_color, user_message_color) if msg_role == 'user' else (gemini_name_color, gemini_message_color)
        role_name = "You" if msg_role == 'user' else f"Gemini {chat_id}"
        return f'<div style="margin-bottom: 1em; color: {current_message_color}; font-size: {chat_font_size}px;"><b style="font-weight: bold; color: {current_role_color}; font-size: {speaker_font_size}px;">{role_name}:</b>{content_html_body}</div>'
    def generate_full_html(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        body_style = f"background-color: {self.app.COLOR_CHAT_DISPLAY}; color: {self.app.user_message_color_var.get()}; font-family: Consolas, monaco, monospace; font-size: {self.app.chat_font_size_var.get()}px; font-weight: normal;"
        html_header = f"<!DOCTYPE html><html><body style='{body_style}'>"
        content = "".join([self.generate_message_html(chat_id, msg) for msg in pane.render_history])
        return html_header + content + "</body></html>"
    def export_conversation(self, chat_id):
        history = self.app.chat_panes[chat_id].render_history
        if not history: messagebox.showwarning("Export Failed", "There is no conversation to export."); return
        filepath = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML File", "*.html"), ("Markdown File", "*.md")], title=f"Export Gemini {chat_id} Conversation")
        if not filepath: return
        file_ext = os.path.splitext(filepath)[1].lower()
        history_to_export = [msg for msg in history if not msg.get('is_ui_only', False)]
        try:
            content = self._generate_html_export(chat_id, history_to_export) if file_ext == ".html" else self._generate_markdown_export(chat_id, history_to_export)
            with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
            messagebox.showinfo("Export Successful", f"Conversation successfully exported to\n{filepath}")
        except Exception as e: messagebox.showerror("Export Failed", f"An error occurred during export: {e}")
    def smart_export(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        if not pane.render_history: messagebox.showwarning("Export Failed", "The conversation is empty."); return
        full_text = "".join(p.get('text', '') for msg in pane.render_history if msg['role'] == 'model' and not msg.get('is_ui_only') for p in msg.get('parts', []))
        extracted_parts = re.findall(r'\[START_SCENE\](.*?)\[END_SCENE\]', full_text, re.DOTALL)
        if not extracted_parts:
            messagebox.showinfo("Smart Export", "No content marked with [START_SCENE]...[END_SCENE] was found.")
            return
        final_content = "\n\n---\n\n".join([part.strip() for part in extracted_parts])
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt"), ("Markdown File", "*.md")], title=f"Smart Export Gemini {chat_id} Content")
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f: f.write(final_content)
            messagebox.showinfo("Export Successful", f"Creative content successfully exported to:\n{filepath}")
        except Exception as e: messagebox.showerror("Export Failed", f"An error occurred during export: {e}")
    def _generate_html_export(self, chat_id, history):
        body_style = f"background-color: {self.app.COLOR_BACKGROUND}; color: {self.app.user_message_color_var.get()}; font-family: Consolas, monaco, monospace; font-size: {self.app.chat_font_size_var.get()}px; padding: 20px; max-width: 800px; margin: auto;"
        html_header = f"<!DOCTYPE html><html><body style='{body_style}'><h1>Conversation with Gemini {chat_id}</h1>"
        content = "".join([self.generate_message_html(chat_id, msg) for msg in history])
        return html_header + content + "</body></html>"
    def _generate_markdown_export(self, chat_id, history):
        md_content = f"# Conversation with Gemini {chat_id}\n\n"
        for message in history:
            full_text = "".join([p.get('text', '') for p in message.get('parts', [])])
            role_name = "**You**" if message['role'] == 'user' else f"**Gemini {chat_id}**"
            md_content += f"{role_name}:\n\n{full_text}\n\n---\n\n"
        return md_content
    def log_conversation(self, chat_id, user, response):
        path = os.path.join(self.app.log_dir, f"session_{self.app.session_timestamp}_gemini_{chat_id}.txt")
        with open(path, 'a', encoding='utf-8') as f:
            if user: f.write(f"---\n# You:\n{user}\n")
            if response: f.write(f"---\n# Gemini {chat_id}:\n{response}\n\n")

# --- END OF UPDATED chat_core.py ---