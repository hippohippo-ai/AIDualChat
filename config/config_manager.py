import json
import os
import customtkinter as ctk
from tkinter import messagebox
import keyring
from pydantic import ValidationError

from .models import AppConfig, DisplaySettings, GoogleAPIKey

class ConfigManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.config_file = 'config.json'
        self.service_id = "AIDualChat"

    def load_config(self) -> AppConfig:
        default_config = AppConfig(configurations=[])
        
        config_to_load = None

        if not os.path.exists(self.config_file):
            config_to_load = default_config
        else:
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config_to_load = AppConfig(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                self.app.logger.error("Config file error, restoring defaults.", error=str(e))
                messagebox.showwarning("Config Error", f"Configuration file is corrupt or invalid. Restoring defaults.\nDetails: {e}")
                config_to_load = default_config
        
        migrated_config = self._migrate_old_keyring_key(config_to_load)
        
        self.save_config(migrated_config)
        return migrated_config

    def save_config(self, config_model: AppConfig):
        self.app.config_model = config_model
        with open(self.config_file, 'w', encoding='utf-8') as f:
            # --- MODIFICATION START ---
            # Replaced .json() with .model_dump_json() for Pydantic V2 compatibility
            f.write(config_model.model_dump_json(indent=4))
            # --- MODIFICATION END ---

    def save_language_setting(self, lang: str):
        if self.app.config_model:
            self.app.config_model.language = lang
            self.save_config(self.app.config_model)

    def save_display_settings(self):
        if not self.app.config_model: return
        try:
            new_settings = DisplaySettings(
                chat_font_size=self.app.chat_font_size_var.get(),
                speaker_font_size=self.app.speaker_font_size_var.get(),
                user_name_color=self.app.user_name_color_var.get(),
                user_message_color=self.app.user_message_color_var.get(),
                ai_name_color=self.app.ai_name_color_var.get(),
                ai_message_color=self.app.ai_message_color_var.get(),
            )
            self.app.config_model.display_settings = new_settings
            self.save_config(self.app.config_model)
        except ValidationError as e:
            self.app.logger.error("Error saving display settings", error=str(e))
    
    def _migrate_old_keyring_key(self, current_config: AppConfig) -> AppConfig:
        old_service_id = "GeminiDualChat"
        try:
            old_key = keyring.get_password(old_service_id, "api_key")
            
            if old_key:
                self.app.logger.info("Found API key from old version, attempting migration.")
                
                if not any(k.api_key == old_key for k in current_config.google_keys):
                    self.app.logger.info("Migrating key to new config structure.")
                    new_key_entry = GoogleAPIKey(api_key=old_key, note="Migrated from old version")
                    current_config.google_keys.append(new_key_entry)
                    
                    try:
                        keyring.delete_password(old_service_id, "api_key")
                        self.app.logger.info("Successfully migrated and deleted old keyring entry.")
                    except Exception as e:
                        self.app.logger.error("Failed to delete old keyring entry after migration.", error=str(e))
                else:
                    self.app.logger.info("Old key already exists in config, deleting old keyring entry.")
                    try:
                        keyring.delete_password(old_service_id, "api_key")
                    except Exception as e:
                        self.app.logger.error("Failed to delete redundant old keyring entry.", error=str(e))

        except Exception as e:
            self.app.logger.warning("Could not access keyring for migration check.", error=str(e))
            
        return current_config