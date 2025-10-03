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