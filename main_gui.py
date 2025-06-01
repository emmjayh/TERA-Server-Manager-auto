# main_gui.py
# Description: Main GUI application for Windows Service Manager.
# Dependencies: PyQt6, psutil (via service_utils)

import sys
import os
import glob # For path detection
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QHeaderView, QMenuBar, QMenu,
    QStatusBar, QMessageBox, QHBoxLayout, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox, QAbstractItemView, QFileDialog,
    QLabel, QSpinBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QAction # QAction for menu

# Attempt to import service_utils.
# This assumes service_utils.py is in the same directory or Python path.
try:
    import service_utils
except ImportError:
    print("Error: service_utils.py not found. Please ensure it's in the same directory or PYTHONPATH.")
    sys.exit(1) # Exit if crucial utilities are missing

# Attempt to import SERVICE_PATH_CUES
try:
    from service_path_cues import SERVICE_PATH_CUES
except ImportError:
    print("Error: service_path_cues.py not found. Please ensure it's in the same directory or PYTHONPATH.")
    # Optionally, provide a default empty list or handle this more gracefully
    SERVICE_PATH_CUES = []
    # sys.exit(1) # Or exit if this is critical

# --- Configuration ---
CONFIG_FILE_PATH = "server_config.json" # Relative to where main_gui.py is run
REFRESH_INTERVAL_MS = 10000  # 10 seconds


class AddEditServiceDialog(QDialog):
    def __init__(self, service_data=None, parent=None):
        super().__init__(parent)
        self.service_data_in = service_data
        self.service_data_out = None
        self.is_editing_mode = bool(service_data)

        if self.is_editing_mode:
            self.setWindowTitle("Edit Service Configuration")
        else:
            self.setWindowTitle("Add Service Configuration")

        self.setMinimumWidth(450)
        self._init_ui()

        if self.is_editing_mode:
            self._populate_fields()
            self.service_name_edit.setReadOnly(True)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.friendly_name_edit = QLineEdit()
        self.service_name_edit = QLineEdit()

        self.app_path_edit = QLineEdit()
        self.app_path_browse_button = QPushButton("Browse...")
        self.app_path_browse_button.clicked.connect(self._browse_app_path)
        app_path_layout = QHBoxLayout()
        app_path_layout.addWidget(self.app_path_edit)
        app_path_layout.addWidget(self.app_path_browse_button)

        self.app_args_edit = QLineEdit()

        self.log_dir_edit = QLineEdit()
        self.log_dir_browse_button = QPushButton("Browse...")
        self.log_dir_browse_button.clicked.connect(self._browse_log_dir)
        log_dir_layout = QHBoxLayout()
        log_dir_layout.addWidget(self.log_dir_edit)
        log_dir_layout.addWidget(self.log_dir_browse_button)

        self.startup_delay_label = QLabel("Startup Delay (seconds):")
        self.startup_delay_spinbox = QSpinBox()
        self.startup_delay_spinbox.setMinimum(0)
        self.startup_delay_spinbox.setMaximum(3600)
        self.startup_delay_spinbox.setValue(0)

        form_layout.addRow("Friendly Name:", self.friendly_name_edit)
        form_layout.addRow("Service Name:", self.service_name_edit)
        form_layout.addRow("Application Path:", app_path_layout)
        form_layout.addRow("Application Arguments:", self.app_args_edit)
        form_layout.addRow("Log Directory:", log_dir_layout)
        form_layout.addRow(self.startup_delay_label, self.startup_delay_spinbox)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def _browse_app_path(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select Application", "", "Executables (*.exe *.bat);;All Files (*)")
        if filePath:
            self.app_path_edit.setText(filePath)

    def _browse_log_dir(self):
        dirPath = QFileDialog.getExistingDirectory(self, "Select Log Directory")
        if dirPath:
            self.log_dir_edit.setText(dirPath)

    def _populate_fields(self):
        if self.service_data_in:
            self.friendly_name_edit.setText(self.service_data_in.get("FriendlyName", ""))
            self.service_name_edit.setText(self.service_data_in.get("ServiceName", ""))
            self.app_path_edit.setText(self.service_data_in.get("AppPath", ""))
            self.app_args_edit.setText(self.service_data_in.get("AppArguments", ""))
            self.log_dir_edit.setText(self.service_data_in.get("LogDirectory", ""))
            delay = self.service_data_in.get("StartupDelaySeconds", 0)
            self.startup_delay_spinbox.setValue(delay)


    def _get_validated_data(self) -> dict | None:
        friendly_name = self.friendly_name_edit.text().strip()
        service_name = self.service_name_edit.text().strip()
        app_path = self.app_path_edit.text().strip()
        log_dir = self.log_dir_edit.text().strip()

        if not friendly_name:
            QMessageBox.warning(self, "Input Error", "Friendly Name cannot be empty.")
            return None
        if not service_name:
            QMessageBox.warning(self, "Input Error", "Service Name cannot be empty.")
            return None
        if " " in service_name or any(c in service_name for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            QMessageBox.warning(self, "Input Error", "Service Name cannot contain spaces or special characters like /\\:*?\"<>|.")
            return None
        if not app_path:
            QMessageBox.warning(self, "Input Error", "Application Path cannot be empty.")
            return None
        if not log_dir:
            QMessageBox.warning(self, "Input Error", "Log Directory cannot be empty.")
            return None

        data = {
            "FriendlyName": friendly_name,
            "ServiceName": service_name,
            "AppPath": app_path,
            "AppArguments": self.app_args_edit.text().strip(),
            "LogDirectory": log_dir
        }
        delay_value = self.startup_delay_spinbox.value()
        if delay_value > 0:
            data["StartupDelaySeconds"] = delay_value
        return data

    def accept(self):
        validated_data = self._get_validated_data()
        if validated_data:
            self.service_data_out = validated_data
            super().accept()
        else:
            self.service_data_out = None

class ConfigEditDialog(QDialog):
    def __init__(self, current_config_data, parent=None):
        super().__init__(parent)
        self.config_data = [dict(item) for item in current_config_data]

        self.setWindowTitle("Edit Service Configurations")
        self.setGeometry(150, 150, 750, 550) # Slightly wider for base dir

        self._init_ui()
        self._populate_config_table()
        self._update_button_states()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Base Directory Layout
        base_dir_layout = QHBoxLayout()
        self.base_dir_label = QLabel("TERA Server Base Directory:")
        self.base_dir_edit = QLineEdit()
        self.base_dir_browse_button = QPushButton("Browse...")
        self.base_dir_browse_button.clicked.connect(self._browse_base_dir)

        base_dir_layout.addWidget(self.base_dir_label)
        base_dir_layout.addWidget(self.base_dir_edit)
        base_dir_layout.addWidget(self.base_dir_browse_button)
        main_layout.addLayout(base_dir_layout)

        # Table for Configurations
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(3)
        self.config_table.setHorizontalHeaderLabels(["Friendly Name", "Service Name", "Application Path"])
        self.config_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.config_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.config_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.config_table.itemSelectionChanged.connect(self._update_button_states)

        header = self.config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        main_layout.addWidget(self.config_table)

        # Buttons Layout (Add, Edit, Remove, Auto-detect)
        crud_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add...")
        self.add_button.clicked.connect(self._add_service)
        self.edit_button = QPushButton("Edit...")
        self.edit_button.clicked.connect(self._edit_service)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_service)

        crud_buttons_layout.addWidget(self.add_button)
        crud_buttons_layout.addWidget(self.edit_button)
        crud_buttons_layout.addWidget(self.remove_button)
        crud_buttons_layout.addStretch()

        self.auto_detect_button = QPushButton("Auto-detect App Paths")
        self.auto_detect_button.clicked.connect(self._auto_detect_paths)
        crud_buttons_layout.addWidget(self.auto_detect_button) # Added here

        main_layout.addLayout(crud_buttons_layout)

        # Main Action Buttons Layout (Save, Cancel)
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._save_config_and_accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        action_buttons_layout.addWidget(self.save_button)
        action_buttons_layout.addWidget(self.cancel_button)
        main_layout.addLayout(action_buttons_layout)

    def _browse_base_dir(self):
        dirPath = QFileDialog.getExistingDirectory(self, "Select TERA Server Base Directory")
        if dirPath:
            self.base_dir_edit.setText(dirPath)

    def _auto_detect_paths(self):
        base_directory = self.base_dir_edit.text().strip()
        if not base_directory or not os.path.isdir(base_directory):
            QMessageBox.warning(self, "Warning", "Please select a valid TERA Server Base Directory first.")
            return

        if not SERVICE_PATH_CUES:
            QMessageBox.warning(self, "Warning", "Service path cues are not loaded. Cannot auto-detect.")
            return

        found_count = 0
        not_found_services = []
        # Create a quick lookup map from ServiceName to its cues
        service_name_to_cues = {item["ServiceName"]: item["SearchCues"] for item in SERVICE_PATH_CUES}

        for service_entry in self.config_data:
            service_name = service_entry.get("ServiceName")
            if not service_name:
                continue # Skip if service entry has no name

            cues = service_name_to_cues.get(service_name)
            if not cues:
                not_found_services.append(service_name)
                continue

            path_found_for_this_service = False
            for cue in cues:
                sub_dir = cue.get("sub_dir", "")
                filename_pattern = cue["filename_pattern"]

                # Construct search path
                # Patterns are expected to be specific, e.g., "HubServer.bat" or "*. HubServer.bat"
                # No further {ServiceName} placeholder replacement needed here based on prior design
                current_search_path = os.path.join(base_directory, sub_dir, filename_pattern)

                # Use glob to find matches
                matches = glob.glob(current_search_path)
                if matches:
                    # Take the first match, normalize path
                    service_entry["AppPath"] = os.path.normpath(matches[0])
                    found_count += 1
                    path_found_for_this_service = True
                    break # Move to the next service in self.config_data

            if not path_found_for_this_service:
                not_found_services.append(service_name)

        self._populate_config_table() # Refresh the table to show updated paths

        message = f"Path detection complete.\n\nFound paths for {found_count} service(s).\n"
        if not_found_services:
            message += f"\nCould not automatically find paths for: {', '.join(not_found_services)}.\nPlease set them manually or verify cues."
        else:
            if found_count > 0: # Only say all found if some were actually processed
                 message += "\nAll configured services with defined cues appear to have paths found."
            elif not self.config_data:
                 message += "\nNo services configured to detect paths for."
            else: # Config data exists, but maybe no cues for any of them
                 message += "\nNo paths were found, possibly due to missing cues or incorrect base directory."


        QMessageBox.information(self, "Auto-detect Paths Result", message)


    def _populate_config_table(self):
        self.config_table.clearContents()
        self.config_table.setRowCount(len(self.config_data))
        for row_idx, item_data in enumerate(self.config_data):
            self.config_table.setItem(row_idx, 0, QTableWidgetItem(item_data.get("FriendlyName", "")))
            self.config_table.setItem(row_idx, 1, QTableWidgetItem(item_data.get("ServiceName", "")))
            self.config_table.setItem(row_idx, 2, QTableWidgetItem(item_data.get("AppPath", "")))
        self._update_button_states()

    def _update_button_states(self):
        is_row_selected = bool(self.config_table.selectedItems())
        self.edit_button.setEnabled(is_row_selected)
        self.remove_button.setEnabled(is_row_selected)

    def _add_service(self):
        dialog = AddEditServiceDialog(parent=self)
        if dialog.exec():
            new_service_data = dialog.service_data_out
            if new_service_data:
                existing_service_names = [s.get("ServiceName", "").lower() for s in self.config_data]
                if new_service_data["ServiceName"].lower() in existing_service_names:
                    QMessageBox.warning(self, "Duplicate Service",
                                        f"A service with the name '{new_service_data['ServiceName']}' already exists.")
                    return

                self.config_data.append(new_service_data)
                self._populate_config_table()

    def _edit_service(self):
        selected_rows = self.config_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        selected_row_index = selected_rows[0].row()
        service_to_edit = self.config_data[selected_row_index]

        dialog = AddEditServiceDialog(service_data=dict(service_to_edit), parent=self)
        if dialog.exec():
            updated_service_data = dialog.service_data_out
            if updated_service_data:
                self.config_data[selected_row_index] = updated_service_data
                self._populate_config_table()

    def _remove_service(self):
        selected_rows = self.config_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        selected_row_index = selected_rows[0].row()
        service_name_to_remove = self.config_data[selected_row_index].get("ServiceName", "Unknown Service")

        reply = QMessageBox.question(self, "Confirm Remove",
                                     f"Are you sure you want to remove service '{service_name_to_remove}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.config_data[selected_row_index]
            self._populate_config_table()

    def _save_config_and_accept(self):
        if service_utils.save_config(CONFIG_FILE_PATH, self.config_data):
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save configuration to '{CONFIG_FILE_PATH}'.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Windows Service Manager")
        self.setGeometry(100, 100, 800, 600)

        self._init_ui()
        self._load_and_display_statuses()

        self.timer = QTimer()
        self.timer.timeout.connect(self._load_and_display_statuses)
        self.timer.start(REFRESH_INTERVAL_MS)

        self._schedule_initial_delayed_starts()


    def _init_ui(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        config_menu = menu_bar.addMenu("&Configuration")
        edit_config_action = QAction("&Edit Configurations...", self)
        edit_config_action.triggered.connect(self._open_config_editor)
        config_menu.addAction(edit_config_action)

        actions_menu = menu_bar.addMenu("&Actions")
        start_all_action = QAction("&Start All Services", self)
        start_all_action.triggered.connect(self._start_all_services)
        actions_menu.addAction(start_all_action)

        stop_all_action = QAction("&Stop All Services", self)
        stop_all_action.triggered.connect(self._stop_all_services)
        actions_menu.addAction(stop_all_action)


        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Friendly Name", "Service Name", "Status", "PID"])

        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        main_layout.addWidget(self.table_widget)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Service")
        self.start_button.clicked.connect(self._start_selected_service)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Service")
        self.stop_button.clicked.connect(self._stop_selected_service)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        button_layout.addStretch()
        self.refresh_button = QPushButton("Refresh Status")
        self.refresh_button.clicked.connect(self._load_and_display_statuses)
        button_layout.addWidget(self.refresh_button)

        main_layout.addLayout(button_layout)

    def _open_config_editor(self):
        self.statusBar.showMessage("Loading configuration for editing...")
        current_config = service_utils.load_config(CONFIG_FILE_PATH)
        if current_config is None:
            current_config = []
            QMessageBox.warning(self, "Configuration Error", f"Could not load configuration from {CONFIG_FILE_PATH}. Starting with an empty editor.")

        dialog = ConfigEditDialog(current_config, self)

        if dialog.exec():
            self.statusBar.showMessage("Configuration updated. Refreshing main display...", 3000)
            self._load_and_display_statuses()
            self._schedule_initial_delayed_starts()
        else:
            self.statusBar.showMessage("Configuration editing cancelled.", 3000)

    def _start_all_services(self):
        self.statusBar.showMessage("Attempting to start all services...")
        config = service_utils.load_config(CONFIG_FILE_PATH)
        if not config:
            QMessageBox.information(self, "Information", "No services configured.")
            self.statusBar.showMessage("No services configured.", 3000)
            return

        services_attempted = 0
        for entry in config:
            service_name = entry.get("ServiceName")
            if service_name:
                status, _ = service_utils.get_service_status(service_name)
                if status.lower() in ['stopped', 'not found']:
                    service_utils.start_service_app(service_name)
                    services_attempted +=1

        self._load_and_display_statuses()
        QMessageBox.information(self, "Action Complete", f"Attempted to start {services_attempted} applicable services. Please check status.")
        self.statusBar.showMessage(f"Attempted to start {services_attempted} services.", 3000)


    def _stop_all_services(self):
        self.statusBar.showMessage("Attempting to stop all services...")
        config = service_utils.load_config(CONFIG_FILE_PATH)
        if not config:
            QMessageBox.information(self, "Information", "No services configured.")
            self.statusBar.showMessage("No services configured.", 3000)
            return

        services_attempted = 0
        for entry in config:
            service_name = entry.get("ServiceName")
            if service_name:
                status, _ = service_utils.get_service_status(service_name)
                if status.lower() in ['running', 'paused']:
                    service_utils.stop_service_app(service_name)
                    services_attempted +=1

        self._load_and_display_statuses()
        QMessageBox.information(self, "Action Complete", f"Attempted to stop {services_attempted} applicable services. Please check status.")
        self.statusBar.showMessage(f"Attempted to stop {services_attempted} services.", 3000)


    def _get_selected_service_info(self) -> tuple[str | None, str | None]:
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return None, None

        current_row = self.table_widget.currentRow()
        if current_row < 0:
            return None, None

        service_name_item = self.table_widget.item(current_row, 1)
        status_item = self.table_widget.item(current_row, 2)

        if service_name_item and status_item:
            return service_name_item.text(), status_item.text()
        return None, None

    def _update_button_states(self):
        service_name, status = self._get_selected_service_info()

        if service_name and status:
            status_lower = status.lower()
            can_start = status_lower in ['stopped', 'not found']
            can_stop = status_lower in ['running', 'paused']
            self.start_button.setEnabled(can_start)
            self.stop_button.setEnabled(can_stop)
        else:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    def _start_selected_service(self):
        service_name, status = self._get_selected_service_info()
        if service_name:
            self.statusBar.showMessage(f"Attempting to start '{service_name}'...")
            success = service_utils.start_service_app(service_name)
            if success:
                QMessageBox.information(self, "Start Service", f"Successfully sent start command for '{service_name}'.")
                self.statusBar.showMessage(f"Start command sent for '{service_name}'. Refreshing...", 3000)
            else:
                QMessageBox.warning(self, "Start Service", f"Failed to start service '{service_name}'. Check logs or service status.")
                self.statusBar.showMessage(f"Failed to start '{service_name}'.", 5000)
            self._load_and_display_statuses()

    def _stop_selected_service(self):
        service_name, status = self._get_selected_service_info()
        if service_name:
            self.statusBar.showMessage(f"Attempting to stop '{service_name}'...")
            success = service_utils.stop_service_app(service_name)
            if success:
                QMessageBox.information(self, "Stop Service", f"Successfully sent stop command for '{service_name}'.")
                self.statusBar.showMessage(f"Stop command sent for '{service_name}'. Refreshing...", 3000)
            else:
                QMessageBox.warning(self, "Stop Service", f"Failed to stop service '{service_name}'. Check logs or service status.")
                self.statusBar.showMessage(f"Failed to stop '{service_name}'.", 5000)
            self._load_and_display_statuses()

    def _load_and_display_statuses(self):
        self.statusBar.showMessage("Loading configuration and statuses...")

        selected_service_name = None
        if self.table_widget.selectedItems():
            current_row = self.table_widget.currentRow()
            if current_row >= 0:
                item = self.table_widget.item(current_row, 1)
                if item:
                    selected_service_name = item.text()

        self.table_widget.clearSelection()

        config = service_utils.load_config(CONFIG_FILE_PATH)

        if not config:
            self.table_widget.setRowCount(0)
            if not os.path.exists(CONFIG_FILE_PATH):
                self.statusBar.showMessage(f"Error: Configuration file '{CONFIG_FILE_PATH}' not found.", 5000)
                self.table_widget.setRowCount(1)
                item = QTableWidgetItem(f"Configuration file '{CONFIG_FILE_PATH}' not found.")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(0,0, item)
                self.table_widget.setSpan(0,0,1,4)
            else:
                self.statusBar.showMessage("Configuration loaded, but no services defined or error during load.", 5000)
            self._update_button_states()
            return

        self.table_widget.setRowCount(len(config))
        row_to_reselect = -1

        for row_index, entry in enumerate(config):
            service_name = entry.get("ServiceName")
            friendly_name = entry.get("FriendlyName", service_name if service_name else "N/A")

            if not service_name:
                self._set_table_row(row_index, friendly_name, "N/A - Config Error", "Invalid Config", "N/A")
                status_item = self.table_widget.item(row_index, 2)
                if status_item: status_item.setForeground(QColor("orange"))
                continue

            status, pid = service_utils.get_service_status(service_name)
            pid_str = str(pid) if pid is not None else "N/A"

            self._set_table_row(row_index, friendly_name, service_name, status, pid_str)

            if service_name == selected_service_name:
                row_to_reselect = row_index

            status_item = self.table_widget.item(row_index, 2)
            if status_item:
                if status == "running":
                    status_item.setForeground(QColor("green"))
                elif status == "stopped":
                    status_item.setForeground(QColor("red"))
                elif status == "Not Found":
                    status_item.setForeground(QColor(Qt.GlobalColor.darkGray))
                elif status == "paused":
                    status_item.setForeground(QColor("blue"))
                elif status in ["start_pending", "stop_pending", "continue_pending", "pause_pending"]:
                     status_item.setForeground(QColor(Qt.GlobalColor.magenta))
                else:
                    status_item.setForeground(QColor("orange"))

        if row_to_reselect != -1:
            self.table_widget.selectRow(row_to_reselect)

        self._update_button_states()
        self.statusBar.showMessage(f"Statuses updated. {len(config)} services loaded.", 3000)

    def _set_table_row(self, row_index, friendly_name, service_name, status, pid_str):
        fn_item = QTableWidgetItem(friendly_name)
        sn_item = QTableWidgetItem(service_name)
        status_item = QTableWidgetItem(status)
        pid_item = QTableWidgetItem(pid_str)

        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table_widget.setItem(row_index, 0, fn_item)
        self.table_widget.setItem(row_index, 1, sn_item)
        self.table_widget.setItem(row_index, 2, status_item)
        self.table_widget.setItem(row_index, 3, pid_item)

    def _schedule_initial_delayed_starts(self):
        self.statusBar.showMessage("Scheduling initial delayed service starts...", 2000)
        config_data = service_utils.load_config(CONFIG_FILE_PATH)

        if not config_data:
            self.statusBar.showMessage("No configuration for delayed starts.", 3000)
            return

        for entry in config_data:
            service_name = entry.get("ServiceName")
            delay_seconds = entry.get("StartupDelaySeconds", 0)

            if service_name and delay_seconds > 0:
                current_status, _ = service_utils.get_service_status(service_name)
                if current_status == "stopped":
                    QTimer.singleShot(delay_seconds * 1000, lambda s=service_name: self._attempt_delayed_start(s))
                    self.statusBar.showMessage(f"'{service_name}' scheduled for delayed start in {delay_seconds}s.", 5000)

    def _attempt_delayed_start(self, service_name: str):
        self.statusBar.showMessage(f"Attempting delayed start for '{service_name}'...", 3000)

        current_status, _ = service_utils.get_service_status(service_name)
        if current_status != "stopped":
            self.statusBar.showMessage(f"Delayed start for '{service_name}' skipped: Service no longer stopped (status: {current_status}).", 5000)
            self._load_and_display_statuses()
            return

        success = service_utils.start_service_app(service_name)
        if success:
            self.statusBar.showMessage(f"Delayed start command issued for '{service_name}'.", 5000)
        else:
            self.statusBar.showMessage(f"Failed to issue delayed start command for '{service_name}'.", 5000)

        self._load_and_display_statuses()


if __name__ == "__main__":
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"Warning: '{CONFIG_FILE_PATH}' not found in the current directory ({os.getcwd()}).")
        print("The application might not display any services.")
        print("Please ensure the configuration file is present or run this script from the project's root directory.")

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
