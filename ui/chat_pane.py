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
        self._model_response_accumulator = ""
        self.uploaded_files = {}

        self.token_info_var = ctk.StringVar(value="Tokens: 0 | 0")
        self.auto_reply_var = ctk.BooleanVar(value=False)
        self.countdown_var = ctk.StringVar(value="")

        self.file_listbox = None
        self.model_display_label = None
        self.send_button = None
        self.stop_button = None
        self.regenerate_button = None
        self.auto_reply_checkbox = None
        self.status_label = None
        self.progress_bar = None

        self._create_widgets()

    def _create_widgets(self):
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=0)

        display_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        display_container.grid(row=0, column=0, sticky="nsew", columnspan=2)
        display_container.grid_columnconfigure(0, weight=1)
        display_container.grid_rowconfigure(0, weight=1)

        self.model_display_label = ctk.CTkLabel(display_container, text="", font=self.app.FONT_SMALL, fg_color=("#000000", "#2B2B2B"), text_color=self.app.COLOR_TEXT_MUTED, corner_radius=5)
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

        ctk.CTkLabel(controls_frame, textvariable=self.countdown_var, font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(controls_frame, textvariable=self.token_info_var, font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(10,0))
        
        # --- FIXED: Use a dedicated frame that can be hidden without affecting layout ---
        self.bottom_bar_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        self.bottom_bar_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")
        self.bottom_bar_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_bar_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(self.bottom_bar_frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        self.status_label.grid(row=0, column=0, padx=5, sticky="w")
        
        self.bottom_bar_frame.grid_remove() # Hide the whole frame

    def update_text(self):
        if self.send_button and self.send_button.winfo_exists():
            self.send_button.configure(text=self.lang.get('send'))
        if self.stop_button and self.stop_button.winfo_exists():
            self.stop_button.configure(text=self.lang.get('stop'))
        if self.regenerate_button and self.regenerate_button.winfo_exists():
            self.regenerate_button.configure(text=self.lang.get('regen'))
        if self.auto_reply_checkbox and self.auto_reply_checkbox.winfo_exists():
            other_id = 2 if self.chat_id == 1 else 1
            self.auto_reply_checkbox.configure(text=self.lang.get('auto_reply_to').format(other_id))

    def update_ui_for_sending(self):
        self.user_input.configure(state='disabled')
        self.send_button.configure(state='disabled')
        self.regenerate_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.bottom_bar_frame.grid() # Show the frame
        self.progress_bar.start()

    def restore_ui_after_response(self):
        self.user_input.configure(state='normal')
        self.send_button.configure(state='normal')
        self.regenerate_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.progress_bar.stop()
        self.bottom_bar_frame.grid_remove() # Hide the frame
        self.status_label.configure(text="")
        self.user_input.focus_set()

    def update_status_message(self, text):
        self.status_label.configure(text=text)

    def update_current_model_display(self, text):
        self.current_model_display_name = text
        self.model_display_label.configure(text=f"  {text}  ")

    def reset_model_response_stream(self):
        self._model_response_accumulator = ""
        new_message = {'role': 'model', 'parts': [{'text': ""}]}
        self.render_history.append(new_message)
        self.render_full_history(scroll_to_bottom=True)

    def append_model_response_stream(self, text_chunk):
        self._model_response_accumulator += text_chunk
        if self.render_history and self.render_history[-1]['role'] == 'model':
            self.render_history[-1]['parts'][0]['text'] = self._model_response_accumulator
            self.render_full_history(scroll_to_bottom=True)
    
    def finalize_model_response_stream(self):
        self.restore_ui_after_response()
        self.render_full_history()

    def render_full_history(self, scroll_to_bottom=False):
        self.reset_html_accumulator()
        for message in self.render_history:
            html_segment = self.app.chat_core.generate_message_html(self.chat_id, message)
            self.html_body_content += html_segment
        self.chat_display.set_html(self.html_body_content + "</body></html>")
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
        self.render_history.clear()
        self.total_tokens = 0
        self.token_info_var.set("Tokens: 0 | 0")
        self.current_generation_id += 1
        self.render_full_history()
        raw_display = self.app.raw_log_displays.get(self.chat_id)
        if raw_display:
            raw_display.delete('1.0', tk.END)
        
    def get_ready_files(self):
        return [data['result'] for data in self.uploaded_files.values() if data['status'] == 'done']