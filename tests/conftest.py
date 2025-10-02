import pytest
from unittest.mock import MagicMock

# This file sets up fixtures that can be used by all test files.
# A fixture provides a fixed baseline upon which tests can reliably and repeatedly execute.

@pytest.fixture
def mock_app():
    """Creates a mock of the main application class with necessary attributes."""
    app = MagicMock()
    app.logger = MagicMock()
    app.config_model = MagicMock()
    # Mock any other top-level attributes needed by the classes under test
    return app

@pytest.fixture
def mock_state_manager(mock_app):
    """Creates a mock of the StateManager."""
    state_manager = MagicMock()
    state_manager.app = mock_app
    state_manager.logger = mock_app.logger
    state_manager.config_model = mock_app.config_model
    return state_manager