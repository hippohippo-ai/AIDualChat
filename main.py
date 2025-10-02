import customtkinter as ctk
from tkinter import messagebox
import os
from datetime import datetime
import queue
import structlog

from utils.logging_config import setup_logging
from utils.language import LanguageManager
from config.config_manager import ConfigManager
from services.state_manager import StateManager
from core.chat_core import ChatCore
from ui.main_window import MainWindow

class AIDualChatApp:
    def __init__(self, root):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title("AI Dual Chat")
        self.root.geometry("1600x900")
        self.root.minsize(1200, 800)

        # --- UI Styling ---
        self.COLOR_BACKGROUND = "#1E1F22"
        self.COLOR_SIDEBAR = "#282A2E"
        self.COLOR_INPUT_AREA = "#282A2E"
        self.COLOR_CHAT_DISPLAY = "#1E1F22"
        self.COLOR_WIDGET_BG = "#3C3F44"
        self.COLOR_TEXT = "#FFFFFF"
        self.COLOR_TEXT_MUTED = "#B0B0B0"
        self.COLOR_BORDER = "#4E5157"
        self.FONT_GENERAL = ctk.CTkFont(family="Roboto", size=14)
        self.FONT_BOLD = ctk.CTkFont(family="Roboto", size=14, weight="bold")
        self.FONT_SMALL = ctk.CTkFont(family="Roboto", size=12)
        self.FONT_CHAT = ctk.CTkFont(family="Consolas", size=12)
        root.configure(fg_color=self.COLOR_BACKGROUND)

        self.LEFT_SIDEBAR_WIDTH_FULL = 240
        self.RIGHT_SIDEBAR_WIDTH_FULL = 300
        self.SIDEBAR_WIDTH_COLLAPSED = 40

        # --- Core Components ---
        self.logger = structlog.get_logger()
        self.lang = LanguageManager()
        self.response_queue = queue.Queue()
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # --- State and Service Initialization ---
        self.config_manager = ConfigManager(self)
        self.config_model = self.config_manager.load_config()
        self.lang.set_language(self.config_model.language)

        self.state_manager = StateManager(self, self.config_model)
        self.state_manager.start_background_refresh()

        self.chat_core = ChatCore(self)

        # --- UI Variables ---
        self.delay_var = ctk.StringVar(value=str(self.config_model.auto_reply_delay_minutes))
        self.chat_font_size_var = ctk.IntVar(value=self.config_model.display_settings.chat_font_size)
        self.speaker_font_size_var = ctk.IntVar(value=self.config_model.display_settings.speaker_font_size)
        self.user_name_color_var = ctk.StringVar(value=self.config_model.display_settings.user_name_color)
        self.user_message_color_var = ctk.StringVar(value=self.config_model.display_settings.user_message_color)
        self.ai_name_color_var = ctk.StringVar(value=self.config_model.display_settings.ai_name_color)
        self.ai_message_color_var = ctk.StringVar(value=self.config_model.display_settings.ai_message_color)

        # --- UI Element Dictionaries ---
        self.chat_panes = {}
        self.raw_log_displays = {}
        # Right sidebar widgets are dynamically created and managed in MainWindow and its delegates
        self.active_ai_config = {
            1: {"provider": None, "model": None, "key_id": None, "preset_id": None},
            2: {"provider": None, "model": None, "key_id": None, "preset_id": None}
        }

        # --- Build UI ---
        self.main_window = MainWindow(self)
        self.main_window.create_widgets()

        # --- Final Setup ---
        self.main_window.apply_config_to_ui(self.config_model.get_active_configuration(), startup=True)
        self._on_display_setting_change() # Initial render

        # Bind events
        self.chat_font_size_var.trace_add("write", self._on_display_setting_change_and_save)
        self.speaker_font_size_var.trace_add("write", self._on_display_setting_change_and_save)
        self.user_name_color_var.trace_add("write", self._on_display_setting_change_and_save)
        self.user_message_color_var.trace_add("write", self._on_display_setting_change_and_save)
        self.ai_name_color_var.trace_add("write", self._on_display_setting_change_and_save)
        self.ai_message_color_var.trace_add("write", self._on_display_setting_change_and_save)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.chat_core.process_queue()

    def _on_display_setting_change(self, *args):
        if hasattr(self, 'chat_core') and self.chat_core is not None:
            self.chat_core.rerender_all_panes()

    def _on_display_setting_change_and_save(self, *args):
        self._on_display_setting_change()
        self.config_manager.save_display_settings()

    def on_closing(self):
        self.logger.info("Application closing. Stopping background tasks.")
        self.state_manager.stop_background_refresh()
        # Potentially save active config here if desired
        # self.config_manager.save_current_config()
        self.root.destroy()

if __name__ == "__main__":
    setup_logging()
    if not os.path.exists("logs"):
        os.makedirs("logs")
    root = ctk.CTk()
    app = AIDualChatApp(root)
    root.mainloop()