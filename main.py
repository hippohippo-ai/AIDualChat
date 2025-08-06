# --- START OF FILE main.py ---

# Gemini Dual Chat GUI - Final Stable Version

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import google.generativeai as genai
import threading
import queue
import os
import json
import mimetypes
from datetime import datetime
import re
import uuid

try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.styles import get_style_by_name
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    print("Pygments not found. Code syntax highlighting will be disabled. Run 'pip install Pygments' to enable it.")


class GeminiChatApp:
    def __init__(self, root):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = root
        self.root.title("Gemini Dual Chat - Final")
        self.root.geometry("1366x800")

        self.chat_sessions = {}
        self.total_tokens, self.token_info_vars = {}, {}
        self.model_selectors, self.chat_displays, self.user_inputs, self.send_buttons, self.stop_buttons = {}, {}, {}, {}, {}
        self.progress_bars, self.options_prompts = {}, {}
        self.file_lists = {}
        self.auto_reply_vars = {1: ctk.BooleanVar(value=False), 2: ctk.BooleanVar(value=False)}
        
        self.temp_vars, self.topp_vars = {}, {}
        self.temp_labels, self.topp_labels = {}, {}
        
        self.response_queue = queue.Queue()
        self.current_generation_id = {1: 0, 2: 0}
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.gemini_response_counters = {1: 0, 2: 0}
        self.current_nav_index = {1: 0, 2: 0}

        self.streaming_responses = {1: "", 2: ""}

        self.load_config()

        self.delay_var = ctk.StringVar(value=str(self.config.get("auto_reply_delay_minutes", 1.0)))
        
        self.api_key = self.config.get("api_key")
        if not self.api_key or "PASTE_YOUR" in self.api_key:
            self.prompt_for_api_key()
            if not self.api_key or "PASTE_YOUR" in self.api_key:
                messagebox.showerror("API Key Required", "An API key is required to run the application.")
                root.destroy()
                return

        try:
            genai.configure(api_key=self.api_key)
            self.available_models = self.fetch_available_models()
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to connect. Check API key/internet.\n\nError: {e}")
            root.destroy()
            return

        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        self.create_widgets()
        for chat_id in [1, 2]:
            self.prime_chat_session(chat_id)
        self.process_queue()

    def prompt_for_api_key(self):
        dialog = ctk.CTkInputDialog(text="Please enter your Gemini API Key:", title="API Key Required")
        key = dialog.get_input()
        if key:
            self.api_key = key
            self.config["api_key"] = key
            self._save_config_to_file(self.config)
            messagebox.showinfo("API Key Saved", "API Key has been saved to config.json. Please restart if you were having connection issues.")

    def fetch_available_models(self):
        models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models: raise Exception("No usable models found for your API key.")
        return sorted(models)

    def load_config(self):
        self.config_file = 'config.json'
        default_config = {
            "api_key": "PASTE_YOUR_GEMINI_API_KEY_HERE", "auto_reply_delay_minutes": 1.0,
            "default_model_1": "gemini-1.5-pro-latest", "default_model_2": "gemini-1.5-flash-latest",
            "preferred_models_in_dropdown": ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"],
            "gemini_1": {"system_prompt": "You are Gemini 1. You format responses in Markdown.", "temperature": 0.7, "top_p": 1.0},
            "gemini_2": {"system_prompt": "You are Gemini 2. You format responses in Markdown.", "temperature": 0.7, "top_p": 1.0}
        }
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f: json.dump(default_config, f, indent=2)
            self.config = default_config
        else:
            try:
                with open(self.config_file, 'r') as f: loaded_config = json.load(f)
                self.config = default_config
                for key, value in loaded_config.items():
                    if isinstance(value, dict) and key in self.config: self.config[key].update(value)
                    else: self.config[key] = value
            except json.JSONDecodeError:
                messagebox.showerror("Config Error", f"Could not decode '{self.config_file}'. Using default.")
                self.config = default_config

    def _save_config_to_file(self, config_data):
        with open(self.config_file, 'w') as f: json.dump(config_data, f, indent=2)

    def _open_file_dialog(self, chat_id):
        file_paths = filedialog.askopenfilenames()
        if file_paths:
            listbox = self.file_lists[chat_id]
            if not hasattr(listbox, 'full_paths'): listbox.full_paths = []
            for path in file_paths:
                listbox.insert(tk.END, os.path.basename(path))
                listbox.full_paths.append(path)

    def _remove_selected_files(self, chat_id):
        listbox = self.file_lists[chat_id]
        if hasattr(listbox, 'full_paths'):
            selections = listbox.curselection()
            for index in reversed(selections):
                listbox.delete(index)
                listbox.full_paths.pop(index)

    def _remove_all_files(self, chat_id):
        listbox = self.file_lists[chat_id]
        listbox.delete(0, tk.END)
        if hasattr(listbox, 'full_paths'): listbox.full_paths = []

    def prime_chat_session(self, chat_id, from_event=False, history=None):
        try:
            model_name = self.model_selectors[chat_id].get()
            generation_config = genai.types.GenerationConfig(temperature=self.temp_vars[chat_id].get(), top_p=self.topp_vars[chat_id].get())
            model = genai.GenerativeModel(model_name, generation_config=generation_config)
            if history:
                self.chat_sessions[chat_id] = model.start_chat(history=history)
            else:
                prompt = self.options_prompts[chat_id].get("1.0", tk.END).strip()
                initial_history = [{'role': 'user', 'parts': [prompt]}, {'role': 'model', 'parts': ["Understood."]}]
                self.chat_sessions[chat_id] = model.start_chat(history=initial_history)
            self.total_tokens[chat_id] = 0
            self.token_info_vars[chat_id].set("Tokens: Last 0 | Total 0")
            if from_event and not history:
                self.clear_chat_window(chat_id)
                self.append_message(self.chat_displays[chat_id], f"--- Session reset with model: {model_name} ---", "system")
                self._remove_all_files(chat_id)
        except Exception as e:
            messagebox.showerror("Model Error", f"Failed to start chat with '{model_name}'. Error: {e}")

    def _create_model_list_for_dropdown(self):
        preferred_models = self.config.get("preferred_models_in_dropdown", [])
        separator = "──────────"
        model_list = [m for m in preferred_models if m in self.available_models]
        other_models = [m for m in self.available_models if m not in model_list]
        if model_list and other_models: model_list.append(separator)
        model_list.extend(other_models)
        return model_list

    def _make_readonly(self, event):
        if event.state & 4: return
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'): return
        return "break"

    def _create_chat_area(self, parent, chat_id, default_model):
        config_key = f'gemini_{chat_id}'
        self.temp_vars[chat_id] = ctk.DoubleVar(value=self.config.get(config_key, {}).get('temperature', 0.7))
        self.topp_vars[chat_id] = ctk.DoubleVar(value=self.config.get(config_key, {}).get('top_p', 1.0))
        notebook = ctk.CTkTabview(parent)
        notebook.add("Conversation"); notebook.add("Options")
        convo_frame = notebook.tab("Conversation"); options_frame = notebook.tab("Options")
        top_frame = ctk.CTkFrame(convo_frame); top_frame.pack(fill=tk.X, padx=5, pady=(5,0)); top_frame.grid_columnconfigure(0, weight=1)
        model_list = self._create_model_list_for_dropdown()
        self.model_selectors[chat_id] = ctk.CTkComboBox(top_frame, values=model_list)
        self.model_selectors[chat_id].grid(row=0, column=0, sticky="ew", padx=(0, 5)); self.model_selectors[chat_id].set(default_model)
        self.model_selectors[chat_id].bind("<<ComboboxSelected>>", lambda event, c=chat_id: self.on_model_change(c))
        nav_up_button = ctk.CTkButton(top_frame, text="↑", width=30, command=lambda c=chat_id: self.navigate_gemini_response(c, 'up')); nav_up_button.grid(row=0, column=1, padx=(0, 2))
        nav_down_button = ctk.CTkButton(top_frame, text="↓", width=30, command=lambda c=chat_id: self.navigate_gemini_response(c, 'down')); nav_down_button.grid(row=0, column=2, padx=(0,10))
        save_button = ctk.CTkButton(top_frame, text="Save", width=50, command=lambda c=chat_id: self.save_session(c)); save_button.grid(row=0, column=3, padx=(0,2))
        load_button = ctk.CTkButton(top_frame, text="Load", width=50, command=lambda c=chat_id: self.load_session(c)); load_button.grid(row=0, column=4)
        chat_font = ctk.CTkFont(family="Consolas", size=14)
        self.chat_displays[chat_id] = ctk.CTkTextbox(convo_frame, wrap="word", font=chat_font, state='normal'); self.chat_displays[chat_id].bind("<KeyPress>", self._make_readonly)
        self.chat_displays[chat_id].pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self._setup_highlighting_tags(chat_id)
        self.user_inputs[chat_id] = ctk.CTkTextbox(convo_frame, height=120, wrap="word", font=chat_font)
        self.user_inputs[chat_id].pack(padx=5, pady=5, fill=tk.X); self.user_inputs[chat_id].bind("<Control-Return>", lambda event, c=chat_id: self.send_message(c))
        controls_frame = ctk.CTkFrame(convo_frame); controls_frame.pack(fill=tk.X, padx=5, pady=5)
        send_button_text = "Send (Ctrl+Enter)"; self.send_buttons[chat_id] = ctk.CTkButton(controls_frame, text=send_button_text, command=lambda c=chat_id: self.send_message(c))
        self.send_buttons[chat_id].pack(side=tk.LEFT, padx=(0, 5))
        self.stop_buttons[chat_id] = ctk.CTkButton(controls_frame, text="Stop", width=60, command=lambda c=chat_id: self.stop_generation(c), state="disabled")
        self.stop_buttons[chat_id].pack(side=tk.LEFT, padx=(0, 10))
        toggle_text = "Auto-reply to Gemini 2" if chat_id == 1 else "Auto-reply to Gemini 1"
        ctk.CTkCheckBox(controls_frame, text=toggle_text, variable=self.auto_reply_vars[chat_id]).pack(side=tk.LEFT)
        self.token_info_vars[chat_id] = ctk.StringVar(value="Tokens: Last 0 | Total 0")
        ctk.CTkLabel(controls_frame, textvariable=self.token_info_vars[chat_id]).pack(side=tk.LEFT, padx=10)
        self.progress_bars[chat_id] = ctk.CTkProgressBar(convo_frame, mode='indeterminate')
        ctk.CTkLabel(options_frame, text="System Prompt").pack(anchor='w', padx=5)
        self.options_prompts[chat_id] = ctk.CTkTextbox(options_frame, height=120, wrap="word")
        self.options_prompts[chat_id].pack(fill=tk.X, padx=5, pady=(0, 10))
        self.options_prompts[chat_id].insert('1.0', self.config.get(config_key, {}).get('system_prompt', ''))
        params_frame = ctk.CTkFrame(options_frame); params_frame.pack(fill='x', padx=5, pady=5)
        self.temp_labels[chat_id] = ctk.CTkLabel(params_frame, text=f"Temperature: {self.temp_vars[chat_id].get():.2f}")
        self.temp_labels[chat_id].pack(side='left', padx=5)
        temp_slider = ctk.CTkSlider(params_frame, from_=0, to=1, variable=self.temp_vars[chat_id], command=lambda v, c=chat_id: self.update_slider_label(c, 'temp'))
        temp_slider.pack(side='left', fill='x', expand=True)
        self.topp_labels[chat_id] = ctk.CTkLabel(params_frame, text=f"Top-P: {self.topp_vars[chat_id].get():.2f}")
        self.topp_labels[chat_id].pack(side='left', padx=5)
        topp_slider = ctk.CTkSlider(params_frame, from_=0, to=1, variable=self.topp_vars[chat_id], command=lambda v, c=chat_id: self.update_slider_label(c, 'topp'))
        topp_slider.pack(side='left', fill='x', expand=True)
        delay_frame = ctk.CTkFrame(options_frame); delay_frame.pack(fill=tk.X, pady=5, padx=5)
        ctk.CTkLabel(delay_frame, text="Auto-Reply Delay (min):").pack(side=tk.LEFT)
        ctk.CTkEntry(delay_frame, textvariable=self.delay_var, width=5).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(options_frame, text="Save Settings & Reset Chat", command=lambda c=chat_id: self.save_and_apply_settings(c)).pack(pady=10)
        file_frame = ctk.CTkFrame(options_frame); file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar = tk.Scrollbar(file_frame); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set, bg="#2A2D2E", fg="white", borderwidth=0, highlightthickness=0)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); self.file_lists[chat_id] = listbox
        file_buttons = ctk.CTkFrame(options_frame); file_buttons.pack(pady=5)
        ctk.CTkButton(file_buttons, text="Add Files", command=lambda c=chat_id: self._open_file_dialog(c)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(file_buttons, text="Remove Selected", command=lambda c=chat_id: self._remove_selected_files(c)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(file_buttons, text="Clear Files", command=lambda c=chat_id: self._remove_all_files(c)).pack(side=tk.LEFT, padx=5)
        return notebook
    
    def update_slider_label(self, chat_id, param_type):
        if param_type == 'temp': self.temp_labels[chat_id].configure(text=f"Temperature: {self.temp_vars[chat_id].get():.2f}")
        elif param_type == 'topp': self.topp_labels[chat_id].configure(text=f"Top-P: {self.topp_vars[chat_id].get():.2f}")

    def _setup_highlighting_tags(self, chat_id):
        display = self.chat_displays[chat_id]
        display.tag_config("user", foreground="#A9DFBF"); display.tag_config("gemini", foreground="#A9CCE3")
        display.tag_config("system", foreground="gray70"); display.tag_config("error", foreground="#F5B7B1")
        display.tag_config("autoreply", foreground="#FAD7A0"); display.tag_config("sel", background="#0078D7", foreground="white")
        display.tag_config("md_bold", foreground="#FFFFFF"); display.tag_config("md_italic", offset="2p")
        display.tag_config("md_code_inline", foreground="#FAD7A0", background="#2B2B2B")
        display.tag_config("md_code_block", background="#2B2B2B", lmargin1=20, lmargin2=20, rmargin=20)
        if PYGMENTS_AVAILABLE:
            try:
                style = get_style_by_name('monokai')
                for token, s in style:
                    fg = s.get('color')
                    if fg: display.tag_config(str(token), foreground=f'#{fg}')
            except Exception: print("Could not load Pygments style.")

    def create_widgets(self):
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        main_container.grid_columnconfigure(0, weight=1, uniform="equal_columns")
        main_container.grid_columnconfigure(1, weight=1, uniform="equal_columns")
        main_container.grid_rowconfigure(0, weight=1)
        default1, default2 = self.config.get("default_model_1"), self.config.get("default_model_2")
        notebook1 = self._create_chat_area(main_container, 1, default1); notebook1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        notebook2 = self._create_chat_area(main_container, 2, default2); notebook2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    def save_and_apply_settings(self, chat_id):
        try:
            delay_value = float(self.delay_var.get())
            if delay_value < 0: raise ValueError
            self.config["auto_reply_delay_minutes"] = delay_value
        except (ValueError, TypeError): messagebox.showerror("Invalid Input", "Delay must be a positive number."); return
        config_key = f'gemini_{chat_id}'; self.config.setdefault(config_key, {})
        self.config[config_key]['system_prompt'] = self.options_prompts[chat_id].get("1.0", tk.END).strip()
        self.config[config_key]['temperature'] = self.temp_vars[chat_id].get()
        self.config[config_key]['top_p'] = self.topp_vars[chat_id].get()
        self._save_config_to_file(self.config)
        messagebox.showinfo("Saved", "Settings saved to config.json. Resetting chat to apply changes.")
        self.prime_chat_session(chat_id, from_event=True)

    def process_queue(self):
        try:
            msg = self.response_queue.get_nowait()
            chat_id = msg['chat_id']
            if msg.get('generation_id') != self.current_generation_id[chat_id]: return
            msg_type = msg.get('type')

            if msg_type == 'stream_start':
                self.streaming_responses[chat_id] = ""
                display = self.chat_displays[chat_id]
                
                self.gemini_response_counters[chat_id] += 1
                nav_mark_name = f"gemini_resp_{chat_id}_{self.gemini_response_counters[chat_id]}"
                display.insert(tk.END, f"Gemini {chat_id}: ", "gemini")
                display.mark_set(nav_mark_name, display.index(f"{tk.INSERT}-1c"))
                display.mark_gravity(nav_mark_name, "left")
                
                mark_name = f"stream_start_{chat_id}"
                display.mark_set(mark_name, tk.END)
                display.mark_gravity(mark_name, "left")

            elif msg_type == 'stream_chunk':
                self.streaming_responses[chat_id] += msg['text']
                self.append_text_to_stream(chat_id, msg['text'])

            elif msg_type == 'stream_end':
                full_response_text = self.streaming_responses[chat_id]
                self.highlight_markdown(chat_id, full_response_text)
                self.restore_ui_after_response(chat_id)
                if msg.get('usage'): self.update_token_counts(chat_id, msg['usage'])
                self.log_conversation(chat_id, msg['user_message'], full_response_text)
                if self.auto_reply_vars[chat_id].get():
                    if any(word in full_response_text.lower() for word in ("error", "safety", "empty", "invalid", "failed")) or not full_response_text.strip():
                         self.auto_reply_vars[chat_id].set(False)
                         self.append_message(self.chat_displays[chat_id], "--- Auto-reply stopped due to potential error or empty response. ---", "system")
                    else: self.schedule_auto_reply(chat_id, full_response_text)
            elif msg_type == 'error':
                self.restore_ui_after_response(chat_id)
                self.append_message(self.chat_displays[chat_id], msg['text'], "error")
        except queue.Empty: pass
        finally: self.root.after(100, self.process_queue)
    
    def highlight_markdown(self, chat_id, text):
        display = self.chat_displays[chat_id]
        mark_name = f"stream_start_{chat_id}"
        
        # --- FIX: Lock the widget during the sensitive delete/replace operation ---
        display.configure(state='disabled')
        
        try:
            # This deletes the raw, unformatted text that was streamed in.
            display.delete(mark_name, tk.END)
        except tk.TclError:
            # This error is expected if the mark doesn't exist when loading a session.
            pass
        finally:
            # Always clean up the stream-specific mark.
            display.mark_unset(mark_name)

        code_blocks, text_no_code = {}, text
        def extract_code(match, is_block):
            placeholder = f"__CODE__{uuid.uuid4()}__"
            code_blocks[placeholder] = (match.group(0), is_block); return placeholder
        text_no_code = re.sub(r"```[\s\S]*?```", lambda m: extract_code(m, True), text_no_code)
        text_no_code = re.sub(r"`[^`]*?`", lambda m: extract_code(m, False), text_no_code)
        segments, last_pos = [], 0
        md_regex = re.compile(r"(?<!\*)\*\*(?P<bold>.+?)\*\*(?!\*)|(?<!\*)\*(?P<italic>[^*]+?)\*(?!\*)")
        for match in md_regex.finditer(text_no_code):
            start, end = match.span()
            if start > last_pos: segments.append(('gemini', text_no_code[last_pos:start]))
            bold_text, italic_text = match.group('bold'), match.group('italic')
            if bold_text: segments.append(('md_bold', bold_text))
            elif italic_text: segments.append(('md_italic', italic_text))
            last_pos = end
        if last_pos < len(text_no_code): segments.append(('gemini', text_no_code[last_pos:]))
        for tag, content in segments:
            if content in code_blocks:
                full_code, is_block = code_blocks[content]
                if is_block:
                    match = re.match(r"```(?P<lang>[\w\+#-]*)\n(?P<code>[\s\S]+?)\n```", full_code)
                    if match:
                        code_text, lang = match.group('code'), match.group('lang').lower()
                        display.insert(tk.END, "\n")
                        if PYGMENTS_AVAILABLE:
                            try:
                                lexer = get_lexer_by_name(lang, stripall=True) if lang else guess_lexer(code_text)
                                for token, text_chunk in lex(code_text, lexer): display.insert(tk.END, text_chunk, (str(token), "md_code_block"))
                            except Exception: display.insert(tk.END, code_text, ("md_code_block",))
                        else: display.insert(tk.END, code_text, ("md_code_block",))
                        display.insert(tk.END, "\n")
                    else: display.insert(tk.END, full_code, ("md_code_block",))
                else: display.insert(tk.END, full_code[1:-1], ("gemini", "md_code_inline"))
            else: display.insert(tk.END, content, ("gemini", tag))
        display.insert(tk.END, "\n\n")
        
        # --- FIX: Unlock the widget after the update is complete ---
        display.configure(state='normal')

    def append_text_to_stream(self, chat_id, text):
        display = self.chat_displays[chat_id]
        display.insert(tk.END, text)
        display.yview(tk.END)

    def update_token_counts(self, chat_id, usage_metadata):
        if not usage_metadata: return
        last = usage_metadata.get('prompt_token_count', 0) + usage_metadata.get('candidates_token_count', 0)
        self.total_tokens[chat_id] += last
        self.token_info_vars[chat_id].set(f"Tokens: Last {last} | Total {self.total_tokens[chat_id]}")

    def restore_ui_after_response(self, chat_id):
        self.user_inputs[chat_id].configure(state='normal'); self.send_buttons[chat_id].configure(state='normal')
        self.stop_buttons[chat_id].configure(state='disabled'); self.progress_bars[chat_id].pack_forget()
        self.progress_bars[chat_id].stop(); self.user_inputs[chat_id].focus_set()

    def update_ui_for_sending(self, chat_id):
        self.user_inputs[chat_id].configure(state='disabled'); self.send_buttons[chat_id].configure(state='disabled')
        self.stop_buttons[chat_id].configure(state='normal'); self.progress_bars[chat_id].pack(fill=tk.X, padx=5, pady=5)
        self.progress_bars[chat_id].start()

    def send_message(self, chat_id, message=None):
        is_user_message = not message
        if is_user_message:
            msg = self.user_inputs[chat_id].get("1.0", tk.END).strip()
            if msg: self.user_inputs[chat_id].delete("1.0", tk.END)
        else: msg = message
        if not msg: return "break"
        listbox = self.file_lists[chat_id]
        files = listbox.full_paths if hasattr(listbox, 'full_paths') else []
        tag, label = ("user", "You:") if is_user_message else ("autoreply", f"Gemini {2 if chat_id == 1 else 1} (Auto):")
        msg_display = f"{label} {msg}"
        if files: msg_display += f"\nAttached: {', '.join([os.path.basename(p) for p in files])}"
        self.append_message(self.chat_displays[chat_id], "\n" + msg_display, tag)
        self._remove_all_files(chat_id)
        self.current_generation_id[chat_id] += 1
        generation_id = self.current_generation_id[chat_id]
        self.update_ui_for_sending(chat_id)
        thread = threading.Thread(target=self.api_call_thread, args=(self.chat_sessions[chat_id], msg, chat_id, files, generation_id))
        thread.daemon = True; thread.start()
        return "break"

    def stop_generation(self, chat_id): self.current_generation_id[chat_id] += 1

    def api_call_thread(self, session, msg, chat_id, files, generation_id):
        try:
            content = [msg]
            if files:
                uploaded_files = []
                for path in files:
                    try:
                        uploaded_file = genai.upload_file(path=path)
                        uploaded_files.append(uploaded_file)
                    except Exception as e:
                        self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"File Error: {os.path.basename(path)}. Error: {e}", 'generation_id': generation_id})
                        return
                content.extend(uploaded_files)
            self.response_queue.put({'type': 'stream_start', 'chat_id': chat_id, 'generation_id': generation_id})
            response = session.send_message(content, stream=True)
            for chunk in response:
                if self.current_generation_id[chat_id] != generation_id:
                    self.response_queue.put({'type': 'error', 'text': "\n--- Generation stopped by user ---\n", 'chat_id': chat_id, 'generation_id': self.current_generation_id[chat_id]})
                    return
                if not chunk.parts: continue
                if chunk.text:
                    self.response_queue.put({'type': 'stream_chunk', 'chat_id': chat_id, 'text': chunk.text, 'generation_id': generation_id})
            if self.current_generation_id[chat_id] == generation_id:
                usage_meta = response.usage_metadata
                usage_dict = {'prompt_token_count': usage_meta.prompt_token_count, 'candidates_token_count': usage_meta.candidates_token_count} if usage_meta else None
                self.response_queue.put({'type': 'stream_end', 'chat_id': chat_id, 'usage': usage_dict, 'user_message': msg, 'generation_id': generation_id})
        except Exception as e:
            self.response_queue.put({'type': 'error', 'chat_id': chat_id, 'text': f"API Error: {e}", 'generation_id': generation_id})

    def schedule_auto_reply(self, source_id, message):
        target_id = 2 if source_id == 1 else 1
        try:
            delay_minutes = float(self.delay_var.get())
            if delay_minutes < 0: raise ValueError
            delay_ms = int(delay_minutes * 60 * 1000)
        except (ValueError, TypeError):
            self.auto_reply_vars[source_id].set(False)
            self.append_message(self.chat_displays[source_id], "--- Auto-reply stopped: Invalid delay value in Options ---", "error")
            return
        self.root.after(delay_ms, lambda: self.send_message(target_id, message))

    def log_conversation(self, chat_id, user, response):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        path = os.path.join(self.log_dir, f"gemini_{chat_id}_full_{self.session_timestamp}.txt")
        with open(path, 'a', encoding='utf-8') as f: f.write(f"{timestamp}\nUSER: {user}\nGEMINI: {response}\n\n")
    
    def append_message(self, display, message, tag):
        display.tag_remove("sel", "1.0", tk.END)
        display.insert(tk.END, message, tag)
        display.insert(tk.END, "\n")
        # Find which chat_id this display belongs to in order to reset its nav index
        for chat_id, chat_display in self.chat_displays.items():
            if chat_display == display:
                self.current_nav_index[chat_id] = 0
                break
        display.yview(tk.END)

    def navigate_gemini_response(self, chat_id, direction):
        display = self.chat_displays[chat_id]
        total_responses = self.gemini_response_counters[chat_id]
        if total_responses == 0: self.root.bell(); return
        current_index = self.current_nav_index[chat_id]
        new_index = 0; display.tag_remove("sel", "1.0", tk.END)
        if direction == 'up':
            if current_index == 0: new_index = total_responses
            elif current_index > 1: new_index = current_index - 1
            else: new_index = total_responses
        else:
            if current_index == 0: new_index = 1
            elif current_index < total_responses: new_index = current_index + 1
            else: new_index = 1
        if new_index != 0:
            self.current_nav_index[chat_id] = new_index
            target_mark = f"gemini_resp_{chat_id}_{new_index}"
            display.tag_add("sel", f"{target_mark} linestart", f"{target_mark} lineend")
            display.see(target_mark)

    def clear_chat_window(self, chat_id):
        display = self.chat_displays[chat_id]
        display.delete('1.0', tk.END)
        self.gemini_response_counters[chat_id] = 0
        self.current_nav_index[chat_id] = 0

    def on_model_change(self, chat_id):
        if messagebox.askyesno("Confirm Reset", "Changing the model will reset this conversation. Continue?"):
            self.prime_chat_session(chat_id, from_event=True)

    def save_session(self, chat_id):
        if not self.chat_sessions.get(chat_id) or not self.chat_sessions[chat_id].history:
            messagebox.showwarning("Warning", "Nothing to save.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Session Files", "*.json")], title=f"Save Chat {chat_id} Session")
        if not filepath: return
        try:
            history_list = [{'role': c.role, 'parts': [p.text for p in c.parts if hasattr(p, 'text')]} for c in self.chat_sessions[chat_id].history]
            session_data = {"model_name": self.model_selectors[chat_id].get(), "system_prompt": self.options_prompts[chat_id].get("1.0", tk.END).strip(),
                "temperature": self.temp_vars[chat_id].get(), "top_p": self.topp_vars[chat_id].get(), "history": history_list}
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(session_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Session for Chat {chat_id} saved successfully.")
        except Exception as e: messagebox.showerror("Error", f"Failed to save session: {e}")

    def load_session(self, chat_id):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Session Files", "*.json")], title=f"Load Chat {chat_id} Session")
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f: session_data = json.load(f)
            self.model_selectors[chat_id].set(session_data['model_name'])
            self.options_prompts[chat_id].delete("1.0", tk.END); self.options_prompts[chat_id].insert("1.0", session_data['system_prompt'])
            self.temp_vars[chat_id].set(session_data.get('temperature', 0.7)); self.topp_vars[chat_id].set(session_data.get('top_p', 1.0))
            self.update_slider_label(chat_id, 'temp'); self.update_slider_label(chat_id, 'topp')
            self.clear_chat_window(chat_id)
            if chat_id in self.chat_sessions: del self.chat_sessions[chat_id]
            history_from_json = session_data['history']
            self.prime_chat_session(chat_id, history=history_from_json)
            display = self.chat_displays[chat_id]
            for i, message_data in enumerate(self.chat_sessions[chat_id].history):
                try:
                    role, parts = message_data.role, message_data.parts
                    if not parts or not hasattr(parts[0], 'text'): continue
                    text = parts[0].text
                    if (i == 0 and role == 'user') or (role == 'model' and text == "Understood."): continue
                    if role == 'user':
                        self.append_message(display, f"You: {text}", "user")
                    elif role == 'model':
                        self.gemini_response_counters[chat_id] += 1
                        nav_mark_name = f"gemini_resp_{chat_id}_{self.gemini_response_counters[chat_id]}"
                        display.insert(tk.END, f"Gemini {chat_id}: ", "gemini")
                        display.mark_set(nav_mark_name, display.index(tk.INSERT))
                        display.mark_gravity(nav_mark_name, "left")
                        self.highlight_markdown(chat_id, text)
                except (AttributeError, IndexError): continue
            messagebox.showinfo("Success", f"Session for Chat {chat_id} loaded successfully.")
        except Exception as e: messagebox.showerror("Error", f"Failed to load session: {e}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = GeminiChatApp(root)
    root.mainloop()