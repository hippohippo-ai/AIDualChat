import customtkinter as ctk
import threading
from tkinter import messagebox
from services.providers.base_provider import ProviderError
from config.models import AIConfig

class RightSidebarHandler:
    def __init__(self, app_instance, main_window):
        self.app = app_instance
        self.main_window = main_window
        self.lang = app_instance.lang
        self.lang_updatable_widgets = []

        self.sidebar_frame = None
        self.content_frame = None
        self.toggle_button = None
        
        self.provider_vars = {1: ctk.StringVar(), 2: ctk.StringVar()}
        self.model_vars = {1: ctk.StringVar(), 2: ctk.StringVar()}
        self.key_vars = {1: ctk.StringVar(), 2: ctk.StringVar()}
        self.preset_vars = {1: ctk.StringVar(), 2: ctk.StringVar()}
        
        self.provider_selectors = {1: None, 2: None}
        self.model_selectors = {1: None, 2: None}
        self.key_selectors = {1: None, 2: None}
        self.preset_selectors = {1: None, 2: None}
        
        self.persona_prompts = {1: None, 2: None}
        self.context_prompts = {1: None, 2: None}
        self.temp_vars = {1: ctk.DoubleVar(value=0.7), 2: ctk.DoubleVar(value=0.7)}
        self.temp_labels = {1: None, 2: None}
        self.web_search_vars = {1: ctk.BooleanVar(), 2: ctk.BooleanVar()}
        
        self.header_labels = {}
        self.dropdown_labels = {}
        
        self.config_selector_var = ctk.StringVar()
        self.config_description_entry = None

    def create_sidebar(self, parent):
        self.sidebar_frame = ctk.CTkFrame(parent, width=self.app.RIGHT_SIDEBAR_WIDTH_FULL, fg_color=self.app.COLOR_SIDEBAR, corner_radius=10)
        self.sidebar_frame.pack_propagate(False)
        
        toggle_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        toggle_frame.pack(fill="x", pady=5, padx=5)
        
        self.toggle_button = ctk.CTkButton(toggle_frame, text="▶", command=self.toggle_sidebar, width=25, height=25, font=self.app.FONT_GENERAL)
        self.toggle_button.pack(anchor="nw")

        self.content_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        
        self._create_configuration_selector_panel(self.content_frame)
        ctk.CTkFrame(self.content_frame, height=2, fg_color=self.app.COLOR_BORDER).pack(fill="x", padx=15, pady=10)
        
        scrollable_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True)

        self._create_model_settings_panel(scrollable_frame, 1)
        self._create_model_settings_panel(scrollable_frame, 2)
        
        # --- FIXED: Re-added Auto-Reply Delay setting ---
        self._create_global_settings_panel(scrollable_frame)

        self.content_frame.pack(fill="both", expand=True)
        return self.sidebar_frame

    def _create_configuration_selector_panel(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=0)
        frame.grid_columnconfigure(0, weight=1)
        
        main_header = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(family="Roboto", size=18, weight="bold"), text_color=self.app.COLOR_TEXT)
        main_header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.lang_updatable_widgets.append((main_header, 'configuration'))

        config_display_names = [f"{c.name} | {c.description}" for c in self.app.config_model.configurations]
        self.config_selector = ctk.CTkComboBox(frame, values=config_display_names, variable=self.config_selector_var, command=self._on_global_config_select, state="readonly")
        self.config_selector.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        desc_label = ctk.CTkLabel(frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        desc_label.grid(row=2, column=0, sticky="w", pady=(5,0))
        self.lang_updatable_widgets.append((desc_label, 'description'))

        self.config_description_entry = ctk.CTkEntry(frame, font=self.app.FONT_GENERAL)
        self.config_description_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        save_btn = ctk.CTkButton(frame, text="", command=self._save_current_global_config)
        save_btn.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.lang_updatable_widgets.append((save_btn, 'save_active_config'))
        
    # --- FIXED: Reworked to use a collapsible frame ---
    def _create_model_settings_panel(self, parent, chat_id):
        collapsible_frame, header_label = self._create_collapsible_frame(parent, 'ai_settings', chat_id)
        self.header_labels[chat_id] = header_label
        
        content_frame = collapsible_frame # The content frame is the one returned

        presets = [p.name for p in self.app.config_model.presets]
        self.preset_selectors[chat_id] = self._create_dropdown(content_frame, 'preset', self.preset_vars[chat_id], presets, lambda choice, c=chat_id: self.on_preset_select(c, choice))
        
        selectors_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        selectors_frame.pack(fill="x", padx=0, pady=0)

        providers = list(self.app.state_manager.providers.keys())
        self.provider_selectors[chat_id] = self._create_dropdown(selectors_frame, 'provider', self.provider_vars[chat_id], providers, lambda choice, c=chat_id: self.on_provider_select(c, choice))

        self.model_selectors[chat_id] = self._create_dropdown(selectors_frame, 'model', self.model_vars[chat_id], [], lambda choice, c=chat_id: self.on_model_select(c, choice))
        
        self.key_selectors[chat_id] = self._create_dropdown(selectors_frame, 'key', self.key_vars[chat_id], [], lambda choice, c=chat_id: self.on_key_select(c, choice))
        
        self.persona_prompts[chat_id] = self._create_textbox(content_frame, 'persona', 120)
        self.context_prompts[chat_id] = self._create_textbox(content_frame, 'context', 80)
        
        params_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        params_frame.pack(fill='x', padx=15, pady=5)
        self.temp_labels[chat_id] = ctk.CTkLabel(params_frame, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        self.temp_labels[chat_id].pack(side='left')
        ctk.CTkSlider(params_frame, from_=0, to=2, variable=self.temp_vars[chat_id], command=lambda v, c=chat_id: self.update_slider_label(c)).pack(side='left', fill='x', expand=True, padx=5)
        self.update_slider_label(chat_id)

        web_search_cb = ctk.CTkCheckBox(content_frame, text="", variable=self.web_search_vars[chat_id])
        web_search_cb.pack(anchor='w', padx=15, pady=5)
        self.lang_updatable_widgets.append((web_search_cb, 'web_search_enabled'))

    # --- NEW: Function to create global settings like auto-reply delay ---
    def _create_global_settings_panel(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(20, 5))
        frame.grid_columnconfigure(1, weight=1)

        header_label = ctk.CTkLabel(frame, text=self.lang.get('global_settings'), font=self.app.FONT_BOLD)
        header_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        delay_label = ctk.CTkLabel(frame, text=self.lang.get('auto_reply_delay'), font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        delay_label.grid(row=1, column=0, sticky="w")
        
        delay_entry = ctk.CTkEntry(frame, textvariable=self.app.delay_var, width=50, font=self.app.FONT_GENERAL)
        delay_entry.grid(row=1, column=1, sticky="w", padx=10)

    # --- NEW: Helper for creating collapsible frames ---
    def _create_collapsible_frame(self, parent, text_key, *args):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=5, pady=2)

        header = ctk.CTkFrame(container, fg_color="transparent", cursor="hand2")
        header.pack(fill="x")

        chevron_label = ctk.CTkLabel(header, text="▼", font=self.app.FONT_GENERAL, text_color=self.app.COLOR_TEXT_MUTED)
        chevron_label.pack(side="left", padx=(10,5))
        
        header_label = ctk.CTkLabel(header, text="", font=self.app.FONT_BOLD, text_color=self.app.COLOR_TEXT)
        header_label.pack(side="left")
        self.lang_updatable_widgets.append((header_label, text_key, *args))

        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.pack(fill="x", after=header)
        
        def toggle_content(event=None):
            if content_frame.winfo_ismapped():
                content_frame.pack_forget()
                chevron_label.configure(text="▶")
            else:
                content_frame.pack(fill="x", after=header)
                chevron_label.configure(text="▼")
        
        header.bind("<Button-1>", toggle_content)
        header_label.bind("<Button-1>", toggle_content)
        chevron_label.bind("<Button-1>", toggle_content)
        
        return content_frame, header_label

    def _create_dropdown(self, parent, label_key, variable, values, command):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(3, 3), anchor="w")
        label = ctk.CTkLabel(frame, text=self.lang.get(label_key), width=80, anchor="w")
        label.pack(side="left")
        self.dropdown_labels[(parent, label_key)] = label
        
        dropdown = ctk.CTkComboBox(frame, variable=variable, values=values or [], command=command, state="readonly")
        dropdown.pack(side="left", fill="x", expand=True)
        return dropdown

    def _create_textbox(self, parent, label_key, height):
        label = ctk.CTkLabel(parent, text="", font=self.app.FONT_SMALL, text_color=self.app.COLOR_TEXT_MUTED)
        label.pack(anchor='w', padx=15, pady=(5,0))
        self.lang_updatable_widgets.append((label, label_key))
        
        textbox = ctk.CTkTextbox(parent, height=height, wrap="word", font=self.app.FONT_CHAT)
        textbox.pack(fill="x", padx=15, pady=2, expand=True)
        return textbox

    def update_slider_label(self, chat_id):
        if self.temp_labels.get(chat_id) and self.temp_labels[chat_id].winfo_exists():
            temp_text = self.lang.get('temperature', self.temp_vars[chat_id].get())
            self.temp_labels[chat_id].configure(text=temp_text)

    def apply_global_config_profile(self, profile, startup=False):
        if not startup:
            if not messagebox.askyesno(self.lang.get('confirm'), self.lang.get('confirm_apply_config')):
                return
        
        self.app.config_model.active_config_index = self.app.config_model.configurations.index(profile)
        
        active_display_name = f"{profile.name} | {profile.description}"
        self.config_selector_var.set(active_display_name)
        self.config_description_entry.delete(0, 'end')
        self.config_description_entry.insert(0, profile.description)
        
        self.apply_config_to_ui(profile.ai_1, 1, from_global=True)
        self.apply_config_to_ui(profile.ai_2, 2, from_global=True)

    def apply_config_to_ui(self, ai_config, chat_id, from_preset=False, from_global=False):
        if not from_preset and not from_global:
            self.preset_vars[chat_id].set(self.lang.get('select_preset'))
        
        self.provider_vars[chat_id].set(ai_config.provider or self.lang.get('select_provider'))
        self.on_provider_select(chat_id, ai_config.provider, set_model=ai_config.model, set_key_id=ai_config.key_id, is_initial_setup=True)
        
        self.persona_prompts[chat_id].delete("1.0", "end")
        self.persona_prompts[chat_id].insert("1.0", ai_config.persona_prompt)
        
        self.context_prompts[chat_id].delete("1.0", "end")
        self.context_prompts[chat_id].insert("1.0", ai_config.context_prompt)
        
        self.temp_vars[chat_id].set(ai_config.temperature)
        self.web_search_vars[chat_id].set(ai_config.web_search_enabled)

    def on_provider_select(self, chat_id, provider_name, set_model=None, set_key_id=None, is_initial_setup=False):
        if not provider_name or provider_name.startswith('---'):
            self.model_selectors[chat_id].configure(values=[])
            self.model_vars[chat_id].set(self.lang.get('select_provider'))
            self.key_selectors[chat_id].master.pack_forget()
            return

        if not is_initial_setup:
            self.app.active_ai_config[chat_id] = {"provider": provider_name, "model": None, "key_id": None, "preset_id": None}
            self.preset_vars[chat_id].set(self.lang.get('select_preset'))
        else:
            self.app.active_ai_config[chat_id].update({"provider": provider_name, "model": set_model, "key_id": set_key_id})
        
        self.update_selectors_for_pane(chat_id)

    def on_model_select(self, chat_id, model_name):
        if model_name.startswith('---'): return
        self.app.active_ai_config[chat_id]['model'] = model_name
        self.preset_vars[chat_id].set(self.lang.get('select_preset'))
        self.update_pane_model_display(chat_id)
        
    def on_key_select(self, chat_id, key_note_and_id):
        if key_note_and_id.startswith('---'): return
        try:
            key_suffix = key_note_and_id.split('(')[-1][:-1]
            key_obj = next((k for k in self.app.config_model.google_keys if k.id.endswith(key_suffix)), None)
            if key_obj:
                self.app.active_ai_config[chat_id]['key_id'] = key_obj.id
                self.preset_vars[chat_id].set(self.lang.get('select_preset'))
            else:
                raise IndexError
        except IndexError:
            self.app.logger.warning("Could not parse key_id from dropdown.", value=key_note_and_id)

    def on_preset_select(self, chat_id, preset_name):
        if preset_name.startswith('---'): return
        
        preset = next((p for p in self.app.config_model.presets if p.name == preset_name), None)
        if preset:
            self.app.logger.info(f"Applying preset '{preset.name}' to AI {chat_id}")
            preset_ai_config = AIConfig(
                provider=preset.provider,
                model=preset.model,
                key_id=preset.key_id
            )
            self.apply_config_to_ui(preset_ai_config, chat_id, from_preset=True)
            self.app.active_ai_config[chat_id]['preset_id'] = preset.id

    def _get_sorted_google_models(self, all_models):
        preferred = self.app.config_model.preferred_models
        
        preferred_in_list = [m for m in preferred if m in all_models]
        other_models = sorted([m for m in all_models if m not in preferred_in_list])
        
        if preferred_in_list and other_models:
            return preferred_in_list + ["──────────"] + other_models
        elif preferred_in_list:
            return preferred_in_list
        else:
            return other_models

    def update_selectors_for_pane(self, chat_id):
        config = self.app.active_ai_config[chat_id]
        provider_name = config.get("provider")
        provider = self.app.state_manager.get_provider(provider_name)

        if provider and provider.is_configured():
            models = provider.get_models()
            
            if provider_name == "Google":
                models = self._get_sorted_google_models(models)

            self.model_selectors[chat_id].configure(values=models or [self.lang.get('no_models_available')])
            if models:
                current_model = config.get("model")
                if current_model and current_model in models and "──" not in current_model:
                    self.model_vars[chat_id].set(current_model)
                else:
                    first_valid_model = next((m for m in models if "──" not in m), None)
                    if first_valid_model:
                        self.model_vars[chat_id].set(first_valid_model)
                        self.app.active_ai_config[chat_id]['model'] = first_valid_model
                    else:
                        self.model_vars[chat_id].set(self.lang.get('no_models_available'))
            else:
                self.model_vars[chat_id].set(self.lang.get('no_models_available'))
        else:
            self.model_selectors[chat_id].configure(values=[])
            self.model_vars[chat_id].set(self.lang.get('select_provider'))
            
        if provider_name == "Google":
            keys = self.app.config_model.google_keys
            key_list = [f"{key.note or 'No Note'} ({key.id[-4:]})" for key in keys]
            self.key_selectors[chat_id].master.pack(fill="x", padx=15, pady=(3, 3), anchor="w")
            self.key_selectors[chat_id].configure(values=key_list or [self.lang.get('no_keys_available')])
            if keys:
                current_key_id = config.get("key_id")
                current_key_item = next((item for item in key_list if current_key_id and current_key_id[-4:] in item), None)
                if current_key_item:
                    self.key_vars[chat_id].set(current_key_item)
                else:
                    self.key_vars[chat_id].set(key_list[0])
                self.on_key_select(chat_id, self.key_vars[chat_id].get())
            else:
                self.key_vars[chat_id].set(self.lang.get('no_keys_available'))
        else:
            self.key_selectors[chat_id].master.pack_forget()
            self.app.active_ai_config[chat_id]['key_id'] = None

        self.update_pane_model_display(chat_id)

    def update_pane_model_display(self, chat_id):
        config = self.app.active_ai_config.get(chat_id, {})
        provider = config.get("provider")
        model = config.get("model")
        if provider and model and not model.startswith('---'):
            self.app.chat_panes[chat_id].update_current_model_display(f"{provider}: {model}")
        else:
            self.app.chat_panes[chat_id].update_current_model_display(self.lang.get('select_model'))

    def update_all_presets_selectors(self):
        presets = [p.name for p in self.app.config_model.presets]
        for i in [1, 2]:
            selector = self.preset_selectors.get(i)
            if selector:
                selector.configure(values=presets or [self.lang.get('no_presets_available')])
                selector.set(self.lang.get('select_preset'))

    def update_all_text(self):
        for widget, key, *args in self.lang_updatable_widgets:
            if widget and widget.winfo_exists():
                widget.configure(text=self.lang.get(key, *args))
        for key, label in self.dropdown_labels.items():
            parent, label_key = key
            if parent.winfo_exists():
                label.configure(text=self.lang.get(label_key))
        for i in [1, 2]:
            self.update_slider_label(i)

    def toggle_sidebar(self, initial=False):
        if self.sidebar_frame is None: return
        is_expanded = self.sidebar_frame.cget('width') == self.app.RIGHT_SIDEBAR_WIDTH_FULL
        if initial: is_expanded = True

        if is_expanded:
            self.content_frame.pack_forget()
            self.sidebar_frame.configure(width=self.app.SIDEBAR_WIDTH_COLLAPSED)
            self.toggle_button.configure(text="◀")
        else:
            self.sidebar_frame.configure(width=self.app.RIGHT_SIDEBAR_WIDTH_FULL)
            self.content_frame.pack(fill="both", expand=True)
            self.toggle_button.configure(text="▶")

    def _on_global_config_select(self, choice_string):
        choice_name = choice_string.split(' | ')[0]
        profile = next((p for p in self.app.config_model.configurations if p.name == choice_name), None)
        if profile:
            self.apply_global_config_profile(profile)

    def _gather_ai_config_from_ui(self, chat_id):
        key_selection = self.key_vars[chat_id].get()
        key_id = None
        if key_selection and not key_selection.startswith('---'):
            try:
                key_suffix = key_selection.split('(')[-1][:-1]
                key_obj = next((k for k in self.app.config_model.google_keys if k.id.endswith(key_suffix)), None)
                if key_obj:
                    key_id = key_obj.id
            except (ValueError, IndexError):
                pass
        
        return AIConfig(
            provider=self.provider_vars[chat_id].get() if not self.provider_vars[chat_id].get().startswith('---') else None,
            model=self.model_vars[chat_id].get() if not self.model_vars[chat_id].get().startswith('---') else None,
            key_id=key_id,
            persona_prompt=self.persona_prompts[chat_id].get("1.0", "end-1c").strip(),
            context_prompt=self.context_prompts[chat_id].get("1.0", "end-1c").strip(),
            temperature=self.temp_vars[chat_id].get(),
            web_search_enabled=self.web_search_vars[chat_id].get()
        )

    def _save_current_global_config(self):
        active_index = self.app.config_model.active_config_index
        profile = self.app.config_model.configurations[active_index]
        
        profile.description = self.config_description_entry.get().strip()
        profile.ai_1 = self._gather_ai_config_from_ui(1)
        profile.ai_2 = self._gather_ai_config_from_ui(2)

        self.app.config_manager.save_config(self.app.config_model)

        config_display_names = [f"{c.name} | {c.description}" for c in self.app.config_model.configurations]
        self.config_selector.configure(values=config_display_names)
        self.config_selector_var.set(f"{profile.name} | {profile.description}")
        
        messagebox.showinfo(self.lang.get('success'), self.lang.get('config_saved'))

    def start_api_call_with_failover(self, chat_id, message, trace_id):
        thread = threading.Thread(target=self._api_call_thread_with_failover, args=(chat_id, message, trace_id))
        thread.daemon = True
        thread.start()

    def _api_call_thread_with_failover(self, chat_id, message, trace_id):
        pane = self.app.chat_panes[chat_id]
        
        pane.current_generation_id += 1
        self.app.root.after(0, pane.update_ui_for_sending)
        
        active_config = self.app.active_ai_config[chat_id].copy()
        active_config['generation_id'] = pane.current_generation_id
        
        provider_name = active_config.get("provider")
        provider = self.app.state_manager.get_provider(provider_name)

        if not provider or not active_config.get("model") or active_config.get("model", "").startswith("---"):
            self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': self.lang.get('error_provider_model_selection')})
            self.app.root.after(0, pane.restore_ui_after_response)
            return

        try:
            for event in provider.send_message(chat_id, active_config, message, trace_id):
                event['chat_id'] = chat_id
                event['generation_id'] = active_config['generation_id']
                self.app.response_queue.put(event)
        
        except ProviderError as e:
            if provider_name == "Google" and not e.is_fatal:
                self.app.logger.warning("Google provider error, attempting failover.", error=str(e))
                
                failed_key_id = active_config.get("key_id")
                key_obj = self.app.config_model.get_google_key_by_id(failed_key_id)
                failed_key_note = key_obj.note if key_obj else "N/A"
                next_key = self.app.state_manager.get_next_available_google_key(failed_key_id)

                if next_key:
                    system_msg = self.lang.get('failover_message', old_key_note=failed_key_note, new_key_note=next_key.note)
                    self.app.response_queue.put({'type': 'system', 'chat_id': chat_id, 'text': system_msg})
                    
                    self.app.active_ai_config[chat_id]['key_id'] = next_key.id
                    self.app.root.after(0, self.update_selectors_for_pane, chat_id)
                    
                    self._api_call_thread_with_failover(chat_id, message, trace_id)
                    return
                else:
                    self.app.logger.error("Failover failed: No other available Google keys.")
                    self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"Failover failed. All Google Keys are unavailable. Original error: {e}"})
            else:
                 self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': str(e)})
            self.app.root.after(0, pane.restore_ui_after_response)
        
        except Exception as e:
            self.app.logger.error("An unexpected error occurred in the API thread.", error=str(e), exc_info=True)
            self.app.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"An unexpected error occurred: {e}"})
            self.app.root.after(0, pane.restore_ui_after_response)