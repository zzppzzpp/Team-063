import sys
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget,\
    QVBoxLayout, QHBoxLayout, QStackedLayout, QPushButton, QLabel,\
    QFrame, QGridLayout, QLineEdit, QRadioButton
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QSize
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.ticker import FormatStrFormatter

class Color(QWidget):
    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class mplgraph(FigureCanvasQTAgg):
    def __init__(self,parent=None, width=5, height=4,dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(mplgraph, self).__init__(fig)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        mainlayout = QGridLayout()

        #output data frame
        output_data_layout = QVBoxLayout()

        self.output_data_title = QLabel()
        self.output_data_title.setText("Output Data")
        self.output_data_title.setAlignment(Qt.AlignCenter)
        self.output_data_title.setStyleSheet("font: bold 30px")
        output_data_layout.addWidget(self.output_data_title)

        output = mplgraph(self, width=15, height=6,dpi=100)
        output.axes.plot([0,1,2,3,4], [10,1,20,3,40])
        output_data_layout.addWidget(output)

        #arduino = serial.Serial(port="COM3", baudrate=9600)
        def scan_button_clicked(self):
            #arduino.Write("A", "utf-8")
            print("clicked")

        def reset_button_clicked():
            #arduino.Write("B","utf-8")
            print("reset clicked")

        def forward_button_clicked():
            #arduino.Write("C","utf-8")
            print("forward clicked")

        def backward_button_clicked():
            #arduino.Write("D","utf-8")
            print("backward clicked")

        def stop_button_clicked():
            #arduino.Write("E","utf-8")
            print("stop clicked")

        #manual motion control
        motion_control_layout = QVBoxLayout()

        self.motion_control_title = QLabel()
        self.motion_control_title.setText("Manual Motion Control")
        self.motion_control_title.setAlignment(Qt.AlignBottom)
        self.motion_control_title.setStyleSheet("font: bold 30px")
        motion_control_layout.addWidget(self.motion_control_title)

        reset_button = QPushButton("Reset")
        motion_control_layout.addWidget(reset_button)
        reset_button.clicked.connect(reset_button_clicked)

        forward_button = QPushButton("Forward")
        motion_control_layout.addWidget(forward_button)
        forward_button.clicked.connect(forward_button_clicked)

        backward_button = QPushButton("Backward")
        motion_control_layout.addWidget(backward_button)
        backward_button.clicked.connect(backward_button_clicked)

        stop_button = QPushButton("Stop")
        motion_control_layout.addWidget(stop_button)
        stop_button.clicked.connect(stop_button_clicked)

        #scan control
        scan_control_layout = QGridLayout()
        scan_control_title = QLabel("Scan Control")
        scan_control_title.setAlignment(Qt.AlignHCenter)
        scan_control_title.setStyleSheet("font: bold 30px")

        scan_control_layout.addWidget(scan_control_title, 0, 0, 1, 3)

        begin_position = QLabel("Begin Position")
        scan_control_layout.addWidget(begin_position,1,0)

        begin_input = QLineEdit()
        scan_control_layout.addWidget(begin_input, 1, 1, 1, 2)
        end_input = QLineEdit()
        scan_control_layout.addWidget(end_input,2,1,1,2)

        end_position = QLabel("End Position")
        scan_control_layout.addWidget(end_position, 2, 0)

        scan_speed = QLabel("Scan Speed")
        scan_control_layout.addWidget(scan_speed, 3, 0)
        self.fast = QRadioButton("Fast")
        self.fast.setChecked(True)
        scan_control_layout.addWidget(self.fast, 3,1)
        self.slow = QRadioButton("Slow")
        scan_control_layout.addWidget(self.slow, 3,2)

        scan_button = QPushButton("scan")
        scan_control_layout.addWidget(scan_button, 4,0,1,3)
        scan_button.clicked.connect(scan_button_clicked)



        #main layout
        mainlayout.addLayout(motion_control_layout,0,0)
        mainlayout.addLayout(scan_control_layout,1,0)
        mainlayout.addLayout(output_data_layout, 0, 1, 2, 4)

        widget = QWidget()
        widget.setLayout(mainlayout)
        self.setCentralWidget(widget)

app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()