import customtkinter as ctk
import os
from datetime import datetime
import json # Import json for parsing log entries
from tkinter import ttk # Import ttk for Treeview
import re # Import re for regular expressions

class LogViewerWindow(ctk.CTkToplevel):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.app = app_instance
        self.title(self.app.lang.get('log_viewer_title'))
        self.geometry("1000x700") # Adjusted width for 4 columns
        self.grab_set() # Make window modal

        self.grid_columnconfigure(0, weight=0) # Left panel (log list) does not expand horizontally
        self.grid_columnconfigure(1, weight=1) # Right panel (log content) expands horizontally
        self.grid_rowconfigure(0, weight=1) # Single row expands vertically

        self.current_selected_log_button = None # To keep track of the currently selected log file button

        # Left frame for log file list
        self.log_list_frame = ctk.CTkFrame(self, width=250) # Fixed width for left panel
        self.log_list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns") # Stick north-south
        self.log_list_frame.grid_propagate(False) # Prevent frame from resizing to fit content
        self.log_list_frame.grid_columnconfigure(0, weight=1)
        self.log_list_frame.grid_rowconfigure(1, weight=1) # Make the scrollable frame expand vertically

        self.log_files_label = ctk.CTkLabel(self.log_list_frame, text=self.app.lang.get('log_files_label'), font=self.app.FONT_SMALL)
        self.log_files_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.log_files_scrollable_frame = ctk.CTkScrollableFrame(self.log_list_frame) # Removed fixed height
        self.log_files_scrollable_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Right frame for log content preview (Treeview)
        self.log_content_frame = ctk.CTkFrame(self)
        self.log_content_frame.grid(row=0, column=1, padx=10, pady=(0, 10), sticky="nsew")
        self.log_content_frame.grid_columnconfigure(0, weight=1)
        self.log_content_frame.grid_rowconfigure(0, weight=0)
        self.log_content_frame.grid_rowconfigure(1, weight=1) # Make the Treeview row expand

        self.log_content_label = ctk.CTkLabel(self.log_content_frame, text=self.app.lang.get('log_content_label'), font=self.app.FONT_SMALL)
        self.log_content_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        # Configure Treeview style
        style = ttk.Style()
        style.theme_use("default") # Use default theme as a base
        style.configure("Treeview",
                        background="#1E1F22", # Black background
                        foreground="white",
                        fieldbackground="#1E1F22",
                        bordercolor="#1E1F22",
                        rowheight=25)
        style.map('Treeview', background=[('selected', '#3C3F44')]) # Selected item background
        style.configure("Treeview.Heading",
                        background="#282A2E", # Darker background for headings
                        foreground="white",
                        font=self.app.FONT_BOLD)
        style.map("Treeview.Heading", background=[('active', '#3C3F44')])

        # Define tags for coloring
        self.log_tree = ttk.Treeview(self.log_content_frame, columns=("time", "name", "level", "message"), show="headings")
        self.log_tree.tag_configure('warning', background='#4A4A00', foreground='yellow') # Dark yellow background for warning
        self.log_tree.tag_configure('error', background='#4A0000', foreground='red') # Dark red background for error
        self.log_tree.tag_configure('critical', background='#4A0000', foreground='red', font=self.app.FONT_BOLD) # Critical is also red and bold

        self.log_tree.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Configure columns
        self.log_tree.heading("time", text=self.app.lang.get('log_col_time'), anchor="w")
        self.log_tree.heading("name", text=self.app.lang.get('log_col_name'), anchor="w")
        self.log_tree.heading("level", text=self.app.lang.get('log_col_level'), anchor="w")
        self.log_tree.heading("message", text=self.app.lang.get('log_col_message'), anchor="w")

        self.log_tree.column("time", width=150, minwidth=100, stretch=False)
        self.log_tree.column("name", width=200, minwidth=100, stretch=False)
        self.log_tree.column("level", width=80, minwidth=60, stretch=False)
        self.log_tree.column("message", width=600, minwidth=200, stretch=True) # Adjusted width

        # Add scrollbars
        vsb = ctk.CTkScrollbar(self.log_content_frame, orientation="vertical", command=self.log_tree.yview)
        hsb = ctk.CTkScrollbar(self.log_content_frame, orientation="horizontal", command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        self.load_log_files()
        self.update_text()

    def select_log_file(self, file_path, button_widget):
        """Handles log file selection and highlighting."""
        # Reset previous selection
        if self.current_selected_log_button:
            self.current_selected_log_button.configure(fg_color="transparent")
        
        # Set new selection
        button_widget.configure(fg_color=self.app.COLOR_WIDGET_BG) # Use a distinct color for selected
        self.current_selected_log_button = button_widget
        
        self.show_log_content(file_path)

    def load_log_files(self):
        for widget in self.log_files_scrollable_frame.winfo_children():
            widget.destroy()

        log_dir = "logs"
        if not os.path.exists(log_dir):
            ctk.CTkLabel(self.log_files_scrollable_frame, text=self.app.lang.get('no_logs_found')).pack(padx=5, pady=2, anchor="w")
            return

        log_files = sorted([f for f in os.listdir(log_dir) if f.startswith("app_") and f.endswith(".log")], reverse=True)

        if not log_files:
            ctk.CTkLabel(self.log_files_scrollable_frame, text=self.app.lang.get('no_logs_found')).pack(padx=5, pady=2, anchor="w")
            return

        for log_file in log_files:
            file_path = os.path.join(log_dir, log_file)
            timestamp_str = log_file.replace("app_", "").replace(".log", "")
            try:
                dt_object = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                display_name = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                display_name = log_file

            btn = ctk.CTkButton(self.log_files_scrollable_frame, text=display_name, anchor="w", fg_color="transparent", text_color=self.app.COLOR_TEXT)
            btn.configure(command=lambda path=file_path, current_btn=btn: self.select_log_file(path, current_btn)) # Capture btn as current_btn
            btn.pack(fill="x", padx=5, pady=2)

    def show_log_content(self, file_path):
        # Clear existing content
        for i in self.log_tree.get_children():
            self.log_tree.delete(i)

        # Regex to parse the standard logging prefix
        log_prefix_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^ ]+) - ([A-Z]+) - (.*)$")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    time_col = ""
                    name_col = ""
                    level_col = ""
                    message_col = ""
                    tags = ()

                    match = log_prefix_pattern.match(line)
                    if match:
                        time_col = match.group(1)
                        name_col = match.group(2)
                        level_col = match.group(3).upper() # Ensure uppercase for consistent tagging
                        remaining_line = match.group(4)

                        # Determine tag for coloring based on level from prefix
                        if level_col == "WARNING":
                            tags = ('warning',)
                        elif level_col == "ERROR" or level_col == "CRITICAL":
                            tags = ('error',)

                        # Try to find and parse the JSON part
                        json_start_index = remaining_line.find('{"event":')
                        if json_start_index != -1:
                            json_part = remaining_line[json_start_index:]
                            # suffix_part = remaining_line[json_start_index + len(json_part):] # No longer needed

                            try:
                                log_entry = json.loads(json_part)
                                message_col = log_entry.get("event", "")
                                
                                # The 'other' column is removed, so no need to build other_col
                                # other_fields = {k: v for k, v in log_entry.items() if k not in ["event", "level", "timestamp", "filename", "lineno", "logger", "logger_name"]}
                                # other_col_parts = []
                                # if other_fields:
                                #     other_col_parts.append(json.dumps(other_fields, ensure_ascii=False))
                                # if "filename" in log_entry and "lineno" in log_entry:
                                #     other_col_parts.append(f"{log_entry['filename']}:{log_entry['lineno']}")
                                # if suffix_part.strip():
                                #     other_col_parts.append(suffix_part.strip())
                                # other_col = " ".join(other_col_parts)

                            except json.JSONDecodeError:
                                # If JSON parsing fails, put the whole remaining_line into message_col
                                message_col = remaining_line
                        else:
                            # No JSON part found, put the whole remaining_line into message_col
                            message_col = remaining_line
                    else:
                        # Line does not match expected prefix format, put whole line into message_col
                        message_col = line

                    self.log_tree.insert("", "end", values=(time_col, name_col, level_col, message_col), tags=tags)

        except Exception as e:
            self.log_tree.insert("", "end", values=("", "ERROR", "", f"Error reading log file: {e}"), tags=('error',))

    def update_text(self):
        self.title(self.app.lang.get('log_viewer_title'))
        self.log_files_label.configure(text=self.app.lang.get('log_files_label'))
        self.log_content_label.configure(text=self.app.lang.get('log_content_label'))
        
        # Update Treeview headings
        self.log_tree.heading("time", text=self.app.lang.get('log_col_time'), anchor="w")
        self.log_tree.heading("name", text=self.app.lang.get('log_col_name'), anchor="w")
        self.log_tree.heading("level", text=self.app.lang.get('log_col_level'), anchor="w")
        self.log_tree.heading("message", text=self.app.lang.get('log_col_message'), anchor="w")

        # Reload log files to update button texts if language changes
        self.load_log_files()