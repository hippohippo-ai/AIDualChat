# --- START OF FILE main.py ---

# Gemini Dual Chat GUI - Final Stable Version

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import google.generativeai as genai
import threading
import queue
import os
import json
from datetime import datetime
import re
import uuid
import time
import math
from tkhtmlview import HTMLLabel
from markdown_it import MarkdownIt

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
        self.FONT_CHAT = ctk.CTkFont(family="Consolas", size=14)
        root.configure(fg_color=self.COLOR_BACKGROUND)

        self.SIDEBAR_WIDTH_FULL = 280
        self.SIDEBAR_WIDTH_COLLAPSED = 40

        # --- State Management (Back to simple, dual-window logic) ---
        self.chat_sessions = {}
        self.response_queue = queue.Queue()
        self.current_generation_id = {1: 0, 2: 0}
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        self.raw_log_displays = {}
        self.available_models = []
        self.config_description_entry = None
        self.md = MarkdownIt()

        self.load_config()
        self.delay_var = ctk.StringVar(value=str(self.config.get("auto_reply_delay_minutes", 1.0)))
        
        self.api_key = self.config.get("api_key")
        genai.configure(api_key=self.api_key)

        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        self.create_widgets()

        # Apply the active configuration to the UI, but don't reset sessions yet
        active_config = self.config['configurations'][self.config.get('active_config_index', 0)]
        self._apply_config_to_ui(active_config, startup=True)

        try:
            self.available_models = self.fetch_available_models()
            self._update_model_dropdowns()
        except Exception as e:
            self.available_models = []
            messagebox.showwarning("API Connection Error", 
                                 f"Could not connect to Google AI, likely due to an invalid API key or a network issue. Please provide a valid key.")
            self.prompt_for_api_key()

        # Prime sessions only if models were loaded
        if self.available_models:
            for chat_id in [1, 2]: self.prime_chat_session(chat_id)
            
        self.process_queue()

    def prompt_for_api_key(self):
        dialog = ctk.CTkInputDialog(text="Please enter your Gemini API Key:", title="API Key Required")
        key = dialog.get_input()
        if not key:
            return

        try:
            # Test the new key by fetching models
            genai.configure(api_key=key)
            self.available_models = self.fetch_available_models()
            
            # If successful, save the key and re-initialize the app state
            self.api_key = key
            self.config["api_key"] = key
            self._save_config_to_file(self.config)
            
            messagebox.showinfo("Success", "API Key is valid and has been updated. Re-initializing models.")
            
            self._update_model_dropdowns()
            
            for chat_id in [1, 2]:
                self.prime_chat_session(chat_id, from_event=True)

        except Exception as e:
            messagebox.showerror("Invalid API Key", f"The provided API key is invalid or there was a network error.\n\nPlease try again.\n\nError: {e}")

    def _update_model_dropdowns(self):
        model_list = self._create_model_list_for_dropdown()
        if not model_list:
            return
        for selector in self.model_selectors.values():
            selector.configure(values=model_list)
        
        default1 = self.config.get("default_model_1")
        default2 = self.config.get("default_model_2")
        
        # Set to default if available, otherwise fall back to the first model in the list
        self.model_selectors[1].set(default1 if default1 in model_list else model_list[0])
        self.model_selectors[2].set(default2 if default2 in model_list else model_list[0])

    def fetch_available_models(self):
        models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models: raise Exception("No usable models found for your API key.")
        return sorted(models)

    def load_config(self):
        self.config_file = 'config.json'

        # Create a default list of 10 configuration profiles
        configurations = []
        for i in range(10):
            profile = {
                "name": f"Config {i}",
                "description": "Default configuration" if i == 0 else "Empty",
                "gemini_1": {
                    "model": "gemini-2.5-pro",
                    "system_prompt": "You are Gemini 1, a helpful and concise assistant.",
                    "temperature": 0.7,
                    "top_p": 1.0
                },
                "gemini_2": {
                    "model": "gemini-2.5-pro",
                    "system_prompt": "You are Gemini 2, a creative and detailed assistant.",
                    "temperature": 0.7,
                    "top_p": 1.0
                }
            }
            configurations.append(profile)

        default_config = {
            "api_key": "PASTE_YOUR_GEMINI_API_KEY_HERE",
            "auto_reply_delay_minutes": 1.0,
            "active_config_index": 0,
            "preferred_models": ["gemini-2.5-pro", "gemini-2.5-flash"],
            "configurations": configurations
        }

        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            self.config = default_config
        else:
            try:
                with open(self.config_file, 'r') as f: self.config = json.load(f)
                
                config_changed = False
                if 'configurations' not in self.config or not isinstance(self.config['configurations'], list):
                    raise ValueError("Missing 'configurations' list, regenerating config.")

                # Check each profile for the 'description' key and add it if missing
                for profile in self.config['configurations']:
                    if 'description' not in profile:
                        profile['description'] = "Empty"
                        config_changed = True
                
                if config_changed:
                    self._save_config_to_file(self.config)

            except (json.JSONDecodeError, KeyError, ValueError):
                # If file is corrupt, old format, or fails validation, overwrite with new default
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.config = default_config

    def _save_config_to_file(self, config_data):
        with open(self.config_file, 'w') as f: json.dump(config_data, f, indent=2)

    def prime_chat_session(self, chat_id, from_event=False, history=None, system_prompt=None):
        if not self.available_models:
            messagebox.showerror("No Models Loaded", "Cannot start a chat session. Please set a valid API key first.")
            return
        try:
            model_name = self.model_selectors[chat_id].get()

            active_config_index = self.config.get('active_config_index', 0)
            active_profile = self.config['configurations'][active_config_index]
            agent_config = active_profile[f'gemini_{chat_id}']

            generation_config = genai.types.GenerationConfig(temperature=agent_config['temperature'])
            
            sys_prompt = system_prompt if system_prompt is not None else self.options_prompts[chat_id].get("1.0", tk.END).strip()
            
            model = genai.GenerativeModel(model_name, system_instruction=sys_prompt, generation_config=generation_config)
            
            self.chat_sessions[chat_id] = model.start_chat(history=history or [])
            
            self.total_tokens[chat_id] = 0
            self.update_token_counts(chat_id, None, True)
            
            if from_event:
                if not history:
                    if self.raw_log_displays.get(chat_id):
                        self.raw_log_displays[chat_id].delete('1.0', tk.END)
                    system_msg = f"# --- Session reset with model: {model_name} ---"
                    self.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
                    self.append_message(chat_id, system_msg, "system")
                    self._render_chat_display(chat_id)
                self._remove_all_files(chat_id)
                
        except Exception as e: 
            messagebox.showerror("Model Error", f"Failed to start chat for Gemini {chat_id}. Error: {e}")
    
    def create_widgets(self):
        self.root.grid_columnconfigure(1, weight=1); self.root.grid_rowconfigure(0, weight=1)
        self.left_sidebar = self._create_left_sidebar(self.root); self.left_sidebar.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="nsw")
        self.central_area = self._create_central_area(self.root); self.central_area.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.right_sidebar = self._create_right_sidebar(self.root); self.right_sidebar.grid(row=0, column=2, padx=(0, 5), pady=5, sticky="nse")
        self._toggle_left_sidebar()

    def _toggle_left_sidebar(self):
        is_expanded = self.left_sidebar.cget('width') == self.SIDEBAR_WIDTH_FULL
        if is_expanded: self.left_sidebar.content_frame.pack_forget(); self.left_sidebar.configure(width=self.SIDEBAR_WIDTH_COLLAPSED); self.left_toggle_button.configure(text="▶")
        else: self.left_sidebar.configure(width=self.SIDEBAR_WIDTH_FULL); self.left_sidebar.content_frame.pack(fill="x", before=self.left_sidebar.spacer); self.left_toggle_button.configure(text="◀")

    def _toggle_right_sidebar(self):
        is_expanded = self.right_sidebar.cget('width') == self.SIDEBAR_WIDTH_FULL
        if is_expanded: self.right_sidebar.content_frame.pack_forget(); self.right_sidebar.configure(width=self.SIDEBAR_WIDTH_COLLAPSED); self.right_toggle_button.configure(text="◀")
        else: self.right_sidebar.configure(width=self.SIDEBAR_WIDTH_FULL); self.right_sidebar.content_frame.pack(fill="both", expand=True); self.right_toggle_button.configure(text="▶")

    def _create_left_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=self.SIDEBAR_WIDTH_FULL, fg_color=self.COLOR_SIDEBAR, corner_radius=10); sidebar.pack_propagate(False)
        toggle_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); toggle_frame.pack(fill="x", pady=5, padx=5)
        self.left_toggle_button = ctk.CTkButton(toggle_frame, text="◀", command=self._toggle_left_sidebar, width=25, height=25, font=self.FONT_GENERAL); self.left_toggle_button.pack(anchor="ne")
        sidebar.content_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); sidebar.content_frame.pack(fill="x")
        ctk.CTkLabel(sidebar.content_frame, text="STUDIO", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.COLOR_TEXT).pack(pady=(0,20), padx=20, anchor="w")
        session_content = self._create_collapsible_frame(sidebar.content_frame, "Session Management")
        ctk.CTkButton(session_content, text="New Session", command=self.new_session, fg_color="transparent", text_color=self.COLOR_TEXT, anchor="w", font=self.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Save Gemini 1", command=lambda: self.save_session(1), fg_color="transparent", text_color=self.COLOR_TEXT, anchor="w", font=self.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Save Gemini 2", command=lambda: self.save_session(2), fg_color="transparent", text_color=self.COLOR_TEXT, anchor="w", font=self.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Load Gemini 1", command=lambda: self.load_session(1), fg_color="transparent", text_color=self.COLOR_TEXT, anchor="w", font=self.FONT_GENERAL).pack(fill="x", padx=15)
        ctk.CTkButton(session_content, text="Load Gemini 2", command=lambda: self.load_session(2), fg_color="transparent", text_color=self.COLOR_TEXT, anchor="w", font=self.FONT_GENERAL).pack(fill="x", padx=15, pady=(0,10))
        sidebar.spacer = ctk.CTkFrame(sidebar, fg_color="transparent"); sidebar.spacer.pack(expand=True, fill="y")
        return sidebar

    def _create_central_area(self, parent):
        tab_view = ctk.CTkTabview(parent, fg_color=self.COLOR_INPUT_AREA); tab_view.grid(row=0, column=0, sticky="nsew")
        
        tab1 = tab_view.add("Gemini 1")
        tab2 = tab_view.add("Gemini 2")
        tab3 = tab_view.add("Gemini 1 (Raw)")
        tab4 = tab_view.add("Gemini 2 (Raw)")

        self._create_chat_panel(tab1, 1)
        self._create_chat_panel(tab2, 2)

        # Create raw log displays in the new tabs
        for chat_id, tab in zip([1, 2], [tab3, tab4]):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            display = ctk.CTkTextbox(tab, wrap="word", font=self.FONT_CHAT, state='normal', fg_color=self.COLOR_CHAT_DISPLAY, text_color=self.COLOR_TEXT)
            display.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.raw_log_displays[chat_id] = display
        
        return tab_view

    def _create_chat_panel(self, parent, chat_id):
        parent.grid_columnconfigure(0, weight=1); parent.grid_rowconfigure(0, weight=1)
        
        # Use HTMLLabel for rich text display
        self.chat_displays[chat_id] = HTMLLabel(parent, background=self.COLOR_CHAT_DISPLAY, foreground=self.COLOR_TEXT, font=(self.FONT_CHAT.cget("family"), self.FONT_CHAT.cget("size")))
        self.chat_displays[chat_id].grid(row=0, column=0, sticky="nsew")
        self.chat_displays[chat_id].configure(state='normal')


        input_frame = ctk.CTkFrame(parent, fg_color=self.COLOR_INPUT_AREA); input_frame.grid(row=1, column=0, pady=(5, 0), sticky="ew"); input_frame.grid_columnconfigure(0, weight=1)
        
        self.user_inputs[chat_id] = ctk.CTkTextbox(input_frame, height=120, wrap="word", font=self.FONT_CHAT, fg_color=self.COLOR_CHAT_DISPLAY, border_width=1, border_color=self.COLOR_BORDER)
        self.user_inputs[chat_id].grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.user_inputs[chat_id].bind("<Control-Return>", lambda event, c=chat_id: self.send_message(c))

        controls_frame = ctk.CTkFrame(input_frame, fg_color="transparent"); controls_frame.grid(row=0, column=1, padx=(0,10), pady=5, sticky="ns")
        self.send_buttons[chat_id] = ctk.CTkButton(controls_frame, text="Send", command=lambda c=chat_id: self.send_message(c), font=self.FONT_GENERAL, width=70)
        self.send_buttons[chat_id].pack(pady=(0,2), fill="x")
        self.stop_buttons[chat_id] = ctk.CTkButton(controls_frame, text="Stop", command=lambda c=chat_id: self.stop_generation(c), font=self.FONT_GENERAL, width=70, state="disabled")
        self.stop_buttons[chat_id].pack(pady=(2,10), fill="x")

        auto_reply_text = "Auto-reply to Gemini 2" if chat_id == 1 else "Auto-reply to Gemini 1"
        ctk.CTkCheckBox(controls_frame, text=auto_reply_text, variable=self.auto_reply_vars[chat_id], font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).pack(anchor="w")
        
        self.token_info_vars[chat_id] = ctk.StringVar(value="Tokens: 0 | 0")
        ctk.CTkLabel(controls_frame, textvariable=self.token_info_vars[chat_id], font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).pack(anchor="w", pady=(10,0))
        
        self.progress_bars[chat_id] = ctk.CTkProgressBar(input_frame, mode='indeterminate');
        self.progress_bars[chat_id].grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.progress_bars[chat_id].grid_remove()

    def _create_right_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=self.SIDEBAR_WIDTH_FULL, fg_color=self.COLOR_SIDEBAR, corner_radius=10); sidebar.pack_propagate(False)
        toggle_frame = ctk.CTkFrame(sidebar, fg_color="transparent"); toggle_frame.pack(fill="x", pady=5, padx=5)
        self.right_toggle_button = ctk.CTkButton(toggle_frame, text="▶", command=self._toggle_right_sidebar, width=25, height=25, font=self.FONT_GENERAL); self.right_toggle_button.pack(anchor="nw")
        sidebar.content_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent"); sidebar.content_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(sidebar.content_frame, text="CONFIGURATION", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.COLOR_TEXT).pack(pady=(0,10), padx=20, anchor="w")

        # --- Configuration Profile Selector ---
        config_selector_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent")
        config_selector_frame.pack(fill="x", padx=15, pady=(0, 10))
        config_selector_frame.grid_columnconfigure(0, weight=1)

        # Format dropdown values as "Name | Description"
        config_display_names = [f"{c['name']} | {c['description']}" for c in self.config.get('configurations', [])]
        active_display_name = config_display_names[self.config.get('active_config_index', 0)]
        self.config_selector_var = ctk.StringVar(value=active_display_name)
        
        self.config_selector = ctk.CTkComboBox(config_selector_frame, values=config_display_names, variable=self.config_selector_var, command=self._on_config_select, state="readonly")
        self.config_selector.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        # Add description entry box
        ctk.CTkLabel(config_selector_frame, text="Description:", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=(5,0))
        self.config_description_entry = ctk.CTkEntry(config_selector_frame, font=self.FONT_GENERAL)
        self.config_description_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ctk.CTkButton(config_selector_frame, text="Save to Active Config", command=self._save_current_config).grid(row=3, column=0, columnspan=2, sticky="ew")
        
        # Add a separator
        ctk.CTkFrame(sidebar.content_frame, height=1, fg_color=self.COLOR_BORDER).pack(fill="x", padx=15, pady=10)


        model_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent"); model_frame.pack(fill="x", padx=15, pady=5); model_frame.grid_columnconfigure(0, weight=1)
        model_list = self._create_model_list_for_dropdown()
        ctk.CTkLabel(model_frame, text="Gemini 1 Model", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        self.model_selectors[1] = ctk.CTkComboBox(model_frame, values=model_list, command=lambda e, c=1: self.on_model_change(c), font=self.FONT_GENERAL, dropdown_font=self.FONT_GENERAL, fg_color=self.COLOR_WIDGET_BG, border_color=self.COLOR_BORDER, button_color=self.COLOR_WIDGET_BG, dropdown_fg_color=self.COLOR_WIDGET_BG, state="readonly")
        self.model_selectors[1].grid(row=1, column=0, pady=(0,10), sticky="ew")
        ctk.CTkLabel(model_frame, text="Gemini 2 Model", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).grid(row=2, column=0, sticky="w")
        self.model_selectors[2] = ctk.CTkComboBox(model_frame, values=model_list, command=lambda e, c=2: self.on_model_change(c), font=self.FONT_GENERAL, dropdown_font=self.FONT_GENERAL, fg_color=self.COLOR_WIDGET_BG, border_color=self.COLOR_BORDER, button_color=self.COLOR_WIDGET_BG, dropdown_fg_color=self.COLOR_WIDGET_BG, state="readonly")
        self.model_selectors[2].grid(row=3, column=0, pady=(0,10), sticky="ew")
        config_frame = ctk.CTkFrame(sidebar.content_frame, fg_color="transparent"); config_frame.pack(fill="x", padx=15, pady=(10,5)); config_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(config_frame, text="Auto-Reply Delay (min)", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w")
        ctk.CTkEntry(config_frame, textvariable=self.delay_var, width=50, font=self.FONT_GENERAL, fg_color=self.COLOR_WIDGET_BG, border_color=self.COLOR_BORDER, border_width=1).grid(row=0, column=1, sticky="w", padx=10)
        ctk.CTkButton(config_frame, text="Set API Key", command=self.prompt_for_api_key, font=self.FONT_GENERAL).grid(row=1, column=0, columnspan=2, pady=(10,0), sticky="ew")
        self._create_model_settings_panel(sidebar.content_frame, 1)
        self._create_model_settings_panel(sidebar.content_frame, 2)
        return sidebar

    def _create_model_list_for_dropdown(self):
        preferred = self.config.get("preferred_models", [])
        top_list = [m for m in preferred if m in self.available_models]
        other_list = sorted([m for m in self.available_models if m not in top_list])
        if top_list and other_list: return top_list + ["──────────"] + other_list
        return self.available_models

    def _create_model_settings_panel(self, parent, chat_id):
        content = self._create_collapsible_frame(parent, f"Gemini {chat_id} Settings")
        ctk.CTkLabel(content, text="System Instructions", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).pack(anchor='w', padx=5, pady=(5,0))
        self.options_prompts[chat_id] = ctk.CTkTextbox(content, height=100, wrap="word", font=self.FONT_CHAT, fg_color=self.COLOR_WIDGET_BG, border_color=self.COLOR_BORDER, border_width=1)
        self.options_prompts[chat_id].pack(fill="both", padx=5, pady=2, expand=True)
        params_frame = ctk.CTkFrame(content, fg_color="transparent"); params_frame.pack(fill='x', padx=5, pady=5)
        self.temp_labels[chat_id] = ctk.CTkLabel(params_frame, text="Temperature: 0.00", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED); self.temp_labels[chat_id].pack(side='left')
        ctk.CTkSlider(params_frame, from_=0, to=1, variable=self.temp_vars[chat_id], command=lambda v, c=chat_id: self.update_slider_label(c, 'temp')).pack(side='left', fill='x', expand=True, padx=5)
        ctk.CTkLabel(content, text="Files", font=self.FONT_SMALL, text_color=self.COLOR_TEXT_MUTED).pack(anchor='w', padx=5, pady=(5,0))
        file_frame = ctk.CTkFrame(content, fg_color=self.COLOR_WIDGET_BG, border_color=self.COLOR_BORDER, border_width=1); file_frame.pack(fill="both", expand=True, padx=5, pady=5)
        listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_TEXT, borderwidth=0, highlightthickness=0, font=self.FONT_SMALL); listbox.pack(side="left", fill="both", expand=True)
        self.file_lists[chat_id] = listbox
        file_buttons = ctk.CTkFrame(content, fg_color="transparent"); file_buttons.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(file_buttons, text="+", command=lambda c=chat_id: self._open_file_dialog(c), font=self.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_buttons, text="-", command=lambda c=chat_id: self._remove_selected_files(c), font=self.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)
        ctk.CTkButton(file_buttons, text="x", command=lambda c=chat_id: self._remove_all_files(c), font=self.FONT_GENERAL, width=40).pack(side="left", expand=True, padx=2)

    def _create_collapsible_frame(self, parent, text):
        container = ctk.CTkFrame(parent, fg_color="transparent"); container.pack(fill="x", padx=5, pady=2)
        header = ctk.CTkFrame(container, fg_color="transparent", cursor="hand2"); header.pack(fill="x")
        chevron_label = ctk.CTkLabel(header, text="▶", font=self.FONT_GENERAL, text_color=self.COLOR_TEXT_MUTED); chevron_label.pack(side="left", padx=(10,5))
        header_label = ctk.CTkLabel(header, text=text, font=self.FONT_BOLD, text_color=self.COLOR_TEXT); header_label.pack(side="left")
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        def toggle_content(event=None):
            if content_frame.winfo_ismapped(): content_frame.pack_forget(); chevron_label.configure(text="▶")
            else: content_frame.pack(fill="x", after=header); chevron_label.configure(text="▼")
        header.bind("<Button-1>", toggle_content); header_label.bind("<Button-1>", toggle_content); chevron_label.bind("<Button-1>", toggle_content)
        return content_frame

    def send_message(self, chat_id, message_text=None):
        is_auto_reply = message_text is not None
        if not is_auto_reply:
            msg = self.user_inputs[chat_id].get("1.0", tk.END).strip()
            if not msg: return "break"
            self.user_inputs[chat_id].delete("1.0", tk.END)
        else:
            msg = message_text.strip()

        self._start_api_call(chat_id, msg)
        return "break"

    def _start_api_call(self, chat_id, message):
        files = self.file_lists[chat_id].full_paths if hasattr(self.file_lists[chat_id], 'full_paths') else []
        if files: self.append_message(chat_id, f"Attached: {', '.join([os.path.basename(p) for p in files])}", "system")
        self.current_generation_id[chat_id] += 1; self.update_ui_for_sending(chat_id)
        thread = threading.Thread(target=self.api_call_thread, args=(self.chat_sessions[chat_id], message, chat_id, files, self.current_generation_id[chat_id])); thread.daemon = True; thread.start()
        self._remove_all_files(chat_id)
        
    def process_queue(self):
        try:
            msg = self.response_queue.get_nowait()
            chat_id, msg_type = msg['chat_id'], msg.get('type')
            if msg.get('generation_id') != self.current_generation_id[chat_id] and msg_type not in ['info', 'error']: return
            
            display = self.chat_displays.get(chat_id)
            raw_display = self.raw_log_displays.get(chat_id)

            if msg_type == 'stream_start':
                label = f"Gemini {chat_id}:"
                if raw_display:
                    raw_display.insert(tk.END, f"\n---\n# {label}\n")
                    raw_display.see(tk.END)

            elif msg_type == 'stream_chunk':
                if raw_display:
                    raw_display.insert(tk.END, msg['text']); raw_display.see(tk.END)

            elif msg_type == 'stream_end':
                full_response_text = msg.get('full_text', '')
                if display:
                    self._render_chat_display(chat_id)
                
                self.restore_ui_after_response(chat_id)
                if msg.get('usage'): self.update_token_counts(chat_id, msg['usage'])
                self.log_conversation(chat_id, msg['user_message'], full_response_text)
                
                target_id = 2 if chat_id == 1 else 1
                if self.auto_reply_vars[chat_id].get():
                    self._schedule_follow_up(target_id, full_response_text)
            elif msg_type in ['error', 'info']:
                self.restore_ui_after_response(chat_id)
                # Add system/error message to session history
                role = 'model' # Treat system/error messages as coming from the model for display purposes
                self.chat_sessions[chat_id].history.append({'role': role, 'parts': [{'text': msg['text']}]})
                
                # Update raw log display
                self.append_message(chat_id, msg['text'], 'system' if msg_type == 'info' else 'error')

                # Update formatted display
                self._render_chat_display(chat_id)
        except queue.Empty: pass
        finally: self.root.after(100, self.process_queue)

    def _schedule_follow_up(self, target_id, message):
        try:
            delay_minutes = float(self.delay_var.get())
            if delay_minutes < 0: raise ValueError
            delay_seconds = delay_minutes * 60
            if delay_seconds > 0:
                system_msg = f"--- Auto-replying in {delay_seconds:.1f} seconds... ---"
                self.chat_sessions[target_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
                self.append_message(target_id, system_msg, "system")
                self._render_chat_display(target_id)
                self.root.after(int(delay_seconds * 1000), lambda: self.send_message(target_id, message))
            else: self.send_message(target_id, message)
        except (ValueError, TypeError):
            system_msg = "--- Invalid auto-reply delay. Sending immediately. ---"
            self.chat_sessions[target_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
            self.append_message(target_id, system_msg, "error")
            self._render_chat_display(target_id)
            self.send_message(target_id, message)
        
    def stop_generation(self, chat_id):
        self.current_generation_id[chat_id] += 1
        self.restore_ui_after_response(chat_id)
        system_msg = "\n--- Generation stopped by user. ---\n"
        self.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
        self.append_message(chat_id, system_msg, "system")
        self._render_chat_display(chat_id)

    def update_ui_for_sending(self, chat_id):
        self.user_inputs[chat_id].configure(state='disabled'); self.send_buttons[chat_id].configure(state='disabled')
        self.stop_buttons[chat_id].configure(state='normal'); self.progress_bars[chat_id].grid(); self.progress_bars[chat_id].start()

    def restore_ui_after_response(self, chat_id):
        self.user_inputs[chat_id].configure(state='normal'); self.send_buttons[chat_id].configure(state='normal')
        self.stop_buttons[chat_id].configure(state='disabled'); self.progress_bars[chat_id].stop(); self.progress_bars[chat_id].grid_remove(); self.user_inputs[chat_id].focus_set()

    def append_message(self, chat_id, label, tag, content=""):
        # Raw display
        raw_display = self.raw_log_displays.get(chat_id)
        if raw_display:
            raw_display.insert(tk.END, f"\n---\n# {label}\n")
            raw_display.insert(tk.END, content)
            raw_display.see(tk.END)
    
    def new_session(self):
        for chat_id in [1, 2]:
            self.prime_chat_session(chat_id, from_event=True)
            system_msg = "--- New session started. ---"
            self.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
            self.append_message(chat_id, system_msg, "system")
            self._render_chat_display(chat_id)
        self.delay_var.set(str(self.config.get("auto_reply_delay_minutes", 1.0)))

    def update_token_counts(self, chat_id, usage_metadata, reset=False):
        if reset: self.total_tokens[chat_id] = 0; self.token_info_vars[chat_id].set(f"Tokens: 0 | 0"); return
        if not usage_metadata: return
        last = usage_metadata.get('prompt_token_count', 0) + usage_metadata.get('candidates_token_count', 0)
        self.total_tokens[chat_id] += last; self.token_info_vars[chat_id].set(f"Tokens: {last} | {self.total_tokens[chat_id]}")
    
    def _render_chat_display(self, chat_id):
        """Renders the entire chat history for a given chat_id to its HTMLLabel."""
        if chat_id not in self.chat_sessions or not hasattr(self.chat_sessions[chat_id], 'history'):
            return

        display_widget = self.chat_displays[chat_id]
        display_widget.delete("1.0", tk.END) # Clear existing content

        history = self.chat_sessions[chat_id].history
        # Basic CSS for styling the chat
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="background-color: #1E1F22; color: #FFFFFF; font-family: Consolas, monaco, monospace;">
        """
        for message in history:
            # The first message is the system prompt, which we don't display
            if message == history[0]:
                continue

            # Determine how to access role and parts based on message type
            if isinstance(message, dict):
                msg_role = message['role']
                msg_parts = message['parts']
                full_text = "".join([p['text'] for p in msg_parts if 'text' in p])
            else: # Assume it's a genai.types.Content object
                msg_role = message.role
                msg_parts = message.parts
                full_text = "".join([p.text for p in msg_parts if hasattr(p, 'text')])

            content_html = self.md.render(full_text)

            # Post-process content_html to add inline styles to <pre> and <code> tags
            pre_style = "background-color: #2B2B2B; padding: 10px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word;"
            code_style = "font-family: Consolas, monaco, monospace;" # Inherited from body, but good to be explicit

            # Apply style to <pre> tags
            content_html = re.sub(r'<pre>(.*?)</pre>', r'<pre style="' + pre_style + r'">\1</pre>', content_html, flags=re.DOTALL)
            # Apply style to <code> tags (only if not inside <pre> already, or if it's inline code)
            # For simplicity, let's apply it to all <code> tags.
            content_html = re.sub(r'<code>(.*?)</code>', r'<code style="' + code_style + r'">\1</code>', content_html, flags=re.DOTALL)

            role_color = "#A9DFBF" if msg_role == 'user' else "#A9CCE3"
            role_name = "You" if msg_role == 'user' else f"Gemini {chat_id}"
            
            html_content += f'''
            <div style="margin-bottom: 1em; color: #FFFFFF;">
                <b style="font-weight: bold; color: {role_color};">{role_name}:</b>
                {content_html}
            </div>
            '''

        
        html_content += "</body></html>"
        self.chat_displays[chat_id].set_html(html_content)
        self.chat_displays[chat_id].update_idletasks() # Ensure the view updates
        self.chat_displays[chat_id].yview_moveto(1.0) # Scroll to bottom

    def _apply_config_to_ui(self, config_profile, startup=False):
        """Updates all UI controls based on the provided config profile."""
        # Config description
        if self.config_description_entry:
            self.config_description_entry.delete(0, tk.END)
            self.config_description_entry.insert(0, config_profile.get("description", ""))

        # Gemini 1
        g1_config = config_profile['gemini_1']
        self.model_selectors[1].set(g1_config['model'])
        self.options_prompts[1].delete("1.0", tk.END)
        self.options_prompts[1].insert("1.0", g1_config['system_prompt'])
        self.temp_vars[1].set(g1_config['temperature'])
        self.update_slider_label(1, 'temp')

        # Gemini 2
        g2_config = config_profile['gemini_2']
        self.model_selectors[2].set(g2_config['model'])
        self.options_prompts[2].delete("1.0", tk.END)
        self.options_prompts[2].insert("1.0", g2_config['system_prompt'])
        self.temp_vars[2].set(g2_config['temperature'])
        self.update_slider_label(2, 'temp')

        if not startup:
            if messagebox.askyesno("Confirm", "Applying a new configuration will reset both chat sessions. Continue?"):
                for chat_id in [1, 2]:
                    self.prime_chat_session(chat_id, from_event=True)

    def _on_config_select(self, choice_string):
        """Handles selection of a new configuration profile from the dropdown."""
        choice_name = choice_string.split(' | ')[0]
        new_index = next((i for i, conf in enumerate(self.config['configurations']) if conf['name'] == choice_name), None)
        if new_index is None: return

        self.config['active_config_index'] = new_index
        
        selected_profile = self.config['configurations'][new_index]
        self._apply_config_to_ui(selected_profile)

    def _save_current_config(self):
        """Saves the current UI settings to the active configuration profile."""
        active_index = self.config.get('active_config_index', 0)
        
        # Read all settings from the UI
        current_settings = {
            "name": f"Config {active_index}", # Name is fixed
            "description": self.config_description_entry.get(),
            "gemini_1": {
                "model": self.model_selectors[1].get(),
                "system_prompt": self.options_prompts[1].get("1.0", tk.END).strip(),
                "temperature": 1.0
            },
            "gemini_2": {
                "model": self.model_selectors[2].get(),
                "system_prompt": self.options_prompts[2].get("1.0", tk.END).strip(),
                "temperature": 1.0
            }
        }
        
        # Update the config data and save to file
        self.config['configurations'][active_index] = current_settings
        self.config['active_config_index'] = active_index # Ensure active index is saved
        self._save_config_to_file(self.config)
        
        # Update the text in the dropdown to reflect the new description
        config_display_names = [f"{c['name']} | {c['description']}" for c in self.config.get('configurations', [])]
        self.config_selector.configure(values=config_display_names)
        self.config_selector_var.set(config_display_names[active_index])

        messagebox.showinfo("Saved", f"Current settings have been saved to 'Config {active_index}'.")

        if messagebox.askyesno("Apply Settings", "Settings saved. Do you want to apply them now by resetting the chat sessions?"):
            for chat_id in [1, 2]:
                self.prime_chat_session(chat_id, from_event=True)

    def update_slider_label(self, chat_id, param_type):
        if param_type == 'temp': self.temp_labels[chat_id].configure(text=f"Temperature: {self.temp_vars[chat_id].get():.2f}")
    
    def on_model_change(self, chat_id):
        if messagebox.askyesno("Confirm", f"Changing model for Gemini {chat_id} will reset its history. Continue?"):
            self.config[f"default_model_{chat_id}"] = self.model_selectors[chat_id].get(); self._save_config_to_file(self.config)
            self.prime_chat_session(chat_id, from_event=True)

    def _open_file_dialog(self, chat_id):
        paths = filedialog.askopenfilenames()
        if paths:
            listbox = self.file_lists[chat_id]
            if not hasattr(listbox, 'full_paths'): listbox.full_paths = []
            for p in paths: listbox.insert(tk.END, os.path.basename(p)); listbox.full_paths.append(p)
                
    def _remove_selected_files(self, chat_id):
        listbox = self.file_lists[chat_id]
        if hasattr(listbox, 'full_paths'):
            for i in reversed(listbox.curselection()): listbox.delete(i); listbox.full_paths.pop(i)

    def _remove_all_files(self, chat_id):
        listbox = self.file_lists[chat_id]
        if hasattr(listbox, 'full_paths'): listbox.delete(0, tk.END); listbox.full_paths = []
        
    def api_call_thread(self, session, msg, chat_id, files, generation_id):
        response = None
        try:
            content = [msg]
            if files: content.extend([genai.upload_file(path=p) for p in files])
            self.response_queue.put({'type': 'stream_start', 'chat_id': chat_id, 'generation_id': generation_id})
            response = session.send_message(content, stream=True)
            for chunk in response:
                if self.current_generation_id[chat_id] != generation_id: return
                if chunk.text: self.response_queue.put({'type': 'stream_chunk', 'chat_id': chat_id, 'text': chunk.text, 'generation_id': generation_id})
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and ("quota" in error_str.lower() or "rate limit" in error_str.lower()):
                match = re.search(r"retry in ([\d\.]+)s", error_str.lower())
                delay = math.ceil(float(match.group(1))) + 1 if match else 60
                self.response_queue.put({'type': 'info', 'chat_id': chat_id, 'text': f"\n--- Retrying Gemini {chat_id} in {delay}s... ---\n", 'generation_id': generation_id})
                time.sleep(delay); self.api_call_thread(session, msg, chat_id, files, generation_id); return
            else: self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"API Error: {e}", 'generation_id': generation_id})
        finally:
            if self.current_generation_id[chat_id] != generation_id: return
            if response is not None:
                is_ok, reason, full_text = False, "UNKNOWN", ""
                try: full_text = response.text
                except Exception: pass
                if response.candidates:
                    finish_reason_enum = response.candidates[0].finish_reason; reason = finish_reason_enum.name
                    if reason == "STOP": is_ok = True
                usage_meta = response.usage_metadata
                usage_dict = {'prompt_token_count': usage_meta.prompt_token_count, 'candidates_token_count': usage_meta.candidates_token_count} if usage_meta else None
                self.response_queue.put({'type': 'stream_end', 'chat_id': chat_id, 'usage': usage_dict, 'user_message': msg, 'generation_id': generation_id, 'is_ok': is_ok, 'full_text': full_text})
                if not is_ok:
                    try:
                        session.rewind()
                        error_text = f"--- Gemini {chat_id} response stopped abnormally (Reason: {reason}). Chat history has been repaired. The automated reply chain is stopped. ---"
                        self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': error_text, 'generation_id': generation_id})
                    except ValueError:
                        error_text = f"--- Gemini {chat_id} response stopped abnormally (Reason: {reason}). Could not repair history. Starting a new session is recommended. ---"
                        self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': error_text, 'generation_id': generation_id})
            else: self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': "--- API call failed to return a response object. Check connection. ---", 'generation_id': generation_id})

    def save_session(self, chat_id):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title=f"Save Gemini {chat_id} Session")
        if not filepath: return
        try:
            history = [{'role': c.role, 'parts': [p.text for p in c.parts if hasattr(p, 'text')]} for c in self.chat_sessions[chat_id].history]
            session_data = {"model_name": self.model_selectors[chat_id].get(), "system_prompt": self.options_prompts[chat_id].get("1.0", tk.END).strip(), "history": history}
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(session_data, f, indent=2)
            messagebox.showinfo("Success", f"Session for Gemini {chat_id} saved.")
        except Exception as e: messagebox.showerror("Error", f"Failed to save session: {e}")
        
    def load_session(self, chat_id):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title=f"Load Session into Gemini {chat_id}")
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            history = session_data.get('history', [])

            # 1. Set the UI elements
            self.model_selectors[chat_id].set(session_data['model_name'])
            self.options_prompts[chat_id].delete("1.0", tk.END)
            self.options_prompts[chat_id].insert("1.0", session_data['system_prompt'])

            # 2. Prime the backend model with the full history
            self.prime_chat_session(chat_id, history=history, from_event=True)

            # 3. Clear the raw log display
            if self.raw_log_displays.get(chat_id):
                self.raw_log_displays[chat_id].delete("1.0", tk.END)

            # 4. Add a system message to history and render
            system_msg = f"--- Loaded session. History restored. ---"
            self.chat_sessions[chat_id].history.append({'role': 'model', 'parts': [{'text': system_msg}]})
            self.append_message(chat_id, system_msg, "system")
            self._render_chat_display(chat_id)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load session: {e}")

    def log_conversation(self, chat_id, user, response):
        path = os.path.join(self.log_dir, f"session_{self.session_timestamp}_gemini_{chat_id}.txt")
        with open(path, 'a', encoding='utf-8') as f:
            if user:
                f.write(f"---\n# You:\n{user}\n")
            f.write(f"---\n# Gemini {chat_id}:\n{response}\n\n")

if __name__ == "__main__":
    root = ctk.CTk()
    app = GeminiChatApp(root)
    root.mainloop()