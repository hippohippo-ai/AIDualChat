# --- START OF UPDATED ui_elements.py ---

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog, colorchooser
import os
from chat_pane import ChatPane

class UIElements:
    def __init__(self, app_instance, callbacks):
        self.app = app_instance
        self.callbacks = callbacks
        self.lang = app_instance.lang
        self.lang_updatable_widgets = []

    def create_widgets(self):
        self.app.root.grid_columnconfigure(1, weight=1)
        self.app.root.grid_rowconfigure(0, weight=1)
        self.app.left_sidebar = self._create_left_sidebar(self.app.root)
        self.app.left_sidebar.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="nsw")
        self.app.central_area = self._create_central_area(self.app.root)
        self.app.central_area.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.app.right_sidebar = self._create_right_sidebar(self.app.root)
        self.app.right_sidebar.grid(row=0, column=2, padx=(0, 5), pady=5, sticky="nse")
        self._toggle_left_sidebar()
        self.update_all_text()

    def _create_right_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=self.app.RIGHT_SIDEBAR_WIDTH_FULL, fg_color=self.app.COLOR_SIDEBAR, corner_radius=10)
        sidebar.pack_propagate(False)
        
        # Create the toggle button directly on the sidebar, so it's always visible
        toggle_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        toggle_frame.pack(fill="x", pady=5, padx=5)
        self.app.right_toggle_button = ctk.CTkButton(toggle_frame, text="▶", command=self._toggle_right_sidebar, width=25, height=25, font=self.app.FONT_GENERAL)
        self.app.right_toggle_button.pack(anchor="nw")

        # This main content_frame is now a regular frame that will be toggled
        sidebar.content_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        
        # --- Top Section (Fixed) ---
        top_fixed_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent")
        top_fixed_frame.pack(fill="x", padx=0, pady=0)

        widget = ctk.CTkLabel(top_fixed_frame, text="", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.app.COLOR_TEXT)
        widget.pack(pady=(0,10), padx=20, anchor="w")
        self.lang_updatable_widgets.append((widget, 'configuration'))
        
        self._create_configuration_selector_panel(top_fixed_frame)

        # --- Separator ---
        ctk.CTkFrame(sidebar.content_frame, height=2, fg_color=self.app.COLOR_BORDER).pack(fill="x", padx=15, pady=10)

        # --- Bottom Section (Scrollable) ---
        bottom_scrollable_frame = ctk.CTkScrollableFrame(sidebar.content_frame, fg_color="transparent")
        bottom_scrollable_frame.pack(fill="both", expand=True)

        self._create_model_selector_panel(bottom_scrollable_frame)
        self._create_global_settings_panel(bottom_scrollable_frame)
        self._create_model_settings_panel(bottom_scrollable_frame, 1)
        self._create_model_settings_panel(bottom_scrollable_frame, 2)
        
        # Initially pack the content frame so it's visible
        sidebar.content_frame.pack(fill="both", expand=True)
        
        return sidebar

    def _on_lang_change(self, lang):
        self.lang.set_language(lang)
        self.app.config_manager.save_language_setting(lang)
        self.update_all_text()

    def update_all_text(self):
        # Update widgets managed by UIElements
        for widget, key, *args in self.lang_updatable_widgets:
            if widget.winfo_exists():
                widget.configure(text=self.lang.get(key).format(*args))
        
        # Delegate text updates to each ChatPane instance
        for pane in self.app.chat_panes.values():
            pane.update_text()
        
        # Update widgets that need special formatting
        self.update_slider_label(1, 'temp')
        self.update_slider_label(2, 'temp')

    def _toggle_left_sidebar(self):
        is_expanded = self.app.left_sidebar.cget('width') == self.app.LEFT_SIDEBAR_WIDTH_FULL
        if is_expanded: self.app.left_sidebar.content_frame.pack_forget(); self.app.left_sidebar.configure(width=self.app.SIDEBAR_WIDTH_COLLAPSED); self.app.left_toggle_button.configure(text="▶")
        else: self.app.left_sidebar.configure(width=self.app.LEFT_SIDEBAR_WIDTH_FULL); self.app.left_sidebar.content_frame.pack(fill="x", before=self.app.left_sidebar.spacer); self.app.left_toggle_button.configure(text="◀")
        
    def _toggle_right_sidebar(self):
        sidebar = self.app.right_sidebar
        is_expanded = sidebar.cget('width') == self.app.RIGHT_SIDEBAR_WIDTH_FULL
        
        if is_expanded:
            # Hide content, shrink sidebar, change button text
            sidebar.content_frame.pack_forget()
            sidebar.configure(width=self.app.SIDEBAR_WIDTH_COLLAPSED)
            self.app.right_toggle_button.configure(text="◀")
        else:
            # Expand sidebar, show content, change button text
            sidebar.configure(width=self.app.RIGHT_SIDEBAR_WIDTH_FULL)
            # Make sure content appears after the toggle button's frame
            sidebar.content_frame.pack(fill="both", expand=True)
            self.app.right_toggle_button.configure(text="▶")
    
    def _create_left_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=self.app.LEFT_SIDEBAR_WIDTH_FULL, fg_color=self.app.COLOR_SIDEBAR, corner_radius=10); sidebar.pack_propagate(False)
        toggle_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); toggle_frame.pack(fill="x", pady=5, padx=5)
        self.app.left_toggle_button = ctk.CTkButton(toggle_frame, text="◀", command=self._toggle_left_sidebar, width=25, height=25, font=self.app.FONT_GENERAL); self.app.left_toggle_button.pack(anchor="ne")
        sidebar.content_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); sidebar.content_frame.pack(fill="x")
        widget = ctk.CTkLabel(sidebar.content_frame, text="", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.app.COLOR_TEXT); widget.pack(pady=(0,20), padx=20, anchor="w")
        self.lang_updatable_widgets.append((widget, 'studio'))
        self._create_session_management_panel(sidebar.content_frame)
        self._create_display_panel(sidebar.content_frame)
        sidebar.spacer = ctk.CTkFrame(sidebar, fg_color="transparent"); sidebar.spacer.pack(expand=True, fill="y")
        return sidebar

    def _create_session_management_panel(self, parent):
        frame, header_label = self._create_collapsible_frame(parent, "session_management")
        self.lang_updatable_widgets.append((header_label, 'session_management'))
        widgets_to_add = [
            ('new_session', self.callbacks['on_new_session']), ('save_gemini_1', lambda: self.callbacks['on_save_session'](1)),
            ('save_gemini_2', lambda: self.callbacks['on_save_session'](2)), ('load_gemini_1', lambda: self.callbacks['on_load_session'](1)),
            ('load_gemini_2', lambda: self.callbacks['on_load_session'](2)),
        ]
        for key, command in widgets_to_add:
            widget = ctk.CTkButton(frame, text="", command=command, fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL); widget.pack(fill="x", padx=15)
            self.lang_updatable_widgets.append((widget, key))
        ctk.CTkFrame(frame, height=1, fg_color=self.app.COLOR_BORDER).pack(fill="x", padx=15, pady=5)
        export_widgets = [
            ('export_gemini_1', lambda: self.callbacks['on_export_conversation'](1)), ('export_gemini_2', lambda: self.callbacks['on_export_conversation'](2)),
            ('smart_export_g1', lambda: self.callbacks['on_smart_export'](1)), ('smart_export_g2', lambda: self.callbacks['on_smart_export'](2)),
        ]
        for key, command in export_widgets:
            widget = ctk.CTkButton(frame, text="", command=command, fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL); widget.pack(fill="x", padx=15, pady=(0,5))
            self.lang_updatable_widgets.append((widget, key))

    def _create_display_panel(self, parent):
        frame, header_label = self._create_collapsible_frame(parent, "display")
        self.lang_updatable_widgets.append((header_label, 'display'))
        lang_frame = ctk.CTkFrame(frame, fg_color="transparent"); lang_frame.pack(fill="x", padx=15, pady=(5,10))
        lang_label = ctk.CTkLabel(lang_frame, text=""); lang_label.pack(side="left", padx=(0,5))
        self.lang_updatable_widgets.append((lang_label, 'language'))
        self.lang_selector = ctk.CTkSegmentedButton(lang_frame, values=["en", "zh"], command=self._on_lang_change)
        self.lang_selector.set(self.app.lang.language)
        self.lang_selector.pack(side="left")
        font_size_frame_name = ctk.CTkFrame(frame, fg_color="transparent"); font_size_frame_name.pack(fill="x", padx=15, pady=(5,0))
        widget = ctk.CTkLabel(font_size_frame_name, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.pack(side="left", padx=(0,5))
        self.lang_updatable_widgets.append((widget, 'name_font_size'))
        self.name_font_size_spinbox = self._create_spinbox_entry(font_size_frame_name, self.app.speaker_font_size_var, 6, 30, 40, self.app.FONT_GENERAL); self.name_font_size_spinbox.pack(side="left")
        font_size_frame_chat = ctk.CTkFrame(frame, fg_color="transparent"); font_size_frame_chat.pack(fill="x", padx=15, pady=(0,5))
        widget = ctk.CTkLabel(font_size_frame_chat, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.pack(side="left", padx=(0,5))
        self.lang_updatable_widgets.append((widget, 'chat_font_size'))
        self.chat_font_size_spinbox = self._create_spinbox_entry(font_size_frame_chat, self.app.chat_font_size_var, 6, 30, 40, self.app.FONT_GENERAL); self.chat_font_size_spinbox.pack(side="left")
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.pack(anchor="w", padx=15, pady=(10,0))
        self.lang_updatable_widgets.append((widget, 'chat_colors'))
        color_grid_frame = ctk.CTkFrame(frame, fg_color="transparent"); color_grid_frame.pack(fill="x", padx=15, pady=(0,5)); color_grid_frame.grid_columnconfigure(0, weight=1); color_grid_frame.grid_columnconfigure(1, weight=1)
        def create_color_picker(parent, grid_row, grid_col, label_key, color_var):
            f = ctk.CTkFrame(parent, fg_color="transparent"); f.grid(row=grid_row, column=grid_col, sticky="nsew", padx=5, pady=5)
            lbl = ctk.CTkLabel(f, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); lbl.pack()
            self.lang_updatable_widgets.append((lbl, label_key))
            btn = ctk.CTkButton(f, text="", fg_color=color_var.get(), width=50, height=25, command=lambda: self._pick_color(color_var, btn)); btn.pack()
            return btn
        self.user_name_color_button = create_color_picker(color_grid_frame, 0, 0, 'user_name', self.app.user_name_color_var)
        self.user_message_color_button = create_color_picker(color_grid_frame, 0, 1, 'user_message', self.app.user_message_color_var)
        self.gemini_name_color_button = create_color_picker(color_grid_frame, 1, 0, 'gemini_name', self.app.gemini_name_color_var)
        self.gemini_message_color_button = create_color_picker(color_grid_frame, 1, 1, 'gemini_message', self.app.gemini_message_color_var)
        widget = ctk.CTkButton(frame, text="", command=self.callbacks['on_restore_display_defaults'], font=self.app.FONT_GENERAL); widget.pack(fill="x", padx=15, pady=(10,0))
        self.lang_updatable_widgets.append((widget, 'restore_defaults'))

    def _create_central_area(self, parent):
        tab_view = ctk.CTkTabview(parent, fg_color=self.app.COLOR_INPUT_AREA); tab_view.grid(row=0, column=0, sticky="nsew")
        self.app.central_tab_view = tab_view
        tab1 = tab_view.add("Gemini 1"); tab2 = tab_view.add("Gemini 2")
        self.app.chat_panes[1] = ChatPane(self.app, 1, tab1)
        self.app.chat_panes[2] = ChatPane(self.app, 2, tab2)
        raw_tab_1 = tab_view.add("Gemini 1 (Raw)"); raw_tab_2 = tab_view.add("Gemini 2 (Raw)")
        self._create_raw_log_panel(raw_tab_1, 1); self._create_raw_log_panel(raw_tab_2, 2)
        return tab_view

    def _create_raw_log_panel(self, parent, chat_id):
        parent.grid_columnconfigure(0, weight=1); parent.grid_rowconfigure(0, weight=1)
        display = ctk.CTkTextbox(parent, wrap="word", font=self.app.FONT_CHAT, state='normal', fg_color=self.app.COLOR_CHAT_DISPLAY, text_color=self.app.COLOR_TEXT)
        display.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.app.raw_log_displays[chat_id] = display
    
    def _create_configuration_selector_panel(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=15, pady=(0, 10)); frame.grid_columnconfigure(0, weight=1)
        config_display_names = [f"{c['name']} | {c['description']}" for c in self.app.config_manager.config.get('configurations', [])]
        active_display_name = config_display_names[self.app.config_manager.config.get('active_config_index', 0)]
        self.app.config_selector_var = ctk.StringVar(value=active_display_name)
        self.app.config_selector = ctk.CTkComboBox(frame, values=config_display_names, variable=self.app.config_selector_var, command=self.callbacks['on_config_select'], state="readonly")
        self.app.config_selector.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.grid(row=1, column=0, sticky="w", pady=(5,0))
        self.lang_updatable_widgets.append((widget, 'description'))
        self.app.config_description_entry = ctk.CTkEntry(frame, font=self.app.FONT_GENERAL); self.app.config_description_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        widget = ctk.CTkButton(frame, text="", command=self.callbacks['on_save_current_config']); widget.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.lang_updatable_widgets.append((widget, 'save_active_config'))
    
    def _create_model_selector_panel(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=15, pady=5); frame.grid_columnconfigure(0, weight=1)
        model_list = self.app.gemini_api._create_model_list_for_dropdown()
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.grid(row=0, column=0, sticky="w")
        self.lang_updatable_widgets.append((widget, 'gemini_1_model'))
        self.app.model_selectors[1] = ctk.CTkComboBox(frame, values=model_list, command=lambda e, c=1: self.app.gemini_api.on_model_change(c), font=self.app.FONT_GENERAL, dropdown_font=self.app.FONT_GENERAL, state="readonly")
        self.app.model_selectors[1].grid(row=1, column=0, pady=(0,10), sticky="ew")
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.grid(row=2, column=0, sticky="w")
        self.lang_updatable_widgets.append((widget, 'gemini_2_model'))
        self.app.model_selectors[2] = ctk.CTkComboBox(frame, values=model_list, command=lambda e, c=2: self.app.gemini_api.on_model_change(c), font=self.app.FONT_GENERAL, dropdown_font=self.app.FONT_GENERAL, state="readonly")
        self.app.model_selectors[2].grid(row=3, column=0, pady=(0,10), sticky="ew")

    def _create_global_settings_panel(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=15, pady=(10,5)); frame.grid_columnconfigure(1, weight=1)
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.grid(row=0, column=0, sticky="w")
        self.lang_updatable_widgets.append((widget, 'auto_reply_delay'))
        ctk.CTkEntry(frame, textvariable=self.app.delay_var, width=50, font=self.app.FONT_GENERAL).grid(row=0, column=1, sticky="w", padx=10)
        widget = ctk.CTkButton(frame, text="", command=self.app.gemini_api.prompt_for_api_key, font=self.app.FONT_GENERAL); widget.grid(row=1, column=0, columnspan=2, pady=(10,0), sticky="ew")
        self.lang_updatable_widgets.append((widget, 'set_api_key'))

    def _create_model_settings_panel(self, parent, chat_id):
        frame, header_label = self._create_collapsible_frame(parent, "gemini_settings", chat_id)
        self.lang_updatable_widgets.append((header_label, 'gemini_settings', chat_id))
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.pack(anchor='w', padx=5, pady=(5,0))
        self.lang_updatable_widgets.append((widget, 'persona'))
        self.app.options_prompts[chat_id] = ctk.CTkTextbox(frame, height=100, wrap="word", font=self.app.FONT_CHAT)
        self.app.options_prompts[chat_id].pack(fill="x", padx=5, pady=2, expand=True)
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.pack(anchor='w', padx=5, pady=(5,0))
        self.lang_updatable_widgets.append((widget, 'context'))
        self.app.context_prompts[chat_id] = ctk.CTkTextbox(frame, height=120, wrap="word", font=self.app.FONT_CHAT)
        self.app.context_prompts[chat_id].pack(fill="x", padx=5, pady=2, expand=True)
        params_frame = ctk.CTkFrame(frame, fg_color="transparent"); params_frame.pack(fill='x', padx=5, pady=5)
        self.app.temp_labels[chat_id] = ctk.CTkLabel(params_frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); self.app.temp_labels[chat_id].pack(side='left')
        self.update_slider_label(chat_id, 'temp')
        ctk.CTkSlider(params_frame, from_=0, to=1, variable=self.app.temp_vars[chat_id], command=lambda v, c=chat_id: self.update_slider_label(c, 'temp')).pack(side='left', fill='x', expand=True, padx=5)
        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED); widget.pack(anchor='w', padx=5, pady=(5,0))
        self.lang_updatable_widgets.append((widget, 'files'))
        file_frame = ctk.CTkFrame(frame, fg_color=self.app.COLOR_WIDGET_BG, border_color=self.app.COLOR_BORDER, border_width=1); file_frame.pack(fill="both", expand=True, padx=5, pady=5)
        listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, bg=self.app.COLOR_WIDGET_BG, fg=self.app.COLOR_TEXT, borderwidth=0, highlightthickness=0, font=self.app.FONT_SMALL); listbox.pack(side="left", fill="both", expand=True)
        pane = self.app.chat_panes.get(chat_id)
        if pane: pane.file_listbox = listbox
        file_buttons = ctk.CTkFrame(frame, fg_color="transparent"); file_buttons.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(file_buttons, text="+", command=lambda c=chat_id: self._open_file_dialog(c), font=self.app.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_buttons, text="-", command=lambda c=chat_id: self._remove_selected_files(c), font=self.app.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_buttons, text="x", command=lambda c=chat_id: self._remove_all_files(c), font=self.app.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)

    def _create_collapsible_frame(self, parent, text_key, *args):
        container = ctk.CTkFrame(parent, fg_color="transparent"); container.pack(fill="x", padx=5, pady=2)
        header = ctk.CTkFrame(container, fg_color="transparent", cursor="hand2"); header.pack(fill="x")
        chevron_label = ctk.CTkLabel(header, text="▶", font=self.app.FONT_GENERAL, text_color=self.app.COLOR_TEXT_MUTED); chevron_label.pack(side="left", padx=(10,5))
        header_label = ctk.CTkLabel(header, text="", font=self.app.FONT_BOLD, text_color=self.app.COLOR_TEXT); header_label.pack(side="left")
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        def toggle_content(event=None):
            if content_frame.winfo_ismapped(): content_frame.pack_forget(); chevron_label.configure(text="▶")
            else: content_frame.pack(fill="x", after=header); chevron_label.configure(text="▼")
        header.bind("<Button-1>", toggle_content); header_label.bind("<Button-1>", toggle_content); chevron_label.bind("<Button-1>", toggle_content)
        return content_frame, header_label

    def update_slider_label(self, chat_id, param_type):
        if param_type == 'temp':
            if chat_id in self.app.temp_labels and self.app.temp_labels[chat_id].winfo_exists():
                temp_text = self.lang.get('temperature').format(self.app.temp_vars[chat_id].get())
                self.app.temp_labels[chat_id].configure(text=temp_text)
                
    def _open_file_dialog(self, chat_id):
        paths = filedialog.askopenfilenames()
        if paths:
            pane = self.app.chat_panes[chat_id]
            for p in paths:
                pane.file_listbox.insert(tk.END, os.path.basename(p))
                pane.file_listbox_paths.append(p)
    def _remove_selected_files(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        selected_indices = pane.file_listbox.curselection()
        for i in reversed(selected_indices):
            pane.file_listbox.delete(i)
            pane.file_listbox_paths.pop(i)
    def _remove_all_files(self, chat_id):
        pane = self.app.chat_panes[chat_id]
        pane.file_listbox.delete(0, tk.END)
        pane.file_listbox_paths.clear()
    def _create_spinbox_entry(self, parent, textvariable, min_value, max_value, width, font):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_minus = ctk.CTkButton(frame, text="-", width=20, height=20, font=font, command=lambda: self._decrement_spinbox(textvariable, min_value)); button_minus.pack(side="left", padx=(0,2))
        entry = ctk.CTkEntry(frame, width=width, font=font, justify="center"); entry.pack(side="left")
        entry.insert(0, str(textvariable.get()))
        def on_textvariable_change(*args):
            if entry.winfo_exists():
                entry.delete(0, tk.END); entry.insert(0, str(textvariable.get()))
        textvariable.trace_add("write", on_textvariable_change)
        def validate_and_set_value(event=None):
            try:
                val_str = entry.get()
                if val_str:
                    is_int = isinstance(textvariable, ctk.IntVar)
                    new_val = int(float(val_str)) if is_int else float(val_str)
                    new_val = max(min_value, min(new_val, max_value))
                    if textvariable.get() != new_val: textvariable.set(new_val)
                else:
                    if textvariable.get() != min_value: textvariable.set(min_value)
            except (ValueError, tk.TclError):
                if entry.winfo_exists():
                    entry.delete(0, tk.END); entry.insert(0, str(textvariable.get()))
        entry.bind("<Return>", validate_and_set_value)
        entry.bind("<FocusOut>", validate_and_set_value)
        button_plus = ctk.CTkButton(frame, text="+", width=20, height=20, font=font, command=lambda: self._increment_spinbox(textvariable, max_value)); button_plus.pack(side="left", padx=(2,0))
        return frame
    def _decrement_spinbox(self, textvariable, min_value):
        try:
            current_value = textvariable.get()
            if current_value > min_value: textvariable.set(current_value - 1)
        except ValueError: pass
    def _increment_spinbox(self, textvariable, max_value):
        try:
            current_value = textvariable.get()
            if current_value < max_value: textvariable.set(current_value + 1)
        except ValueError: pass
    def _pick_color(self, color_var, button_widget):
        color_code = colorchooser.askcolor(title="Choose color")[1]
        if color_code:
            color_var.set(color_code)
            button_widget.configure(fg_color=color_code)

# --- END OF FINAL, FULLY CORRECTED ui_elements.py ---