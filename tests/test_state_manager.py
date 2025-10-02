from collections import deque
from unittest.mock import MagicMock, patch

from services.state_manager import StateManager
from config.models import GoogleAPIKey

def test_get_next_available_google_key_simple_case(mock_app):
    """Test finding the next valid key in a simple scenario."""
    key1 = GoogleAPIKey(id="key1", api_key="123", note="Valid Key")
    key2 = GoogleAPIKey(id="key2", api_key="456", note="Invalid Key")
    
    mock_app.config_model.get_google_keys.return_value = [key1, key2]
    
    state_manager = StateManager(mock_app, mock_app.config_model)
    
    # Mock the provider and its status check
    mock_google_provider = MagicMock()
    mock_google_provider.get_key_status.side_effect = lambda key_id: {"is_valid": True} if key_id == "key1" else {"is_valid": False}
    state_manager.get_provider = MagicMock(return_value=mock_google_provider)
    
    next_key = state_manager.get_next_available_google_key()
    
    assert next_key is not None
    assert next_key.id == "key1"

def test_get_next_available_google_key_with_failover(mock_app):
    """Test that it correctly skips a failed key and finds the next valid one."""
    key1 = GoogleAPIKey(id="key1", api_key="123", note="Failed Key")
    key2 = GoogleAPIKey(id="key2", api_key="456", note="Valid Key")
    key3 = GoogleAPIKey(id="key3", api_key="789", note="Another Valid Key")
    
    mock_app.config_model.get_google_keys.return_value = [key1, key2, key3]
    
    state_manager = StateManager(mock_app, mock_app.config_model)

    mock_google_provider = MagicMock()
    mock_google_provider.get_key_status.side_effect = lambda key_id: {"is_valid": False} if key_id == "key1" else {"is_valid": True}
    state_manager.get_provider = MagicMock(return_value=mock_google_provider)
    
    next_key = state_manager.get_next_available_google_key(failed_key_id="key1")
    
    assert next_key is not None
    assert next_key.id == "key2"