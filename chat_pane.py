# --- START OF FINAL CORRECTED chat_pane.py ---

import tkinter as tk
import customtkinter as ctk
from tkhtmlview import HTMLLabel
import os

class ChatPane:
    """
    Manages all UI elements and state for a single chat panel.
    """
    def __init__(self, app_instance, chat_id, parent_tab):
        self.app = app_instance
        self.chat_id = chat_id
        self.parent = parent_tab
        self.lang = app_instance.lang

        # --- State Management for this Pane ---
        self.render_history = []
        self.total_tokens = 0
        self.current_generation_id = 0
        
        self.html_body_content = ""

        # --- UI Variable Initialization ---
        self.token_info_var = ctk.StringVar(value="Tokens: 0 | 0")
        self.auto_reply_var = ctk.BooleanVar(value=False)
        self.countdown_var = ctk.StringVar(value="")
        
        self.file_listbox = None
        self.file_listbox_paths = []

        # --- UI Element Handles ---
        self.send_button = None
        self.stop_button = None
        self.regenerate_button = None
        self.auto_reply_checkbox = None

        self._create_widgets()
        self.reset_html_accumulator()

    def _create_widgets(self):
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)

        self.chat_display = HTMLLabel(self.parent, background=self.app.COLOR_CHAT_DISPLAY)
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ctk.CTkScrollbar(self.parent, command=self.chat_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        input_frame = ctk.CTkFrame(self.parent, fg_color=self.app.COLOR_INPUT_AREA)
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

        ctk.CTkLabel(controls_frame, textvariable=self.countdown_var, font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(controls_frame, textvariable=self.token_info_var, font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(10,0))

        self.progress_bar = ctk.CTkProgressBar(input_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.progress_bar.grid_remove()
    
    # --- START OF FIX ---
    def update_text(self):
        """Updates all language-dependent text within this pane."""
        if self.send_button and self.send_button.winfo_exists():
            self.send_button.configure(text=self.lang.get('send'))
        if self.stop_button and self.stop_button.winfo_exists():
            self.stop_button.configure(text=self.lang.get('stop'))
        if self.regenerate_button and self.regenerate_button.winfo_exists():
            self.regenerate_button.configure(text=self.lang.get('regen'))
        if self.auto_reply_checkbox and self.auto_reply_checkbox.winfo_exists():
            other_id = 2 if self.chat_id == 1 else 1
            self.auto_reply_checkbox.configure(text=self.lang.get('auto_reply_to').format(other_id))
    # --- END OF FIX ---
            
    def update_ui_for_sending(self):
        self.user_input.configure(state='disabled')
        self.send_button.configure(state='disabled')
        self.regenerate_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.progress_bar.grid()
        self.progress_bar.start()

    def restore_ui_after_response(self):
        self.user_input.configure(state='normal')
        self.send_button.configure(state='normal')
        self.regenerate_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.user_input.focus_set()
        
    def clear_session(self):
        self.render_history.clear()
        self.total_tokens = 0
        self.token_info_var.set("Tokens: 0 | 0")
        self.current_generation_id += 1
        self.reset_html_accumulator()
        self.chat_display.set_html(self.html_body_content + "</body></html>")
        raw_display = self.app.raw_log_displays.get(self.chat_id)
        if raw_display:
            raw_display.delete('1.0', tk.END)
            
    def reset_html_accumulator(self):
        chat_font_size = self.app.chat_font_size_var.get()
        user_message_color = self.app.user_message_color_var.get()
        body_style = f"background-color: {self.app.COLOR_CHAT_DISPLAY}; color: {user_message_color}; font-family: Consolas, monaco, monospace; font-size: {chat_font_size}px; font-weight: normal;"
        self.html_body_content = f"<!DOCTYPE html><html><body style='{body_style}'>"

    def render_message_incrementally(self, message):
        html_segment = self.app.chat_core.generate_message_html(self.chat_id, message)
        self.html_body_content += html_segment
        self.chat_display.set_html(self.html_body_content + "</body></html>")
        self.chat_display.update_idletasks()
        self.chat_display.yview_moveto(1.0)

    def render_full_history(self):
        self.reset_html_accumulator()
        for message in self.render_history:
            html_segment = self.app.chat_core.generate_message_html(self.chat_id, message)
            self.html_body_content += html_segment
        self.chat_display.set_html(self.html_body_content + "</body></html>")
        self.chat_display.update_idletasks()
        self.chat_display.yview_moveto(1.0)

# --- END OF FINAL CORRECTED chat_pane.py ---