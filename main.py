# --- START OF UPDATED main.py ---

import customtkinter as ctk
from tkinter import messagebox
import google.generativeai as genai
import os
from datetime import datetime
import queue
from config_manager import ConfigManager
from gemini_api import GeminiAPI
from ui_elements import UIElements
from chat_core import ChatCore
from chat_pane import ChatPane

class GeminiChatApp:
    def __init__(self, root):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title("Gemini Dual Chat")
        self.root.geometry("1600x900")
        self.root.minsize(1000, 800)

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

        self.SIDEBAR_WIDTH_FULL = 280
        self.SIDEBAR_WIDTH_COLLAPSED = 40

        # --- State Management ---
        self.chat_sessions = {}
        self.response_queue = queue.Queue()
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # --- UI Element Dictionaries ---
        self.chat_panes = {}
        self.model_selectors = {}
        self.options_prompts = {} # Renamed to Persona
        self.context_prompts = {} # NEW: For Context
        self.temp_vars = {1: ctk.DoubleVar(), 2: ctk.DoubleVar()}
        self.temp_labels = {}
        self.raw_log_displays = {}
        self.available_models = []
        self.config_description_entry = None
        
        # Font size and color variables
        self.chat_font_size_var = ctk.IntVar(value=8)
        self.speaker_font_size_var = ctk.IntVar(value=12)
        self.user_name_color_var = ctk.StringVar(value="#A9DFBF")
        self.user_message_color_var = ctk.StringVar(value="#FFFFFF")
        self.gemini_name_color_var = ctk.StringVar(value="#A9CCE3")
        self.gemini_message_color_var = ctk.StringVar(value="#FFFFFF")

        # --- Module Initialization ---
        self.config_manager = ConfigManager(self)
        self.config_manager.load_config()
        self.delay_var = ctk.StringVar(value=str(self.config.get("auto_reply_delay_minutes", 1.0)))
        
        self.gemini_api = GeminiAPI(self)
        self.api_key = self.config.get("api_key")
        genai.configure(api_key=self.api_key)

        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        self.chat_core = ChatCore(self)
        
        ui_callbacks = {
            'on_new_session': self.chat_core.new_session,
            'on_save_session': self.chat_core.save_session,
            'on_load_session': self.chat_core.load_session,
            'on_export_conversation': self.chat_core.export_conversation,
            'on_smart_export': self.chat_core.smart_export, # NEW
            'on_restore_display_defaults': self.config_manager._restore_display_settings,
            'on_config_select': self.config_manager._on_config_select,
            'on_save_current_config': self.config_manager._save_current_config,
        }
        self.ui_elements = UIElements(self, ui_callbacks)
        self.ui_elements.create_widgets()

        active_config = self.config_manager.config['configurations'][self.config_manager.config.get('active_config_index', 0)]
        self.config_manager._apply_config_to_ui(active_config, startup=True)

        try:
            self.available_models = self.gemini_api.fetch_available_models()
            self.gemini_api._update_model_dropdowns()
        except Exception as e:
            self.available_models = []
            messagebox.showwarning("API Connection Error", 
                                 f"Could not connect to Google AI. Please provide a valid key.\nError: {e}")
            self.gemini_api.prompt_for_api_key()

        if self.available_models:
            for chat_id in [1, 2]: self.gemini_api.prime_chat_session(chat_id)
            
        self._on_display_setting_change_and_save()

        self.chat_font_size_var.trace_add("write", self._on_display_setting_change_and_save)
        self.speaker_font_size_var.trace_add("write", self._on_display_setting_change_and_save)
        self.user_name_color_var.trace_add("write", self._on_display_setting_change_and_save)
        self.user_message_color_var.trace_add("write", self._on_display_setting_change_and_save)
        self.gemini_name_color_var.trace_add("write", self._on_display_setting_change_and_save)
        self.gemini_message_color_var.trace_add("write", self._on_display_setting_change_and_save)

        self.chat_core.process_queue()

    def _on_display_setting_change_and_save(self, *args):
        if hasattr(self, 'chat_core') and self.chat_core is not None:
            self.chat_core.rerender_all_panes()
            self.config_manager._save_display_settings()
    
if __name__ == "__main__":
    root = ctk.CTk()
    app = GeminiChatApp(root)
    root.mainloop()

# --- END OF UPDATED main.py ---