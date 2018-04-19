from PyDAQmx import *
import numpy as np
import time

class NIDAQControlClass(object):
    def __init__(self):
        self.AO_channel = 'Dev0/ai0'
        self.sampling_freq = 1000.0
        self.buffer_size = int(10.0*self.sampling_freq)
        self.voltage_min = -10.0
        self.voltage_max = 10.0
        self.task = None

    def device_init(self, AO_channel='Dev0/ai0', sampling_freq=1000.0, voltage_min=-10.0, voltage_max=10.0):
        self.AO_channel = AO_channel
        self.sampling_freq = sampling_freq
        self.buffer_size = int(10.0 * self.sampling_freq)
        self.voltage_min = voltage_min
        self.voltage_max = voltage_max
        self.task = Task()
        self.task.CreateAIVoltageChan(self.AO_channel, '', DAQmx_Val_RSE, self.voltage_min, self.voltage_max,
                                      DAQmx_Val_Volts, None)
        self.task.CfgSampClkTiming('', self.sampling_freq, DAQmx_Val_Rising, DAQmx_Val_ContSamps, self.buffer_size)

    def start_reading_data(self):
        if self.task is not None:
            self.task.StartTask()

    def stop_reading_data(self):
        if self.task is not None:
            self.task.StopTask()
            self.task = None

    def read_data(self, number_to_read, time_out=0.1):
        available_data_number = uInt32(0)
        self.task.GetReadAvailSampPerChan(byref(available_data_number))
        if available_data_number.value >= number_to_read:
            read = int32(0)
            data = np.zeros((self.buffer_size,), dtype=numpy.float64)
            self.task.ReadAnalogF64(number_to_read, time_out, DAQmx_Val_GroupByChannel, data, self.buffer_size,
                                    byref(read), None)
            return data[:read.value], read.value
        else:
            return None, 0

    def check_data_available(self, number_to_read):
        available_data_number = uInt32(0)
        self.task.GetReadAvailSampPerChan(byref(available_data_number))
        if available_data_number.value >= number_to_read:
            return True
        else:
            return False


if __name__ == '__main__':
    nidaq = NIDAQControlClass()
    nidaq.device_init()
    nidaq.start_reading_data()
    data, value = nidaq.read_data(700)
    print data
    print value
    data, value = nidaq.read_data(500)
    print data
    print value
    nidaq.stop_reading_data()