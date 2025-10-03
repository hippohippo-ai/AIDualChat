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

# --- START OF UPDATED config/models.py ---

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Any
import uuid

def new_id():
    return str(uuid.uuid4())

class GoogleAPIKey(BaseModel):
    id: str = Field(default_factory=new_id)
    api_key: str
    note: str = ""

    @field_validator('api_key')
    @classmethod
    def must_be_ascii(cls, v: str) -> str:
        if not v.isascii():
            raise ValueError('API Key must contain only ASCII characters.')
        return v

class OllamaSettings(BaseModel):
    host: str = "http://localhost:11434"

class Preset(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    provider: str
    model: str
    key_id: Optional[str] = None

class AIConfig(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    key_id: Optional[str] = None
    preset_id: Optional[str] = None
    persona_prompt: str = "You are a helpful assistant."
    context_prompt: str = ""
    # --- FIX: Replaced confloat with Field validation for Pydantic V2 ---
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    web_search_enabled: bool = False

class ConfigurationProfile(BaseModel):
    name: str
    description: str
    ai_1: AIConfig = Field(default_factory=AIConfig)
    ai_2: AIConfig = Field(default_factory=AIConfig)

class DisplaySettings(BaseModel):
    # --- FIX: Replaced conint with Field validation for Pydantic V2 ---
    chat_font_size: int = Field(default=12, ge=6, le=30)
    speaker_font_size: int = Field(default=14, ge=6, le=30)
    user_name_color: str = "#A9DFBF"
    user_message_color: str = "#FFFFFF"
    ai_name_color: str = "#A9CCE3"
    ai_message_color: str = "#FFFFFF"

class AppConfig(BaseModel):
    version: int = 2
    # --- FIX: Replaced confloat with Field validation for Pydantic V2 ---
    auto_reply_delay_minutes: float = Field(default=1.0, ge=0.0)
    # --- FIX: Replaced conint with Field validation for Pydantic V2 ---
    active_config_index: int = Field(default=0, ge=0, le=9)
    language: str = "en"
    
    preferred_models: List[str] = Field(default_factory=lambda: ["gemini-2.5-pro", "gemini-2.5-flash"])
    
    google_keys: List[GoogleAPIKey] = Field(default_factory=list)
    ollama_settings: OllamaSettings = Field(default_factory=OllamaSettings)
    presets: List[Preset] = Field(default_factory=list)
    
    configurations: List[ConfigurationProfile]
    display_settings: DisplaySettings = Field(default_factory=DisplaySettings)

    @model_validator(mode='before')
    @classmethod
    def ensure_ten_configs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Use .get() to avoid KeyError if the key doesn't exist yet
            configurations = data.get('configurations', [])
            if configurations is None: # Handle case where "configurations": null is in the json
                configurations = []

            if len(configurations) < 10:
                for i in range(len(configurations), 10):
                    configurations.append({'name': f"Config {i}", 'description': ""})
            data['configurations'] = configurations[:10]
        return data

    def get_active_configuration(self):
        return self.configurations[self.active_config_index]

    def get_google_key_by_id(self, key_id: str) -> Optional[GoogleAPIKey]:
        return next((key for key in self.google_keys if key.id == key_id), None)

    def get_preset_by_id(self, preset_id: str) -> Optional[Preset]:
        return next((p for p in self.presets if p.id == preset_id), None)

# --- END OF UPDATED config/models.py ---