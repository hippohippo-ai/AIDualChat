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

from abc import ABC, abstractmethod

class ProviderError(Exception):
    """Custom exception for provider-related errors."""
    def __init__(self, message, is_fatal=False):
        super().__init__(message)
        self.is_fatal = is_fatal

class BaseProvider(ABC):
    """Abstract base class for all AI providers."""
    def __init__(self, app_instance, state_manager):
        self.app = app_instance
        self.state_manager = state_manager
        self.logger = app_instance.logger.bind(provider=self.__class__.__name__)

    @abstractmethod
    def get_name(self):
        """Return the display name of the provider."""
        pass

    @abstractmethod
    def is_configured(self):
        """Check if the provider has the necessary configuration to operate."""
        pass

    @abstractmethod
    def refresh_status(self):
        """
        Refresh the provider's status, like API key validity or model lists.
        This method should update the central state managed by StateManager.
        """
        pass

    @abstractmethod
    def get_models(self):
        """Return a list of available model names for this provider."""
        pass

    @abstractmethod
    def send_message(self, chat_id, model_config, message, trace_id):
        """
        Send a message to the AI model and handle the response.
        This should be a generator that yields events for the response queue.
        """
        pass

    def get_history_for_api(self, render_history):
        """
        Convert the app's internal render_history to a format
        suitable for the provider's API.
        Default implementation filters out UI-only messages.
        Can be overridden by subclasses if needed.
        """
        return [msg for msg in render_history if not msg.get('is_ui_only', False)]