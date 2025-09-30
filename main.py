# --- START OF FILE main.py ---

# Gemini Dual Chat GUI - Final Stable Version

import customtkinter as ctk
from tkinter import messagebox
import google.generativeai as genai
import os
from datetime import datetime
import queue
from markdown_it import MarkdownIt
from config_manager import ConfigManager
from gemini_api import GeminiAPI
from ui_elements import UIElements
from chat_core import ChatCore

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
        self.COLOR_TEXT_SELECTED = "#FFFFFF"
        self.COLOR_BORDER = "#4E5157"
        self.FONT_GENERAL = ctk.CTkFont(family="Roboto", size=14)
        self.FONT_BOLD = ctk.CTkFont(family="Roboto", size=14, weight="bold")
        self.FONT_SMALL = ctk.CTkFont(family="Roboto", size=12)
        self.FONT_CHAT = ctk.CTkFont(family="Consolas", size=12)
        root.configure(fg_color=self.COLOR_BACKGROUND)

        self.SIDEBAR_WIDTH_FULL = 280
        self.SIDEBAR_WIDTH_COLLAPSED = 40

        # --- State Management (Back to simple, dual-window logic) ---
        self.chat_sessions = {}
        self.response_queue = queue.Queue()
        self.current_generation_id = {1: 0, 2: 0}
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.render_history = {1: [], 2: []}

        # --- UI Element Dictionaries (keyed by chat_id) ---
        self.model_selectors = {}
        self.options_prompts = {}
        self.temp_vars = {1: ctk.DoubleVar(), 2: ctk.DoubleVar()}
        self.topp_vars = {1: ctk.DoubleVar(), 2: ctk.DoubleVar()}
        self.temp_labels, self.topp_labels = {}, {}
        self.file_lists = {}
        self.token_info_vars = {1: ctk.StringVar(value="Tokens: 0 | 0"), 2: ctk.StringVar(value="Tokens: 0 | 0")}
        self.total_tokens = {1:0, 2:0}
        self.chat_displays = {}
        self.user_inputs = {}
        self.send_buttons = {}
        self.stop_buttons = {}
        self.progress_bars = {}
        self.auto_reply_vars = {1: ctk.BooleanVar(value=False), 2: ctk.BooleanVar(value=False)}
        self.countdown_vars = {1: ctk.StringVar(value=""), 2: ctk.StringVar(value="")}
        self.raw_log_displays = {}
        self.available_models = []
        self.config_description_entry = None
        self.md = MarkdownIt('commonmark')

        # Font size variables
        self.chat_font_size_var = ctk.IntVar(value=8)
        self.speaker_font_size_var = ctk.IntVar(value=12)

        # Color variables
        self.user_name_color_var = ctk.StringVar(value="#A9DFBF")
        self.user_message_color_var = ctk.StringVar(value="#FFFFFF")
        self.gemini_name_color_var = ctk.StringVar(value="#A9CCE3")
        self.gemini_message_color_var = ctk.StringVar(value="#FFFFFF")

        # Traces for display settings
        # Removed trace_add calls to prevent TclError during initialization.
        # _on_display_setting_change_and_save will be called manually after setup.

        self.config_manager = ConfigManager(self) # Instantiate ConfigManager
        self.config_manager.load_config() # Call load_config from ConfigManager
        self.delay_var = ctk.StringVar(value=str(self.config.get("auto_reply_delay_minutes", 1.0)))
        
        self.gemini_api = GeminiAPI(self) # Instantiate GeminiAPI
        self.api_key = self.config.get("api_key")
        genai.configure(api_key=self.api_key)

        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        self.ui_elements = UIElements(self) # Instantiate UIElements
        self.chat_core = ChatCore(self) # Instantiate ChatCore
        self.ui_elements.create_widgets() # Call create_widgets from UIElements

        # Apply the active configuration to the UI, but don't reset sessions yet
        active_config = self.config_manager.config['configurations'][self.config_manager.config.get('active_config_index', 0)]
        self.config_manager._apply_config_to_ui(active_config, startup=True)

        try:
            self.available_models = self.gemini_api.fetch_available_models()
            self.gemini_api._update_model_dropdowns()
        except Exception as e:
            self.available_models = []
            messagebox.showwarning("API Connection Error", 
                                 f"Could not connect to Google AI, likely due to an invalid API key or a network issue. Please provide a valid key.")
            self.gemini_api.prompt_for_api_key()

        # Prime sessions only if models were loaded
        if self.available_models:
            for chat_id in [1, 2]: self.gemini_api.prime_chat_session(chat_id)
            
        # Manually call _on_display_setting_change_and_save after all setup is complete
        self._on_display_setting_change_and_save()

        # Re-add traces for display settings to enable immediate updates
        self.chat_font_size_var.trace_add("write", lambda *args: self._on_display_setting_change_and_save())
        self.speaker_font_size_var.trace_add("write", lambda *args: self._on_display_setting_change_and_save())
        self.user_name_color_var.trace_add("write", lambda *args: self._on_display_setting_change_and_save())
        self.user_message_color_var.trace_add("write", lambda *args: self._on_display_setting_change_and_save())
        self.gemini_name_color_var.trace_add("write", lambda *args: self._on_display_setting_change_and_save())
        self.gemini_message_color_var.trace_add("write", lambda *args: self._on_display_setting_change_and_save())

        self.chat_core.process_queue()

    def _on_display_setting_change_and_save(self):
        if hasattr(self, 'chat_core') and self.chat_core is not None:
            self.chat_core._render_chat_display(1)
            self.chat_core._render_chat_display(2)
            self.config_manager._save_display_settings() # Save config












    






















        



        







    



    
 # Scroll to bottom








    







        




if __name__ == "__main__":
    root = ctk.CTk()
    app = GeminiChatApp(root)
    root.mainloop()