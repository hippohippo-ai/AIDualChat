# --- START OF CORRECTED state_manager.py ---

import threading
import time
from collections import deque

from services.providers.google_provider import GoogleProvider
from services.providers.ollama_provider import OllamaProvider

class StateManager:
    def __init__(self, app_instance, config_model):
        self.app = app_instance
        self.logger = app_instance.logger
        self.config_model = config_model
        
        self.providers = {
            "Google": GoogleProvider(app_instance, self),
            "Ollama": OllamaProvider(app_instance, self)
        }
        
        self._refresh_thread = None
        self._stop_event = threading.Event()

    def get_provider(self, provider_name):
        return self.providers.get(provider_name)

    def start_background_refresh(self):
        self.logger.info("Starting background state refresh thread.")
        self._stop_event.clear()
        self._refresh_thread = threading.Thread(target=self._run_refresh_loop, daemon=True)
        self._refresh_thread.start()

    def stop_background_refresh(self):
        self.logger.info("Stopping background state refresh thread.")
        self._stop_event.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=5)

    def _run_refresh_loop(self):
        self.app.logger.info("Background refresh loop started.")
        # Initial refresh on startup
        self.refresh_all_provider_states(is_startup=True)

        while not self._stop_event.is_set():
            self._stop_event.wait(600) # Wait for 10 minutes or until stopped
            if not self._stop_event.is_set():
                self.refresh_all_provider_states()
        self.app.logger.info("Background refresh loop stopped.")

    def refresh_all_provider_states(self, is_startup=False):
        self.logger.info("Executing periodic state refresh for all providers.")
        for name, provider in self.providers.items():
            if provider.is_configured():
                self.logger.info(f"Refreshing state for provider: {name}")
                provider.refresh_status()
        
        # --- START OF FIX ---
        # Schedule UI updates to run on the main thread after state has been refreshed.
        if hasattr(self.app, 'main_window'):
            # Update Model Manager window if it's open
            if self.app.main_window.model_manager_window and self.app.main_window.model_manager_window.winfo_exists():
                self.app.root.after(0, self.app.main_window.model_manager_window.update_provider_tabs)
            
            # ALWAYS update the right sidebar and status indicator
            self.app.root.after(0, self.app.main_window.right_sidebar.handle_state_update, is_startup)
            self.app.root.after(0, self.app.main_window.update_status_indicator)
        # --- END OF FIX ---


    def get_google_keys(self):
        return self.config_model.google_keys

    def get_next_available_google_key(self, failed_key_id=None):
        keys = self.get_google_keys()
        if not keys:
            return None

        key_deque = deque(keys)
        # Rotate deque until the failed key is at the front, if provided
        if failed_key_id:
            try:
                index = next(i for i, key in enumerate(key_deque) if key.id == failed_key_id)
                key_deque.rotate(-index)
                key_deque.popleft() # Remove the failed key from consideration for this turn
            except StopIteration:
                pass # Failed key not found, start from the beginning

        # Find the next key that is not in an error state
        for _ in range(len(key_deque)):
            key = key_deque.popleft()
            provider = self.get_provider("Google")
            if provider and provider.get_key_status(key.id).get("is_valid", False):
                self.logger.info(f"Found next available Google key.", key_id=key.id, note=key.note)
                return key
        
        self.logger.warning("No available Google keys found after checking all options.")
        return None

# --- END OF CORRECTED state_manager.py ---