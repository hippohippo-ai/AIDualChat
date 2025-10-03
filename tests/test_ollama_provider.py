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

from unittest.mock import MagicMock, patch
import requests

from services.providers.ollama_provider import OllamaProvider
from config.models import OllamaSettings

# We use the 'mocker' fixture provided by pytest-mock to easily patch external libraries
def test_refresh_status_success(mocker, mock_app, mock_state_manager):
    """Test successful refresh of Ollama status."""
    mock_state_manager.config_model.ollama_settings = OllamaSettings(host="http://test.host:1234")
    
    provider = OllamaProvider(mock_app, mock_state_manager)

    # Mock the 'requests.get' calls
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = [
        {"version": "0.1.2"}, # Response for /api/version
        {"models": [{"name": "llama3:latest"}, {"name": "test-model:7b"}]} # Response for /api/tags
    ]
    mocker.patch('requests.get', return_value=mock_response)
    
    provider.refresh_status()
    
    status = provider.get_status()
    assert status["is_available"] is True
    assert status["version"] == "0.1.2"
    assert "llama3:latest" in status["models"]
    assert "test-model:7b" in status["models"]

def test_refresh_status_connection_error(mocker, mock_app, mock_state_manager):
    """Test how the provider handles a connection error."""
    mock_state_manager.config_model.ollama_settings = OllamaSettings(host="http://bad.host:1234")
    
    provider = OllamaProvider(mock_app, mock_state_manager)
    
    # Make the requests.get call raise a connection error
    mocker.patch('requests.get', side_effect=requests.exceptions.ConnectionError("Test connection error"))
    
    provider.refresh_status()
    
    status = provider.get_status()
    assert status["is_available"] is False
    assert status["version"] == "Connection Error"
    assert status["models"] == []