import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget,\
    QVBoxLayout, QHBoxLayout, QStackedLayout, QPushButton, QLabel,\
    QFrame, QGridLayout, QLineEdit, QRadioButton, QButtonGroup
from PyQt5.QtCore import Qt, QSize, QCoreApplication
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.ticker import FormatStrFormatter
from qtwidgets import Toggle
import pandas as pd
import serial
import ast
from base64 import encode
from datetime import datetime, date
import numpy as np
from LedIndicator import *
arduino = serial.Serial(port="/dev/cu.usbmodem14201", baudrate=250000) #/dev/cu.usbserial-1420

encoderData = []
sensorData = []

def moving_average(x, w):
    return (np.convolve(x, np.ones(w), 'valid') / w).tolist()

class dataProcessing:
    def __init__(self, rawData):
        self.default_distance = 20
        self.rawData = rawData

    def length_calculation(self):
        data_distance = self.rawData['Distance'] > self.default_distance
        filtered_data = self.rawData[data_distance]
        filtered_position = filtered_data["Position"]
        max_position = filtered_position.max()
        min_position = filtered_position.min()
        length = round((max_position - min_position), 2)
        return str(length-3)

class mplgraph(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4,dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        self.axes.set_xlabel("Sensor Position (mm)", fontsize=8)
        self.axes.set_ylabel("Sensor Measurement (cm)", fontsize=8)
        self.axes.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
        self.axes.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        self.axes.set_ylim(0, 40)
        self.axes.set_xlim(0, 800)
        self.axes.set_title("Output Graph", fontweight="bold", fontsize=15)
        super(mplgraph,self).__init__(fig)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.setWindowTitle("Gantry Control System")
        #self.setFixedSize(1000,400)
        mainlayout = QGridLayout()

        #scan status layout
        scan_status_layout = QVBoxLayout()

        scan_status_layout.setContentsMargins(30,0,30,0)#left, top, right, bottom
        self.scan_status_title = QLabel("Scan Status")
        self.scan_status_title.setStyleSheet("font: bold 30px")
        self.scan_status_title.setAlignment(Qt.AlignCenter)
        scan_status_layout.addWidget(self.scan_status_title, alignment=Qt.AlignTop)

        scan_control_layout = QGridLayout()
        scan_control_layout.setRowStretch(2, 5)
        scan_control_layout.setSpacing(0)
        scan_control_layout.setContentsMargins(0,10,0,5)
        self.scan_forward = QLabel("Scan on Forward")
        self.scan_backward = QLabel("Scan on Backward")
        self.scan_direction_toggle = Toggle()
        self.scan_detection = QLabel("Sensor Speed Mode")
        self.scan_motion = QLabel("Sensor Resolution Mode")
        self.scan_mode_toggle = Toggle()
        scan_control_layout.addWidget(self.scan_forward,0,0)
        scan_control_layout.addWidget(self.scan_direction_toggle,0,1)
        scan_control_layout.addWidget(self.scan_backward,0,2)
        scan_control_layout.addWidget(self.scan_detection,1,0)
        scan_control_layout.addWidget(self.scan_mode_toggle,1,1)
        scan_control_layout.addWidget(self.scan_motion,1,2)
        scan_status_layout.addLayout(scan_control_layout)

        indicator_layout = QGridLayout()
        indicator_layout.setRowStretch(5,1)
        indicator_layout.setSpacing(15)
        self.scan_in_progress = QLabel("Scanning in Progress")
        self.scan_completed = QLabel("Scanning Completed")
        self.scan_error = QLabel("Scanning Error")
        self.abort = QPushButton("Abort Scan")
        self.abort.setFixedSize(200,30)
        self.stop = False

        self.abort.clicked.connect(self.stop_scan)
        self.abort.setStyleSheet("font: bold;")
        self.scan_progress_led = LedIndicator(self)
        self.scan_completed_led = LedIndicator(self)
        self.error_led = LedIndicator(self)

        #set error led to red
        self.error_led.on_color_1 = QColor(255, 0, 0)
        self.error_led.on_color_2 = QColor(176, 0, 0)
        self.error_led.off_color_1 = QColor(28, 0, 0)
        self.error_led.off_color_2 = QColor(156, 0, 0)

        #disable clicking led
        self.scan_progress_led.setDisabled(True)
        self.scan_completed_led.setDisabled(True)
        self.error_led.setDisabled(True)

        indicator_layout.addWidget(self.scan_in_progress,0,0)
        #indicator_layout.addWidget(self.green_led_label,0,1, alignment=Qt.AlignCenter)
        indicator_layout.addWidget(self.scan_progress_led, 0, 1, alignment=Qt.AlignCenter)
        indicator_layout.addWidget(self.scan_completed,1,0)
        #indicator_layout.addWidget(self.green_led_label2, 1, 1, alignment=Qt.AlignCenter)
        indicator_layout.addWidget(self.scan_completed_led, 1, 1, alignment=Qt.AlignCenter)
        indicator_layout.addWidget(self.scan_error,2,0)
        #indicator_layout.addWidget(self.red_led_label, 2, 1, alignment=Qt.AlignCenter)
        indicator_layout.addWidget(self.error_led, 2, 1, alignment=Qt.AlignCenter)
        indicator_layout.addWidget(self.abort,3,0,1,2, alignment=Qt.AlignCenter)
        scan_status_layout.addLayout(indicator_layout)

        output_layout = QGridLayout()
        output_layout.setSpacing(10)
        output_layout.setContentsMargins(0,10,0,0)
        self.measurements = QLabel("Measurements")
        self.measurements.setStyleSheet("font: bold 18px")
        self.small_diameter = QLabel("Log small diameter (cm)")
        self.large_diameter = QLabel("Log large diameter (cm)")
        self.length = QLabel("Log Length (mm)")
        self.small_diameter_box = QLineEdit()
        self.small_diameter_box.setFixedWidth(100)
        self.large_diameter_box = QLineEdit()
        self.large_diameter_box.setFixedWidth(100)
        self.length_box = QLineEdit()
        self.length_box.setFixedWidth(100)
        output_layout.addWidget(self.measurements,0,0,1,2,alignment=Qt.AlignCenter)
        output_layout.addWidget(self.small_diameter,1,0, alignment=Qt.AlignCenter)
        output_layout.addWidget(self.small_diameter_box,1,1,alignment=Qt.AlignLeft)
        output_layout.addWidget(self.large_diameter,2,0, alignment=Qt.AlignCenter)
        output_layout.addWidget(self.large_diameter_box,2,1,alignment=Qt.AlignLeft)
        output_layout.addWidget(self.length,3,0,alignment=Qt.AlignCenter)
        output_layout.addWidget(self.length_box,3,1,alignment=Qt.AlignLeft)
        scan_status_layout.addLayout(output_layout)

        scan_status_layout.addStretch(200)

        #output data frame
        output_data_layout = QVBoxLayout()
        # data = pd.read_csv('testdata.csv')
        # self.y = data['Distance']
        # self.x = data['Position']
        self.output = mplgraph(self, width=15, height=3,dpi=100)

        #output.setFixedSize(500,500)
        output_data_layout.addWidget(self.output)

        def scan_button_clicked():
            print("clicked")

            start_pos = begin_input.text()
            end_pos = end_input.text()
            if not (start_pos or end_pos): #begin and end are empty
                print('empty')
            elif not (start_pos and end_pos): #one input is empty
                print('error')
            elif (start_pos and end_pos): #input
                
                start_angle = int ((int(start_pos) / 0.0065) / 100)
                end_angle = int ( (int(end_pos) / 0.0065) / 100)

                print(start_angle)
                print(end_angle)

            dataIn = ""
            readData = True
            arduino.write(bytes("A", 'utf-8'))

            print("scanning...")
            self.scan_completed_led.setChecked(self.scan_completed_led.isChecked())
            self.scan_progress_led.setChecked(not self.scan_progress_led.isChecked())
            self.error_led.setChecked(self.error_led.isChecked())

            print(dataIn)
            while readData:
                print("****looping")

                QCoreApplication.processEvents()
                dataIn = arduino.readline().decode('utf-8')
                if "STOP" in dataIn:
                    self.scan_completed_led.setChecked(not self.scan_completed_led.isChecked())
                    self.scan_progress_led.setChecked(not self.scan_progress_led.isChecked())

                    break

                if self.stop:
                    self.stop = False
                    self.error_led.setChecked(not self.error_led.isChecked())
                    break
            
                encAndSensor = dataIn.strip().split(",")

                encoderData.append(int(encAndSensor[0]))
                sensorData.append(int(encAndSensor[1]))
                    
            arduino.write(bytes("P", 'utf-8'))
            arduino.write(bytes("S", 'utf-8'))

            i = 0
            encoderDataFixed = []
            while i < len(encoderData):
                encoderDataFixed.append(-100 * (encoderData[i] - encoderData[0]) * 2*3.141592/1024 * 0.0065 )
                i += 1

            i = 0
            sensorDataFixed = []
            while i < len(sensorData):
                sensorDataFixed.append( 40 - (100*(sensorData[i] * 0.35/1024 ) ) - 4.9)
                i += 1

            # sensorDataFiltered = moving_average(np.array(sensorDataFixed),100)
            # encoderDataFixed = moving_average(np.array(encoderDataFixed),100)

            sensorValuesLog = []
            for value in sensorDataFixed:
                if value > 20:
                    sensorValuesLog.append(value)


            small_diameter_value = 0
            large_diameter_value = 0
            if get_average(sensorValuesLog[0:1000]) < get_average(sensorValuesLog[-1000:]):
                small_diameter_value = get_average(sensorValuesLog[0:1000])
                large_diameter_value = get_average(sensorValuesLog[-1000:])
            else:
                small_diameter_value = get_average(sensorValuesLog[-1000:])
                large_diameter_value = get_average(sensorValuesLog[0:1000])

            self.small_diameter_box.setText(str(small_diameter_value)[0:5])
            self.large_diameter_box.setText(str(large_diameter_value)[0:5])

            # Generate CSV file with sensor data
            d = {'Position':encoderDataFixed, 'Distance':sensorDataFixed}
            df1 = pd.DataFrame(data=d)

            now = datetime.now()
            current_time = now.strftime("%H%M_%S")
            today = date.today()
            fileName = str(today)+'-'+str(current_time)+'.csv'
            df1.to_csv(fileName)

            rawData = pd.read_csv(fileName)
            data = dataProcessing(rawData)
            self.length = data.length_calculation()
            
            self.length_box.setText(self.length)

            self.output.axes.cla()
            self.output.axes.set_xlabel("Sensor Position (mm)", fontsize=8)
            self.output.axes.set_ylabel("Sensor Measurement (cm)", fontsize=8)
            self.output.axes.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
            self.output.axes.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
            self.output.axes.set_ylim(0, 50)
            self.output.axes.set_xlim(0, 100)
            self.output.axes.set_title("Output Graph", fontweight="bold", fontsize=15)
            self.output.axes.plot(encoderDataFixed, sensorDataFixed, linestyle=':', marker='o')
            self.output.draw()

        def reset_button_clicked():
            arduino.write(bytes("R", 'utf-8'))
            arduino.write(bytes("S", 'utf-8'))            
            print("reset clicked")

        def forward_button_clicked():
            arduino.write(bytes("F", 'utf-8'))
            arduino.write(bytes("S", 'utf-8'))
            print("forward clicked")

        def backward_button_clicked():
            arduino.write(bytes("B", 'utf-8'))
            arduino.write(bytes("S", 'utf-8'))
            print("backward clicked")

        def stop_button_clicked():
            arduino.write(bytes("S", 'utf-8'))
            print("stop clicked")

        # motion control
        motion_control_layout = QVBoxLayout()
        motion_control_layout.setContentsMargins(10,0,0,15)
        motion_control_layout.setSpacing(10)
        self.motion_control_title = QLabel("Motor Control")
        #self.motion_control_title.setAlignment(Qt.AlignBaseline)
        self.motion_control_title.setStyleSheet("font: bold 30px")
        motion_control_layout.addWidget(self.motion_control_title, alignment=Qt.AlignBottom)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedHeight(30)
        motion_control_layout.addWidget(self.reset_button)
        self.reset_button.clicked.connect(reset_button_clicked)

        self.forward_button = QPushButton("Forward")
        self.forward_button.setFixedHeight(30)
        motion_control_layout.addWidget(self.forward_button)
        self.forward_button.clicked.connect(forward_button_clicked)

        self.backward_button = QPushButton("Backward")
        self.backward_button.setFixedHeight(30)
        motion_control_layout.addWidget(self.backward_button)
        self.backward_button.clicked.connect(backward_button_clicked)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedHeight(30)
        motion_control_layout.addWidget(self.stop_button)
        self.stop_button.clicked.connect(stop_button_clicked)

        #scan control
        scan_control_layout = QGridLayout()
        scan_control_layout.setContentsMargins(10,0,0,10)
        scan_control_layout.setSpacing(10)
        scan_control_title = QLabel("Scan Control")
        scan_control_title.setAlignment(Qt.AlignCenter)
        scan_control_title.setStyleSheet("font: bold 30px")
        scan_control_layout.addWidget(scan_control_title, 0, 0, 1, 3, alignment=Qt.AlignBottom)

        begin_position = QLabel("Begin Position")
        scan_control_layout.addWidget(begin_position,1,0)

        begin_input = QLineEdit()
        scan_control_layout.addWidget(begin_input, 1, 1, 1, 2)
        end_input = QLineEdit()
        scan_control_layout.addWidget(end_input,2,1,1,2)

        end_position = QLabel("End Position")
        scan_control_layout.addWidget(end_position, 2, 0)

        def fast_checked():
            sender = self.sender()
            if sender.isChecked():
                print(sender.text())
                arduino.write(bytes("W", 'utf-8'))
                arduino.write(bytes("S", 'utf-8'))

        def slow_checked():
            sender = self.sender()
            if sender.isChecked():
                arduino.write(bytes("Q", 'utf-8'))
                arduino.write(bytes("S", 'utf-8'))


        scan_speed = QLabel("Scan Speed")
        scan_control_layout.addWidget(scan_speed, 3, 0)
        self.fast = QRadioButton("Fast")
        self.fast.setChecked(True)
        self.fast.toggled.connect(fast_checked)
        scan_control_layout.addWidget(self.fast, 3,1)
        self.slow = QRadioButton("Slow")
        self.slow.toggled.connect(slow_checked)
        scan_control_layout.addWidget(self.slow, 3,2)

        scan_button = QPushButton("Scan")
        scan_control_layout.addWidget(scan_button, 4,0,1,3)
        scan_button.clicked.connect(scan_button_clicked)
        # scan_button.clicked.connect(diameter_calculation)
        # scan_button.clicked.connect(length_calculation)

        #main layout
        #row, column, rowSpan, columnSpan
        mainlayout.addLayout(motion_control_layout,0,0)
        mainlayout.addLayout(scan_control_layout,1,0)
        mainlayout.addLayout(scan_status_layout,0,1,2,1)
        mainlayout.addLayout(output_data_layout,0,2,2,1)

        widget = QWidget()
        widget.setLayout(mainlayout)
        self.setCentralWidget(widget)

    def stop_scan(self):
        self.stop = True

def get_average(num):
    sum_num = 0
    for t in num:
        sum_num = sum_num + t           

    avg = sum_num / len(num)
    return avg

app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()
