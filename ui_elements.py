import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from tkhtmlview import HTMLLabel
from tkinter import colorchooser

class UIElements:
    def __init__(self, app_instance):
        self.app = app_instance

    def create_widgets(self):
        self.app.root.grid_columnconfigure(1, weight=1); self.app.root.grid_rowconfigure(0, weight=1)
        self.app.left_sidebar = self._create_left_sidebar(self.app.root); self.app.left_sidebar.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="nsw")
        self.app.central_area = self._create_central_area(self.app.root); self.app.central_area.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.app.right_sidebar = self._create_right_sidebar(self.app.root); self.app.right_sidebar.grid(row=0, column=2, padx=(0, 5), pady=5, sticky="nse")
        self._toggle_left_sidebar()

    def _toggle_left_sidebar(self):
        is_expanded = self.app.left_sidebar.cget('width') == self.app.SIDEBAR_WIDTH_FULL
        if is_expanded: self.app.left_sidebar.content_frame.pack_forget(); self.app.left_sidebar.configure(width=self.app.SIDEBAR_WIDTH_COLLAPSED); self.app.left_toggle_button.configure(text="▶")
        else: self.app.left_sidebar.configure(width=self.app.SIDEBAR_WIDTH_FULL); self.app.left_sidebar.content_frame.pack(fill="x", before=self.app.left_sidebar.spacer); self.app.left_toggle_button.configure(text="◀")

    def _toggle_right_sidebar(self):
        is_expanded = self.app.right_sidebar.cget('width') == self.app.SIDEBAR_WIDTH_FULL
        if is_expanded: self.app.right_sidebar.content_frame.pack_forget(); self.app.right_sidebar.configure(width=self.app.SIDEBAR_WIDTH_COLLAPSED); self.app.right_toggle_button.configure(text="◀")
        else: self.app.right_sidebar.configure(width=self.app.SIDEBAR_WIDTH_FULL); self.app.right_sidebar.content_frame.pack(fill="both", expand=True); self.app.right_toggle_button.configure(text="▶")

    def _create_left_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=self.app.SIDEBAR_WIDTH_FULL, fg_color=self.app.COLOR_SIDEBAR, corner_radius=10); sidebar.pack_propagate(False)
        toggle_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); toggle_frame.pack(fill="x", pady=5, padx=5)
        self.app.left_toggle_button = ctk.CTkButton(toggle_frame, text="◀", command=self._toggle_left_sidebar, width=25, height=25, font=self.app.FONT_GENERAL); self.app.left_toggle_button.pack(anchor="ne")
        sidebar.content_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); sidebar.content_frame.pack(fill="x")
        ctk.CTkLabel(sidebar.content_frame, text="STUDIO", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.app.COLOR_TEXT).pack(pady=(0,20), padx=20, anchor="w")
        session_content = self._create_collapsible_frame(sidebar.content_frame, "Session Management")
        ctk.CTkButton(session_content, text="New Session", command=self.app.chat_core.new_session, fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Save Gemini 1", command=lambda: self.app.chat_core.save_session(1), fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Save Gemini 2", command=lambda: self.app.chat_core.save_session(2), fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Load Gemini 1", command=lambda: self.app.chat_core.load_session(1), fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Load Gemini 2", command=lambda: self.app.chat_core.load_session(2), fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL).pack(fill="x", padx=15, pady=(0,10))

        display_content = self._create_collapsible_frame(sidebar.content_frame, "Display") # New collapsible frame
        
        # Font Size Spinboxes
        font_size_frame_name = ctk.CTkFrame(display_content, fg_color="transparent")
        font_size_frame_name.pack(fill="x", padx=15, pady=(5,0))
        ctk.CTkLabel(font_size_frame_name, text="Name Font Size:", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(side="left", padx=(0,5))
        self.name_font_size_spinbox = self._create_spinbox_entry(font_size_frame_name, self.app.speaker_font_size_var, 6, 30, 40, self.app.FONT_GENERAL)
        self.name_font_size_spinbox.pack(side="left")
        
        font_size_frame_chat = ctk.CTkFrame(display_content, fg_color="transparent")
        font_size_frame_chat.pack(fill="x", padx=15, pady=(0,5))
        ctk.CTkLabel(font_size_frame_chat, text="Chat Font Size:", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(side="left", padx=(0,5))
        self.chat_font_size_spinbox = self._create_spinbox_entry(font_size_frame_chat, self.app.chat_font_size_var, 6, 30, 40, self.app.FONT_GENERAL)
        self.chat_font_size_spinbox.pack(side="left")

        # Color Pickers
        color_picker_label = ctk.CTkLabel(display_content, text="Chat Colors:", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        color_picker_label.pack(anchor="w", padx=15, pady=(10,0))

        color_grid_frame = ctk.CTkFrame(display_content, fg_color="transparent")
        color_grid_frame.pack(fill="x", padx=15, pady=(0,5))
        color_grid_frame.grid_columnconfigure(0, weight=1)
        color_grid_frame.grid_columnconfigure(1, weight=1)

        # User Name Color
        user_name_frame = ctk.CTkFrame(color_grid_frame, fg_color="transparent")
        user_name_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(user_name_frame, text="User Name", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack()
        self.user_name_color_button = ctk.CTkButton(user_name_frame, text="", fg_color=self.app.user_name_color_var.get(), width=50, height=25, command=lambda: self._pick_color(self.app.user_name_color_var, self.user_name_color_button))
        self.user_name_color_button.pack()

        # User Message Color
        user_message_frame = ctk.CTkFrame(color_grid_frame, fg_color="transparent")
        user_message_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(user_message_frame, text="User Message", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack()
        self.user_message_color_button = ctk.CTkButton(user_message_frame, text="", fg_color=self.app.user_message_color_var.get(), width=50, height=25, command=lambda: self._pick_color(self.app.user_message_color_var, self.user_message_color_button))
        self.user_message_color_button.pack()

        # Gemini Name Color
        gemini_name_frame = ctk.CTkFrame(color_grid_frame, fg_color="transparent")
        gemini_name_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(gemini_name_frame, text="Gemini Name", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack()
        self.gemini_name_color_button = ctk.CTkButton(gemini_name_frame, text="", fg_color=self.app.gemini_name_color_var.get(), width=50, height=25, command=lambda: self._pick_color(self.app.gemini_name_color_var, self.gemini_name_color_button))
        self.gemini_name_color_button.pack()

        # Gemini Message Color
        gemini_message_frame = ctk.CTkFrame(color_grid_frame, fg_color="transparent")
        gemini_message_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(gemini_message_frame, text="Gemini Message", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack()
        self.gemini_message_color_button = ctk.CTkButton(gemini_message_frame, text="", fg_color=self.app.gemini_message_color_var.get(), width=50, height=25, command=lambda: self._pick_color(self.app.gemini_message_color_var, self.gemini_message_color_button))
        self.gemini_message_color_button.pack()

        # Restore Display Settings Button
        ctk.CTkButton(display_content, text="Restore Defaults", command=self.app.config_manager._restore_display_settings, font=self.app.FONT_GENERAL).pack(fill="x", padx=15, pady=(10,0))

        sidebar.spacer = ctk.CTkFrame(sidebar, fg_color="transparent"); sidebar.spacer.pack(expand=True, fill="y")
        return sidebar

    def _create_central_area(self, parent):
        tab_view = ctk.CTkTabview(parent, fg_color=self.app.COLOR_INPUT_AREA); tab_view.grid(row=0, column=0, sticky="nsew")
        self.app.central_tab_view = tab_view

        # Create main chat tabs
        tab1 = tab_view.add("Gemini 1")
        tab2 = tab_view.add("Gemini 2")
        self._create_chat_panel(tab1, 1)
        self._create_chat_panel(tab2, 2)

        # Create raw log tabs and their content directly
        raw_tab_1 = tab_view.add("Gemini 1 (Raw)")
        raw_tab_2 = tab_view.add("Gemini 2 (Raw)")

        raw_tab_1.grid_columnconfigure(0, weight=1)
        raw_tab_1.grid_rowconfigure(0, weight=1)
        display1 = ctk.CTkTextbox(raw_tab_1, wrap="word", font=self.app.FONT_CHAT, state='normal', fg_color=self.app.COLOR_CHAT_DISPLAY, text_color=self.app.COLOR_TEXT)
        display1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.app.raw_log_displays[1] = display1

        raw_tab_2.grid_columnconfigure(0, weight=1)
        raw_tab_2.grid_rowconfigure(0, weight=1)
        display2 = ctk.CTkTextbox(raw_tab_2, wrap="word", font=self.app.FONT_CHAT, state='normal', fg_color=self.app.COLOR_CHAT_DISPLAY, text_color=self.app.COLOR_TEXT)
        display2.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.app.raw_log_displays[2] = display2
        
        return tab_view

    def _create_chat_panel(self, parent, chat_id):
        parent.grid_columnconfigure(0, weight=1); parent.grid_rowconfigure(0, weight=1)
        
        self.app.chat_displays[chat_id] = HTMLLabel(parent, background=self.app.COLOR_CHAT_DISPLAY, foreground=self.app.COLOR_TEXT, font=(self.app.FONT_CHAT.cget("family"), self.app.FONT_CHAT.cget("size")))
        self.app.chat_displays[chat_id].grid(row=0, column=0, sticky="nsew")
        self.app.chat_displays[chat_id].configure(state='normal')

        # Add scrollbar
        scrollbar = ctk.CTkScrollbar(parent, command=self.app.chat_displays[chat_id].yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.app.chat_displays[chat_id].configure(yscrollcommand=scrollbar.set)


        input_frame = ctk.CTkFrame(parent, fg_color=self.app.COLOR_INPUT_AREA); input_frame.grid(row=1, column=0, pady=(5, 0), sticky="ew"); input_frame.grid_columnconfigure(0, weight=1)
        
        self.app.user_inputs[chat_id] = ctk.CTkTextbox(input_frame, height=120, wrap="word", font=self.app.FONT_CHAT, fg_color=self.app.COLOR_CHAT_DISPLAY, border_width=1, border_color=self.app.COLOR_BORDER)
        self.app.user_inputs[chat_id].grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.app.user_inputs[chat_id].bind("<Control-Return>", lambda event, c=chat_id: self.app.chat_core.send_message(c))

        controls_frame = ctk.CTkFrame(input_frame, fg_color="transparent"); controls_frame.grid(row=0, column=1, padx=(0,10), pady=5, sticky="ns")
        self.app.send_buttons[chat_id] = ctk.CTkButton(controls_frame, text="Send", command=lambda c=chat_id: self.app.chat_core.send_message(c), font=self.app.FONT_GENERAL, width=70)
        self.app.send_buttons[chat_id].pack(pady=(0,2), fill="x")
        self.app.stop_buttons[chat_id] = ctk.CTkButton(controls_frame, text="Stop", command=lambda c=chat_id: self.app.chat_core.stop_generation(c), font=self.app.FONT_GENERAL, width=70, state="disabled")
        self.app.stop_buttons[chat_id].pack(pady=(2,10), fill="x")

        auto_reply_text = "Auto-reply to Gemini 2" if chat_id == 1 else "Auto-reply to Gemini 1"
        ctk.CTkCheckBox(controls_frame, text=auto_reply_text, variable=self.app.auto_reply_vars[chat_id], font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w")
        
        # Countdown timer label
        ctk.CTkLabel(controls_frame, textvariable=self.app.countdown_vars[chat_id], font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(5,0))

        self.app.token_info_vars[chat_id] = ctk.StringVar(value="Tokens: 0 | 0")
        ctk.CTkLabel(controls_frame, textvariable=self.app.token_info_vars[chat_id], font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor="w", pady=(10,0))
        
        self.app.progress_bars[chat_id] = ctk.CTkProgressBar(input_frame, mode='indeterminate');
        self.app.progress_bars[chat_id].grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.app.progress_bars[chat_id].grid_remove()

    def _create_right_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=self.app.SIDEBAR_WIDTH_FULL, fg_color=self.app.COLOR_SIDEBAR, corner_radius=10); sidebar.pack_propagate(False)
        toggle_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); toggle_frame.pack(fill="x", pady=5, padx=5)
        self.app.right_toggle_button = ctk.CTkButton(toggle_frame, text="▶", command=self._toggle_right_sidebar, width=25, height=25, font=self.app.FONT_GENERAL); self.app.right_toggle_button.pack(anchor="nw")
        sidebar.content_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent"); sidebar.content_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(sidebar.content_frame, text="CONFIGURATION", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.app.COLOR_TEXT).pack(pady=(0,10), padx=20, anchor="w")

        config_selector_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent")
        config_selector_frame.pack(fill="x", padx=15, pady=(0, 10))
        config_selector_frame.grid_columnconfigure(0, weight=1)

        config_display_names = [f"{c['name']} | {c['description']}" for c in self.app.config_manager.config.get('configurations', [])]
        active_display_name = config_display_names[self.app.config_manager.config.get('active_config_index', 0)]
        self.app.config_selector_var = ctk.StringVar(value=active_display_name)
        
        self.app.config_selector = ctk.CTkComboBox(config_selector_frame, values=config_display_names, variable=self.app.config_selector_var, command=self.app.config_manager._on_config_select, state="readonly")
        self.app.config_selector.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(config_selector_frame, text="Description:", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=(5,0))
        self.app.config_description_entry = ctk.CTkEntry(config_selector_frame, font=self.app.FONT_GENERAL)
        self.app.config_description_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ctk.CTkButton(config_selector_frame, text="Save to Active Config", command=self.app.config_manager._save_current_config).grid(row=3, column=0, columnspan=2, sticky="ew")
        
        ctk.CTkFrame(sidebar.content_frame, height=1, fg_color=self.app.COLOR_BORDER).pack(fill="x", padx=15, pady=10)


        model_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent"); model_frame.pack(fill="x", padx=15, pady=5); model_frame.grid_columnconfigure(0, weight=1)
        model_list = self.app.gemini_api._create_model_list_for_dropdown()
        ctk.CTkLabel(model_frame, text="Gemini 1 Model", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self.app.model_selectors[1] = ctk.CTkComboBox(model_frame, values=model_list, command=lambda e, c=1: self.app.gemini_api.on_model_change(c), font=self.app.FONT_GENERAL, dropdown_font=self.app.FONT_GENERAL, fg_color=self.app.COLOR_WIDGET_BG, border_color=self.app.COLOR_BORDER, button_color=self.app.COLOR_WIDGET_BG, dropdown_fg_color=self.app.COLOR_WIDGET_BG, state="readonly")
        self.app.model_selectors[1].grid(row=1, column=0, pady=(0,10), sticky="ew")
        ctk.CTkLabel(model_frame, text="Gemini 2 Model", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).grid(row=2, column=0, sticky="w")
        self.app.model_selectors[2] = ctk.CTkComboBox(model_frame, values=model_list, command=lambda e, c=2: self.app.gemini_api.on_model_change(c), font=self.app.FONT_GENERAL, dropdown_font=self.app.FONT_GENERAL, fg_color=self.app.COLOR_WIDGET_BG, border_color=self.app.COLOR_BORDER, button_color=self.app.COLOR_WIDGET_BG, dropdown_fg_color=self.app.COLOR_WIDGET_BG, state="readonly")
        self.app.model_selectors[2].grid(row=3, column=0, pady=(0,10), sticky="ew")
        config_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent"); config_frame.pack(fill="x", padx=15, pady=(10,5)); config_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(config_frame, text="Auto-Reply Delay (min)", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(config_frame, textvariable=self.app.delay_var, width=50, font=self.app.FONT_GENERAL, fg_color=self.app.COLOR_WIDGET_BG, border_color=self.app.COLOR_BORDER, border_width=1).grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkButton(config_frame, text="Set API Key", command=self.app.gemini_api.prompt_for_api_key, font=self.app.FONT_GENERAL).grid(row=1, column=0, columnspan=2, pady=(10,0), sticky="ew")
        self._create_model_settings_panel(sidebar.content_frame, 1)
        self._create_model_settings_panel(sidebar.content_frame, 2)
        return sidebar

    def _create_model_settings_panel(self, parent, chat_id):
        content = self._create_collapsible_frame(parent, f"Gemini {chat_id} Settings")
        ctk.CTkLabel(content, text="System Instructions", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor='w', padx=5, pady=(5,0))
        self.app.options_prompts[chat_id] = ctk.CTkTextbox(content, height=100, wrap="word", font=self.app.FONT_CHAT, fg_color=self.app.COLOR_WIDGET_BG, border_color=self.app.COLOR_BORDER, border_width=1)
        self.app.options_prompts[chat_id].pack(fill="both", padx=5, pady=2, expand=True)
        params_frame = ctk.CTkFrame(content, fg_color="transparent"); params_frame.pack(fill='x', padx=5, pady=5)
        self.app.temp_labels[chat_id] = ctk.CTkLabel(params_frame, text="Temperature: 0.00", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); self.app.temp_labels[chat_id].pack(side='left')
        ctk.CTkSlider(params_frame, from_=0, to=1, variable=self.app.temp_vars[chat_id], command=lambda v, c=chat_id: self.update_slider_label(c, 'temp')).pack(side='left', fill='x', expand=True, padx=5)
        ctk.CTkLabel(content, text="Files", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED).pack(anchor='w', padx=5, pady=(5,0))
        file_frame = ctk.CTkFrame(content, fg_color=self.app.COLOR_WIDGET_BG, border_color=self.app.COLOR_BORDER, border_width=1); file_frame.pack(fill="both", expand=True, padx=5, pady=5)
        listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, bg=self.app.COLOR_WIDGET_BG, fg=self.app.COLOR_TEXT, borderwidth=0, highlightthickness=0, font=self.app.FONT_SMALL); listbox.pack(side="left", fill="both", expand=True)
        self.app.file_lists[chat_id] = listbox
        file_buttons = ctk.CTkFrame(content, fg_color="transparent"); file_buttons.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(file_buttons, text="+", command=lambda c=chat_id: self._open_file_dialog(c), font=self.app.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_buttons, text="-", command=lambda c=chat_id: self._remove_selected_files(c), font=self.app.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_buttons, text="x", command=lambda c=chat_id: self._remove_all_files(c), font=self.app.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)

    def _create_collapsible_frame(self, parent, text):
        container = ctk.CTkFrame(parent, fg_color="transparent"); container.pack(fill="x", padx=5, pady=2)
        header = ctk.CTkFrame(container, fg_color="transparent", cursor="hand2"); header.pack(fill="x")
        chevron_label = ctk.CTkLabel(header, text="▶", font=self.app.FONT_GENERAL, text_color=self.app.COLOR_TEXT_MUTED); chevron_label.pack(side="left", padx=(10,5))
        header_label = ctk.CTkLabel(header, text=text, font=self.app.FONT_BOLD, text_color=self.app.COLOR_TEXT); header_label.pack(side="left")
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        def toggle_content(event=None):
            if content_frame.winfo_ismapped(): content_frame.pack_forget(); chevron_label.configure(text="▶")
            else: content_frame.pack(fill="x", after=header); chevron_label.configure(text="▼")
        header.bind("<Button-1>", toggle_content); header_label.bind("<Button-1>", toggle_content); chevron_label.bind("<Button-1>", toggle_content)
        return content_frame

    def _open_file_dialog(self, chat_id):
        paths = filedialog.askopenfilenames()
        if paths:
            listbox = self.app.file_lists[chat_id]
            if not hasattr(listbox, 'full_paths'): listbox.full_paths = []
            for p in paths: listbox.insert(tk.END, os.path.basename(p)); listbox.full_paths.append(p)
                
    def _remove_selected_files(self, chat_id):
        listbox = self.app.file_lists[chat_id]
        if hasattr(listbox, 'full_paths'):
            for i in reversed(listbox.curselection()): listbox.delete(i); listbox.full_paths.pop(i)

    def _remove_all_files(self, chat_id):
        listbox = self.app.file_lists[chat_id]
        if hasattr(listbox, 'full_paths'): listbox.delete(0, tk.END); listbox.full_paths = []

    def update_slider_label(self, chat_id, param_type):
        if param_type == 'temp': self.app.temp_labels[chat_id].configure(text=f"Temperature: {self.app.temp_vars[chat_id].get():.2f}")

    def _create_spinbox_entry(self, parent, textvariable, min_value, max_value, width, font):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        button_minus = ctk.CTkButton(frame, text="-", width=20, height=20, font=font, command=lambda: self._decrement_spinbox(textvariable, min_value))
        button_minus.pack(side="left", padx=(0,2))
        
        entry = ctk.CTkEntry(frame, textvariable=textvariable, width=width, font=font, justify="center")
        entry.pack(side="left")
        
        button_plus = ctk.CTkButton(frame, text="+", width=20, height=20, font=font, command=lambda: self._increment_spinbox(textvariable, max_value))
        button_plus.pack(side="left", padx=(2,0))
        
        return frame

    def _decrement_spinbox(self, textvariable, min_value):
        try:
            current_value = textvariable.get()
            if current_value > min_value:
                textvariable.set(current_value - 1)
        except ValueError:
            pass # Handle non-integer input if necessary

    def _increment_spinbox(self, textvariable, max_value):
        try:
            current_value = textvariable.get()
            if current_value < max_value:
                textvariable.set(current_value + 1)
        except ValueError:
            pass # Handle non-integer input if necessary

    def _pick_color(self, color_var, button_widget):
        color_code = colorchooser.askcolor(title="Choose color")[1]
        if color_code:
            color_var.set(color_code)
            button_widget.configure(fg_color=color_code)
            self.app.chat_core._render_chat_display(1) # Re-render both chats to apply new color
            self.app.chat_core._render_chat_display(2)