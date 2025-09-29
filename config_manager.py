import json
import os
import customtkinter as ctk
from tkinter import messagebox, filedialog

class ConfigManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.config_file = 'config.json'
        self.config = {} # Initialize config here, will be loaded by load_config

    def load_config(self):
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
            "configurations": configurations,
            "display_settings": {
                "chat_font_size": 8,
                "speaker_font_size": 12,
                "user_name_color": "#A9DFBF",
                "user_message_color": "#FFFFFF",
                "gemini_name_color": "#A9CCE3",
                "gemini_message_color": "#FFFFFF"
            }
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

                for profile in self.config['configurations']:
                    if 'description' not in profile:
                        profile['description'] = "Empty"
                        config_changed = True
                
                if config_changed:
                    self._save_config_to_file(self.config)

            except (json.JSONDecodeError, KeyError, ValueError):
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.config = default_config
        
        self.app.config = self.config # Update app's config reference

        # Apply loaded display settings to app variables
        display_settings = self.config.get("display_settings", default_config["display_settings"])
        self.app.chat_font_size_var.set(display_settings.get("chat_font_size", default_config["display_settings"]["chat_font_size"]))
        self.app.speaker_font_size_var.set(display_settings.get("speaker_font_size", default_config["display_settings"]["speaker_font_size"]))
        self.app.user_name_color_var.set(display_settings.get("user_name_color", default_config["display_settings"]["user_name_color"]))
        self.app.user_message_color_var.set(display_settings.get("user_message_color", default_config["display_settings"]["user_message_color"]))
        self.app.gemini_name_color_var.set(display_settings.get("gemini_name_color", default_config["display_settings"]["gemini_name_color"]))
        self.app.gemini_message_color_var.set(display_settings.get("gemini_message_color", default_config["display_settings"]["gemini_message_color"]))

    def _save_config_to_file(self, config_data):
        with open(self.config_file, 'w') as f: json.dump(config_data, f, indent=2)

    def _apply_config_to_ui(self, config_profile, startup=False):
        if self.app.config_description_entry:
            self.app.config_description_entry.delete(0, ctk.END)
            self.app.config_description_entry.insert(0, config_profile.get("description", ""))

        g1_config = config_profile['gemini_1']
        self.app.model_selectors[1].set(g1_config['model'])
        self.app.options_prompts[1].delete("1.0", ctk.END)
        self.app.options_prompts[1].insert("1.0", g1_config['system_prompt'])
        self.app.temp_vars[1].set(g1_config['temperature'])
        self.app.ui_elements.update_slider_label(1, 'temp')

        g2_config = config_profile['gemini_2']
        self.app.model_selectors[2].set(g2_config['model'])
        self.app.options_prompts[2].delete("1.0", ctk.END)
        self.app.options_prompts[2].insert("1.0", g2_config['system_prompt'])
        self.app.temp_vars[2].set(g2_config['temperature'])
        self.app.ui_elements.update_slider_label(2, 'temp')

        if not startup:
            if messagebox.askyesno("Confirm", "Applying a new configuration will reset both chat sessions. Continue?"):
                for chat_id in [1, 2]:
                    self.app.gemini_api.prime_chat_session(chat_id, from_event=True)

    def _on_config_select(self, choice_string):
        choice_name = choice_string.split(' | ')[0]
        new_index = next((i for i, conf in enumerate(self.config['configurations']) if conf['name'] == choice_name), None)
        if new_index is None: return

        self.config['active_config_index'] = new_index
        self.app.config['active_config_index'] = new_index # Update app's config reference
        
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
                "temperature": self.app.temp_vars[1].get()
            },
            "gemini_2": {
                "model": self.app.model_selectors[2].get(),
                "system_prompt": self.app.options_prompts[2].get("1.0", ctk.END).strip(),
                "temperature": self.app.temp_vars[2].get()
            },
            "display_settings": {
                "chat_font_size": self.app.chat_font_size_var.get(),
                "speaker_font_size": self.app.speaker_font_size_var.get(),
                "user_name_color": self.app.user_name_color_var.get(),
                "user_message_color": self.app.user_message_color_var.get(),
                "gemini_name_color": self.app.gemini_name_color_var.get(),
                "gemini_message_color": self.app.gemini_message_color_var.get()
            }
        }
        
        self.config['configurations'][active_index] = current_settings
        self.app.config['configurations'][active_index] = current_settings # Update app's config reference
        self.config['active_config_index'] = active_index
        self.app.config['active_config_index'] = active_index # Update app's config reference
        self._save_config_to_file(self.config) # Corrected
        
        config_display_names = [f"{c['name']} | {c['description']}" for c in self.config.get('configurations', [])]
        self.app.config_selector.configure(values=config_display_names)
        self.app.config_selector_var.set(config_display_names[active_index])

        messagebox.showinfo("Saved", f"Current settings have been saved to 'Config {active_index}'.")

        if messagebox.askyesno("Apply Settings", "Settings saved. Do you want to apply them now by resetting the chat sessions?"):
            for chat_id in [1, 2]:
                self.app.gemini_api.prime_chat_session(chat_id, from_event=True)

    def _save_display_settings(self):
        display_settings = {
            "chat_font_size": self.app.chat_font_size_var.get(),
            "speaker_font_size": self.app.speaker_font_size_var.get(),
            "user_name_color": self.app.user_name_color_var.get(),
            "user_message_color": self.app.user_message_color_var.get(),
            "gemini_name_color": self.app.gemini_name_color_var.get(),
            "gemini_message_color": self.app.gemini_message_color_var.get()
        }
        self.config["display_settings"] = display_settings
        self.app.config["display_settings"] = display_settings
        self._save_config_to_file(self.config)

    def _restore_display_settings(self):
        if messagebox.askyesno("Confirm Restore", "Are you sure you want to restore display settings to defaults?"):
            default_display_settings = {
                "chat_font_size": 8,
                "speaker_font_size": 12,
                "user_name_color": "#A9DFBF",
                "user_message_color": "#FFFFFF",
                "gemini_name_color": "#A9CCE3",
                "gemini_message_color": "#FFFFFF"
            }
            self.app.chat_font_size_var.set(default_display_settings["chat_font_size"])
            self.app.speaker_font_size_var.set(default_display_settings["speaker_font_size"])
            self.app.user_name_color_var.set(default_display_settings["user_name_color"])
            self.app.user_message_color_var.set(default_display_settings["user_message_color"])
            self.app.gemini_name_color_var.set(default_display_settings["gemini_name_color"])
            self.app.gemini_message_color_var.set(default_display_settings["gemini_message_color"])

            # Update button colors directly
            self.app.ui_elements.user_name_color_button.configure(fg_color=default_display_settings["user_name_color"])
            self.app.ui_elements.user_message_color_button.configure(fg_color=default_display_settings["user_message_color"])
            self.app.ui_elements.gemini_name_color_button.configure(fg_color=default_display_settings["gemini_name_color"])
            self.app.ui_elements.gemini_message_color_button.configure(fg_color=default_display_settings["gemini_message_color"])

            self.config["display_settings"] = default_display_settings
            self.app.config["display_settings"] = default_display_settings
            self._save_config_to_file(self.config)

            messagebox.showinfo("Restored", "Display settings restored to defaults.") # Corrected
