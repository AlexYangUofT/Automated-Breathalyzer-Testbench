# Author: Alex Yang; Date: 2024-12
# This program is going to record the flow rates of 2 Flow meters
import atexit
import sys
from time import sleep, time
import csv
from datetime import datetime
from serial import Serial
from sensirion_shdlc_driver import ShdlcSerialPort
from sensirion_driver_adapters.shdlc_adapter.shdlc_channel import ShdlcChannel
from sensirion_uart_sfx6xxx.device import Sfx6xxxDevice

class FlowSensorSFM6000:
    def __init__(self, port1, port2):
        self.device1 = None
        self.device2 = None
        self.channel1 = None
        self.channel2 = None
        self.serial_port1 = None
        self.serial_port2 = None
        
        try:
            print(f"Attempting to connect to Flow Meters on ports {port1} and {port2}")
            
            # First try to open the serial ports
            try:
                # Test if ports are available with basic Serial
                test_port1 = Serial(port1)
                test_port1.close()
                test_port2 = Serial(port2)
                test_port2.close()
            except Exception as e:
                raise Exception(f"Cannot access serial ports: {str(e)}")
            
            # Now initialize the actual devices
            self.serial_port1 = ShdlcSerialPort(port=port1, baudrate=115200)
            self.serial_port2 = ShdlcSerialPort(port=port2, baudrate=115200)
            
            self.channel1 = ShdlcChannel(self.serial_port1)
            self.channel2 = ShdlcChannel(self.serial_port2)
            
            self.device1 = Sfx6xxxDevice(self.channel1)
            self.device2 = Sfx6xxxDevice(self.channel2)
            
            # Reset devices
            self.device1.device_reset()
            self.device2.device_reset()
            
            # Test connection by getting device info
            print(f'Flow Meter 1 Serial Number: {self.device1.get_serial_number()}')
            print(f'Product Name: {self.device1.get_product_name()}')
            print(f'Article Code: {self.device1.get_article_code()}')
            
            print(f'Flow Meter 2 Serial Number: {self.device2.get_serial_number()}')
            print(f'Product Name: {self.device2.get_product_name()}')
            print(f'Article Code: {self.device2.get_article_code()}')
            
            self.is_collecting_data = False
            
        except Exception as e:
            self.cleanup()  # Clean up any partially initialized resources
            raise Exception(f"Flow meter initialization failed: {str(e)}")
        
        atexit.register(self.cleanup)

    def cleanup(self): # Clean up Flow Meter resources
        try:
            if self.device1:
                try:
                    self.device1.device_reset()
                except:
                    pass
            if self.device2:
                try:
                    self.device2.device_reset()
                except:
                    pass
                    
            if self.channel1:
                try:
                    self.channel1.close()
                except:
                    pass
            if self.channel2:
                try:
                    self.channel2.close()
                except:
                    pass
                    
            if self.serial_port1:
                try:
                    self.serial_port1.close()
                except:
                    pass
            if self.serial_port2:
                try:
                    self.serial_port2.close()
                except:
                    pass
                    
            print("Flow meter connections closed successfully")
            
        except Exception as e:
            print(f"Error during flow meter cleanup: {e}")
        finally:
            self.device1 = None
            self.device2 = None
            self.channel1 = None
            self.channel2 = None
            self.serial_port1 = None
            self.serial_port2 = None

    def exit_process(self):
        """Called on program exit"""
        self.cleanup()

    def collect_flow_data_with_duration(self, filename, duration): # Continuously collect and record flow rate data.
        # Collect and record flow rate data for a user-specified duration (seconds)
        start_time = time()
        flow_rates_1 = []
        flow_rates_2 = []
        
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write CSV header
            writer.writerow(["Timestamp", "Elapsed_Time_from_FM", "Measured_Flow_Rate_FM_1(sccm)", "Measured_Flow_Rate_FM_2(sccm)"])
            
            while time() - start_time < duration:
                timestamp_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                flow_rate_1 = self.device1.read_measured_value() * 1000  # Convert from slm to sccm
                if flow_rate_1 < 0:
                    flow_rate_1 = 0
                
                flow_rate_2 = self.device2.read_measured_value() * 1000
                if flow_rate_2 < 0:
                    flow_rate_2 = 0
                        
                Time_difference_from_FM = round(time() - start_time, 2)
                flow_rates_1.append(flow_rate_1)
                flow_rates_2.append(flow_rate_2)
                
                writer.writerow([timestamp_string, Time_difference_from_FM, flow_rate_1, flow_rate_2])
                print(f"Real Timestamp: {timestamp_string}, Elapsed_Time_from_FM: {Time_difference_from_FM:.2} s, Flow Rate Recorded by FM 1: {flow_rate_1:.2f} sccm, Flow Rate Recorded by FM 2: {flow_rate_2:.2f} sccm")
                sleep(0.05)  # Collect data every 0.05 seconds
        
        print(f"Data collection complete. Data saved to {filename}.")
        return flow_rates_1, flow_rates_2

    def calculate_average_flow_rate(self, flow_rates):
        # Calculate the average flow rate from a list of flow rates
        if flow_rates:
            average_flow_rate = sum(flow_rates) / len(flow_rates)
            return average_flow_rate
        else:
            print("No flow rate data being collected")
            return 0