# AIDualChat - A dual-pane chat application for AI models.
# Copyright (C) 2025 Hippohippo-AI
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# --- START OF UPDATED config/config_manager.py ---

import json
import os
import customtkinter as ctk
from tkinter import messagebox
import keyring
from pydantic import ValidationError

from .models import AppConfig, DisplaySettings, GoogleAPIKey
from services.providers.google_provider import GoogleProvider

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
        
        # --- NEW: Sanitize loaded config before returning ---
        sanitized_config = self._sanitize_loaded_config(config_to_load)

        migrated_config = self._migrate_old_keyring_key(sanitized_config)
        
        self.save_config(migrated_config)
        return migrated_config

    # --- NEW: Method to clean up invalid entries on startup ---
    def _sanitize_loaded_config(self, config: AppConfig) -> AppConfig:
        """
        Validates existing Google keys in the loaded config and removes invalid ones.
        This prevents the app from starting with a broken state from a bad config file.
        """
        initial_key_count = len(config.google_keys)
        valid_keys = []
        for key in config.google_keys:
            # We only check for basic ASCII validity here, not live API validation,
            # to ensure a fast startup. Live validation is done in the StateManager.
            if key.api_key.isascii():
                valid_keys.append(key)
            else:
                self.app.logger.warning("Removing invalid (non-ASCII) Google Key from config on startup.", key_id=key.id, note=key.note)

        if len(valid_keys) < initial_key_count:
            config.google_keys = valid_keys
            messagebox.showwarning(
                self.app.lang.get('info'),
                self.app.lang.get('info_invalid_keys_removed'),
                parent=self.app.root
            )
        return config


    def save_config(self, config_model: AppConfig):
        self.app.config_model = config_model
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write(config_model.model_dump_json(indent=4))

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
                    try:
                        # Validate before migrating
                        new_key_entry = GoogleAPIKey(api_key=old_key, note="Migrated from old version")
                        current_config.google_keys.append(new_key_entry)
                    except ValidationError:
                         self.app.logger.warning("Old key from keyring is invalid (non-ASCII) and will not be migrated.")

                    try:
                        keyring.delete_password(old_service_id, "api_key")
                        self.app.logger.info("Successfully processed and deleted old keyring entry.")
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

# --- END OF UPDATED config/config_manager.py ---