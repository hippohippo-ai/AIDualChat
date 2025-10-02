import customtkinter as ctk
from tkinter import messagebox
import uuid

from config.models import GoogleAPIKey, Preset

class ModelManagerWindow(ctk.CTkToplevel):
    def __init__(self, app_instance):
        super().__init__(app_instance.root)
        self.app = app_instance
        self.lang = app_instance.lang
        self.config_model = app_instance.config_model
        
        self.title(self.lang.get('model_manager'))
        self.geometry("900x700")

        self._google_key_widgets = {}
        self._preset_checkbox_vars = {}
        self._preset_provider_var = ctk.StringVar()
        self._preset_model_var = ctk.StringVar()
        self._preset_key_var = ctk.StringVar()

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both")
        
        self.google_tab = self.tab_view.add(self.lang.get('provider_google'))
        self.ollama_tab = self.tab_view.add(self.lang.get('provider_ollama'))
        self.presets_tab = self.tab_view.add(self.lang.get('presets'))
        
        self.create_google_tab()
        self.create_ollama_tab()
        self.create_presets_tab()

    def update_text(self):
        self.title(self.lang.get('model_manager'))
        # This is a bit of a hack to update tab names. A better solution would involve
        # storing tab references, but this works for now.
        if self.tab_view._segmented_button:
            self.tab_view._segmented_button.configure(values=[
                self.lang.get('provider_google'), 
                self.lang.get('provider_ollama'), 
                self.lang.get('presets')
            ])
        # Rebuild content to reflect new language
        self.create_google_tab()
        self.create_ollama_tab()
        self.create_presets_tab()

    # --- Google Tab ---
    def create_google_tab(self):
        # Clear previous widgets
        for widget in self.google_tab.winfo_children():
            widget.destroy()
            
        self.google_tab.grid_columnconfigure(0, weight=1)
        
        entry_frame = ctk.CTkFrame(self.google_tab)
        entry_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        entry_frame.grid_columnconfigure(1, weight=1)

        self.google_key_value_entry = ctk.CTkEntry(entry_frame, placeholder_text=self.lang.get('key_value'), width=300)
        self.google_key_value_entry.grid(row=0, column=0, padx=5, pady=5)
        self.google_key_note_entry = ctk.CTkEntry(entry_frame, placeholder_text=self.lang.get('api_key_note'))
        self.google_key_note_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        add_button = ctk.CTkButton(entry_frame, text=self.lang.get('add_key'), command=self._add_google_key)
        add_button.grid(row=0, column=2, padx=5, pady=5)

        self.google_keys_frame = ctk.CTkScrollableFrame(self.google_tab, label_text=self.lang.get('saved_google_keys'))
        self.google_keys_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.google_keys_frame.grid_columnconfigure(2, weight=1)
        self.google_tab.grid_rowconfigure(1, weight=1)
        
        self.update_google_keys_list()

        action_frame = ctk.CTkFrame(self.google_tab)
        action_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        refresh_button = ctk.CTkButton(action_frame, text=self.lang.get('refresh'), command=lambda: self.app.state_manager.refresh_all_provider_states(force=True))
        refresh_button.pack(side="left", padx=5, pady=5)
        delete_button = ctk.CTkButton(action_frame, text=self.lang.get('delete_key'), command=self._delete_selected_google_keys, fg_color="red")
        delete_button.pack(side="right", padx=5, pady=5)

    def update_google_keys_list(self):
        for widget in self.google_keys_frame.winfo_children():
            widget.destroy()
        self._google_key_widgets.clear()

        for i, key in enumerate(self.config_model.google_keys):
            status_info = self.app.state_manager.get_provider("Google").get_key_status(key.id)
            
            key_frame = ctk.CTkFrame(self.google_keys_frame, fg_color=("gray85", "gray17"))
            key_frame.pack(fill="x", padx=5, pady=3)
            key_frame.grid_columnconfigure(2, weight=1)

            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(key_frame, text="", variable=var, width=20)
            cb.grid(row=0, column=0, padx=5, pady=5)
            self._google_key_widgets[key.id] = var

            status_color = "green" if status_info.get("is_valid") else ("red" if status_info.get("is_valid") is False else "gray")
            status_label = ctk.CTkLabel(key_frame, text="●", text_color=status_color, font=ctk.CTkFont(size=20))
            status_label.grid(row=0, column=1, padx=(0, 5), pady=5)
            
            note_text = key.note or "(No Note)"
            key_display = f"{key.api_key[:4]}...{key.api_key[-4:]}"
            info_label = ctk.CTkLabel(key_frame, text=f"{note_text} ({key_display})", anchor="w")
            info_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

            quota_text = status_info.get('quota', 'Unknown')
            quota_label = ctk.CTkLabel(key_frame, text=quota_text, anchor="e", text_color="gray")
            quota_label.grid(row=0, column=3, padx=5, pady=5, sticky="e")
    
    def _add_google_key(self):
        key_value = self.google_key_value_entry.get().strip()
        key_note = self.google_key_note_entry.get().strip()
        
        if not key_value:
            messagebox.showerror(self.lang.get('error'), "API Key value cannot be empty.")
            return

        new_key = GoogleAPIKey(api_key=key_value, note=key_note)
        self.config_model.google_keys.append(new_key)
        self.app.config_manager.save_config(self.config_model)
        
        self.google_key_value_entry.delete(0, 'end')
        self.google_key_note_entry.delete(0, 'end')
        self.update_google_keys_list()
        self.app.state_manager.refresh_all_provider_states(force=True)

    def _delete_selected_google_keys(self):
        ids_to_delete = {key_id for key_id, var in self._google_key_widgets.items() if var.get()}
        if not ids_to_delete:
            return

        self.config_model.google_keys = [key for key in self.config_model.google_keys if key.id not in ids_to_delete]
        self.app.config_manager.save_config(self.config_model)
        
        self.update_google_keys_list()

    # --- Ollama Tab ---
    def create_ollama_tab(self):
        for widget in self.ollama_tab.winfo_children():
            widget.destroy()

        self.ollama_tab.grid_columnconfigure(0, weight=1)

        settings_frame = ctk.CTkFrame(self.ollama_tab)
        settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        host_label = ctk.CTkLabel(settings_frame, text=self.lang.get('ollama_host'))
        host_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.ollama_host_entry = ctk.CTkEntry(settings_frame)
        self.ollama_host_entry.insert(0, self.config_model.ollama_settings.host)
        self.ollama_host_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        save_button = ctk.CTkButton(settings_frame, text=self.lang.get('save_and_refresh'), command=self._save_and_refresh_ollama)
        save_button.grid(row=0, column=2, padx=5, pady=5)
        
        status_frame = ctk.CTkFrame(self.ollama_tab, fg_color=("gray85", "gray17"))
        status_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(status_frame, text=self.lang.get('ollama_status')).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ollama_status_label = ctk.CTkLabel(status_frame, text="Unknown", anchor="w")
        self.ollama_status_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(status_frame, text=self.lang.get('ollama_version')).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ollama_version_label = ctk.CTkLabel(status_frame, text="Unknown", anchor="w")
        self.ollama_version_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.ollama_models_frame = ctk.CTkScrollableFrame(self.ollama_tab, label_text=self.lang.get('ollama_models'))
        self.ollama_models_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.ollama_tab.grid_rowconfigure(2, weight=1)
        
        self.update_ollama_status()
    
    def _save_and_refresh_ollama(self):
        new_host = self.ollama_host_entry.get().strip()
        if not new_host:
            messagebox.showerror(self.lang.get('error'), "Ollama host cannot be empty.")
            return
        
        self.config_model.ollama_settings.host = new_host
        self.app.config_manager.save_config(self.config_model)
        self.app.state_manager.get_provider("Ollama").refresh_status()
        # The refresh will trigger a UI update via the StateManager's callback mechanism

    def update_ollama_status(self):
        status_info = self.app.state_manager.get_provider("Ollama").get_status()
        
        if status_info.get("is_available"):
            self.ollama_status_label.configure(text=self.lang.get('status_ok'), text_color="green")
        else:
            self.ollama_status_label.configure(text=status_info.get("version", self.lang.get('status_unavailable')), text_color="red")
        
        self.ollama_version_label.configure(text=status_info.get("version", "N/A"))
        
        for widget in self.ollama_models_frame.winfo_children():
            widget.destroy()
            
        models = status_info.get("models", [])
        if not models:
             label = ctk.CTkLabel(self.ollama_models_frame, text=self.lang.get('no_models_available'), text_color="gray")
             label.pack(anchor="w", padx=10)
        else:
            for model_name in models:
                label = ctk.CTkLabel(self.ollama_models_frame, text=model_name)
                label.pack(anchor="w", padx=10)

    # --- Presets Tab ---
    def create_presets_tab(self):
        for widget in self.presets_tab.winfo_children():
            widget.destroy()

        self.presets_tab.grid_columnconfigure(0, weight=1)
        self.presets_tab.grid_rowconfigure(1, weight=1)

        entry_frame = ctk.CTkFrame(self.presets_tab)
        entry_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        entry_frame.grid_columnconfigure(1, weight=1)

        self.preset_name_entry = ctk.CTkEntry(entry_frame, placeholder_text=self.lang.get('preset_name'))
        self.preset_name_entry.grid(row=0, column=0, padx=5, pady=5)
        
        dropdown_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        dropdown_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        dropdown_frame.grid_columnconfigure((0,1,2), weight=1)

        self._preset_provider_selector = ctk.CTkComboBox(dropdown_frame, variable=self._preset_provider_var, 
                                                         values=["Google", "Ollama"], command=self._on_preset_provider_select)
        self._preset_provider_selector.grid(row=0, column=0, padx=2, sticky="ew")
        
        self._preset_model_selector = ctk.CTkComboBox(dropdown_frame, variable=self._preset_model_var, state="disabled")
        self._preset_model_selector.grid(row=0, column=1, padx=2, sticky="ew")
        
        self._preset_key_selector = ctk.CTkComboBox(dropdown_frame, variable=self._preset_key_var, state="disabled")
        self._preset_key_selector.grid(row=0, column=2, padx=2, sticky="ew")
        
        self._preset_provider_var.set(self.lang.get('select_provider'))
        
        add_button = ctk.CTkButton(entry_frame, text=self.lang.get('add_preset'), command=self._add_preset)
        add_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.presets_frame = ctk.CTkScrollableFrame(self.presets_tab, label_text=self.lang.get('saved_presets'))
        self.presets_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.update_presets_list()

        delete_button = ctk.CTkButton(self.presets_tab, text=self.lang.get('delete_preset'), command=self._delete_selected_presets, fg_color="red")
        delete_button.grid(row=2, column=0, padx=10, pady=10, sticky="e")

    def _on_preset_provider_select(self, provider_name):
        self._preset_model_selector.configure(state="readonly")
        provider = self.app.state_manager.get_provider(provider_name)
        if provider:
            models = provider.get_models()
            if provider_name == "Google":
                # Apply preferred sorting here too
                models = self.app.main_window.right_sidebar._get_sorted_google_models(models)
            self._preset_model_selector.configure(values=models or [])
            self._preset_model_var.set(next((m for m in models if "──" not in m), self.lang.get('no_models_available')))
        
        if provider_name == "Google":
            self._preset_key_selector.configure(state="readonly")
            keys = self.app.config_model.google_keys
            key_list = [f"{key.note or 'No Note'} ({key.id[-4:]})" for key in keys]
            self._preset_key_selector.configure(values=key_list or [])
            self._preset_key_var.set(key_list[0] if key_list else self.lang.get('no_keys_available'))
        else:
            self._preset_key_var.set("")
            self._preset_key_selector.configure(state="disabled", values=[])

    def _add_preset(self):
        name = self.preset_name_entry.get().strip()
        provider = self._preset_provider_var.get()
        model = self._preset_model_var.get()
        
        if not all([name, provider, model]) or provider.startswith('---') or model.startswith('---'):
            messagebox.showerror(self.lang.get('error'), self.lang.get('error_preset_fields'))
            return

        key_id = None
        if provider == "Google":
            key_selection = self._preset_key_var.get()
            if key_selection.startswith('---'):
                messagebox.showerror(self.lang.get('error'), self.lang.get('error_preset_key'))
                return
            try:
                key_suffix = key_selection.split('(')[-1][:-1]
                key_obj = next((k for k in self.app.config_model.google_keys if k.id.endswith(key_suffix)), None)
                if key_obj:
                    key_id = key_obj.id
                else:
                    raise IndexError
            except IndexError:
                messagebox.showerror(self.lang.get('error'), "Invalid API Key selection for preset.")
                return
        
        new_preset = Preset(name=name, provider=provider, model=model, key_id=key_id)
        self.config_model.presets.append(new_preset)
        self.app.config_manager.save_config(self.config_model)
        
        self.preset_name_entry.delete(0, 'end')
        self.update_presets_list()
        self.app.main_window.right_sidebar.update_all_presets_selectors()

    def update_presets_list(self):
        for widget in self.presets_frame.winfo_children():
            widget.destroy()
        self._preset_checkbox_vars.clear()

        for preset in self.config_model.presets:
            frame = ctk.CTkFrame(self.presets_frame, fg_color=("gray90", "gray19"))
            frame.pack(fill="x", pady=2, padx=2)
            
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(frame, text="", variable=var, width=20)
            cb.pack(side="left", padx=5)
            self._preset_checkbox_vars[preset.id] = var
            
            key_note = ""
            if preset.provider == "Google" and preset.key_id:
                key_obj = self.app.config_model.get_google_key_by_id(preset.key_id)
                key_note = f" (Key: {key_obj.note if key_obj else 'N/A'})"
                
            label_text = f"'{preset.name}': {preset.provider} -> {preset.model}{key_note}"
            label = ctk.CTkLabel(frame, text=label_text, anchor="w")
            label.pack(side="left", fill="x", expand=True, padx=5)

    def _delete_selected_presets(self):
        ids_to_delete = {pid for pid, var in self._preset_checkbox_vars.items() if var.get()}
        if not ids_to_delete: return
        
        self.config_model.presets = [p for p in self.config_model.presets if p.id not in ids_to_delete]
        self.app.config_manager.save_config(self.config_model)
        
        self.update_presets_list()
        self.app.main_window.right_sidebar.update_all_presets_selectors()

    def update_provider_tabs(self):
        if self.winfo_exists():
            self.update_google_keys_list()
            self.update_ollama_status()