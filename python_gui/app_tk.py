import tkinter
import tkinter.filedialog # For file/directory dialogs
import tkinter.messagebox # For error popup if service_utils is missing
import customtkinter
import os
import glob # For path detection

# Assuming service_utils.py and service_path_cues.py are in the same directory (python_gui)
try:
    import service_utils
except ImportError as e_import:
    import sys
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    if current_script_dir not in sys.path:
        sys.path.insert(0, current_script_dir)
    try:
        import service_utils
    except ImportError as e_final:
        service_utils = None

try:
    from service_path_cues import SERVICE_PATH_CUES
except ImportError:
    SERVICE_PATH_CUES = []


customtkinter.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"


class AddEditServiceWindow(customtkinter.CTkToplevel):
    def __init__(self, master, service_data=None, existing_service_names=None):
        super().__init__(master)
        self.master_window = master

        self.service_data_in = service_data # Store initial data for editing
        self.existing_service_names = existing_service_names if existing_service_names else []
        self.is_editing_mode = service_data is not None
        self.result_data = None # This will hold the data to be returned

        if self.is_editing_mode:
            self.title("Edit Service")
        else:
            self.title("Add Service")

        self.geometry("500x350")
        self.transient(master)
        self.grab_set()

        self._init_ui()

        if self.is_editing_mode and self.service_data_in:
            self._populate_fields()
            self.service_name_entry.configure(state="disabled")

    def _init_ui(self):
        main_frame = customtkinter.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        main_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(main_frame, text="Friendly Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.friendly_name_entry = customtkinter.CTkEntry(main_frame)
        self.friendly_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        customtkinter.CTkLabel(main_frame, text="Service Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.service_name_entry = customtkinter.CTkEntry(main_frame)
        self.service_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        customtkinter.CTkLabel(main_frame, text="App Path:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        app_path_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        app_path_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        app_path_frame.grid_columnconfigure(0, weight=1)
        self.app_path_entry = customtkinter.CTkEntry(app_path_frame)
        self.app_path_entry.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.app_path_browse_button = customtkinter.CTkButton(app_path_frame, text="Browse...", width=70, command=self._browse_app_path)
        self.app_path_browse_button.grid(row=0, column=1)

        customtkinter.CTkLabel(main_frame, text="App Arguments:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.app_args_entry = customtkinter.CTkEntry(main_frame)
        self.app_args_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        customtkinter.CTkLabel(main_frame, text="Log Directory:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        log_dir_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        log_dir_frame.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        log_dir_frame.grid_columnconfigure(0, weight=1)
        self.log_dir_entry = customtkinter.CTkEntry(log_dir_frame)
        self.log_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.log_dir_browse_button = customtkinter.CTkButton(log_dir_frame, text="Browse...", width=70, command=self._browse_log_dir)
        self.log_dir_browse_button.grid(row=0, column=1)

        customtkinter.CTkLabel(main_frame, text="Startup Delay (sec):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.startup_delay_entry = customtkinter.CTkEntry(main_frame)
        self.startup_delay_entry.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        self.startup_delay_entry.insert(0, "0")

        button_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.ok_button = customtkinter.CTkButton(button_frame, text="OK", command=self._on_ok)
        self.ok_button.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.cancel_button = customtkinter.CTkButton(button_frame, text="Cancel", command=self._on_cancel, fg_color="gray")
        self.cancel_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")


    def _populate_fields(self):
        self.friendly_name_entry.insert(0, self.service_data_in.get("FriendlyName", ""))
        self.service_name_entry.insert(0, self.service_data_in.get("ServiceName", ""))
        self.app_path_entry.insert(0, self.service_data_in.get("AppPath", ""))
        self.app_args_entry.insert(0, self.service_data_in.get("AppArguments", ""))
        self.log_dir_entry.insert(0, self.service_data_in.get("LogDirectory", ""))
        self.startup_delay_entry.delete(0, "end")
        self.startup_delay_entry.insert(0, str(self.service_data_in.get("StartupDelaySeconds", 0)))

    def _browse_app_path(self):
        filePath = tkinter.filedialog.askopenfilename(parent=self, title="Select Application", filetypes=(("Executable files", "*.exe *.bat"), ("All files", "*.*")))
        if filePath:
            self.app_path_entry.delete(0, "end")
            self.app_path_entry.insert(0, filePath)

    def _browse_log_dir(self):
        dirPath = tkinter.filedialog.askdirectory(parent=self, title="Select Log Directory")
        if dirPath:
            self.log_dir_entry.delete(0, "end")
            self.log_dir_entry.insert(0, dirPath)

    def _on_ok(self):
        friendly_name = self.friendly_name_entry.get().strip()
        service_name = self.service_name_entry.get().strip()
        app_path = self.app_path_entry.get().strip()
        app_args = self.app_args_entry.get().strip()
        log_dir = self.log_dir_entry.get().strip()
        startup_delay_str = self.startup_delay_entry.get().strip()

        if not friendly_name:
            friendly_name = service_name

        if not service_name:
            tkinter.messagebox.showerror("Error", "Service Name cannot be empty.", parent=self)
            return
        if not app_path:
            tkinter.messagebox.showerror("Error", "App Path cannot be empty.", parent=self)
            return
        if not log_dir:
             tkinter.messagebox.showerror("Error", "Log Directory cannot be empty.", parent=self)
             return

        if " " in service_name or any(c in service_name for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            tkinter.messagebox.showerror("Error", "Service Name cannot contain spaces or special characters like /\\:*?\"<>|.", parent=self)
            return

        try:
            delay_value = int(startup_delay_str)
            if not (0 <= delay_value <= 3600):
                raise ValueError("Delay out of range")
        except ValueError:
            tkinter.messagebox.showerror("Error", "Startup Delay must be an integer between 0 and 3600.", parent=self)
            return

        if not self.is_editing_mode:
            if service_name.lower() in [name.lower() for name in self.existing_service_names]:
                tkinter.messagebox.showerror("Error", f"Service Name '{service_name}' already exists.", parent=self)
                return

        self.result_data = {
            "FriendlyName": friendly_name,
            "ServiceName": service_name,
            "AppPath": app_path,
            "AppArguments": app_args,
            "LogDirectory": log_dir
        }
        if delay_value > 0:
            self.result_data["StartupDelaySeconds"] = delay_value

        self.destroy()

    def _on_cancel(self):
        self.result_data = None
        self.destroy()

class ConfigEditWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_window = master
        self.config_data_changed = False

        self.title("Edit Service Configurations")
        self.geometry("1000x700")
        self.transient(master)
        self.grab_set()

        if service_utils:
            self.config_data_original = service_utils.load_config(master.config_file_path)
        else:
            self.config_data_original = []
            tkinter.messagebox.showerror("Error", "service_utils not available. Cannot load config.", parent=self)

        self.config_data_working_copy = [dict(item) for item in self.config_data_original]
        self.selected_service_index = None

        self._init_ui()
        self._populate_config_list()
        self._update_edit_remove_button_states()

    def _init_ui(self):
        main_frame = customtkinter.CTkFrame(self)
        main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        base_dir_frame = customtkinter.CTkFrame(main_frame)
        base_dir_frame.pack(fill="x", pady=5, padx=5)
        customtkinter.CTkLabel(base_dir_frame, text="TERA Server Base Directory:").pack(side="left", padx=5)
        self.base_dir_edit = customtkinter.CTkEntry(base_dir_frame, width=400)
        self.base_dir_edit.pack(side="left", expand=True, fill="x", padx=5)
        self.base_dir_browse_button = customtkinter.CTkButton(base_dir_frame, text="Browse...", width=80, command=self._browse_base_dir)
        self.base_dir_browse_button.pack(side="left", padx=5)

        controls_frame = customtkinter.CTkFrame(main_frame)
        controls_frame.pack(fill="x", pady=5, padx=5)
        self.auto_detect_button = customtkinter.CTkButton(controls_frame, text="Auto-detect App Paths", command=self._auto_detect_paths)
        self.auto_detect_button.pack(side="left", padx=5)
        self.add_button = customtkinter.CTkButton(controls_frame, text="Add Service...", command=self._add_service)
        self.add_button.pack(side="left", padx=5)
        self.edit_button = customtkinter.CTkButton(controls_frame, text="Edit Service...", command=self._edit_service)
        self.edit_button.pack(side="left", padx=5)
        self.remove_button = customtkinter.CTkButton(controls_frame, text="Remove Service", command=self._remove_service)
        self.remove_button.pack(side="left", padx=5)

        customtkinter.CTkLabel(main_frame, text="Service Configurations:", font=customtkinter.CTkFont(weight="bold")).pack(pady=(10,0))
        self.scrollable_config_frame = customtkinter.CTkScrollableFrame(main_frame, height=300)
        self.scrollable_config_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.service_row_widgets = []

        save_cancel_frame = customtkinter.CTkFrame(main_frame)
        save_cancel_frame.pack(fill="x", pady=10, padx=5)
        save_cancel_frame.grid_columnconfigure(0, weight=1)
        self.save_button = customtkinter.CTkButton(save_cancel_frame, text="Save Changes", command=self._save_changes)
        self.save_button.pack(side="right", padx=10)
        self.cancel_button = customtkinter.CTkButton(save_cancel_frame, text="Cancel", command=self.destroy, fg_color="gray")
        self.cancel_button.pack(side="right", padx=10)


    def _browse_base_dir(self):
        dirPath = tkinter.filedialog.askdirectory(parent=self, title="Select TERA Server Base Directory")
        if dirPath:
            self.base_dir_edit.delete(0, "end")
            self.base_dir_edit.insert(0, dirPath)

    def _populate_config_list(self):
        for widget_info in self.service_row_widgets:
            widget_info["frame"].destroy()
        self.service_row_widgets.clear()

        current_selection_index_before_repop = self.selected_service_index
        self.selected_service_index = None

        headers = ["Friendly Name", "Service Name", "Application Path"]
        header_frame_list = customtkinter.CTkFrame(self.scrollable_config_frame, fg_color="transparent")
        header_frame_list.pack(fill="x", pady=(0,5), before=self.scrollable_config_frame.winfo_children()[0] if self.scrollable_config_frame.winfo_children() else None)
        for col, header_text in enumerate(headers):
            header_frame_list.grid_columnconfigure(col, weight=1 if col == 0 else (2 if col == 1 else 3))
            customtkinter.CTkLabel(header_frame_list, text=header_text, font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=col, padx=5, sticky="w")
        self.service_row_widgets.append({"frame": header_frame_list, "is_header": True})

        for idx, service_item in enumerate(self.config_data_working_copy):
            row_frame = customtkinter.CTkFrame(self.scrollable_config_frame, height=30, fg_color="transparent")
            row_frame.pack(fill="x", pady=1, padx=1)

            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=2)
            row_frame.grid_columnconfigure(2, weight=3)

            fn_label = customtkinter.CTkLabel(row_frame, text=service_item.get("FriendlyName", "N/A"), anchor="w")
            fn_label.grid(row=0, column=0, padx=5, sticky="ew")
            sn_label = customtkinter.CTkLabel(row_frame, text=service_item.get("ServiceName", "N/A"), anchor="w")
            sn_label.grid(row=0, column=1, padx=5, sticky="ew")
            ap_label = customtkinter.CTkLabel(row_frame, text=service_item.get("AppPath", "N/A"), anchor="w")
            ap_label.grid(row=0, column=2, padx=5, sticky="ew")

            self.service_row_widgets.append({"frame": row_frame, "data": service_item, "index": idx})

            for widget in [row_frame, fn_label, sn_label, ap_label]:
                 widget.bind("<Button-1>", lambda event, index=idx: self._on_service_row_selected(index))

        if current_selection_index_before_repop is not None and current_selection_index_before_repop < len(self.config_data_working_copy):
             self._on_service_row_selected(current_selection_index_before_repop)
        else:
            self._update_edit_remove_button_states()


    def _on_service_row_selected(self, index):
        for i, widget_info in enumerate(self.service_row_widgets):
            if not widget_info.get("is_header", False):
                if i == self.selected_service_index +1:
                     widget_info["frame"].configure(fg_color="transparent")

        self.selected_service_index = index
        if self.selected_service_index is not None and (self.selected_service_index + 1) < len(self.service_row_widgets):
            self.service_row_widgets[self.selected_service_index + 1]["frame"].configure(fg_color=("gray75", "gray25"))

        self._update_edit_remove_button_states()


    def _update_edit_remove_button_states(self):
        can_edit_remove = self.selected_service_index is not None
        self.edit_button.configure(state="normal" if can_edit_remove else "disabled")
        self.remove_button.configure(state="normal" if can_edit_remove else "disabled")

    def _add_service(self):
        existing_names = [s.get("ServiceName", "") for s in self.config_data_working_copy]
        dialog = AddEditServiceWindow(master=self, existing_service_names=existing_names)
        self.wait_window(dialog)
        if dialog.result_data:
            self.config_data_working_copy.append(dialog.result_data)
            self._populate_config_list()
            new_index = len(self.config_data_working_copy) - 1
            if new_index >=0 :
                 self._on_service_row_selected(new_index)

    def _edit_service(self):
        if self.selected_service_index is None or self.selected_service_index >= len(self.config_data_working_copy):
            tkinter.messagebox.showwarning("No Selection", "Please select a service to edit.", parent=self)
            return

        service_to_edit = self.config_data_working_copy[self.selected_service_index]
        dialog = AddEditServiceWindow(master=self, service_data=dict(service_to_edit))
        self.wait_window(dialog)
        if dialog.result_data:
            self.config_data_working_copy[self.selected_service_index] = dialog.result_data
            self._populate_config_list()
            self._on_service_row_selected(self.selected_service_index)

    def _remove_service(self):
        if self.selected_service_index is None or self.selected_service_index >= len(self.config_data_working_copy):
            tkinter.messagebox.showwarning("No Selection", "Please select a service to remove.", parent=self)
            return

        service_to_remove = self.config_data_working_copy[self.selected_service_index]
        if tkinter.messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{service_to_remove.get('FriendlyName')}'?", parent=self):
            del self.config_data_working_copy[self.selected_service_index]
            self.selected_service_index = None
            self._populate_config_list()

    def _auto_detect_paths(self):
        base_directory = self.base_dir_edit.get().strip()
        if not base_directory or not os.path.isdir(base_directory):
            tkinter.messagebox.showwarning("Warning", "Please select a valid TERA Server Base Directory first.", parent=self)
            return

        if not SERVICE_PATH_CUES:
            tkinter.messagebox.showwarning("Warning", "Service path cues are not loaded. Cannot auto-detect.", parent=self)
            return

        found_count = 0
        not_found_services = []
        service_name_to_cues = {item["ServiceName"]: item["SearchCues"] for item in SERVICE_PATH_CUES}

        for service_entry in self.config_data_working_copy:
            service_name = service_entry.get("ServiceName")
            if not service_name: continue

            cues = service_name_to_cues.get(service_name)
            if not cues:
                not_found_services.append(service_name)
                continue

            path_found_for_this_service = False
            for cue in cues:
                sub_dir = cue.get("sub_dir", "")
                filename_pattern = cue["filename_pattern"]
                current_search_path = os.path.join(base_directory, sub_dir, filename_pattern)

                matches = glob.glob(current_search_path)
                if matches:
                    service_entry["AppPath"] = os.path.normpath(matches[0])
                    found_count += 1
                    path_found_for_this_service = True
                    break

            if not path_found_for_this_service:
                not_found_services.append(service_name)

        self._populate_config_list()

        message = f"Path detection complete.\n\nFound paths for {found_count} service(s).\n"
        if not_found_services:
            message += f"\nCould not automatically find paths for: {', '.join(not_found_services)}.\nPlease set them manually or verify cues."
        elif found_count > 0:
             message += "\nAll configured services with defined cues appear to have paths found."
        elif not self.config_data_working_copy:
             message += "\nNo services configured to detect paths for."
        else:
             message += "\nNo paths were found, possibly due to missing cues or incorrect base directory."
        tkinter.messagebox.showinfo("Auto-detect Paths Result", message, parent=self)

    def _save_changes(self):
        if service_utils and service_utils.save_config(self.master_window.config_file_path, self.config_data_working_copy):
            tkinter.messagebox.showinfo("Success", "Configuration saved successfully.", parent=self)
            self.master_window.config_data_changed_by_editor = True
            self.destroy()
        else:
            tkinter.messagebox.showerror("Error", "Failed to save configuration.", parent=self)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Windows Service Manager (Tkinter)")
        self.geometry("1000x650") # Slightly taller for new buttons row

        self.service_utils_available = bool(service_utils)
        self.config_data_changed_by_editor = False

        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server_config.json")
        self.config_file_path = os.path.normpath(self.config_file_path)


        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Top control frame for Edit Config button
        top_controls_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        top_controls_frame.pack(fill="x", pady=(0,5))
        self.edit_config_button = customtkinter.CTkButton(top_controls_frame, text="Edit Configurations", command=self._open_config_editor)
        self.edit_config_button.pack(anchor="ne") # Anchor to top-right

        # Header for the service list
        header_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(0,5))

        self.headers = ["Friendly Name", "Service Name", "Status", "PID", "Actions"]
        self.column_weights = [3, 2, 1, 1, 2]

        for i, header_text in enumerate(self.headers):
            header_frame.grid_columnconfigure(i, weight=self.column_weights[i])
            header_label = customtkinter.CTkLabel(header_frame, text=header_text, font=customtkinter.CTkFont(weight="bold"))
            header_label.grid(row=0, column=i, padx=5, pady=2, sticky="ew")


        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.main_frame)
        self.scrollable_frame.pack(pady=5, padx=10, fill="both", expand=True)
        self.service_row_frames = []

        # Bottom control buttons frame
        bottom_controls_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_controls_frame.pack(fill="x", pady=10, padx=10)

        self.start_all_button = customtkinter.CTkButton(bottom_controls_frame, text="Start All Services", command=self._start_all_services)
        self.start_all_button.pack(side="left", padx=5)

        self.stop_all_button = customtkinter.CTkButton(bottom_controls_frame, text="Stop All Services", command=self._stop_all_services)
        self.stop_all_button.pack(side="left", padx=5)

        # Spacer to push refresh to the right
        spacer = customtkinter.CTkFrame(bottom_controls_frame, fg_color="transparent")
        spacer.pack(side="left", expand=True)

        self.refresh_button = customtkinter.CTkButton(bottom_controls_frame, text="Refresh Status", command=self.load_and_display_statuses)
        self.refresh_button.pack(side="right", padx=5)


        self.status_bar = customtkinter.CTkLabel(self, text="Welcome!", anchor="w") # Updated initial message
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=5)

        if not self.service_utils_available:
            error_message = "CRITICAL ERROR: service_utils.py not found.\n\nPlease ensure service_utils.py is in the python_gui directory.\n\nThe application cannot function without it."
            self.status_bar.configure(text=error_message, text_color="red")
            tkinter.messagebox.showerror("Error", error_message, parent=self)
            self.refresh_button.configure(state="disabled")
            self.edit_config_button.configure(state="disabled")
            if hasattr(self, 'start_all_button'): self.start_all_button.configure(state="disabled")
            if hasattr(self, 'stop_all_button'): self.stop_all_button.configure(state="disabled")
            return

        self.load_and_display_statuses()
        self.after(10000, self.auto_refresh_statuses)
        self.after(500, self._schedule_initial_delayed_starts)


    def _open_config_editor(self):
        if not self.service_utils_available:
            tkinter.messagebox.showerror("Error", "service_utils.py not available. Cannot edit configurations.", parent=self)
            return

        self.config_data_changed_by_editor = False
        config_editor_window = ConfigEditWindow(self)
        self.wait_window(config_editor_window)

        if self.config_data_changed_by_editor:
            self.status_bar.configure(text="Configuration updated. Refreshing statuses...")
            self.load_and_display_statuses()
            self.after(500, self._schedule_initial_delayed_starts)
        else:
            self.status_bar.configure(text="Configuration edit cancelled or no changes made.")


    def auto_refresh_statuses(self):
        if self.service_utils_available:
            self.load_and_display_statuses()
        self.after(10000, self.auto_refresh_statuses)

    def create_service_row(self, parent_frame, service_info, status_info):
        row_frame = customtkinter.CTkFrame(parent_frame, fg_color=("gray90", "gray20"), height=30)
        row_frame.pack(fill="x", pady=1, padx=1)

        for i, weight in enumerate(self.column_weights):
            row_frame.grid_columnconfigure(i, weight=weight)

        friendly_name = service_info.get("FriendlyName", "N/A")
        service_name = service_info.get("ServiceName", "N/A")
        status, pid = status_info

        details = [
            friendly_name,
            service_name,
            status,
            str(pid if pid is not None else "N/A")
        ]

        for i, detail_text in enumerate(details):
            detail_label = customtkinter.CTkLabel(row_frame, text=detail_text, anchor="w")
            detail_label.grid(row=0, column=i, padx=5, pady=2, sticky="ew")

            if i == 2:
                color = "white"
                if status == "running": color = "lightgreen"
                elif status == "stopped": color = "salmon"
                elif status == "Not Found": color = "gray"
                elif "pending" in status.lower(): color = "orange"
                elif status == "ConfigError": color = "yellow"
                detail_label.configure(text_color=color)

        actions_frame = customtkinter.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=4, sticky="ew", padx=5)

        start_button = customtkinter.CTkButton(actions_frame, text="Start", width=60)
        start_button.pack(side="left", padx=2)

        stop_button = customtkinter.CTkButton(actions_frame, text="Stop", width=60)
        stop_button.pack(side="left", padx=2)

        if service_name != "N/A" and service_name != "INVALID_CONFIG":
            start_button.configure(command=lambda s=service_name: self._start_single_service(s))
            stop_button.configure(command=lambda s=service_name: self._stop_single_service(s))
        else:
            start_button.configure(state="disabled")
            stop_button.configure(state="disabled")

        status_lower = status.lower()
        if service_name == "N/A" or service_name == "INVALID_CONFIG" or status == "ConfigError":
            start_button.configure(state="disabled")
            stop_button.configure(state="disabled")
        elif status_lower == "running":
            start_button.configure(state="disabled")
            stop_button.configure(state="normal")
        elif status_lower == "stopped":
            start_button.configure(state="normal")
            stop_button.configure(state="disabled")
        else:
            start_button.configure(state="disabled")
            stop_button.configure(state="disabled")
            if status_lower == "not found":
                start_button.configure(state="normal")
        return row_frame

    def _start_single_service(self, service_name: str):
        if service_name == "N/A" or service_name == "INVALID_CONFIG" or not self.service_utils_available:
            return

        self.status_bar.configure(text=f"Attempting to start {service_name}...")
        success = service_utils.start_service_app(service_name)

        if success:
            self.status_bar.configure(text=f"Start command issued for {service_name}.")
        else:
            self.status_bar.configure(text=f"Failed to issue start command for {service_name}.")
            tkinter.messagebox.showerror("Error", f"Could not start service: {service_name}", parent=self)

        self.load_and_display_statuses()

    def _stop_single_service(self, service_name: str):
        if service_name == "N/A" or service_name == "INVALID_CONFIG" or not self.service_utils_available:
            return

        self.status_bar.configure(text=f"Attempting to stop {service_name}...")
        success = service_utils.stop_service_app(service_name)

        if success:
            self.status_bar.configure(text=f"Stop command issued for {service_name}.")
        else:
            self.status_bar.configure(text=f"Failed to issue stop command for {service_name}.")
            tkinter.messagebox.showerror("Error", f"Could not stop service: {service_name}", parent=self)

        self.load_and_display_statuses()

    def _start_all_services(self):
        if not self.service_utils_available:
            tkinter.messagebox.showerror("Error", "Service utilities are not available.", parent=self)
            return

        self.status_bar.configure(text="Attempting to start all configured services...")
        config = service_utils.load_config(self.config_file_path)
        if not config:
            self.status_bar.configure(text="No services configured.")
            tkinter.messagebox.showinfo("Information", "No services configured.", parent=self)
            return

        started_count = 0
        already_running_count = 0
        failed_to_start = []

        for entry in config:
            service_name = entry.get("ServiceName")
            if service_name:
                status, _ = service_utils.get_service_status(service_name)
                if status == "stopped" or status == "Not Found":
                    if service_utils.start_service_app(service_name):
                        started_count += 1
                    else:
                        failed_to_start.append(service_name)
                elif status == "running":
                    already_running_count +=1

        self.load_and_display_statuses()
        summary_message = f"Start All action complete.\n\nStarted: {started_count}\nAlready Running: {already_running_count}"
        if failed_to_start:
            summary_message += f"\nFailed to start: {', '.join(failed_to_start)}"

        self.status_bar.configure(text=f"Start All: {started_count} started, {already_running_count} already running.")
        tkinter.messagebox.showinfo("Start All Services", summary_message, parent=self)

    def _stop_all_services(self):
        if not self.service_utils_available:
            tkinter.messagebox.showerror("Error", "Service utilities are not available.", parent=self)
            return

        self.status_bar.configure(text="Attempting to stop all configured services...")
        config = service_utils.load_config(self.config_file_path)
        if not config:
            self.status_bar.configure(text="No services configured.")
            tkinter.messagebox.showinfo("Information", "No services configured.", parent=self)
            return

        stopped_count = 0
        already_stopped_count = 0
        failed_to_stop = []

        for entry in config:
            service_name = entry.get("ServiceName")
            if service_name:
                status, _ = service_utils.get_service_status(service_name)
                if status == "running" or status == "paused":
                    if service_utils.stop_service_app(service_name):
                        stopped_count += 1
                    else:
                        failed_to_stop.append(service_name)
                elif status == "stopped":
                    already_stopped_count +=1

        self.load_and_display_statuses()
        summary_message = f"Stop All action complete.\n\nStopped: {stopped_count}\nAlready Stopped: {already_stopped_count}"
        if failed_to_stop:
            summary_message += f"\nFailed to stop: {', '.join(failed_to_stop)}"

        self.status_bar.configure(text=f"Stop All: {stopped_count} stopped, {already_stopped_count} already stopped.")
        tkinter.messagebox.showinfo("Stop All Services", summary_message, parent=self)


    def load_and_display_statuses(self):
        if not self.service_utils_available:
            self.status_bar.configure(text="ERROR: service_utils.py not found. Functionality limited.")
            return

        self.status_bar.configure(text="Loading service configurations...")

        config = service_utils.load_config(self.config_file_path)

        for frame in self.service_row_frames:
            frame.destroy()
        self.service_row_frames.clear()

        if not config:
            if not os.path.exists(self.config_file_path):
                 msg = f"ERROR: Configuration file '{self.config_file_path}' not found."
            else:
                 msg = f"No services found in '{self.config_file_path}' or file is empty/invalid."

            self.status_bar.configure(text=msg)
            no_service_label = customtkinter.CTkLabel(self.scrollable_frame, text=msg)
            no_service_label.pack(pady=20)
            self.service_row_frames.append(no_service_label)
            return

        self.status_bar.configure(text="Fetching service statuses...")
        any_service_valid = False
        for service_entry in config:
            service_name = service_entry.get("ServiceName")
            if service_name:
                any_service_valid = True
                status_tuple = service_utils.get_service_status(service_name)
                row = self.create_service_row(self.scrollable_frame, service_entry, status_tuple)
                self.service_row_frames.append(row)
            else:
                error_info = {"FriendlyName": service_entry.get("FriendlyName", "Unnamed Invalid Entry"), "ServiceName": "INVALID_CONFIG"}
                error_status = ("ConfigError", None)
                row = self.create_service_row(self.scrollable_frame, error_info, error_status)
                self.service_row_frames.append(row)

        if not any_service_valid and config:
            msg = "Configuration file has entries but all are missing 'ServiceName'."
            self.status_bar.configure(text=msg)
            no_service_label = customtkinter.CTkLabel(self.scrollable_frame, text=msg)
            no_service_label.pack(pady=20)
            self.service_row_frames.append(no_service_label)
            return

        self.status_bar.configure(text="Status display updated.")

    def _schedule_initial_delayed_starts(self):
        if not self.service_utils_available: return
        self.status_bar.configure(text="Scheduling initial delayed service starts...")
        config_data = service_utils.load_config(self.config_file_path)

        if not config_data:
            self.status_bar.configure(text="No configuration for delayed starts.")
            return

        for entry in config_data:
            service_name = entry.get("ServiceName")
            delay_seconds = entry.get("StartupDelaySeconds", 0)

            if service_name and delay_seconds > 0:
                current_status, _ = service_utils.get_service_status(service_name)
                if current_status == "stopped":
                    self.after(delay_seconds * 1000, lambda s=service_name: self._attempt_delayed_start(s))
                    self.status_bar.configure(text=f"'{service_name}' scheduled for delayed start in {delay_seconds}s.")

    def _attempt_delayed_start(self, service_name: str):
        if not self.service_utils_available: return
        self.status_bar.configure(text=f"Attempting delayed start for {service_name}...")

        current_status, _ = service_utils.get_service_status(service_name)
        if current_status != "stopped":
            self.status_bar.configure(text=f"Delayed start for '{service_name}' skipped: Service no longer stopped (status: {current_status}).")
            self.load_and_display_statuses()
            return

        success = service_utils.start_service_app(service_name)
        if success:
            self.status_bar.configure(text=f"Delayed start command issued for '{service_name}'.")
        else:
            self.status_bar.configure(text=f"Failed to issue delayed start command for '{service_name}'.")

        self.load_and_display_statuses()


if __name__ == "__main__":
    app = App()
    app.mainloop()

```
