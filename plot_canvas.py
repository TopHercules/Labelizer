import pandas as pd
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        # Enable and customize the grid
        self.ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
        self.data = None
        self.selected_file = None
        self.fall_labels = []
        self.cid_click = self.mpl_connect('button_press_event', self.on_click)
        self.cid_scroll = self.mpl_connect('scroll_event', self.on_scroll)
        self.cid_motion = self.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_release = self.mpl_connect('button_release_event', self.on_release)
        self.panning = False
        self.pan_start = None
        self.fixed_duration = datetime.timedelta(seconds=4)  # Fixed duration for fall areas
        print("PlotCanvas initialized")

    def plot(self, data):
        self.data = data
        self.ax.clear()
        self.ax.plot(data['TS'], data['AX'], label='AX')
        self.ax.plot(data['TS'], data['AY'], label='AY')
        self.ax.plot(data['TS'], data['AZ'], label='AZ')
        self.ax.legend()
        self.ax.set_xlabel('Timestamp')
        self.ax.set_ylabel('Acceleration')
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        # Enable and customize the grid
        self.ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
        self.draw()
        print("Data plotted")

    def load_csv(self, filepath):
        try:
            self.selected_file = filepath
            data = pd.read_csv(filepath, sep=',', header=0, names=['MAC', 'TS', 'AX', 'AY', 'AZ'])
            data['TS'] = pd.to_datetime(data['TS'], unit='s')
            self.plot(data)
            print(f"CSV loaded from {filepath}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == 1:
            x = mdates.num2date(event.xdata)
            label_type = 'fall'
            self.fall_labels.append((x, label_type))
            self.ax.axvspan(x - self.fixed_duration, x + self.fixed_duration, color='red', alpha=0.2)
            self.ax.axvline(x, color='red', linestyle='--', linewidth=0.5)
            self.draw()
            print(f"Label added at {x} as {label_type}")
        elif event.button == 3:  # Right mouse button for 'not fall' labels
            x = mdates.num2date(event.xdata)
            label_type = 'not fall'
            self.fall_labels.append((x, label_type))
            self.ax.axvspan(x - self.fixed_duration, x + self.fixed_duration, color='green', alpha=0.2)
            self.ax.axvline(x, color='green', linestyle='--', linewidth=0.5)
            self.draw()
            print(f"Label added at {x} as {label_type}")
        elif event.button == 2:  # Middle mouse button for panning
            self.panning = True
            self.pan_start = event.xdata, event.ydata

    def on_scroll(self, event):
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        scale_factor = 0.9 if event.button == 'up' else 1.1

        if event.guiEvent.modifiers() & Qt.ShiftModifier:
            # Horizontal zoom
            new_x_range = (x_max - x_min) * scale_factor
            self.ax.set_xlim([x_center - new_x_range / 2, x_center + new_x_range / 2])
            print("Horizontal zoom event")
        else:
            # Vertical zoom
            new_y_range = (y_max - y_min) * scale_factor
            self.ax.set_ylim([y_center - new_y_range / 2, y_center + new_y_range / 2])
            print("Vertical zoom event")

        self.draw()

    def on_motion(self, event):
        if not self.panning or event.inaxes != self.ax:
            return
        x_start, y_start = self.pan_start
        dx = event.xdata - x_start
        dy = event.ydata - y_start
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        self.ax.set_xlim(x_min - dx, x_max - dx)
        self.ax.set_ylim(y_min - dy, y_max - dy)
        self.draw()
        print(f"Pan event with dx={dx}, dy={dy}")

    def on_release(self, event):
        if event.button == 2:  # Middle mouse button
            self.panning = False
            self.pan_start = None
            print("Pan released")

    def save_labels(self, filename):
        try:
            with open(filename, 'w') as f:
                for x, label in self.fall_labels:
                    f.write(f'{x},{label}\n')
            print(f"Labels saved to {filename}")
        except Exception as e:
            print(f"Error saving labels: {e}")

    def load_labels(self, filename):
        try:
            self.fall_labels.clear()
            self.ax.clear()
            if self.data is not None:
                self.plot(self.data)
            with open(filename, 'r') as f:
                for line in f:
                    x, label = line.strip().split(',')
                    x = pd.to_datetime(x)
                    self.fall_labels.append((x, label))
                    if label == 'fall':
                        self.ax.axvspan(x - self.fixed_duration, x + self.fixed_duration, color='red', alpha=0.2)
                        self.ax.axvline(x, color='red', linestyle='--', linewidth=0.5)
                    else:
                        self.ax.axvline(x, color='green', linestyle='--', linewidth=0.5)
            self.draw()
            print(f"Labels loaded from {filename}")
        except Exception as e:
            print(f"Error loading labels: {e}")
