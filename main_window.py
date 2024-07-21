import os
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction, QVBoxLayout, QWidget
from plot_canvas import PlotCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Labelizer Tool')
        
        # Create main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        
        # Create layout
        layout = QVBoxLayout(self.main_widget)
        
        # Create PlotCanvas and add to layout
        self.plot_canvas = PlotCanvas(self.main_widget)
        layout.addWidget(self.plot_canvas)
        
        # Create menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        
        # Create actions
        openFile = QAction('Open', self)
        openFile.triggered.connect(self.showDialog)
        fileMenu.addAction(openFile)
        
        saveFile = QAction('Save Labels', self)
        saveFile.triggered.connect(self.save_labels)
        fileMenu.addAction(saveFile)

        loadLabels = QAction('Load Labels', self)
        loadLabels.triggered.connect(self.load_labels)
        fileMenu.addAction(loadLabels)
        
        self.show()
        
        # Attempt to load existing labels on startup
        if os.path.exists('falls.csv'):
            self.plot_canvas.load_labels('falls.csv')
        print("Main window initialized")

    def showDialog(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'CSV Files (*.csv)', options=options)
        if file:
            self.plot_canvas.load_csv(file)

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
