from PyQt5 import QtCore, QtWidgets, QtGui, uic
import sys
import numpy as np
import pyqtgraph as pg
import NIDAQControl
import time
import pandas as pd

qtCreatorFile = 'ui_optimic.ui'
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class OptiMic(QtBaseClass, Ui_MainWindow):
    def __init__(self,  parent=None):
        super(OptiMic, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('OptiMic Control Dialog')
        self.nidaq = NIDAQControl.NIDAQControlClass()
        self.p0 = self.ui_data_plot.addPlot()
        self.p0.setLabel('left', 'Voltage (V)')
        self.p0.setLabel('bottom', 'Time (s)')
        self.plot = self.p0.plot()
        self.polling_data_number = 100
        self.buffer_size = 1000
        self.data = None
        self.display_data = np.zeros(self.buffer_size)
        self.time = None
        self.running = False

    def on_ui_start_button_released(self):
        AO_channel = self.ui_input_channel.text()
        sampling_freq = self.ui_sampling_freq.value()
        voltage_min = self.ui_min_voltage.value()
        voltage_max = self.ui_max_voltage.value()
        sleep_time = 100.0 / sampling_freq
        self.time = np.linspace(-self.buffer_size/sampling_freq, 0, self.buffer_size)
        self.polling_data_number = int(sampling_freq * self.ui_data_polling_time.value())
        self.nidaq.device_init(AO_channel, sampling_freq, voltage_min, voltage_max)
        self.running = True
        self.nidaq.start_reading_data()
        self.data_reading_thread = DataReadThread(self)
        self.data_reading_thread.dataReady.connect(self.add_data)
        self.data_reading_thread.start()

    def add_data(self, data):
        if data != [] and data is not None:
            if self.data is None:
                self.data = data
            else:
                self.data = np.hstack((self.data, data))
            l = len(data)
            if l >= self.buffer_size:
                l = self.buffer_size
                data = data[-self.buffer_size:]
            if l != 0:
                self.display_data[:-l] = self.display_data[l:]
                self.display_data[-l:] = data
                self.plot.setData(self.time, self.display_data)

    def on_ui_stop_button_released(self):
        self.running = False
        self.nidaq.stop_reading_data()

    def on_ui_clear_data_button_released(self):
        self.running = False
        self.nidaq.stop_reading_data()
        self.data = None

    def on_ui_select_filename_button_released(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Filename', filter='.csv')
        file_name = file_name[0]
        if file_name[-4:] != '.csv':
            file_name += '.csv'
        if len(file_name) != 0:
            self.ui_filename_text.setText(file_name)

    def on_ui_save_data_button_released(self):
        self.running = False
        self.nidaq.stop_reading_data()
        df = pd.DataFrame(self.data)
        filename = self.ui_filename_text.text()
        df.to_csv(filename, header=None, index=None)


class DataReadThread(QtCore.QThread):
    dataReady = QtCore.pyqtSignal(object)

    def __init__(self, optimic, sleep_time = 0.1, parent=None):
        super(DataReadThread, self).__init__(parent)
        self.optimic = optimic
        self.sleep_time = sleep_time

    def run(self):
        while self.optimic.running:
            if self.optimic.nidaq.check_data_available(self.optimic.polling_data_number) and self.optimic.running:
                data, number_of_data = self.optimic.nidaq.read_data(self.optimic.polling_data_number)
                self.dataReady.emit(data)
            else:
                time.sleep(self.sleep_time)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_win = OptiMic()
    main_win.show()
    app.exec_()