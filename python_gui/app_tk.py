import tkinter
import tkinter.filedialog
import tkinter.messagebox
import customtkinter
import os 
import glob
import threading # For monitoring thread
import time      # For sleep in monitor thread

# Assuming process_manager.py, service_utils.py and service_path_cues.py are in the same directory (python_gui)
try:
    from . import process_manager # Use relative import if app_tk.py is part of a package
    # OR direct import if python_gui is added to PYTHONPATH or when running from project root
    # import process_manager 
except ImportError: # Fallback for running app_tk.py directly from python_gui folder
    import sys
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    if current_script_dir not in sys.path:
        sys.path.insert(0, current_script_dir)
    try:
        import process_manager
    except ImportError as e_final:
        process_manager = None # Explicitly set to None if not found

# service_utils is still needed by ConfigEditWindow for save_config, and App for initial config load path
try:
    from . import service_utils
except ImportError:
    try:
        import service_utils
    except ImportError:
        service_utils = None # Will be checked in App and ConfigEditWindow

try:
    from . import service_path_cues # if SERVICE_PATH_CUES is needed by ConfigEditWindow directly
    SERVICE_PATH_CUES = service_path_cues.SERVICE_PATH_CUES
except ImportError:
    try:
        from service_path_cues import SERVICE_PATH_CUES
    except ImportError:
        SERVICE_PATH_CUES = []


customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class AddEditServiceWindow(customtkinter.CTkToplevel):
    def __init__(self, master, service_data=None, existing_service_names=None):
        super().__init__(master)
        self.master_window = master 

        self.service_data_in = service_data 
        self.existing_service_names = existing_service_names if existing_service_names else []
        self.is_editing_mode = service_data is not None
        self.result_data = None 

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
        button_frame.grid_columnconfigure(0, weight=1); button_frame.grid_columnconfigure(1, weight=1)
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
        if filePath: self.app_path_entry.delete(0, "end"); self.app_path_entry.insert(0, filePath)

    def _browse_log_dir(self):
        dirPath = tkinter.filedialog.askdirectory(parent=self, title="Select Log Directory")
        if dirPath: self.log_dir_entry.delete(0, "end"); self.log_dir_entry.insert(0, dirPath)

    def _on_ok(self):
        friendly_name = self.friendly_name_entry.get().strip()
        service_name = self.service_name_entry.get().strip()
        app_path = self.app_path_entry.get().strip()
        app_args = self.app_args_entry.get().strip()
        log_dir = self.log_dir_entry.get().strip()
        startup_delay_str = self.startup_delay_entry.get().strip()
        if not friendly_name: friendly_name = service_name 
        if not service_name: tkinter.messagebox.showerror("Error", "Service Name cannot be empty.", parent=self); return
        if not app_path: tkinter.messagebox.showerror("Error", "App Path cannot be empty.", parent=self); return
        if not log_dir: tkinter.messagebox.showerror("Error", "Log Directory cannot be empty.", parent=self); return
        if " " in service_name or any(c in service_name for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            tkinter.messagebox.showerror("Error", "Service Name invalid characters.", parent=self); return
        try:
            delay_value = int(startup_delay_str)
            if not (0 <= delay_value <= 3600): raise ValueError("Delay out of range")
        except ValueError: tkinter.messagebox.showerror("Error", "Startup Delay invalid.", parent=self); return
        if not self.is_editing_mode and service_name.lower() in [name.lower() for name in self.existing_service_names]:
            tkinter.messagebox.showerror("Error", f"Service Name '{service_name}' already exists.", parent=self); return
        
        self.result_data = {"FriendlyName": friendly_name, "ServiceName": service_name, "AppPath": app_path, 
                            "AppArguments": app_args, "LogDirectory": log_dir}
        if delay_value > 0: self.result_data["StartupDelaySeconds"] = delay_value
        self.destroy()

    def _on_cancel(self): self.result_data = None; self.destroy()

class ConfigEditWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_window = master
        self.config_data_changed = False 
        self.title("Edit Service Configurations"); self.geometry("1000x700"); self.transient(master); self.grab_set()

        if service_utils: self.config_data_original = service_utils.load_config(process_manager.CONFIG_FILE_PATH) # Use path from process_manager
        else: self.config_data_original = []; tkinter.messagebox.showerror("Error", "service_utils not available.", parent=self)
        
        self.config_data_working_copy = [dict(item) for item in self.config_data_original]
        self.selected_service_index = None
        self._init_ui(); self._populate_config_list(); self._update_edit_remove_button_states()

    def _init_ui(self):
        main_frame = customtkinter.CTkFrame(self); main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        base_dir_frame = customtkinter.CTkFrame(main_frame); base_dir_frame.pack(fill="x", pady=5, padx=5)
        customtkinter.CTkLabel(base_dir_frame, text="TERA Server Base Directory:").pack(side="left", padx=5)
        self.base_dir_edit = customtkinter.CTkEntry(base_dir_frame, width=400); self.base_dir_edit.pack(side="left", expand=True, fill="x", padx=5)
        self.base_dir_browse_button = customtkinter.CTkButton(base_dir_frame, text="Browse...", width=80, command=self._browse_base_dir); self.base_dir_browse_button.pack(side="left", padx=5)
        controls_frame = customtkinter.CTkFrame(main_frame); controls_frame.pack(fill="x", pady=5, padx=5)
        self.auto_detect_button = customtkinter.CTkButton(controls_frame, text="Auto-detect App Paths", command=self._auto_detect_paths); self.auto_detect_button.pack(side="left", padx=5)
        self.add_button = customtkinter.CTkButton(controls_frame, text="Add Service...", command=self._add_service); self.add_button.pack(side="left", padx=5)
        self.edit_button = customtkinter.CTkButton(controls_frame, text="Edit Service...", command=self._edit_service); self.edit_button.pack(side="left", padx=5)
        self.remove_button = customtkinter.CTkButton(controls_frame, text="Remove Service", command=self._remove_service); self.remove_button.pack(side="left", padx=5)
        customtkinter.CTkLabel(main_frame, text="Service Configurations:", font=customtkinter.CTkFont(weight="bold")).pack(pady=(10,0))
        self.scrollable_config_frame = customtkinter.CTkScrollableFrame(main_frame, height=300); self.scrollable_config_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.service_row_widgets = []
        save_cancel_frame = customtkinter.CTkFrame(main_frame); save_cancel_frame.pack(fill="x", pady=10, padx=5)
        save_cancel_frame.grid_columnconfigure(0, weight=1)
        self.save_button = customtkinter.CTkButton(save_cancel_frame, text="Save Changes", command=self._save_changes); self.save_button.pack(side="right", padx=10)
        self.cancel_button = customtkinter.CTkButton(save_cancel_frame, text="Cancel", command=self.destroy, fg_color="gray"); self.cancel_button.pack(side="right", padx=10)

    def _browse_base_dir(self):
        dirPath = tkinter.filedialog.askdirectory(parent=self, title="Select TERA Server Base Directory")
        if dirPath: self.base_dir_edit.delete(0, "end"); self.base_dir_edit.insert(0, dirPath)
    
    def _populate_config_list(self):
        for widget_info in self.service_row_widgets: widget_info["frame"].destroy()
        self.service_row_widgets.clear(); current_selection_index_before_repop = self.selected_service_index; self.selected_service_index = None 
        headers = ["Friendly Name", "Service Name", "Application Path"]
        header_frame_list = customtkinter.CTkFrame(self.scrollable_config_frame, fg_color="transparent")
        header_frame_list.pack(fill="x", pady=(0,5), before=self.scrollable_config_frame.winfo_children()[0] if self.scrollable_config_frame.winfo_children() else None)
        for col, header_text in enumerate(headers):
            header_frame_list.grid_columnconfigure(col, weight=1 if col == 0 else (2 if col == 1 else 3)) 
            customtkinter.CTkLabel(header_frame_list, text=header_text, font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=col, padx=5, sticky="w")
        self.service_row_widgets.append({"frame": header_frame_list, "is_header": True}) 
        for idx, service_item in enumerate(self.config_data_working_copy):
            row_frame = customtkinter.CTkFrame(self.scrollable_config_frame, height=30, fg_color="transparent"); row_frame.pack(fill="x", pady=1, padx=1)
            row_frame.grid_columnconfigure(0, weight=1); row_frame.grid_columnconfigure(1, weight=2); row_frame.grid_columnconfigure(2, weight=3) 
            fn_label = customtkinter.CTkLabel(row_frame, text=service_item.get("FriendlyName", "N/A"), anchor="w"); fn_label.grid(row=0, column=0, padx=5, sticky="ew")
            sn_label = customtkinter.CTkLabel(row_frame, text=service_item.get("ServiceName", "N/A"), anchor="w"); sn_label.grid(row=0, column=1, padx=5, sticky="ew")
            ap_label = customtkinter.CTkLabel(row_frame, text=service_item.get("AppPath", "N/A"), anchor="w"); ap_label.grid(row=0, column=2, padx=5, sticky="ew")
            self.service_row_widgets.append({"frame": row_frame, "data": service_item, "index": idx})
            for widget in [row_frame, fn_label, sn_label, ap_label]: widget.bind("<Button-1>", lambda event, index=idx: self._on_service_row_selected(index))
        if current_selection_index_before_repop is not None and current_selection_index_before_repop < len(self.config_data_working_copy): self._on_service_row_selected(current_selection_index_before_repop)
        else: self._update_edit_remove_button_states()

    def _on_service_row_selected(self, index):
        for i, widget_info in enumerate(self.service_row_widgets):
            if not widget_info.get("is_header", False) and i == self.selected_service_index +1 : widget_info["frame"].configure(fg_color="transparent")
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
        dialog = AddEditServiceWindow(master=self, existing_service_names=existing_names); self.wait_window(dialog)
        if dialog.result_data: self.config_data_working_copy.append(dialog.result_data); self._populate_config_list(); new_index = len(self.config_data_working_copy) - 1; self._on_service_row_selected(new_index) if new_index >=0 else None

    def _edit_service(self):
        if self.selected_service_index is None or self.selected_service_index >= len(self.config_data_working_copy): tkinter.messagebox.showwarning("No Selection", "Please select a service to edit.", parent=self); return
        service_to_edit = self.config_data_working_copy[self.selected_service_index]
        dialog = AddEditServiceWindow(master=self, service_data=dict(service_to_edit)); self.wait_window(dialog)
        if dialog.result_data: self.config_data_working_copy[self.selected_service_index] = dialog.result_data; self._populate_config_list(); self._on_service_row_selected(self.selected_service_index)

    def _remove_service(self):
        if self.selected_service_index is None or self.selected_service_index >= len(self.config_data_working_copy): tkinter.messagebox.showwarning("No Selection", "Please select a service to remove.", parent=self); return
        service_to_remove = self.config_data_working_copy[self.selected_service_index]
        if tkinter.messagebox.askyesno("Confirm Delete", f"Remove '{service_to_remove.get('FriendlyName')}'?", parent=self):
            del self.config_data_working_copy[self.selected_service_index]; self.selected_service_index = None; self._populate_config_list() 

    def _auto_detect_paths(self):
        base_directory = self.base_dir_edit.get().strip()
        if not base_directory or not os.path.isdir(base_directory): tkinter.messagebox.showwarning("Warning", "Valid Base Directory required.", parent=self); return
        if not SERVICE_PATH_CUES: tkinter.messagebox.showwarning("Warning", "Path cues not loaded.", parent=self); return
        found_count = 0; not_found_services = []
        service_name_to_cues = {item["ServiceName"]: item["SearchCues"] for item in SERVICE_PATH_CUES}
        for service_entry in self.config_data_working_copy:
            service_name = service_entry.get("ServiceName"); cues = service_name_to_cues.get(service_name)
            if not service_name or not cues: not_found_services.append(service_name or "Unnamed"); continue
            path_found = False
            for cue in cues:
                current_search_path = os.path.join(base_directory, cue.get("sub_dir", ""), cue["filename_pattern"])
                matches = glob.glob(current_search_path)
                if matches: service_entry["AppPath"] = os.path.normpath(matches[0]); found_count += 1; path_found = True; break
            if not path_found: not_found_services.append(service_name)
        self._populate_config_list()
        message = f"Detection complete. Found paths for {found_count} service(s).\n"
        if not_found_services: message += f"\nCould not find: {', '.join(not_found_services)}."
        tkinter.messagebox.showinfo("Auto-detect Result", message, parent=self)

    def _save_changes(self):
        if service_utils and service_utils.save_config(self.master_window.config_file_path, self.config_data_working_copy):
            tkinter.messagebox.showinfo("Success", "Configuration saved.", parent=self)
            self.master_window.config_data_changed_by_editor = True; self.destroy()
        else: tkinter.messagebox.showerror("Error", "Failed to save configuration.", parent=self)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows Process Manager (Tkinter)"); self.geometry("1000x650")
        self.process_manager_available = bool(process_manager)
        self.config_data_changed_by_editor = False 
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close

        if not self.process_manager_available:
            tkinter.messagebox.showerror("Critical Error", "process_manager.py not found or failed to import. Application cannot continue.", parent=self if self._window_exists else None)
            if self._window_exists: self.destroy()
            else: sys.exit(1)
            return

        self._init_ui()
        if process_manager.load_configuration():
            self.status_bar.configure(text="Configuration loaded.")
        else:
            self.status_bar.configure(text=f"ERROR: Failed to load configuration from {process_manager.CONFIG_FILE_PATH}. Check console.")
            tkinter.messagebox.showwarning("Config Error", f"Failed to load {process_manager.CONFIG_FILE_PATH}. Please check the file or create one using 'Edit Configurations'.", parent=self)
        
        self.load_and_display_statuses() # Initial display
        
        process_manager.start_monitoring()
        self.monitor_thread = threading.Thread(target=self._run_process_monitor, daemon=True)
        self.monitor_thread.start()
        
        self.gui_refresh_timer_ms = 1000 # Refresh GUI every second
        self.after(self.gui_refresh_timer_ms, self.refresh_gui_statuses) 
        
        self.after(500, self._schedule_initial_delayed_starts) 

    def _init_ui(self):
        self.main_frame = customtkinter.CTkFrame(self); self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        top_controls_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent"); top_controls_frame.pack(fill="x", pady=(0,5))
        self.edit_config_button = customtkinter.CTkButton(top_controls_frame, text="Edit Configurations", command=self._open_config_editor); self.edit_config_button.pack(anchor="ne") 
        header_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent"); header_frame.pack(fill="x", padx=10, pady=(0,5))
        self.headers = ["Friendly Name", "Service Name", "Status", "PID", "Actions"]; self.column_weights = [3, 2, 1, 1, 2] 
        for i, header_text in enumerate(self.headers):
            header_frame.grid_columnconfigure(i, weight=self.column_weights[i])
            customtkinter.CTkLabel(header_frame, text=header_text, font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=i, padx=5, pady=2, sticky="ew")
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.main_frame); self.scrollable_frame.pack(pady=5, padx=10, fill="both", expand=True)
        self.service_row_frames = [] 
        bottom_controls_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent"); bottom_controls_frame.pack(fill="x", pady=10, padx=10)
        self.start_all_button = customtkinter.CTkButton(bottom_controls_frame, text="Start All Services", command=self._start_all_services); self.start_all_button.pack(side="left", padx=5)
        self.stop_all_button = customtkinter.CTkButton(bottom_controls_frame, text="Stop All Services", command=self._stop_all_services); self.stop_all_button.pack(side="left", padx=5)
        spacer = customtkinter.CTkFrame(bottom_controls_frame, fg_color="transparent"); spacer.pack(side="left", expand=True)
        self.refresh_button = customtkinter.CTkButton(bottom_controls_frame, text="Refresh Status", command=self.load_and_display_statuses); self.refresh_button.pack(side="right", padx=5)
        self.status_bar = customtkinter.CTkLabel(self, text="Welcome!", anchor="w"); self.status_bar.pack(side="bottom", fill="x", padx=10, pady=5)

        if not self.process_manager_available: # Should be caught in __init__ but as safeguard
            self.refresh_button.configure(state="disabled"); self.edit_config_button.configure(state="disabled")
            self.start_all_button.configure(state="disabled"); self.stop_all_button.configure(state="disabled")

    def on_closing(self):
        print("Closing application...")
        if self.process_manager_available:
            process_manager.stop_monitoring()
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            print("Waiting for monitor thread to join...")
            self.monitor_thread.join(timeout=process_manager.MONITOR_INTERVAL_SECONDS + 1) # Wait a bit longer than interval
            if self.monitor_thread.is_alive():
                print("Monitor thread did not join in time.")
        self.destroy()

    def _run_process_monitor(self):
        if not self.process_manager_available: return
        print("Process monitor thread started.")
        while process_manager.monitoring_active:
            process_manager.monitor_and_restart_processes()
            # GUI updates are handled by the main thread's timer (refresh_gui_statuses)
            # to avoid direct GUI calls from this thread.
            # The monitor_and_restart_processes updates the shared managed_processes dict.
            time.sleep(process_manager.MONITOR_INTERVAL_SECONDS)
        print("Process monitor thread finished.")

    def refresh_gui_statuses(self):
        """Refreshes the GUI from process_manager.managed_processes. Called by main thread timer."""
        if self.process_manager_available:
            self.load_and_display_statuses() # This reads from process_manager.managed_processes
        self.after(self.gui_refresh_timer_ms, self.refresh_gui_statuses)


    def _open_config_editor(self):
        if not self.process_manager_available: tkinter.messagebox.showerror("Error", "Process manager not available.", parent=self); return
        self.config_data_changed_by_editor = False 
        config_editor_window = ConfigEditWindow(self); self.wait_window(config_editor_window) 
        if self.config_data_changed_by_editor: 
            self.status_bar.configure(text="Configuration updated. Reloading and refreshing...")
            if process_manager.load_configuration(): # Reload config in process_manager
                 self.load_and_display_statuses() # Update GUI from new state
                 self.after(500, self._schedule_initial_delayed_starts) 
            else:
                self.status_bar.configure(text="Error reloading configuration after edit.")
                tkinter.messagebox.showerror("Error", "Failed to reload configuration after edit.", parent=self)
        else: self.status_bar.configure(text="Configuration edit cancelled or no changes made.")

    def create_service_row(self, parent_frame, service_config, status_tuple):
        row_frame = customtkinter.CTkFrame(parent_frame, fg_color=("gray90", "gray20"), height=30); row_frame.pack(fill="x", pady=1, padx=1) 
        for i, weight in enumerate(self.column_weights): row_frame.grid_columnconfigure(i, weight=weight)
        friendly_name = service_config.get("FriendlyName", "N/A"); service_name = service_config.get("ServiceName", "N/A") 
        status, pid = status_tuple
        details = [friendly_name, service_name, status, str(pid if pid is not None else "N/A")]
        for i, detail_text in enumerate(details):
            detail_label = customtkinter.CTkLabel(row_frame, text=detail_text, anchor="w"); detail_label.grid(row=0, column=i, padx=5, pady=2, sticky="ew")
            if i == 2: 
                color = "white" 
                if status == "running": color = "lightgreen"
                elif status == "stopped": color = "salmon"
                elif status == "Not Found": color = "gray"
                elif "pending" in status.lower() or "stopping" in status.lower() or "starting" in status.lower(): color = "orange"
                elif status.startswith("error"): color = "orangered"
                elif status == "ConfigError": color = "yellow"
                detail_label.configure(text_color=color)
        actions_frame = customtkinter.CTkFrame(row_frame, fg_color="transparent"); actions_frame.grid(row=0, column=4, sticky="ew", padx=5)
        start_button = customtkinter.CTkButton(actions_frame, text="Start", width=60); start_button.pack(side="left", padx=2)
        stop_button = customtkinter.CTkButton(actions_frame, text="Stop", width=60); stop_button.pack(side="left", padx=2)
        if service_name != "N/A" and not status.startswith("error") and status != "ConfigError":
            start_button.configure(command=lambda s=service_name: self._start_single_service(s))
            stop_button.configure(command=lambda s=service_name: self._stop_single_service(s))
        else: start_button.configure(state="disabled"); stop_button.configure(state="disabled")
        status_lower = status.lower()
        if status.startswith("error") or status == "ConfigError": start_button.configure(state="disabled"); stop_button.configure(state="disabled")
        elif status_lower == "running": start_button.configure(state="disabled"); stop_button.configure(state="normal")
        elif status_lower == "stopped": start_button.configure(state="normal"); stop_button.configure(state="disabled")
        else: start_button.configure(state="disabled"); stop_button.configure(state="disabled")
        if status_lower == "not found": start_button.configure(state="normal") # Allow start attempt if "Not Found"
        return row_frame

    def _start_single_service(self, service_name: str):
        if not self.process_manager_available: return
        self.status_bar.configure(text=f"Attempting to start {service_name}...")
        success = process_manager.launch_process(service_name)
        if success: self.status_bar.configure(text=f"Start command issued for {service_name}.")
        else: self.status_bar.configure(text=f"Failed to issue start command for {service_name}."); tkinter.messagebox.showerror("Error", f"Could not start: {service_name}", parent=self)
        self.load_and_display_statuses()

    def _stop_single_service(self, service_name: str):
        if not self.process_manager_available: return
        self.status_bar.configure(text=f"Attempting to stop {service_name}...")
        success = process_manager.terminate_process(service_name) # Default mark_user_stopped=True
        if success: self.status_bar.configure(text=f"Stop command issued for {service_name}.")
        else: self.status_bar.configure(text=f"Failed to issue stop command for {service_name}."); tkinter.messagebox.showerror("Error", f"Could not stop: {service_name}", parent=self)
        self.load_and_display_statuses()

    def _start_all_services(self):
        if not self.process_manager_available: tkinter.messagebox.showerror("Error", "Process manager not available.", parent=self); return
        self.status_bar.configure(text="Attempting to start all services...")
        if not process_manager.managed_processes: tkinter.messagebox.showinfo("Information", "No services configured.", parent=self); self.status_bar.configure(text="No services configured."); return
        started, already_running, failed = 0,0,[]
        for service_name, proc_info in list(process_manager.managed_processes.items()): # Iterate copy
            status = proc_info["status"] # Use current known status
            if status == "stopped" or status == "Not Found" or status.startswith("error_"): # Try to start if error or stopped
                proc_info["user_stopped"] = False # Clear user_stopped flag if we are trying to start it
                if process_manager.launch_process(service_name): started += 1
                else: failed.append(service_name)
            elif status == "running": already_running +=1
        self.load_and_display_statuses()
        msg = f"Start All: {started} started, {already_running} already running."; self.status_bar.configure(text=msg)
        if failed: msg += f"\nFailed: {', '.join(failed)}."
        tkinter.messagebox.showinfo("Start All Services", msg, parent=self)

    def _stop_all_services(self):
        if not self.process_manager_available: tkinter.messagebox.showerror("Error", "Process manager not available.", parent=self); return
        self.status_bar.configure(text="Attempting to stop all services...")
        if not process_manager.managed_processes: tkinter.messagebox.showinfo("Information", "No services configured.", parent=self); self.status_bar.configure(text="No services configured."); return
        stopped, already_stopped, failed = 0,0,[]
        for service_name, proc_info in list(process_manager.managed_processes.items()): # Iterate copy
            status = proc_info["status"]
            if status == "running" or status == "paused": # Only stop if it's in a stoppable state
                if process_manager.terminate_process(service_name): stopped += 1 # Default mark_user_stopped=True
                else: failed.append(service_name)
            elif status == "stopped" or status.startswith("error_"): already_stopped +=1
        self.load_and_display_statuses()
        msg = f"Stop All: {stopped} stopped, {already_stopped} already stopped."; self.status_bar.configure(text=msg)
        if failed: msg += f"\nFailed: {', '.join(failed)}."
        tkinter.messagebox.showinfo("Stop All Services", msg, parent=self)

    def load_and_display_statuses(self):
        if not self.process_manager_available: self.status_bar.configure(text="ERROR: Process manager not available."); return
        # self.status_bar.configure(text="Refreshing display...") # Can be too quick / noisy

        for frame in self.service_row_frames: frame.destroy()
        self.service_row_frames.clear()

        active_procs = process_manager.managed_processes
        if not active_procs:
            # Check if config file itself is missing vs empty
            if not os.path.exists(process_manager.CONFIG_FILE_PATH):
                msg = f"ERROR: Configuration file '{process_manager.CONFIG_FILE_PATH}' not found."
            else:
                msg = "No services loaded. Check configuration or console output."
            self.status_bar.configure(text=msg)
            no_service_label = customtkinter.CTkLabel(self.scrollable_frame, text=msg); no_service_label.pack(pady=20)
            self.service_row_frames.append(no_service_label)
            return

        # self.status_bar.configure(text="Updating service rows...") # Still can be noisy
        for service_name, proc_info in active_procs.items():
            config_entry = proc_info["config"] 
            # Ensure get_process_info is called to update status before display, especially for monitor thread changes
            updated_proc_info = process_manager.get_process_info(service_name) # This updates internal state
            status_tuple = (updated_proc_info["status"], updated_proc_info["pid"]) 
            row = self.create_service_row(self.scrollable_frame, config_entry, status_tuple)
            self.service_row_frames.append(row)
        
        # self.status_bar.configure(text="Status display updated.") # A bit redundant if other messages follow quickly

    def _schedule_initial_delayed_starts(self):
        if not self.process_manager_available: return
        self.status_bar.configure(text="Scheduling initial delayed service starts...")
        # Config is already loaded into process_manager.managed_processes
        if not process_manager.managed_processes: self.status_bar.configure(text="No configuration for delayed starts."); return
        
        services_scheduled = 0
        for service_name, proc_info in process_manager.managed_processes.items():
            delay_seconds = proc_info["config"].get("StartupDelaySeconds", 0)
            if delay_seconds > 0:
                # Use current status from process_manager, ensure it's up-to-date
                current_proc_info = process_manager.get_process_info(service_name)
                if current_proc_info["status"] == "stopped" and not current_proc_info.get("user_stopped", False) :
                    self.after(delay_seconds * 1000, lambda s=service_name: self._attempt_delayed_start(s))
                    self.status_bar.configure(text=f"'{s}' scheduled for delayed start in {delay_seconds}s.")
                    services_scheduled +=1
        if services_scheduled == 0:
            self.status_bar.configure(text="No services require delayed start or already running.")


    def _attempt_delayed_start(self, service_name: str):
        if not self.process_manager_available: return
        self.status_bar.configure(text=f"Attempting delayed start for {service_name}...")
        
        proc_info = process_manager.get_process_info(service_name) # Get latest status
        if not proc_info or proc_info["status"] != "stopped" or proc_info.get("user_stopped", False):
            self.status_bar.configure(text=f"Delayed start for '{service_name}' skipped (Status: {proc_info['status'] if proc_info else 'N/A'}, UserStopped: {proc_info.get('user_stopped', False) if proc_info else 'N/A'}).")
            # self.load_and_display_statuses() # Refresh might be good if status changed
            return

        success = process_manager.launch_process(service_name)
        if success: self.status_bar.configure(text=f"Delayed start command issued for '{service_name}'.")
        else: self.status_bar.configure(text=f"Failed to issue delayed start command for '{service_name}'.")
        self.load_and_display_statuses()


if __name__ == "__main__":
    # This check for service_utils helps if process_manager itself can't be imported due to it
    if not service_utils:
         root = tkinter.Tk()
         root.withdraw() # Hide the main tkinter window
         tkinter.messagebox.showerror("Startup Critical Error", "service_utils.py is missing or cannot be imported. The application cannot start.")
         sys.exit(1)

    app = App()
    if app.process_manager_available: # Only run if app initialized correctly
        app.mainloop()
    else:
        # App __init__ already shows a messagebox, this is an additional safeguard
        print("Exiting due to process_manager not being available (likely service_utils missing).")
        sys.exit(1)
```
