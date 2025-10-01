# --- START OF UPDATED config_manager.py ---

import json
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
import keyring

class ConfigManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.config_file = 'config.json'
        self.config = {}
        self.service_id = "GeminiDualChat"

    def save_api_key(self, api_key):
        keyring.set_password(self.service_id, "api_key", api_key)

    def load_config(self):
        # Try to get API key from keyring
        api_key = keyring.get_password(self.service_id, "api_key")

        default_config = {
            "auto_reply_delay_minutes": 1.0,
            "active_config_index": 0,
            "preferred_models": ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-1.0-pro"],
            "language": "en",
            "configurations": [
                {
                    "name": f"Config {i}",
                    "description": "Default configuration" if i == 0 else "Empty",
                    "gemini_1": {"model": "gemini-1.5-pro-latest", "system_prompt": "You are a helpful and concise assistant.", "context": "", "temperature": 0.7, "web_search_enabled": False},
                    "gemini_2": {"model": "gemini-1.5-pro-latest", "system_prompt": "You are a creative and detailed assistant.", "context": "", "temperature": 0.7, "web_search_enabled": False},
                } for i in range(10)
            ],
            "display_settings": {
                "chat_font_size": 8, "speaker_font_size": 12, "user_name_color": "#A9DFBF",
                "user_message_color": "#FFFFFF", "gemini_name_color": "#A9CCE3", "gemini_message_color": "#FFFFFF",
            }
        }

        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f: json.dump(default_config, f, indent=4)
            self.config = default_config
        else:
            try:
                with open(self.config_file, 'r') as f: self.config = json.load(f)
                # Migrate API key from old config
                if not api_key and "api_key" in self.config and self.config["api_key"] != "PASTE_YOUR_GEMINI_API_KEY_HERE":
                    api_key = self.config["api_key"]
                    self.save_api_key(api_key)
                
                # Remove api_key from config file
                if "api_key" in self.config:
                    del self.config["api_key"]
                    self._save_config_to_file(self.config)

                config_changed = False
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
                        config_changed = True
                
                for profile in self.config.get('configurations', []):
                    for agent in ['gemini_1', 'gemini_2']:
                        if 'context' not in profile[agent]:
                            profile[agent]['context'] = ""
                            config_changed = True
                        if 'web_search_enabled' not in profile[agent]:
                            profile[agent]['web_search_enabled'] = False
                            config_changed = True

                if config_changed:
                    self._save_config_to_file(self.config)
            except (json.JSONDecodeError, KeyError, ValueError):
                with open(self.config_file, 'w') as f: json.dump(default_config, f, indent=4)
                self.config = default_config
        
        self.config["api_key"] = api_key if api_key else "PASTE_YOUR_GEMINI_API_KEY_HERE"
        self.app.config = self.config
        
        self.app.lang.set_language(self.config.get("language", "en"))
        
        display_settings = self.config.get("display_settings", default_config["display_settings"])
        # ... (rest of the load_config is the same)
        self.app.chat_font_size_var.set(display_settings.get("chat_font_size", 8))
        self.app.speaker_font_size_var.set(display_settings.get("speaker_font_size", 12))
        self.app.user_name_color_var.set(display_settings.get("user_name_color", "#A9DFBF"))
        self.app.user_message_color_var.set(display_settings.get("user_message_color", "#FFFFFF"))
        self.app.gemini_name_color_var.set(display_settings.get("gemini_name_color", "#A9CCE3"))
        self.app.gemini_message_color_var.set(display_settings.get("gemini_message_color", "#FFFFFF"))


    def _save_config_to_file(self, config_data):
        if 'api_key' in config_data:
            del config_data['api_key']
        with open(self.config_file, 'w') as f: json.dump(config_data, f, indent=2)
        
    def save_language_setting(self, lang):
        self.config['language'] = lang
        self.app.config['language'] = lang
        self._save_config_to_file(self.config)

    def _apply_config_to_ui(self, config_profile, startup=False):
        if self.app.config_description_entry:
            self.app.config_description_entry.delete(0, ctk.END); self.app.config_description_entry.insert(0, config_profile.get("description", ""))

        g1_config = config_profile['gemini_1']
        self.app.model_selectors[1].set(g1_config['model'])
        self.app.options_prompts[1].delete("1.0", ctk.END); self.app.options_prompts[1].insert("1.0", g1_config['system_prompt'])
        self.app.context_prompts[1].delete("1.0", ctk.END); self.app.context_prompts[1].insert("1.0", g1_config.get('context', ''))
        self.app.temp_vars[1].set(g1_config['temperature']); self.app.ui_elements.update_slider_label(1, 'temp')
        self.app.web_search_vars[1].set(g1_config.get('web_search_enabled', False)) # NEW

        g2_config = config_profile['gemini_2']
        self.app.model_selectors[2].set(g2_config['model'])
        self.app.options_prompts[2].delete("1.0", ctk.END); self.app.options_prompts[2].insert("1.0", g2_config['system_prompt'])
        self.app.context_prompts[2].delete("1.0", ctk.END); self.app.context_prompts[2].insert("1.0", g2_config.get('context', ''))
        self.app.temp_vars[2].set(g2_config['temperature']); self.app.ui_elements.update_slider_label(2, 'temp')
        self.app.web_search_vars[2].set(g2_config.get('web_search_enabled', False)) # NEW

        if not startup:
            if messagebox.askyesno("Confirm", "Applying this configuration will reset both chat sessions. Continue?"):
                for chat_id in [1, 2]: self.app.gemini_api.prime_chat_session(chat_id, from_event=True)

    def _on_config_select(self, choice_string):
        # ... (no changes in this method)
        choice_name = choice_string.split(' | ')[0]
        new_index = next((i for i, conf in enumerate(self.config['configurations']) if conf['name'] == choice_name), None)
        if new_index is None: return
        self.config['active_config_index'] = new_index
        self.app.config['active_config_index'] = new_index
        selected_profile = self.config['configurations'][new_index]
        self._apply_config_to_ui(selected_profile)


    def _save_current_config(self):
        active_index = self.config.get('active_config_index', 0)
        
        current_settings = {
            "name": f"Config {active_index}",
            "description": self.app.config_description_entry.get(),
            "gemini_1": {
                "model": self.app.model_selectors[1].get(),
                "system_prompt": self.app.options_prompts[1].get("1.0", ctk.END).strip(),
                "context": self.app.context_prompts[1].get("1.0", ctk.END).strip(),
                "temperature": self.app.temp_vars[1].get(),
                "web_search_enabled": self.app.web_search_vars[1].get() # NEW
            },
            "gemini_2": {
                "model": self.app.model_selectors[2].get(),
                "system_prompt": self.app.options_prompts[2].get("1.0", ctk.END).strip(),
                "context": self.app.context_prompts[2].get("1.0", ctk.END).strip(),
                "temperature": self.app.temp_vars[2].get(),
                "web_search_enabled": self.app.web_search_vars[2].get() # NEW
            },
        }
        
        # ... (rest of the _save_current_config is the same)
        self.config['configurations'][active_index].update(current_settings)
        self.app.config['configurations'][active_index].update(current_settings)
        self.config['active_config_index'] = active_index; self.app.config['active_config_index'] = active_index
        self._save_config_to_file(self.config)
        
        config_display_names = [f"{c['name']} | {c['description']}" for c in self.config.get('configurations', [])]
        self.app.config_selector.configure(values=config_display_names)
        self.app.config_selector_var.set(config_display_names[active_index])
        messagebox.showinfo("Saved", f"Current settings saved to 'Config {active_index}'.")
        if messagebox.askyesno("Apply Settings", "Settings saved. Apply them now by resetting chat sessions?"):
            for chat_id in [1, 2]: self.app.gemini_api.prime_chat_session(chat_id, from_event=True)

    def _save_display_settings(self):
        # ... (no changes in this method)
        display_settings = {
            "chat_font_size": self.app.chat_font_size_var.get(), "speaker_font_size": self.app.speaker_font_size_var.get(),
            "user_name_color": self.app.user_name_color_var.get(), "user_message_color": self.app.user_message_color_var.get(),
            "gemini_name_color": self.app.gemini_name_color_var.get(), "gemini_message_color": self.app.gemini_message_color_var.get(),
        }
        self.config["display_settings"] = display_settings
        self.app.config["display_settings"] = display_settings
        self._save_config_to_file(self.config)

    def _restore_display_settings(self):
        # ... (no changes in this method)
        if messagebox.askyesno("Confirm Restore", "Restore display settings to defaults?"):
            defaults = {"chat_font_size": 8, "speaker_font_size": 12, "user_name_color": "#A9DFBF", "user_message_color": "#FFFFFF", "gemini_name_color": "#A9CCE3", "gemini_message_color": "#FFFFFF"}
            self.app.chat_font_size_var.set(defaults["chat_font_size"])
            self.app.speaker_font_size_var.set(defaults["speaker_font_size"])
            self.app.user_name_color_var.set(defaults["user_name_color"])
            self.app.user_message_color_var.set(defaults["user_message_color"])
            self.app.gemini_name_color_var.set(defaults["gemini_name_color"])
            self.app.gemini_message_color_var.set(defaults["gemini_message_color"])
            self.app.ui_elements.user_name_color_button.configure(fg_color=defaults["user_name_color"])
            self.app.ui_elements.user_message_color_button.configure(fg_color=defaults["user_message_color"])
            self.app.ui_elements.gemini_name_color_button.configure(fg_color=defaults["gemini_name_color"])
            self.app.ui_elements.gemini_message_color_button.configure(fg_color=defaults["gemini_message_color"])
            self.config["display_settings"] = defaults
            self.app.config["display_settings"] = defaults
            self._save_config_to_file(self.config)
            messagebox.showinfo("Restored", "Display settings restored to defaults.")


# --- END OF UPDATED config_manager.py ---