# --- START OF UPDATED language.py ---

class LanguageManager:
    def __init__(self, initial_language='en'):
        self.texts = {
            'en': {
                'studio': 'STUDIO',
                'session_management': 'Session Management',
                'new_session': 'New Session',
                'save_gemini_1': 'Save Gemini 1',
                'save_gemini_2': 'Save Gemini 2',
                'load_gemini_1': 'Load Gemini 1',
                'load_gemini_2': 'Load Gemini 2',
                'export_gemini_1': 'Export Gemini 1',
                'export_gemini_2': 'Export Gemini 2',
                'smart_export_g1': 'Smart Export G1',
                'smart_export_g2': 'Smart Export G2',
                'display': 'Display',
                'language': 'Language',
                'name_font_size': 'Name Font Size:',
                'chat_font_size': 'Chat Font Size:',
                'chat_colors': 'Chat Colors:',
                'user_name': 'User Name',
                'user_message': 'User Message',
                'gemini_name': 'Gemini Name',
                'gemini_message': 'Gemini Message',
                'restore_defaults': 'Restore Defaults',
                'configuration': 'CONFIGURATION',
                'description': 'Description:',
                'save_active_config': 'Save to Active Config',
                'gemini_1_model': 'Gemini 1 Model',
                'gemini_2_model': 'Gemini 2 Model',
                'auto_reply_delay': 'Auto-Reply Delay (min)',
                'set_api_key': 'Set API Key',
                'gemini_settings': 'Gemini {} Settings',
                'persona': 'Persona',
                'context': 'Context',
                'temperature': 'Temperature: {:.2f}',
                'web_search_enabled': 'Enable Web Search',
                'files': 'Attachments',
                'send': 'Send',
                'stop': 'Stop',
                'regen': 'Regen',
                'auto_reply_to': 'Auto-reply to Gemini {}',
                'session_reset_msg': '--- Session reset with model: {} ---',
                'session_loaded_msg': '--- Loaded session with model: {} ---',
                'searching_web': '--- Searching web for: "{}"... ---',
                'search_results_info': '--- Web search results provided to model ---',
                'web_search_failed_fallback': '\n--- ⚠️ Web search failed. Retrying in normal mode... ---\n', # NEW
                'generation_stopped': '\n---\n- Generation stopped by user. ---\n',
                'info_no_previous_message': 'No previous message to regenerate from.',
                'warn_rewind_fail': 'Could not rewind API session. Re-priming session from history.',
            },
            'zh': {
                'studio': '工作室',
                'session_management': '会话管理',
                'new_session': '新会话',
                'save_gemini_1': '保存 Gemini 1',
                'save_gemini_2': '保存 Gemini 2',
                'load_gemini_1': '加载 Gemini 1',
                'load_gemini_2': '加载 Gemini 2',
                'export_gemini_1': '导出 Gemini 1',
                'export_gemini_2': '导出 Gemini 2',
                'smart_export_g1': '智能导出 G1',
                'smart_export_g2': '智能导出 G2',
                'display': '显示设置',
                'language': '语言',
                'name_font_size': '名称字号:',
                'chat_font_size': '聊天字号:',
                'chat_colors': '聊天颜色:',
                'user_name': '用户名称',
                'user_message': '用户消息',
                'gemini_name': 'Gemini 名称',
                'gemini_message': 'Gemini 消息',
                'restore_defaults': '恢复默认',
                'configuration': '配置',
                'description': '描述:',
                'save_active_config': '保存到当前配置',
                'gemini_1_model': 'Gemini 1 模型',
                'gemini_2_model': 'Gemini 2 模型',
                'auto_reply_delay': '自动回复延迟 (分钟)',
                'set_api_key': '设置 API Key',
                'gemini_settings': 'Gemini {} 设定',
                'persona': '角色设定',
                'context': '情景指令',
                'temperature': '温度: {:.2f}',
                'web_search_enabled': '启用联网搜索',
                'files': '附件',
                'send': '发送',
                'stop': '停止',
                'regen': '重试',
                'auto_reply_to': '自动回复 Gemini {}',
                'session_reset_msg': '--- 会话已重置，模型: {} ---',
                'session_loaded_msg': '--- 会话已加载，模型: {} ---',
                'searching_web': '--- 正在联网搜索: "{}"... ---',
                'search_results_info': '--- 已将网络搜索结果提供给模型 ---',
                'web_search_failed_fallback': '\n--- ⚠️ 联网搜索失败，正在以普通模式重试... ---\n', # NEW
                'generation_stopped': '\n---\n- 已被用户停止生成。 ---\n',
                'info_no_previous_message': '没有可重新生成的消息。',
                'warn_rewind_fail': '无法回滚 API 会话，正在从历史记录重新建立会话。',
            }
        }
        self.language = initial_language

    def set_language(self, lang):
        if lang in self.texts:
            self.language = lang

    def get(self, key, *args):
        text = self.texts[self.language].get(key, key)
        if args:
            return text.format(*args)
        return text

# --- END OF UPDATED language.py ---