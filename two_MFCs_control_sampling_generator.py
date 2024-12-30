# Author: Alex Yang; Date: 2024-12
# This program is going to control 2 MFCs to generate corresponding breath samples
import time
import pandas as pd
import sys
from datetime import datetime # handle timestamps and real-time elapsed time
from sensirion_shdlc_driver.errors import ShdlcDeviceError
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sfc5xxx import Sfc5xxxShdlcDevice, Sfc5xxxScaling, \
    Sfc5xxxValveInputSource, Sfc5xxxUnitPrefix, Sfc5xxxUnit, \
    Sfc5xxxUnitTimeBase, Sfc5xxxMediumUnit

class two_MFCs:
    def __init__(self, port1_mfc, port2_mfc):
        try:
            setup_1 = ShdlcSerialPort(port=port1_mfc, baudrate=115200)
            self.device1 = Sfc5xxxShdlcDevice(ShdlcConnection(setup_1), slave_address=0)
            self.unit1 = Sfc5xxxMediumUnit( # define the unit of flow as sccm(cubic centimeters(milliliters) per min)
                Sfc5xxxUnitPrefix.MILLI,
                Sfc5xxxUnit.STANDARD_LITER,
                Sfc5xxxUnitTimeBase.MINUTE
            )
            self.device1.set_user_defined_medium_unit(self.unit1)
            print(f'MFC_1 Serial Number: {self.device1.get_serial_number()}\nMFC_1 Product Name: {self.device1.get_product_name()}\nMFC_1 Article Code: {self.device1.get_article_code()}')

            setup_2 = ShdlcSerialPort(port=port2_mfc, baudrate=115200)
            self.device2 = Sfc5xxxShdlcDevice(ShdlcConnection(setup_2), slave_address=0)
            self.unit2 = Sfc5xxxMediumUnit( # define the unit of flow as sccm(cubic centimeters(milliliters) per min)
                Sfc5xxxUnitPrefix.MILLI,
                Sfc5xxxUnit.STANDARD_LITER,
                Sfc5xxxUnitTimeBase.MINUTE
            )
            self.device2.set_user_defined_medium_unit(self.unit2)
            print(f'MFC_2 Serial Number: {self.device2.get_serial_number()}\nMFC_2 Product Name: {self.device2.get_product_name()}\nMFC_2 Article Code: {self.device2.get_article_code()}')
        
        except Exception as e:
            print(f"Failed to connect to the MFCs: {e}")
            sys.exit(1)

    def set_value_MFC1(self, val):
        print(f"Setting MFC1 flow rate to {val} sccm")
        self.device1.set_setpoint(val, Sfc5xxxScaling.USER_DEFINED)  # Directly set the value without conversion
        
    def set_value_MFC2(self, val):
        print(f"Setting MFC2 flow rate to {val} sccm")
        self.device2.set_setpoint(val, Sfc5xxxScaling.USER_DEFINED)  # Directly set the value without conversion
        
    def exit_procedure(self):
        self.set_value_MFC1(0)  # Stop flow by setting MFC1 to 0
        self.set_value_MFC2(0) 
        print("Exiting and setting flow rate to 0 for both MFCs")

    def run(self, original_flow_rates, FM_timestamps, output_file, lookahead_steps = 1, overshoot_threshold = 500, overshoot_factor = 1.1):
        records = []
        
        # Convert FM_timestamps to numeric values in sec
        FM_timestamps = pd.to_datetime(FM_timestamps, format='%Y-%m-%d %H:%M:%S.%f')
        
        # Use the first timestamp as the start time
        FM_start_time = FM_timestamps[0]
        
        # Calculate elapsed time in sec from FM_timestamps
        elapsed_times_from_FM = (FM_timestamps - FM_start_time).total_seconds()
        
        # Record the real start time for tracking real elapsed time
        start_time = time.time()
        
        for idx, (rate, elapsed_time_FM) in enumerate(zip(original_flow_rates, elapsed_times_from_FM)):
            # Check missing or "Not a Number" values in the datasheet; Return True if the value is NaN. then Skip this iteration 
            if pd.isna(rate) or pd.isna(elapsed_time_FM):
                print(f"Skipping invalid data: rate={rate}, elapsed_time_FM = {elapsed_time_FM}")
                continue
            
            if rate < 0:
                print(f"Flow rate {rate} ccm is negative. Setting it to 0")
                rate = 0
                
            if rate > 20000:
                print(f"Flow rate {rate} ccm is above 20000. Setting it to 20000")
                rate = 20000
            
            # --- Predictive Control Logic ---
            # Look ahead into the future flow rate
            if idx + lookahead_steps < len(original_flow_rates):
                predicted_rate = original_flow_rates[idx + lookahead_steps]
                print(f"Predicted future rate: {predicted_rate} ccm")
            else:
                predicted_rate = rate #If near the end of the list, use the current rate
            
            # --- Overshoot Compensation ---
            # Check if the difference between current and predicted rate is above the threshold
            if abs(predicted_rate - rate) > overshoot_threshold:
                overshoot_rate = predicted_rate * overshoot_factor
                print(f"Applying overshoot: predicted = {predicted_rate} ccm, overshoot = {overshoot_rate} ccm")
                MFC1_flow = overshoot_rate / 2 
                MFC2_flow = overshoot_rate / 2
            else:
                # Split the flow rate into two MFCs
                MFC1_flow = predicted_rate / 2 
                MFC2_flow = predicted_rate / 2
                print(f"Original flow rate: {predicted_rate} ccm | MFC1: {MFC1_flow} ccm | MFC2: {MFC2_flow}")         
        
            # Calculate the real elapsed time from MFC since start
            real_elapsed_time = time.time() - start_time
            time_difference = elapsed_time_FM - real_elapsed_time
            # Ensure we stay on track with elapsed_time_FM (input time)
            if time_difference > 0:
                time.sleep(time_difference)  # wait the required amount of time to match elapsed_time_FM
            else:
                print(f"Real time is ahead by {-time_difference:.2f} seconds, skipping wait.")

            # print(f"Attempting to set flow rate: {rate} sccm at {real_elapsed_time: .2f} seconds")
            self.set_value_MFC1(MFC1_flow)
            self.set_value_MFC2(MFC2_flow)
            
            # time.sleep(0.05)  # 20Hz reading-data speed
            
            # Measure the actual flow from both MFCs with proper scaling
            actual_flow_MFC1 = self.device1.read_measured_value(Sfc5xxxScaling.USER_DEFINED)
            actual_flow_MFC2 = self.device2.read_measured_value(Sfc5xxxScaling.USER_DEFINED)
            combined_actual_flow = actual_flow_MFC1 + actual_flow_MFC2
            
            # .strftime() stands for "string format time", which format a datetime object into string
            real_time_timestamp_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            print(f'Measured combined: {combined_actual_flow} sccm | Elapsed Time from MFC: {real_elapsed_time:.2f} s | Elapsed Time from FM: {elapsed_time_FM: .2f} s')
            
            records.append({
                "timestamp": real_time_timestamp_string,
                "elapsed_time_from_MFC": round(real_elapsed_time, 2),  # Elapsed time in sec, round to 2 decimals
                "elapsed_time_from_FM": round(elapsed_time_FM, 2),
                "input_breath_flow": rate,
                "measured_combined_flow_rate": combined_actual_flow,
                "measure_flow_rate_MFC1": actual_flow_MFC1,
                "measured_flow_rate_MFC2": actual_flow_MFC2
            })
        
        # Save the results to CSV
        df = pd.DataFrame(records)
        df.to_csv(output_file, index=False)
        print(f'Recorded flow rates saved to {output_file}')
        
        # Stop the system immediately after the last valid flow rate being read
        self.exit_procedure()

    def cleanup(self):
        """Clean up resources"""
        try:
            # Set both MFCs to 0 flow rate
            if hasattr(self, 'device1'):
                try:
                    self.device1.set_setpoint(0, Sfc5xxxScaling.USER_DEFINED)
                    if hasattr(self.device1, '_connection') and hasattr(self.device1._connection, '_port'):
                        self.device1._connection._port.close()
                except Exception as e:
                    print(f"Error cleaning up MFC1: {e}")

            if hasattr(self, 'device2'):
                try:
                    self.device2.set_setpoint(0, Sfc5xxxScaling.USER_DEFINED)
                    if hasattr(self.device2, '_connection') and hasattr(self.device2._connection, '_port'):
                        self.device2._connection._port.close()
                except Exception as e:
                    print(f"Error cleaning up MFC2: {e}")

            print("Two MFCs connections closed successfully")
            
        except Exception as e:
            print(f"Error during two MFCs cleanup: {e}")
        finally:
            # Clear device references
            self.device1 = None
            self.device2 = None

# Read CSV file
def read_flow_rates_from_csv(file_path):
    df = pd.read_csv(file_path)
    # Need to change accordingly
    if {"Measured_Flow_Rate_FM(sccm)", "Timestamp"} <= set(df.columns):
        df = df.dropna(subset=["Measured_Flow_Rate_FM(sccm)", "Timestamp"])
        return df["Measured_Flow_Rate_FM(sccm)"].tolist(), df["Timestamp"].tolist()
    else:
        raise ValueError(f"Required columns not found in {file_path}")
