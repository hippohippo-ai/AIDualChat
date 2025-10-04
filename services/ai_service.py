# services/ai_service.py

import threading
from services.providers.base_provider import ProviderError

class AIService:
    def __init__(self, app_instance):
        self.app = app_instance
        self.logger = app_instance.logger
        self.state_manager = app_instance.state_manager
        self.response_queue = app_instance.response_queue
        self.lang = app_instance.lang

    def send_message(self, chat_id, message, trace_id):
        """
        UI层调用的唯一入口。
        启动一个新线程来处理API调用和故障转移。
        """
        thread = threading.Thread(
            target=self._api_call_thread_with_failover,
            args=(chat_id, message, trace_id)
        )
        thread.daemon = True
        thread.start()

    def _api_call_thread_with_failover(self, chat_id, message, trace_id):
        """
        这个方法包含了之前在 RightSidebarHandler 中的所有业务逻辑。
        """
        pane = self.app.chat_panes[chat_id]
        
        # 增加生成ID，为停止生成做准备
        pane.current_generation_id += 1
        self.app.root.after(0, pane.update_ui_for_sending)
        
        active_config = self.app.active_ai_config[chat_id].copy()
        active_config['generation_id'] = pane.current_generation_id
        
        provider_name = active_config.get("provider")
        provider = self.state_manager.get_provider(provider_name)

        if not provider or not active_config.get("model") or active_config.get("model", "").startswith("---"):
            self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': self.lang.get('error_provider_model_selection')})
            self.app.root.after(0, pane.restore_ui_after_response)
            return

        try:
            for event in provider.send_message(chat_id, active_config, message, trace_id):
                event['chat_id'] = chat_id
                event['generation_id'] = active_config['generation_id']
                self.response_queue.put(event)
        
        except ProviderError as e:
            if provider_name == "Google" and not e.is_fatal:
                self.logger.warning("Google provider error, attempting failover.", error=str(e))
                self._handle_google_failover(chat_id, active_config, message, trace_id, str(e))
            else:
                self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': str(e)})
                self.app.root.after(0, pane.restore_ui_after_response)
        
        except Exception as e:
            self.logger.error("An unexpected error occurred in the API thread.", error=str(e), exc_info=True)
            self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"An unexpected error occurred: {e}"})
            self.app.root.after(0, pane.restore_ui_after_response)

    def _handle_google_failover(self, chat_id, active_config, message, trace_id, original_error):
        failed_key_id = active_config.get("key_id")
        key_obj = self.app.config_model.get_google_key_by_id(failed_key_id)
        failed_key_note = key_obj.note if key_obj else "N/A"
        next_key = self.state_manager.get_next_available_google_key(failed_key_id)

        if next_key:
            system_msg = self.lang.get('failover_message', old_key_note=failed_key_note, new_key_note=next_key.note)
            self.response_queue.put({'type': 'system', 'chat_id': chat_id, 'text': system_msg})
            
            # 更新UI层的配置状态
            self.app.active_ai_config[chat_id]['key_id'] = next_key.id
            self.app.root.after(0, self.app.main_window.right_sidebar.update_selectors_for_pane, chat_id)
            
            # 重新尝试
            self._api_call_thread_with_failover(chat_id, message, trace_id)
        else:
            self.logger.error("Failover failed: No other available Google keys.")
            failover_failed_msg = self.lang.get('failover_failed_no_keys') + f" Original error: {original_error}"
            self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': failover_failed_msg})
            self.app.root.after(0, self.app.chat_panes[chat_id].restore_ui_after_response)