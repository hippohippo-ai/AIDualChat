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

import tkinter as tk
import customtkinter as ctk
from tkhtmlview import HTMLLabel
import os
import threading

class ChatPane:
    def __init__(self, app_instance, chat_id, parent_tab):
        self.app = app_instance
        self.chat_id = chat_id
        self.parent = parent_tab
        self.lang = app_instance.lang

        self.render_history = []
        self.total_tokens = 0
        self.current_generation_id = 0
        self.current_model_display_name = ""
        
        self._history_html_cache = ""
        self._current_streaming_message_obj = None

        self.token_info_var = ctk.StringVar(value="Tokens: 0 | 0")
        self.auto_reply_var = ctk.BooleanVar(value=False)
        self.countdown_var = ctk.StringVar(value="")

        # --- BUG #2: Variable to hold the scheduled task ID ---
        self.scheduled_task_id = None

        self.uploaded_files = {}

        self.model_display_label = None
        self.send_button = None
        self.stop_button = None
        self.regenerate_button = None
        self.auto_reply_checkbox = None
        self.status_label = None
        self.progress_bar = None
        self.chat_display = None

        self._create_widgets()

    def _create_widgets(self):
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=0)

        display_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        display_container.grid(row=0, column=0, sticky="nsew", columnspan=2)
        display_container.grid_columnconfigure(0, weight=1)
        display_container.grid_rowconfigure(0, weight=1)

        semi_transparent_color = "#333333" 
        self.model_display_label = ctk.CTkLabel(display_container, text="", font=self.app.FONT_SMALL, fg_color=semi_transparent_color, text_color=self.app.COLOR_TEXT_MUTED, corner_radius=5)
        self.model_display_label.place(relx=0.5, y=20, anchor="center")
        self.model_display_label.lift()

        self.chat_display = HTMLLabel(display_container, background=self.app.COLOR_CHAT_DISPLAY)
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ctk.CTkScrollbar(display_container, command=self.chat_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        input_frame = ctk.CTkFrame(self.parent, fg_color=self.app.COLOR_INPUT_AREA, corner_radius=0)
        input_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.user_input = ctk.CTkTextbox(input_frame, height=120, wrap="word", font=self.app.FONT_CHAT)
        self.user_input.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.user_input.bind("<Control-Return>", lambda event: self.app.chat_core.send_message(self.chat_id))

        controls_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ns")

        self.send_button = ctk.CTkButton(controls_frame, text="", command=lambda: self.app.chat_core.send_message(self.chat_id), width=70)
        self.send_button.pack(pady=(0, 2), fill="x")

        self.stop_button = ctk.CTkButton(controls_frame, text="", command=lambda: self.app.chat_core.stop_generation(self.chat_id), width=70, state="disabled")
        self.stop_button.pack(pady=(2, 2), fill="x")
        
        self.regenerate_button = ctk.CTkButton(controls_frame, text="", command=lambda: self.app.chat_core.regenerate_last_response(self.chat_id), width=70)
        self.regenerate_button.pack(pady=(2, 10), fill="x")

        self.auto_reply_checkbox = ctk.CTkCheckBox(controls_frame, text="", variable=self.auto_reply_var)
        self.auto_reply_checkbox.pack(anchor="w")
        # --- BUG #2: Trace the checkbox to cancel the timer if unchecked ---
        self.auto_reply_var.trace_add("write", self._on_auto_reply_toggle)

        ctk.CTkLabel(controls_frame, textvariable=self.countdown_var, font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(controls_frame, textvariable=self.token_info_var, font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(10,0))
        
        self.bottom_bar_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        self.bottom_bar_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")
        self.bottom_bar_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_bar_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(self.bottom_bar_frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        self.status_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.bottom_bar_frame.grid_remove()

    def update_text(self):
        if self.send_button and self.send_button.winfo_exists(): self.send_button.configure(text=self.lang.get('send'))
        if self.stop_button and self.stop_button.winfo_exists(): self.stop_button.configure(text=self.lang.get('stop'))
        if self.regenerate_button and self.regenerate_button.winfo_exists(): self.regenerate_button.configure(text=self.lang.get('regen'))
        if self.auto_reply_checkbox and self.auto_reply_checkbox.winfo_exists():
            other_id = 2 if self.chat_id == 1 else 1
            self.auto_reply_checkbox.configure(text=self.lang.get('auto_reply_to').format(other_id))

    def update_ui_for_sending(self):
        self.user_input.configure(state='disabled')
        self.send_button.configure(state='disabled')
        self.regenerate_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.bottom_bar_frame.grid()
        self.progress_bar.start()

    def restore_ui_after_response(self):
        self.user_input.configure(state='normal')
        self.send_button.configure(state='normal')
        self.regenerate_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.progress_bar.stop()
        self.bottom_bar_frame.grid_remove()
        self.status_label.configure(text="")
        self.user_input.focus_set()

    def update_status_message(self, text):
        self.status_label.configure(text=text)

    def update_current_model_display(self, text):
        self.current_model_display_name = text
        self.model_display_label.configure(text=f"  {text}  ")

    def _cache_history_html(self):
        self.reset_html_accumulator()
        self._history_html_cache = "".join([self.app.chat_core.generate_message_html(self.chat_id, msg) for msg in self.render_history])

    def reset_model_response_stream(self):
        self._cache_history_html()
        self._current_streaming_message_obj = {
            'role': 'model', 
            'parts': [{'text': ""}],
            'model_name': self.current_model_display_name
        }
        streaming_html = self.app.chat_core.generate_message_html(self.chat_id, self._current_streaming_message_obj)
        self.chat_display.set_html(self.html_body_content + self._history_html_cache + streaming_html + "</body></html>")

    def append_model_response_stream(self, text_chunk):
        if self._current_streaming_message_obj is None: return
        self._current_streaming_message_obj['parts'][0]['text'] += text_chunk
        streaming_html = self.app.chat_core.generate_message_html(self.chat_id, self._current_streaming_message_obj)
        self.chat_display.set_html(self.html_body_content + self._history_html_cache + streaming_html + "</body></html>")
        self.app.root.after(10, lambda: self.chat_display.yview_moveto(1.0))

    def finalize_model_response_stream(self):
        if self._current_streaming_message_obj:
            if not self.render_history or self.render_history[-1] is not self._current_streaming_message_obj:
                 self.render_history.append(self._current_streaming_message_obj)
            self._current_streaming_message_obj = None
            self._history_html_cache = ""
        self.restore_ui_after_response()
        self.render_full_history(scroll_to_bottom=True)

    def render_full_history(self, scroll_to_bottom=False):
        self.reset_html_accumulator()
        html_content = "".join([self.app.chat_core.generate_message_html(self.chat_id, msg) for msg in self.render_history])
        self.chat_display.set_html(self.html_body_content + html_content + "</body></html>")
        if scroll_to_bottom:
            self.app.root.after(50, lambda: self.chat_display.yview_moveto(1.0))

    def reset_html_accumulator(self):
        font_family = self.app.FONT_CHAT.cget('family')
        font_size = self.app.chat_font_size_var.get()
        color = self.app.user_message_color_var.get()
        bg_color = self.app.COLOR_CHAT_DISPLAY
        body_style = f"background-color: {bg_color}; color: {color}; font-family: '{font_family}', Consolas, monaco, monospace; font-size: {font_size}px; font-weight: normal;"
        self.html_body_content = f"<!DOCTYPE html><html><body style='{body_style}'>"
        
    def clear_session(self):
        # --- BUG #2: Cancel any pending tasks before clearing ---
        self.cancel_scheduled_task()
        self.render_history.clear()
        self.total_tokens = 0
        self.token_info_var.set("Tokens: 0 | 0")
        self.current_generation_id += 1
        self.render_full_history()
        raw_display = self.app.raw_log_displays.get(self.chat_id)
        if raw_display:
            raw_display.delete('1.0', tk.END)
        
    def get_ready_files(self):
        return []

    # --- BUGS #1 & #2: New methods for task management ---
    def set_scheduled_task_id(self, job_id):
        """Stores the ID of a scheduled 'after' job."""
        self.scheduled_task_id = job_id

    def cancel_scheduled_task(self):
        """Cancels a pending auto-reply task if it exists."""
        if self.scheduled_task_id:
            self.app.root.after_cancel(self.scheduled_task_id)
            self.set_scheduled_task_id(None)
            self.countdown_var.set("")
            self.app.logger.info(f"Cancelled scheduled task for AI {self.chat_id}")

    def _on_auto_reply_toggle(self, *args):
        """Callback for when the auto-reply checkbox is toggled."""
        if not self.auto_reply_var.get():
            self.cancel_scheduled_task()