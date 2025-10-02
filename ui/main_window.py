import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkinter import filedialog, colorchooser

from .chat_pane import ChatPane
from .model_manager_window import ModelManagerWindow
from .right_sidebar_handler import RightSidebarHandler
from config.models import DisplaySettings

class Tooltip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        text = self.text_func()
        if self.tooltip_window or not text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(tw, text=text, justify='left',
                             fg_color=("#333333", "#444444"), corner_radius=5,
                             font=ctk.CTkFont(size=12), padx=8, pady=4)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class MainWindow:
    def __init__(self, app_instance):
        self.app = app_instance
        self.lang = app_instance.lang
        self.root = app_instance.root
        
        self.lang_updatable_widgets = []

        self.left_sidebar = None
        self.central_area = None
        self.status_indicator = None
        self.status_label = None
        self.mm_button = None
        self.left_toggle_button = None
        
        self.model_manager_window = None
        self.right_sidebar = RightSidebarHandler(app_instance, self)

    def create_widgets(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self._create_left_sidebar()
        self.left_sidebar.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="nsw")
        
        self._create_central_area()
        self.central_area.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.right_sidebar_frame = self.right_sidebar.create_sidebar(self.root)
        self.right_sidebar_frame.grid(row=0, column=2, padx=(0, 5), pady=5, sticky="nse")

        # --- FIXED: Correct initialization order ---
        # 1. Update all texts to their default (expanded) state first.
        self.update_all_text()
        # 2. Then, apply the initial collapsed/expanded state to the sidebars.
        self.toggle_left_sidebar(initial=True)
        self.right_sidebar.toggle_sidebar(initial=False)

    def _create_left_sidebar(self):
        self.left_sidebar = ctk.CTkFrame(self.root, width=self.app.LEFT_SIDEBAR_WIDTH_FULL, fg_color=self.app.COLOR_SIDEBAR, corner_radius=10)
        self.left_sidebar.pack_propagate(False)
        self.left_sidebar.grid_rowconfigure(1, weight=1)

        toggle_frame = ctk.CTkFrame(self.left_sidebar, fg_color="transparent")
        toggle_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.left_toggle_button = ctk.CTkButton(toggle_frame, text="▶", command=self.toggle_left_sidebar, width=25, height=25, font=self.app.FONT_GENERAL)
        self.left_toggle_button.pack(anchor="ne")

        self.left_sidebar.content_frame = ctk.CTkFrame(self.left_sidebar, fg_color="transparent")
        self.left_sidebar.content_frame.grid(row=1, column=0, sticky="nsew")

        widget = ctk.CTkLabel(self.left_sidebar.content_frame, text="", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.app.COLOR_TEXT)
        widget.pack(pady=(0, 20), padx=20, anchor="w")
        self.lang_updatable_widgets.append((widget, 'studio'))

        self._create_session_management_panel(self.left_sidebar.content_frame)
        self._create_display_panel(self.left_sidebar.content_frame)

        footer_frame = ctk.CTkFrame(self.left_sidebar, fg_color="transparent")
        footer_frame.grid(row=2, column=0, sticky="ew", pady=10)

        status_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=5)
        self.status_indicator = ctk.CTkLabel(status_frame, text="●", font=ctk.CTkFont(size=20), text_color="gray")
        self.status_indicator.pack(side="left")
        
        self.status_label = ctk.CTkLabel(status_frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        self.status_label.pack(side="left", padx=5)
        self.lang_updatable_widgets.append((self.status_label, 'status'))

        self.status_tooltip = Tooltip(status_frame, lambda: self.lang.get('status_tooltip'))

        self.mm_button = ctk.CTkButton(footer_frame, text="", command=self.open_model_manager, width=140) # Set default expanded width
        self.mm_button.pack(fill="x", padx=15, pady=5)
        self.lang_updatable_widgets.append((self.mm_button, 'model_manager'))
    
    def _create_session_management_panel(self, parent):
        frame, header_label = self._create_collapsible_frame(parent, "session_management")
        self.lang_updatable_widgets.append((header_label, 'session_management'))
        
        session_widgets = [
            ('new_session', self.app.chat_core.new_session),
            ('save_ai_1', lambda: self.app.chat_core.save_session(1)),
            ('save_ai_2', lambda: self.app.chat_core.save_session(2)),
            ('load_ai_1', lambda: self.app.chat_core.load_session(1)),
            ('load_ai_2', lambda: self.app.chat_core.load_session(2)),
        ]
        for key, command in session_widgets:
            widget = ctk.CTkButton(frame, text="", command=command, fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL)
            widget.pack(fill="x", padx=15)
            self.lang_updatable_widgets.append((widget, key))

        ctk.CTkFrame(frame, height=1, fg_color=self.app.COLOR_BORDER).pack(fill="x", padx=15, pady=5)
        
        export_widgets = [
            ('export_ai_1', lambda: self.app.chat_core.export_conversation(1)),
            ('export_ai_2', lambda: self.app.chat_core.export_conversation(2)),
            ('smart_export_ai_1', lambda: self.app.chat_core.smart_export(1)),
            ('smart_export_ai_2', lambda: self.app.chat_core.smart_export(2)),
        ]
        for key, command in export_widgets:
            widget = ctk.CTkButton(frame, text="", command=command, fg_color="transparent", text_color=self.app.COLOR_TEXT, anchor="w", font=self.app.FONT_GENERAL)
            widget.pack(fill="x", padx=15, pady=(0, 5))
            self.lang_updatable_widgets.append((widget, key))

    def _create_display_panel(self, parent):
        frame, header_label = self._create_collapsible_frame(parent, "display")
        self.lang_updatable_widgets.append((header_label, 'display'))
        
        lang_frame = ctk.CTkFrame(frame, fg_color="transparent")
        lang_frame.pack(fill="x", padx=15, pady=(5, 10))
        lang_label = ctk.CTkLabel(lang_frame, text="")
        lang_label.pack(side="left", padx=(0, 5))
        self.lang_updatable_widgets.append((lang_label, 'language'))
        self.lang_selector = ctk.CTkSegmentedButton(lang_frame, values=["en", "zh"], command=self.on_lang_change)
        self.lang_selector.set(self.app.lang.language)
        self.lang_selector.pack(side="left")

        self._create_spinbox(frame, 'speaker_font_size', self.app.speaker_font_size_var, 6, 30)
        self._create_spinbox(frame, 'chat_font_size', self.app.chat_font_size_var, 6, 30)

        widget = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        widget.pack(anchor="w", padx=15, pady=(10, 0))
        self.lang_updatable_widgets.append((widget, 'chat_colors'))
        
        color_container = ctk.CTkFrame(frame, fg_color="transparent")
        color_container.pack(fill="x", padx=15, pady=(0, 5))

        self._create_color_picker(color_container, 'user_name', self.app.user_name_color_var)
        self._create_color_picker(color_container, 'user_message', self.app.user_message_color_var)
        self._create_color_picker(color_container, 'ai_name', self.app.ai_name_color_var)
        self._create_color_picker(color_container, 'ai_message', self.app.ai_message_color_var)

        restore_btn = ctk.CTkButton(frame, text="", command=self._restore_display_defaults)
        restore_btn.pack(fill="x", padx=15, pady=(10, 0))
        self.lang_updatable_widgets.append((restore_btn, 'restore_defaults'))

    def _create_central_area(self):
        self.central_area = ctk.CTkTabview(self.root, fg_color=self.app.COLOR_INPUT_AREA)
        tab1 = self.central_area.add("AI 1")
        tab2 = self.central_area.add("AI 2")
        self.app.chat_panes[1] = ChatPane(self.app, 1, tab1)
        self.app.chat_panes[2] = ChatPane(self.app, 2, tab2)
        raw_tab_1 = self.central_area.add("AI 1 (Raw)")
        raw_tab_2 = self.central_area.add("AI 2 (Raw)")
        self._create_raw_log_panel(raw_tab_1, 1)
        self._create_raw_log_panel(raw_tab_2, 2)
        return self.central_area

    def _create_raw_log_panel(self, parent, chat_id):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        display = ctk.CTkTextbox(parent, wrap="word", font=self.app.FONT_CHAT, state='normal', fg_color=self.app.COLOR_CHAT_DISPLAY, text_color=self.app.COLOR_TEXT)
        display.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.app.raw_log_displays[chat_id] = display

    def _create_collapsible_frame(self, parent, text_key):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=5, pady=2)
        header = ctk.CTkFrame(container, fg_color="transparent", cursor="hand2")
        header.pack(fill="x")
        chevron_label = ctk.CTkLabel(header, text="▶", font=self.app.FONT_GENERAL, text_color=self.app.COLOR_TEXT_MUTED)
        chevron_label.pack(side="left", padx=(10,5))
        header_label = ctk.CTkLabel(header, text="", font=self.app.FONT_BOLD, text_color=self.app.COLOR_TEXT)
        header_label.pack(side="left")
        
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        
        def toggle_content(event=None):
            if content_frame.winfo_ismapped():
                content_frame.pack_forget()
                chevron_label.configure(text="▶")
            else:
                content_frame.pack(fill="x", after=header)
                chevron_label.configure(text="▼")
        
        header.bind("<Button-1>", toggle_content)
        header_label.bind("<Button-1>", toggle_content)
        chevron_label.bind("<Button-1>", toggle_content)
        
        return content_frame, header_label

    def _create_spinbox(self, parent, label_key, int_var, min_val, max_val):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(5,0))
        
        label = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        label.pack(side="left", padx=(0,5))
        self.lang_updatable_widgets.append((label, label_key))
        
        spinbox_frame = ctk.CTkFrame(frame, fg_color="transparent")
        spinbox_frame.pack(side="left")

        def decrement():
            if int_var.get() > min_val: int_var.set(int_var.get() - 1)
        def increment():
            if int_var.get() < max_val: int_var.set(int_var.get() + 1)

        ctk.CTkButton(spinbox_frame, text="-", width=20, height=20, font=self.app.FONT_GENERAL, command=decrement).pack(side="left")
        entry = ctk.CTkEntry(spinbox_frame, textvariable=int_var, width=40, justify="center", font=self.app.FONT_GENERAL)
        entry.pack(side="left", padx=2)
        ctk.CTkButton(spinbox_frame, text="+", width=20, height=20, font=self.app.FONT_GENERAL, command=increment).pack(side="left")
        
    def _create_color_picker(self, parent, label_key, string_var):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        label = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED, width=120, anchor="w")
        label.pack(side="left", padx=(0, 10))
        self.lang_updatable_widgets.append((label, label_key))
        
        color_button = ctk.CTkButton(frame, text="", fg_color=string_var.get(), width=50, height=25, corner_radius=5, border_width=1, border_color="gray50")
        color_button.pack(side="left")
        
        def pick_color():
            title_text = self.lang.get('choose_color')
            color_code = colorchooser.askcolor(title=title_text, initialcolor=string_var.get())[1]
            if color_code:
                string_var.set(color_code)
        
        color_button.configure(command=pick_color)
        string_var.trace_add("write", lambda *args: color_button.configure(fg_color=string_var.get()))

    def _restore_display_defaults(self):
        if not messagebox.askyesno(self.lang.get('confirm'), self.lang.get('confirm_restore_defaults')):
            return
        
        defaults = DisplaySettings()
        self.app.chat_font_size_var.set(defaults.chat_font_size)
        self.app.speaker_font_size_var.set(defaults.speaker_font_size)
        self.app.user_name_color_var.set(defaults.user_name_color)
        self.app.user_message_color_var.set(defaults.user_message_color)
        self.app.ai_name_color_var.set(defaults.ai_name_color)
        self.app.ai_message_color_var.set(defaults.ai_message_color)
        
        self.app.config_manager.save_display_settings()
        messagebox.showinfo(self.lang.get('success'), self.lang.get('defaults_restored'))

    def on_lang_change(self, lang):
        self.app.lang.set_language(lang)
        self.app.config_manager.save_language_setting(lang)
        self.update_all_text()

    def update_all_text(self):
        for widget, key, *args in self.lang_updatable_widgets:
            if widget and widget.winfo_exists():
                widget.configure(text=self.lang.get(key, *args))
        for pane in self.app.chat_panes.values():
            pane.update_text()
        if self.model_manager_window and self.model_manager_window.winfo_exists():
            self.model_manager_window.update_text()
        self.right_sidebar.update_all_text()

    def toggle_left_sidebar(self, initial=False):
        is_expanded = self.left_sidebar.cget('width') == self.app.LEFT_SIDEBAR_WIDTH_FULL
        if initial: is_expanded = True
        
        if is_expanded:
            self.left_sidebar.content_frame.grid_remove()
            self.left_sidebar.configure(width=self.app.SIDEBAR_WIDTH_COLLAPSED)
            self.left_toggle_button.configure(text="▶")
            self.status_label.pack_forget()
            self.mm_button.configure(text="M", width=25)
        else:
            self.left_sidebar.configure(width=self.app.LEFT_SIDEBAR_WIDTH_FULL)
            self.left_sidebar.content_frame.grid()
            self.left_toggle_button.configure(text="◀")
            self.status_label.pack(side="left", padx=5)
            self.mm_button.configure(text=self.lang.get('model_manager'), width=140)

    def open_model_manager(self):
        if self.model_manager_window is None or not self.model_manager_window.winfo_exists():
            self.model_manager_window = ModelManagerWindow(self.app)
            self.model_manager_window.grab_set()
        else:
            self.model_manager_window.focus()

    def update_status_indicator(self):
        google_provider = self.app.state_manager.get_provider("Google")
        ollama_provider = self.app.state_manager.get_provider("Ollama")
        
        is_google_error = False
        if google_provider and google_provider.is_configured():
            statuses = [s.get("is_valid") for s in google_provider.key_statuses.values()]
            if statuses and not any(statuses):
                is_google_error = True

        is_ollama_error = False
        if ollama_provider and ollama_provider.is_configured():
            if not ollama_provider.get_status().get("is_available"):
                is_ollama_error = True

        if is_google_error or is_ollama_error:
            self.status_indicator.configure(text_color="red")
        elif not (google_provider and google_provider.is_configured()) and not (ollama_provider and ollama_provider.is_configured()):
            self.status_indicator.configure(text_color="yellow")
        else:
            self.status_indicator.configure(text_color="green")
            
    def apply_config_to_ui(self, config_profile, startup=False):
        self.right_sidebar.apply_global_config_profile(config_profile, startup=startup)