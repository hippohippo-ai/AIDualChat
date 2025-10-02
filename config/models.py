from pydantic import BaseModel, Field, conint, confloat, validator
from typing import List, Optional
import uuid

def new_id():
    return str(uuid.uuid4())

class GoogleAPIKey(BaseModel):
    id: str = Field(default_factory=new_id)
    api_key: str
    note: str = ""

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
    temperature: confloat(ge=0.0, le=2.0) = 0.7
    web_search_enabled: bool = False

class ConfigurationProfile(BaseModel):
    name: str
    description: str
    ai_1: AIConfig = Field(default_factory=AIConfig)
    ai_2: AIConfig = Field(default_factory=AIConfig)

class DisplaySettings(BaseModel):
    chat_font_size: conint(ge=6, le=30) = 12
    speaker_font_size: conint(ge=6, le=30) = 14
    user_name_color: str = "#A9DFBF"
    user_message_color: str = "#FFFFFF"
    ai_name_color: str = "#A9CCE3"
    ai_message_color: str = "#FFFFFF"

class AppConfig(BaseModel):
    version: int = 2
    auto_reply_delay_minutes: confloat(ge=0.0) = 1.0
    active_config_index: conint(ge=0, le=9) = 0
    language: str = "en"
    
    # --- FIXED: Re-added preferred_models ---
    preferred_models: List[str] = ["gemini-2.5-pro", "gemini-2.5-flash"]
    
    google_keys: List[GoogleAPIKey] = Field(default_factory=list)
    ollama_settings: OllamaSettings = Field(default_factory=OllamaSettings)
    presets: List[Preset] = Field(default_factory=list)
    
    configurations: List[ConfigurationProfile]
    display_settings: DisplaySettings = Field(default_factory=DisplaySettings)

    @validator('configurations', pre=True, always=True)
    def ensure_ten_configs(cls, v):
        if v is None: v = []
        if len(v) < 10:
            for i in range(len(v), 10):
                v.append(ConfigurationProfile(name=f"Config {i}", description=""))
        return v[:10]

    def get_active_configuration(self):
        return self.configurations[self.active_config_index]

    def get_google_key_by_id(self, key_id: str) -> Optional[GoogleAPIKey]:
        return next((key for key in self.google_keys if key.id == key_id), None)

    def get_preset_by_id(self, preset_id: str) -> Optional[Preset]:
        return next((p for p in self.presets if p.id == preset_id), None)