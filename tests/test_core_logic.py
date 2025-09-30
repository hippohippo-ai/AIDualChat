import pytest
import os
import json
from unittest.mock import MagicMock, patch

# 假设你的文件结构是：
# project/
# |- main.py
# |- config_manager.py
# |- gemini_api.py
# |- tests/
#   |- test_core_logic.py

# 为了能导入你的模块，可能需要设置PYTHONPATH或在测试文件中添加sys.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager import ConfigManager
from chat_core import ChatCore

# --- Fixtures: 可复用的测试设置 ---

@pytest.fixture
def mock_app():
    """创建一个模拟的App实例，包含测试所需的最少属性"""
    app = MagicMock()
    app.config = {}
    app.chat_font_size_var = MagicMock()
    app.speaker_font_size_var = MagicMock()
    app.user_name_color_var = MagicMock()
    # ... 为 ConfigManager 需要的所有 app 属性创建 mock ...
    return app

@pytest.fixture
def temp_config_file(tmp_path):
    """创建一个临时的配置文件路径"""
    return tmp_path / "test_config.json"

# --- 测试 ConfigManager ---

def test_config_manager_creates_default_config(mock_app, temp_config_file):
    """测试: 当配置文件不存在时，ConfigManager是否能创建默认配置"""
    # 准备
    cm = ConfigManager(mock_app)
    cm.config_file = str(temp_config_file)
    
    # 执行
    cm.load_config()
    
    # 断言
    assert temp_config_file.exists()
    with open(temp_config_file, 'r') as f:
        config_data = json.load(f)
    assert "api_key" in config_data
    assert config_data["active_config_index"] == 0
    assert len(config_data["configurations"]) == 10

def test_config_manager_loads_existing_config(mock_app, temp_config_file):
    """测试: ConfigManager是否能正确加载已存在的配置文件"""
    # 准备
    custom_config = {
        "api_key": "my_test_key", 
        "active_config_index": 5,
        "configurations": [{"name": "Config 0", "description": "Test Desc"}] # 简化
    }
    with open(temp_config_file, 'w') as f:
        json.dump(custom_config, f)
        
    cm = ConfigManager(mock_app)
    cm.config_file = str(temp_config_file)
    
    # 执行
    cm.load_config()
    
    # 断言
    assert cm.config["api_key"] == "my_test_key"
    assert cm.config["active_config_index"] == 5
    assert cm.config["configurations"][0]["description"] == "Test Desc"


# --- 测试 ChatCore (示例) ---

@pytest.fixture
def mock_app_for_chatcore():
    """为ChatCore创建一个更详细的mock app"""
    app = MagicMock()
    # 模拟md.render, 否则会报错
    app.md.render.return_value = "<p>mocked html</p>"
    # 模拟UI变量
    app.chat_font_size_var.get.return_value = 10
    app.speaker_font_size_var.get.return_value = 14
    app.user_name_color_var.get.return_value = "#FFFFFF"
    app.user_message_color_var.get.return_value = "#FFFFFF"
    app.gemini_name_color_var.get.return_value = "#FFFFFF"
    app.gemini_message_color_var.get.return_value = "#FFFFFF"
    app.COLOR_BACKGROUND = "#000000"
    
    # 模拟聊天显示组件
    app.chat_displays = {1: MagicMock()}
    
    return app

def test_render_chat_display_generates_html(mock_app_for_chatcore):
    """测试: _render_chat_display 是否能根据历史记录生成HTML"""
    # 准备
    chat_id = 1
    mock_app_for_chatcore.render_history = {
        chat_id: [
            {'role': 'user', 'parts': [{'text': 'Hello'}]},
            {'role': 'model', 'parts': [{'text': 'Hi there'}]}
        ]
    }
    cc = ChatCore(mock_app_for_chatcore)
    
    # 执行
    cc._render_chat_display(chat_id)
    
    # 断言
    # 检查 set_html 是否被调用
    mock_app_for_chatcore.chat_displays[chat_id].set_html.assert_called_once()
    # 获取传递给 set_html 的参数 (HTML字符串)
    html_output = mock_app_for_chatcore.chat_displays[chat_id].set_html.call_args[0][0]
    
    assert "You:" in html_output
    assert "Gemini 1:" in html_output
    assert "<p>mocked html</p>" in html_output # 检查内容是否被渲染