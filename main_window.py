import os
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction, QVBoxLayout, QWidget, QListWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QSplitter
from PyQt5.QtCore import Qt
from plot_canvas import PlotCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Labelizer Tool')

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        layout = QSplitter(Qt.Horizontal)

        left_panel = QVBoxLayout()

        self.csv_list = QListWidget(self)
        self.csv_list.itemClicked.connect(self.load_selected_file)
        left_panel.addWidget(self.csv_list)

        self.interval_input = QLineEdit(self)
        self.interval_input.setPlaceholderText('Interval (seconds)')
        left_panel.addWidget(self.interval_input)

        self.interval_button = QPushButton('Set Interval', self)
        self.interval_button.clicked.connect(self.update_interval)
        left_panel.addWidget(self.interval_button)

        self.split_type_combo = QComboBox(self)
        self.split_type_combo.addItems(['train', 'test', 'split'])
        self.split_type_combo.currentTextChanged.connect(self.update_split_type)
        left_panel.addWidget(self.split_type_combo)

        self.predict_button = QPushButton('Predict', self)
        self.predict_button.clicked.connect(self.predict)
        left_panel.addWidget(self.predict_button)

        left_panel_widget = QWidget()
        left_panel_widget.setLayout(left_panel)
        layout.addWidget(left_panel_widget)

        self.plot_canvas = PlotCanvas(self.main_widget)
        layout.addWidget(self.plot_canvas)

        main_layout = QHBoxLayout()
        main_layout.addWidget(layout)
        self.main_widget.setLayout(main_layout)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')

        openFolder = QAction('Open Folder', self)
        openFolder.triggered.connect(self.show_folder_dialog)
        fileMenu.addAction(openFolder)

        saveFile = QAction('Save Labels', self)
        saveFile.triggered.connect(self.save_labels)
        fileMenu.addAction(saveFile)

        loadLabels = QAction('Load Labels', self)
        loadLabels.triggered.connect(self.load_labels)
        fileMenu.addAction(loadLabels)

        self.show()

    def show_folder_dialog(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, 'Open Folder', '', options=options)
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):
        self.csv_list.clear()
        csv_files = [f for f in os.listdir(folder) if f.endswith('.csv')]
        for csv_file in csv_files:
            self.csv_list.addItem(os.path.join(folder, csv_file))

    def load_selected_file(self, item):
        self.plot_canvas.load_csv(item.text())

    def update_interval(self):
        try:
            interval_seconds = int(self.interval_input.text())
            self.plot_canvas.set_interval(interval_seconds)
            print(f"Interval updated to {interval_seconds} seconds")
        except ValueError:
            print("Invalid interval value")

    def update_split_type(self, split_type):
        self.plot_canvas.set_split_type(split_type)
        print(f"Split type updated to {split_type}")

    def save_labels(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getSaveFileName(self, 'Save Labels', 'falls.csv', 'CSV Files (*.csv)', options=options)
        if file:
            self.plot_canvas.save_labels(file)

    def load_labels(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, 'Open Labels', '', 'CSV Files (*.csv)', options=options)
        if file:
            self.plot_canvas.load_labels(file)

    def predict(self):
        self.plot_canvas.predict_and_plot()
