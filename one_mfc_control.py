# Author: Alex Yang Date: 11-22-2024
# This program is going to control the MFC to output any flow rate between 0 ccm to 10000 ccm
from sensirion_shdlc_driver.errors import ShdlcDeviceError
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sfc5xxx import Sfc5xxxShdlcDevice, Sfc5xxxScaling, \
    Sfc5xxxValveInputSource, Sfc5xxxUnitPrefix, Sfc5xxxUnit, \
    Sfc5xxxUnitTimeBase, Sfc5xxxMediumUnit
from flow_meter_record import FlowSensorSFM6000

class one_MFC:
    def __init__(self, port):
        try:
            print(f"Attempting to connect to MFC on port {port}")
            setup = ShdlcSerialPort(port=port, baudrate=115200)
            self.device = Sfc5xxxShdlcDevice(ShdlcConnection(setup), slave_address=0)
            
            # Test connection
            serial_number = self.device.get_serial_number()
            print(f'Successfully connected to MFC:')
            print(f'Serial Number: {serial_number}')
            print(f'Product Name: {self.device.get_product_name()}')
            print(f'Article Code: {self.device.get_article_code()}')
            
            self.unit = Sfc5xxxMediumUnit(
                Sfc5xxxUnitPrefix.MILLI,
                Sfc5xxxUnit.STANDARD_LITER,
                Sfc5xxxUnitTimeBase.MINUTE)
            self.device.set_user_defined_medium_unit(self.unit)
            
        except Exception as e:
            raise Exception(f"Failed to initialize MFC on port {port}: {str(e)}")
        
    def set_value(self, val): # Set the flow rate on MFC
        self.device.set_setpoint(val, Sfc5xxxScaling.USER_DEFINED)
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'device'):
                self.set_value(0)  # Set flow rate to 0
                if hasattr(self.device, '_connection') and hasattr(self.device._connection, '_port'):
                    self.device._connection._port.close()
                    print("MFC connection closed successfully")
        except Exception as e:
            print(f"Error during MFC cleanup: {e}")