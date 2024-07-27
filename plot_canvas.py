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
        self.split_type = 'train'
        self.use_interval = True
        self.selecting_interval = False
        self.interval_start = None
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
        self.draw()
        print("Data plotted")

    def load_csv(self, filepath):
        try:
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
        if event.button == 1:  # Left click to start interval selection
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
        elif event.button == 3:  # Right click to start interval selection for 'not fall'
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
        self.update_time_format()
        self.draw()

    def update_time_format(self):
        x_min, x_max = self.ax.get_xlim()
        x_range = x_max - x_min
        if x_range < 1 / 24 / 60 / 60:  # Less than 1 second
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S.%f'))
        elif x_range < 1 / 24 / 60:  # Less than 1 minute
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        elif x_range < 1 / 24:  # Less than 1 hour
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        else:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        print(f"Updated time format for x_range: {x_range} days")

    def on_motion(self, event):
        if event.inaxes != self.ax:
            return
        if self.panning:
            x_start, y_start = self.pan_start
            dx = event.xdata - x_start
            dy = event.ydata - y_start
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            self.ax.set_xlim(x_min - dx, x_max - dx)
            self.ax.set_ylim(y_min - dy, y_max - dy)
            self.draw()
            print(f"Pan event with dx={dx}, dy={dy}")
        else:
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
                    # mac = self.data['TAG'][0] if self.data is not None else ''
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
                    mac, date_str, start_time_str, end_time_str, split, fall_status = line.strip().split(',')
                    start_time = pd.to_datetime(f'{date_str} {start_time_str}')
                    end_time = pd.to_datetime(f'{date_str} {end_time_str}') if end_time_str else None
                    label = 'fall' if fall_status == '1' else 'not fall'
                    self.fall_labels.append((mac, start_time, end_time, label, split))
                    print(str(self.data['TS'][0].date()) == date_str)
                    if self.data['TAG'][0] == mac and str(self.data['TS'][0].date()) == date_str:
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
   
    def undo_last_action(self):
        if self.fall_labels:
            last_action = self.fall_labels.pop()
            self.ax.clear()
            self.plot(self.data)
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
            print(f"Last action undone: {last_action}")
        else:
            print("No actions to undo")
    
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
