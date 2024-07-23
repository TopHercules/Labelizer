import pandas as pd
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime
from predict import predict_IMU

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
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
        self.interval = datetime.timedelta(seconds=4)
        self.split_type = 'train'
        self.interval_seconds = 4
        print("PlotCanvas initialized")

    def plot(self, data):
        self.data = data
        self.ax.clear()
        self.ax.plot(data['TS'], data['ax'], label='ax')
        self.ax.plot(data['TS'], data['ay'], label='ay')
        self.ax.plot(data['TS'], data['az'], label='az')
        self.ax.legend()
        self.ax.set_xlabel('Timestamp')
        self.ax.set_ylabel('Acceleration')
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
        self.draw()
        print("Data plotted")

    def load_csv(self, filepath):
        try:
            self.selected_file = filepath
            data = pd.read_csv(filepath, sep=',', header=0, names=['TAG', 'TS', 'ax', 'ay', 'az'])
            data['TS'] = pd.to_datetime(data['TS'], unit='s')
            self.plot(data)
            print(f"CSV loaded from {filepath}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def set_interval(self, interval_seconds):
        self.interval_seconds = interval_seconds
        self.interval = datetime.timedelta(seconds=interval_seconds)
        print(f"Set the interval to {self.interval}")

    def set_split_type(self, split_type):
        self.split_type = split_type

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == 1:
            x = mdates.num2date(event.xdata)
            label_type = 'fall'
            start_time = x
            end_time = x + self.interval if self.interval_seconds != 0 else None
            self.fall_labels.append((start_time, end_time, label_type, self.split_type))
            color = 'red'
            linestyle = '--' if self.split_type in ['test', 'split'] else '-'
            self.ax.axvline(x, color=color, linestyle=linestyle, linewidth=0.5)
            if self.interval_seconds != 0:
                self.ax.axvspan(x - self.interval, x + self.interval, color=color, alpha=0.2)
            self.draw()
            print(f"Label added at {x} as {label_type} with split type {self.split_type}")
        elif event.button == 3:
            x = mdates.num2date(event.xdata)
            label_type = 'not fall'
            start_time = x
            end_time = x + self.interval if self.interval_seconds != 0 else None
            self.fall_labels.append((start_time, end_time, label_type, self.split_type))
            color = 'green'
            linestyle = '--' if self.split_type in ['test', 'split'] else '-'
            self.ax.axvline(x, color=color, linestyle=linestyle, linewidth=0.5)
            if self.interval_seconds != 0:
                self.ax.axvspan(x - self.interval, x + self.interval, color=color, alpha=0.2)
            self.draw()
            print(f"Label added at {x} as {label_type} with split type {self.split_type}")
        elif event.button == 2:
            self.panning = True
            self.pan_start = event.xdata, event.ydata

    def on_scroll(self, event):
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        scale_factor = 0.9 if event.button == 'up' else 1.1
        if event.guiEvent.modifiers() & Qt.ShiftModifier:
            new_x_range = (x_max - x_min) * scale_factor
            self.ax.set_xlim([x_center - new_x_range / 2, x_center + new_x_range / 2])
            print("Horizontal zoom event")
        else:
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
        if event.button == 2:
            self.panning = False
            self.pan_start = None
            print("Pan released")

    def save_labels(self, filename):
        try:
            with open(filename, 'w') as f:
                for start_time, end_time, label, split in self.fall_labels:
                    date = start_time.date()
                    start_time_str = start_time.time()
                    end_time_str = end_time.time() if end_time else ''
                    fall_status = 1 if label == 'fall' else 0
                    mac = self.data['TAG'][0] if self.data is not None else ''
                    f.write(f'{mac},{date},{start_time_str},{end_time_str},{split},{fall_status}\n')
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
                    mac, date_str, start_time_str, end_time_str, split, fall_status = line.strip().split(',')
                    start_time = pd.to_datetime(f'{date_str} {start_time_str}')
                    end_time = pd.to_datetime(f'{date_str} {end_time_str}') if end_time_str else None
                    label = 'fall' if fall_status == '1' else 'not fall'
                    self.fall_labels.append((start_time, end_time, label, split))
                    color = 'red' if label == 'fall' else 'green'
                    linestyle = '--' if split in ['test', 'split'] else '-'
                    self.ax.axvline(start_time, color=color, linestyle=linestyle, linewidth=0.5)
                    if end_time:
                        self.ax.axvspan(start_time, end_time, color=color, alpha=0.2)
            self.draw()
            print(f"Labels loaded from {filename}")
        except Exception as e:
            print(f"Error loading labels: {e}")

    def predict_and_plot(self):
        try:
            if self.data is not None:
                predicted_data = predict_IMU(self.data)
                if predicted_data is not None:
                    self.ax.plot(predicted_data.index.values, predicted_data.values, label='Prediction', color='blue')
                    self.ax.legend()
                    self.draw()
                    print("Prediction plotted")
                else:
                    print("Prediction data is None")
            else:
                print("No data loaded for prediction")
        except Exception as e:
            print(f"Error during prediction and plot: {e}")
