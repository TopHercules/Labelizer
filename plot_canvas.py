import pandas as pd
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import datetime
from predict import predict_IMU
from airgoutils.helpers.configs import Config

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
        self.data = None
        self.selected_file = None
        self.fall_labels = []
        self.cid_click = self.mpl_connect('button_press_event', self.on_click)
        self.cid_motion = self.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_release = self.mpl_connect('button_release_event', self.on_release)
        self.panning = False
        self.pan_start = None
        self.split_type = 'train'
        self.use_interval = True
        self.selecting_interval = False
        self.interval_start = None
        self.zoom_pan_status = {}
        cfg = Config(parse_passwords=False).read_file('imu_labelizer.ini')
        self.LM = datetime.timedelta(seconds=float(cfg.project.lm[0:-3])/1000)
        self.RM = datetime.timedelta(seconds=float(cfg.project.rm[0:-3])/1000)

        # Mouse position label
        self.mouse_pos_label = QLabel(self)
        self.mouse_pos_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.mouse_pos_label.setStyleSheet("background-color: white;")

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
        self.restore_zoom_pan()
        self.draw()
        print("Data plotted")

    def load_csv(self, filepath):
        try:
            self.save_zoom_pan()
            self.selected_file = filepath
            data = pd.read_csv(filepath, sep=',', header=0, names=['TAG', 'TS', 'ax', 'ay', 'az'])
            data['TS'] = pd.to_datetime(data['TS'], unit='s')
            self.plot(data)
            self.update_fall_data()
            print(f"CSV loaded from {filepath}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def set_interval(self, interval_seconds):
        self.interval_seconds = interval_seconds
        self.interval = datetime.timedelta(seconds=interval_seconds)
        print(f"Set the interval to {self.interval}")

    def set_split_type(self, split_type):
        self.split_type = split_type

    def set_use_interval(self, use_interval):
        self.use_interval = use_interval
        print(f"Set use_interval to {self.use_interval}")

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == 1 and (event.guiEvent.modifiers() & Qt.ShiftModifier):  # Left click to start interval selection
            if not self.use_interval:
                x = mdates.num2date(event.xdata)
                label_type = 'fall'
                start_time = x
                end_time = None
                self.fall_labels.append((self.data['TAG'][0], start_time, end_time, label_type, self.split_type))
                color = 'red'
                linestyle = '--' if self.split_type in ['test', 'split'] else '-'
                self.ax.axvspan(x - self.LM, x + self.RM, color=color, alpha=0.2)
                self.ax.axvline(x, color=color, linestyle=linestyle, linewidth=0.5)
                self.draw()
                return

            if not self.selecting_interval:
                self.selecting_interval = True
                self.interval_start = mdates.num2date(event.xdata)
                print(f"Interval start time selected: {self.interval_start}")
                self.ax.axvline(self.interval_start, color='red', linestyle='-', linewidth=0.5)
                self.draw()
            else:  # Left click to end interval selection
                self.selecting_interval = False
                interval_end = mdates.num2date(event.xdata)
                self.ax.axvline(interval_end, color='red', linestyle='-', linewidth=0.5)
                start_time = min(self.interval_start, interval_end)
                end_time = max(self.interval_start, interval_end)
                label_type = 'fall'
                self.fall_labels.append((self.data['TAG'][0], start_time, end_time, label_type, self.split_type))
                self.ax.axvspan(start_time, end_time, color='red', alpha=0.2)
                self.draw()
                print(f"Interval from {start_time} to {end_time} added as {label_type} with split type {self.split_type}")
        elif event.button == 3 and (event.guiEvent.modifiers() & Qt.ShiftModifier):  # Right click to start interval selection for 'not fall'
            if not self.use_interval:
                x = mdates.num2date(event.xdata)
                label_type = 'not fall'
                start_time = x
                end_time = None
                self.fall_labels.append((self.data['TAG'][0], start_time, end_time, label_type, self.split_type))
                color = 'green'
                linestyle = '--' if self.split_type in ['test', 'split'] else '-'
                self.ax.axvspan(x - self.LM, x + self.RM, color=color, alpha=0.2)
                self.ax.axvline(x, color=color, linestyle=linestyle, linewidth=0.5)
                self.draw()
                return

            if not self.selecting_interval:
                self.selecting_interval = True
                self.interval_start = mdates.num2date(event.xdata)
                self.ax.axvline(self.interval_start, color='green', linestyle='-', linewidth=0.5)
                self.draw()
                print(f"Interval start time selected: {self.interval_start}")
            else:  # Right click to end interval selection
                self.selecting_interval = False
                interval_end = mdates.num2date(event.xdata)
                start_time = min(self.interval_start, interval_end)
                end_time = max(self.interval_start, interval_end)
                self.ax.axvline(interval_end, color='green', linestyle='-', linewidth=0.5)   
                label_type = 'not fall'
                self.fall_labels.append((self.data['TAG'][0], start_time, end_time, label_type, self.split_type))
                self.ax.axvspan(start_time, end_time, color='green', alpha=0.2)
                self.draw()
                print(f"Interval from {start_time} to {end_time} added as {label_type} with split type {self.split_type}")

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return
        # Show mouse position time and value
        xdata = mdates.num2date(event.xdata).strftime('%H:%M:%S.%f')
        ydata = event.ydata
        self.mouse_pos_label.setText(f"Time: {xdata}, Value: {ydata:.2f}")
        self.mouse_pos_label.adjustSize()

    def on_release(self, event):
        if event.button == 2:
            self.panning = False
            self.pan_start = None
            print("Pan released")

    def save_labels(self, filename):
        try:
            with open(filename, 'w') as f:
                for tag, start_time, end_time, label, split in self.fall_labels:
                    date = start_time.date()
                    start_time_str = start_time.time()
                    end_time_str = end_time.time() if end_time else ''
                    fall_status = 1 if label == 'fall' else 0
                    mac = tag
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
                    tag, date, start_time, end_time, split, fall_status = line.strip().split(',')
                    start_time = datetime.datetime.strptime(f'{date} {start_time}', '%Y-%m-%d %H:%M:%S.%f')
                    end_time = datetime.datetime.strptime(f'{date} {end_time}', '%Y-%m-%d %H:%M:%S.%f') if end_time else None
                    label = 'fall' if fall_status == '1' else 'not fall'
                    self.fall_labels.append((tag, start_time, end_time, label, split))
                    
                    if self.data['TAG'][0] == tag and self.data['TS'][0].date() == start_time.date():
                        color = 'red' if label == 'fall' else 'green'
                        linestyle = '--' if split in ['test', 'split'] else '-'
                        if end_time:
                            self.ax.axvspan(start_time, end_time, color=color, alpha=0.2)
                        else:
                            self.ax.axvspan(start_time - self.LM, start_time + self.RM, color=color, alpha=0.2)
                            self.ax.axvline(start_time, color=color, linestyle=linestyle, linewidth=0.5)
            self.draw()
            print(f"Labels loaded from {filename}")
        except Exception as e:
            print(f"Error loading labels: {e}")


    def update_fall_data(self):
        for tag, start_time, end_time, label, split in self.fall_labels:
            if self.data['TAG'][0] == tag and self.data['TS'][0].date() == start_time.date():
                color = 'red' if label == 'fall' else 'green'
                linestyle = '--' if split in ['test', 'split'] else '-'
                if end_time:
                    self.ax.axvspan(start_time, end_time, color=color, alpha=0.2)
                else:
                    self.ax.axvspan(start_time - self.LM, start_time + self.RM, color=color, alpha=0.2)
                    self.ax.axvline(start_time, color=color, linestyle=linestyle, linewidth=0.5)
        self.draw()

    def save_zoom_pan(self):
        if self.selected_file:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            self.zoom_pan_status[self.selected_file] = (xlim, ylim)
            print(f"Saved zoom/pan status for {self.selected_file}")

    def restore_zoom_pan(self):
        if self.selected_file and self.selected_file in self.zoom_pan_status:
            xlim, ylim = self.zoom_pan_status[self.selected_file]
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
            print(f"Restored zoom/pan status for {self.selected_file}")

    def closeEvent(self, event):
        self.save_zoom_pan()
        event.accept()
