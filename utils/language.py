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

class LanguageManager:
    def __init__(self, initial_language='en'):
        self.texts = {
            'en': {
                # General
                'error': 'Error', 'success': 'Success', 'info': 'Info', 'status': 'Status', 'confirm': 'Confirm',
                # Main Window
                'studio': 'AI STUDIO', 'session_management': 'Session Management', 'display': 'Display',
                'new_session': 'New Session', 'save_ai_1': 'Save AI 1', 'save_ai_2': 'Save AI 2',
                'load_ai_1': 'Load AI 1', 'load_ai_2': 'Load AI 2', 'language': 'Language:',
                'model_manager': 'Model Manager',
                'export_ai_1': 'Export AI 1', 'export_ai_2': 'Export AI 2', 
                'smart_export_ai_1': 'Smart Export AI 1', 'smart_export_ai_2': 'Smart Export AI 2',
                'status_tooltip': 'Green: All services OK.\nYellow: No services configured.\nRed: At least one service has an error.',
                # Display Panel
                'speaker_font_size': 'Speaker Font:', 'chat_font_size': 'Chat Font:',
                'chat_colors': 'Chat Colors:', 'user_name': 'User Name', 'user_message': 'User Message',
                'ai_name': 'AI Name', 'ai_message': 'AI Message', 'restore_defaults': 'Restore Defaults',
                'confirm_restore_defaults': 'Restore display settings to default?',
                'defaults_restored': 'Defaults restored.', 'choose_color': 'Choose Color',
                # Chat Core & Pane
                'you': 'You', 'session_reset_msg': '--- New session started ---',
                'session_loaded_msg': '--- Session successfully loaded ---',
                'generation_stopped': '\n---\n- Generation stopped by user. ---\n',
                'info_no_previous_message': 'No previous message to regenerate from.',
                'failover_message': '--- [System] API Key "{old_key_note}" failed. Automatically switched to key "{new_key_note}". Retrying... ---',
                'send': 'Send', 'stop': 'Stop', 'regen': 'Regen',
                'auto_reply_to': 'Auto-reply to AI {}',
                'error_no_conversation_to_export': 'There is no conversation to export.',
                'export_successful': 'Conversation successfully exported to\n{}',
                'export_failed': 'An error occurred during export: {}',
                'info_no_smart_content': 'No content marked with [START_SCENE]...[END_SCENE] was found.',
                # Right Sidebar
                'configuration': 'CONFIGURATION PROFILE', 'description': 'Description:', 'save_active_config': 'Save to Active Profile',
                'ai_settings': 'AI {} Settings', 'provider': 'Provider:', 'model': 'Model:', 'api_key': 'API Key:', 'preset': 'Preset:',
                'select_provider': '--- Select Provider ---', 'select_model': '--- Select Model ---',
                'select_key': '--- Select Key ---', 'select_preset': '--- Select Preset ---',
                'no_models_available': '--- No Models Available ---', 'no_keys_available': '--- No Keys Available ---',
                'no_presets_available': '--- No Presets Available ---',
                'persona': 'Persona (System Prompt)', 'context': 'Context', 'temperature': 'Temperature: {:.2f}',
                'web_search_enabled': 'Enable Web Search (Google Only)', 'files': 'Attachments',
                'confirm_apply_config': 'Applying this profile will reset both chat sessions. Continue?',
                'config_saved': 'Profile saved successfully.', 'error_provider_model_selection': 'Error: Provider or model not selected.',
                'global_settings': 'Global Settings','auto_reply_delay': 'Auto-Reply Delay (min):',
                # Model Manager
                'provider_google': 'Google', 'provider_ollama': 'Ollama', 'presets': 'Presets',
                'save_and_refresh': 'Save & Refresh', 'refresh': 'Refresh', 'add_key': 'Add Key',
                'delete_key': 'Delete Selected', 'api_key_note': 'Note (e.g., Personal Key)',
                'key_value': 'API Key Value', 'saved_google_keys': 'Saved Google API Keys',
                'ollama_host': 'Ollama Host Address:', 'ollama_status': 'Status:', 'ollama_version': 'Version:',
                'ollama_models': 'Available Models:', 'status_ok': 'OK', 'status_error': 'Error', 'status_unknown': 'Unknown',
                'status_unconfigured': 'Not Configured', 'status_unavailable': 'Unavailable',
                'preset_name': 'Preset Name:', 'add_preset': 'Add Preset', 'delete_preset': 'Delete Selected',
                'saved_presets': 'Saved Presets', 'error_preset_fields': 'Preset Name, Provider, and Model are required.',
                'error_preset_key': 'An API Key is required for Google presets.',
                'validating': 'Validating...', 'error_key_empty': 'API Key value cannot be empty.',
                'info_invalid_keys_removed': 'One or more invalid API keys were found in your configuration and have been removed.',
                'no_note': 'No Note',
                'validating': 'Validating...',
                'error_key_empty': 'API Key value cannot be empty.',
                'error_host_empty': 'Ollama host cannot be empty.',
                'error_invalid_key_selection': 'Invalid API Key selection for preset.',
                'info_invalid_keys_removed': 'One or more invalid API keys were found in your configuration and have been removed.',
                'status_invalid': 'Invalid',
                'status_permissions_error': 'Permissions Error',
                'failover_failed_no_keys': 'Failover failed: No other available Google keys.',
            },
            'zh': {
                'error': '错误', 'success': '成功', 'info': '信息', 'status': '状态', 'confirm': '确认',
                'studio': 'AI 工作室', 'session_management': '会话管理', 'display': '显示设置',
                'new_session': '新会话', 'save_ai_1': '保存 AI 1', 'save_ai_2': '保存 AI 2',
                'load_ai_1': '加载 AI 1', 'load_ai_2': '加载 AI 2', 'language': '语言:',
                'model_manager': '模型管理器', 'export_ai_1': '导出 AI 1', 'export_ai_2': '导出 AI 2', 
                'smart_export_ai_1': '智能导出 AI 1', 'smart_export_ai_2': '智能导出 AI 2',
                'status_tooltip': '绿色: 所有服务正常。\n黄色: 未配置任何服务。\n红色: 至少一个服务出错。',
                'speaker_font_size': '角色字号:', 'chat_font_size': '聊天字号:',
                'chat_colors': '聊天颜色:', 'user_name': '用户名称', 'user_message': '用户消息',
                'ai_name': 'AI 名称', 'ai_message': 'AI 消息', 'restore_defaults': '恢复默认',
                'confirm_restore_defaults': '确定要将显示设置恢复为默认值吗？',
                'defaults_restored': '已恢复默认设置。', 'choose_color': '选择颜色',
                'you': '您', 'session_reset_msg': '--- 新会话已开始 ---',
                'session_loaded_msg': '--- 会话已成功加载 ---',
                'generation_stopped': '\n---\n- 用户已停止生成。 ---\n',
                'info_no_previous_message': '没有可重新生成的消息。',
                'failover_message': '--- [系统] API密钥 "{old_key_note}" 调用失败。已自动切换到密钥 "{new_key_note}" 并重试... ---',
                'send': '发送', 'stop': '停止', 'regen': '重试', 'auto_reply_to': '自动回复 AI {}',
                'error_no_conversation_to_export': '没有可供导出的对话。',
                'export_successful': '对话已成功导出至\n{}',
                'export_failed': '导出过程中发生错误: {}',
                'info_no_smart_content': '未找到用 [START_SCENE]...[END_SCENE] 标记的内容。',
                'configuration': '配置档案', 'description': '描述:', 'save_active_config': '保存到当前档案',
                'ai_settings': 'AI {} 设定', 'provider': '服务商:', 'model': '模型:', 'api_key': 'API 密钥:', 'preset': '预设:',
                'select_provider': '--- 选择服务商 ---', 'select_model': '--- 选择模型 ---',
                'select_key': '--- 选择密钥 ---', 'select_preset': '--- 选择预设 ---',
                'no_models_available': '--- 无可用模型 ---', 'no_keys_available': '--- 无可用密钥 ---',
                'no_presets_available': '--- 无可用预设 ---',
                'persona': '角色设定', 'context': '情景指令', 'temperature': '温度: {:.2f}',
                'web_search_enabled': '启用联网搜索 (仅限谷歌)', 'files': '附件',
                'confirm_apply_config': '应用此档案将重置两个聊天会话。要继续吗？',
                'config_saved': '档案已成功保存。', 'error_provider_model_selection': '错误：未选择服务商或模型。',
                'provider_google': '谷歌', 'provider_ollama': 'Ollama', 'presets': '预设组合',
                'save_and_refresh': '保存并刷新', 'refresh': '刷新', 'add_key': '添加密钥',
                'delete_key': '删除选中', 'api_key_note': '备注 (例如：个人测试密钥)',
                'key_value': 'API 密钥值', 'saved_google_keys': '已保存的谷歌 API 密钥',
                'ollama_host': 'Ollama 主机地址:', 'ollama_status': '状态:', 'ollama_version': '版本:',
                'ollama_models': '可用模型:', 'status_ok': '正常', 'status_error': '错误', 'status_unknown': '未知',
                'status_unconfigured': '未配置', 'status_unavailable': '不可用',
                'preset_name': '预设名称:', 'add_preset': '添加预设', 'delete_preset': '删除选中',
                'saved_presets': '已保存的预设', 'error_preset_fields': '预设名称、服务商和模型为必填项。',
                'error_preset_key': '谷歌预设需要选择一个 API 密钥。',
                'global_settings': '全局设置','auto_reply_delay': '自动回复延迟 (分钟):',
                'validating': '验证中...','error_key_empty': 'API 密钥值不能为空。',
                'info_invalid_keys_removed': '在您的配置中发现一个或多个无效的API密钥，并已将其移除。',
                'no_note': '无备注',
                'validating': '验证中...',
                'error_key_empty': 'API 密钥值不能为空。',
                'error_host_empty': 'Ollama 主机地址不能为空。',
                'error_invalid_key_selection': '无效的预设 API 密钥选项。',
                'info_invalid_keys_removed': '在您的配置中发现一个或多个无效的API密钥，并已将其移除。',
                'status_invalid': '无效',
                'status_permissions_error': '权限错误',
                'failover_failed_no_keys': '自动切换失败：没有其他可用的谷歌密钥。',
            }
        }
        self.language = initial_language

    def set_language(self, lang):
        if lang in self.texts:
            self.language = lang

    def get(self, key, *args):
        text = self.texts[self.language].get(key)
        if text is None:
            text = self.texts['en'].get(key, key)
        if args:
            return text.format(*args)
        return text
