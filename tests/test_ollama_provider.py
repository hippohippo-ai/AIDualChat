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