import os
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction, QVBoxLayout, QWidget, QListWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QSplitter, QCheckBox
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtCore import Qt
from plot_canvas import PlotCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Plotter")
        self.setGeometry(100, 100, 1200, 800)
        self.canvas = PlotCanvas(self)
        self.init_ui()
        self.csv_dir = ''
        self.csv_files = []
        print("MainWindow initialized")

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Adding Matplotlib toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.select_folder)
        left_layout.addWidget(self.folder_button)

        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.load_selected_csv)
        left_layout.addWidget(self.file_list)

        self.label_save_button = QPushButton("Save Labels")
        self.label_save_button.clicked.connect(self.save_labels)
        left_layout.addWidget(self.label_save_button)

        self.label_load_button = QPushButton("Load Labels")
        self.label_load_button.clicked.connect(self.load_labels)
        left_layout.addWidget(self.label_load_button)

        self.interval_edit = QLineEdit()
        self.interval_edit.setPlaceholderText("Enter interval (seconds)")
        left_layout.addWidget(self.interval_edit)

        self.set_interval_button = QPushButton("Set Interval")
        self.set_interval_button.clicked.connect(self.set_interval)
        left_layout.addWidget(self.set_interval_button)

        self.split_type_combo = QComboBox()
        self.split_type_combo.addItems(['train', 'test', 'split'])
        self.split_type_combo.currentTextChanged.connect(self.set_split_type)
        left_layout.addWidget(self.split_type_combo)

        self.use_interval_checkbox = QCheckBox("Use Interval")
        self.use_interval_checkbox.setChecked(True)
        self.use_interval_checkbox.stateChanged.connect(self.set_use_interval)
        left_layout.addWidget(self.use_interval_checkbox)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.canvas)

        layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        print("UI initialized")

    def select_folder(self):
        self.csv_dir = QFileDialog.getExistingDirectory(self, "Select Folder")
        self.load_csv_files()

    def load_csv_files(self):
        if self.csv_dir:
            self.csv_files = [f for f in os.listdir(self.csv_dir) if f.endswith('.csv')]
            self.file_list.clear()
            self.file_list.addItems(self.csv_files)
            print(f"Loaded CSV files from {self.csv_dir}")

    def load_selected_csv(self):
        selected_items = self.file_list.selectedItems()
        if selected_items:
            selected_file = selected_items[0].text()
            filepath = os.path.join(self.csv_dir, selected_file)
            self.canvas.load_csv(filepath)

    def save_labels(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Labels", "", "CSV Files (*.csv)")
        if filename:
            self.canvas.save_labels(filename)

    def load_labels(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Labels", "", "CSV Files (*.csv)")
        if filename:
            self.canvas.load_labels(filename)

    def set_interval(self):
        try:
            interval_seconds = int(self.interval_edit.text())
            self.canvas.set_interval(interval_seconds)
        except ValueError:
            print("Invalid interval")

    def set_split_type(self, split_type):
        self.canvas.set_split_type(split_type)

    def set_use_interval(self, state):
        self.canvas.set_use_interval(state == Qt.Checked)
