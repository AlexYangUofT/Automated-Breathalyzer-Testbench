# Author: Alex Yang; Date: 2024-12
from tabulate import tabulate
from create_pdf import create_pdf
import sys
from time import sleep
from one_mfc_control import one_MFC
from flow_meter_record import FlowSensorSFM6000
from sensirion_shdlc_driver import ShdlcSerialPort
from all_tables import (first_menu, previous_test_table, second_menu, third_menu, mp_bpv, voc, rh, capnogram, bfu, 
                        flow_diversion_valve, system_leakage, system_functionality, device_testing, input_FM_sample_record_table)
from two_MFCs_control_sampling_generator import two_MFCs
from two_MFCs_control_sampling_generator import read_flow_rates_from_csv
from datetime import datetime
from Extract_firmware_data import SensorDataExtractor
import serial
import time
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.ticker as mticker  # Import ticker for formatting
import os


class TestManager:
    def __init__(self):
        # List to store CO2 values with timestamps
        self.co2_values = {
            'baseline': [],
            'CO2 flow': [],
            'return baseline': []
        }
        
        self.temperature = {
            'baseline': [],
            'breathing': []
        }
        
        self.humidity = {
            'baseline': [],
            'breathing': []
        }
        
        self.all_test_status = {
                "Leakage of MP+BPV Table": False,
                "MP+BPV VOC Loss Table": False,
                "MP+BPV RH Reduction Table": False,
                "Capnogram Leakage Test Table": False,
                "Flow Diversion Valve Leakage Test Table": False,
                "BFU Test Table": False,
                "System Leakage Test Table": False,
                "System Functionality Test Table": False,
                "Device Level Test Table": False
                }
        self.updated_tables = []# Initialize updated_tables as an empty list
        self.device_serial_number = "" # Initialize the device serial number
        self.previous_completed_tests = [] # Initialize previous_completed_tests as an empty list. Also, initialize it as an attribute of the TestManager class
        self.previous_test_note = "" # This is the method, which does not overwtite the self.previous_test_note attribute
        self.current_mfc = None
        self.current_flow_meter = None
        
    def set_device_serial_number(self, serial_number):
        self.device_serial_number = serial_number
    
    def set_previous_completed_tests(self, completed_tests):
        # Sets the previous completed tests and marks them as completed in all_test_status
        self.previous_completed_tests = completed_tests
        for test in completed_tests:
            if test in self.all_test_status:
                self.all_test_status[test] = True
    
    def set_previous_test_note(self, note): # This is the attribute. Sets a note about previous tests.
        self.previous_test_note = note
        
    def generate_completion_summary(self, include_not_completed=True):
        not_completed = [name for name, completed in self.all_test_status.items() if not completed]
        completed = [name for name, completed in self.all_test_status.items() if completed]

        if not not_completed:
            return "Congratulations! Brother/Sister! You finished all tests. This device is ready to be shipped!"
        else:
            message = "You have completed the following tests: " + ", ".join(completed) if completed else "You have not completed any tests."
            if include_not_completed and not_completed:
                message += "\nThe following tests are still pending: " + ", ".join(not_completed)
            return message

    def cleanup_devices(self): # Clean up current device connections
        try:
            if self.current_mfc:
                self.current_mfc.cleanup()
                self.current_mfc = None
            if self.current_flow_meter:
                self.current_flow_meter.cleanup()
                self.current_flow_meter = None
        except Exception as e:
            print(f"Error during device cleanup: {e}")


    def _handle_sensor_measurement(self, sensor_type, measurement_type, field_prefix, sensor_extractor): # Handle sensor measurements
        while True: 
            confirm = input(f"Ready to measure {measurement_type} of {sensor_type}? (y/n): ").strip().lower()
            if confirm == 'n':
                print(f"Please ensure the setup of {sensor_type} is ready before continuing.")
                return False # Will exist the entire function
            elif confirm == 'y':
                break # Will exit the while loop
            else:
                print("Invalid input. Please enter 'y' for Yes or 'n' for No.")

        if sensor_type == "CO2":
            result = sensor_extractor.read_co2_data("CO2")
            unit = "ppm"
            if result is not None:
                # Store the CO2 value with a timestamp
                measurement_key = measurement_type.lower().replace(' ', '_')
                self.co2_values[measurement_key] = result["values"]
                average_co2_values = result["average"]
                
                for field in self.current_table["fields"]:
                    if field["name"] == f"{field_prefix}({measurement_type})":
                        field["user_entry"] = f"{average_co2_values:.2f}{unit}" if unit else f"{average_co2_values:.2f}"
                        expected_result = field.get("expected_result", "N/A")
                        expected_value = float(expected_result.split('(')[0].replace('ppm', '').strip())
                        
                        if measurement_type == "baseline" or measurement_type == "return baseline":
                            field["status"] = "P" if (0 <= average_co2_values <= expected_value) else "F"
                        elif measurement_type == "CO2 flow":
                            field["status"] = "P" if (expected_value <= average_co2_values) else "F"
                return True
            return False
            
        elif sensor_type == "BME":
            data = sensor_extractor.read_BME_data("BME")
            if data is not None:
                measurement_key = measurement_type.lower().replace(' ', '_')
                self.temperature[measurement_key] = data["temperature_32"]
                self.humidity[measurement_key] = data["humidity_32"]
                
                # Update both temperature and humidity fields at once
                for field in self.current_table["fields"]:
                    if field["name"] == f"Temperature({measurement_type})":
                        field["user_entry"] = f"{data['temperature']:.2f}C"
                        expected_result = field.get("expected_result", "N/A")
                        expected_value = float(expected_result.split('(')[0].replace('C', '').strip())
                        if measurement_type == "baseline":
                            field["status"] = "P" if (data['temperature'] <= expected_value) else "F"
                        elif measurement_type == "breathing":
                            field["status"] = "P" if (data['temperature'] >= expected_value) else "F"
                
                    elif field["name"] == f"Humidity({measurement_type})":
                        field["user_entry"] = f"{data['humidity']:.2f}%"
                        expected_result = field.get("expected_result", "N/A")
                        expected_value = float(expected_result.split('(')[0].replace('%', '').strip())
                        if measurement_type == "baseline":
                            field["status"] = "P" if (data['humidity'] <= expected_value) else "F"
                        elif measurement_type == "breathing":
                            field["status"] = "P" if (data['humidity'] >= expected_value) else "F"
                return True
            return False
            
        elif sensor_type.startswith("LS"):
            print(f"\nPlease follow the sequence (unpressed -> pressed -> unpressed) to the Limit Switch that you are testing in the following 10 seconds.")
            
            attempts, count = sensor_extractor.read_limit_switches_data(sensor_type)
            if count == 3:
                ls_number = sensor_type[2] # extracting a character from a string using index position. string indices start at 0
                for field in self.current_table["fields"]:
                    if field["name"] == f"Limit Switch {ls_number}":
                        field["user_entry"] = "0 1 0"
                        expected_result = field.get("expected_result", "N/A")
                        expected_value = expected_result.split('(')[0].strip()
                        field["status"] = "P" if (field["user_entry"] == expected_value) else "F"
                return True
            
            elif attempts >= 10:
                ls_number = sensor_type[2]
                print(f"Max attempts reached. Limit Switch {ls_number} may be not working properly. But we will continue the test. All fail tests will be recorded in the PDF, you can replace any failed components later.")
                for field in self.current_table["fields"]:
                    if field["name"] == f"Limit Switch {ls_number}":
                        field["user_entry"] = "FAIL"    
                        field["status"] = "F"
                return True
            else:
                print(f"Failed to complete the test for Limit Switch {ls_number}. Please try again.")
                return False
            
        elif sensor_type.startswith("SERVO"):
            value = sensor_extractor.read_Servos_data(sensor_type)
            if value is not None:
                # Map the angles to their respective fields
                angle_mapping = {
                    90: "Home Position",
                    135: "Hit Left LS",
                    45: "Hit Right LS"
                }
                
                for angle, position_name in angle_mapping.items():
                    field_name = f"Servo Motor {sensor_type[-1]} ({position_name})"
                    for field in self.current_table["fields"]:
                        if field["name"] == field_name:
                            field["user_entry"] = f"{angle}°"
                            field["status"] = "P"  # Since these are predefined angles, they should always pass
                            break
                return True
            return False
        
        elif sensor_type.startswith("LED"):
            # This command is necessary since it makes LED blink through sensor_extractor
            # field_prefix will be LED 1 or LED 2
            # sensor_type is LED1 or LED2
            # Keep in mind that the field_prefix is different from the sensor_type
            
            value = sensor_extractor.read_LEDs_data(sensor_type)
            if not value:
                print(f"Failed to read data for {sensor_type}.")
                return False
            # Then, the following command is for user to confirm if the LED is working properly
            while True:
                user_response = input(f"Does {sensor_type} display colors properly? (y/n): ").strip().lower()
                if user_response == 'n':
                    print(f"{sensor_type} is not working properly, but we will continue the test. All fail tests will be recorded in the PDF, you can replace any failed components later.")
                    for field in self.current_table["fields"]:
                        if field["name"] == f"{field_prefix} functionality":
                            field["user_entry"] = "FAIL" if user_response == 'n' else "PASS"
                            field["status"] = "P" if (field["user_entry"] == "PASS") else "F"
                    return True
                elif user_response == 'y':
                    for field in self.current_table["fields"]:
                        if field["name"] == f"{field_prefix} functionality":
                            field["user_entry"] = "PASS" if user_response == 'y' else "FAIL"
                            field["status"] = "P" if (field["user_entry"] == "PASS") else "F"
                    return True
                else:
                    print("Invalid input. Please enter 'y' for Yes or 'n' for No.")
                    
        elif sensor_type == "sensor board":
            data = sensor_extractor.read_Sensor_Board_data("sensor board")
            if data:
                # Check if sensing_elements exists in data and has valid values
                if 'actual_sensing_elements' not in data or not data['actual_sensing_elements']:
                    print("Note: No sensing elements data available - skipping chart generation")
                    sensing_elements_chart = None
                else:
                    # Generate the sensing elements chart
                    sensing_elements_chart = self.generate_sensing_elements_chart(data['actual_sensing_elements'])
                
                for field in self.current_table["fields"]:
                    if field["name"] == f"Sensor Board Serial Number":
                        field["user_entry"] = f"{data['sensor_board_serial_number']}"

                    elif field["name"] == f"Sensor Board Functionality":
                        field["user_entry"] = f"{data['total_values_read']}, {data['total_sensing_elements']}, {data['total_saturated_values']}"
                        expected_result = field.get("expected_result", "N/A")
                        # Split both expected and actual values into lists of integers
                        expected_values = [int(x.strip()) for x in expected_result.split('(')[0].strip().split(',')]
                        actual_values = [int(x.strip()) for x in field["user_entry"].split(',')]
                        # Check first two numbers must be equal
                        first_two_match = actual_values[:2] == expected_values[:2]
                        # Check last number can be smaller than or equal to expected
                        last_number_valid = actual_values[2] <= expected_values[2]
                        field["status"] = "P" if (first_two_match and last_number_valid) else "F"
                    
                    elif field["name"] == f"BME in Sensor Board Temperature":
                        field["user_entry"] = f"{data['temperature']:.2f}C"
                        expected_result = field.get("expected_result", "N/A")
                        expected_value = float(expected_result.split('(')[0].replace('C', '').strip())
                        field["status"] = "P" if (data['temperature'] <= expected_value) else "F"
                        
                    elif field["name"] == f"BME in Sensor Board Humidity":
                        field["user_entry"] = f"{data['humidity']:.2f}%"
                        expected_result = field.get("expected_result", "N/A")
                        expected_value = float(expected_result.split('(')[0].replace('%', '').strip())
                        field["status"] = "P" if (data['humidity'] <= expected_value) else "F"
                
                # Only set the chart if it was successfully generated
                if sensing_elements_chart:
                    self.sensing_elements_chart = sensing_elements_chart
                return True
            return False
        else:
            print(f"Invalid sensor type: {sensor_type}")
            return False
    
    def _handle_system_functionality_test(self, table, sensor_extractor): # Handle system functionality testing
        self.current_table = table
        # sensor_type, field_prefix = test_types[choice]
        test_types = {
            "1": ("CO2", "Co2 concen."),
            "2": ("BME", "Humidity"),
            "3": ("LS", "Limit Switch"),
            "4": ("Servo", "Servo"),
            "5": ("LED", "LED"),
            "6": ("Sensor Board", "Sensor Board")
        }

        while True:
            print("\nAvailable tests:")
            print("1. CO2 Sensor")
            print("2. BME Sensor")
            print("3. Limit Switches")
            print("4. Servo Motors")
            print("5. LEDs")
            print("6. Sensor Board")
            print("7. Complete Testing")
            
            choice = input("Enter test number (or 'q' to quit): ").strip().lower()
            if choice == 'q':
                break # Exits the while loop completely and ask user to input their name, date, MB serial number, remark
                
            if choice == "7":
                # Except name, date, MB serial number, remark, all other fields must be filled
                all_fields_filled = all(
                    field.get("user_entry")
                    for field in table["fields"]
                    if field["name"] not in ["Name", "Date", "Motherboard Serial Number", "Remark"]
                )
                if all_fields_filled:
                    print("Congratulations! All system functionality tests completed successfully. You can either choose to continue the rest of the tests or quit the program to fix the issues.")
                    break # Exits the while loop completely and ask user to input their name, date, MB serial number, remark
                print("Not all tests have been completed. Please complete all tests.")
                continue # Repeat the while loop, back to the test selection menu

            if choice in test_types:
                sensor_type, field_prefix = test_types[choice]
                
                if choice == "1":  # CO2 sensor
                    measurements = ["baseline", "CO2 flow", "return baseline"]
                    for measurement in measurements:
                        if not self._handle_sensor_measurement(sensor_type, measurement, field_prefix, sensor_extractor):
                            break # Exits the for loop completely
                    continue # Return to test selection menu
                        
                elif choice == "2":  # BME sensor
                    print("\nBME Sensor Testing:")
                    print("1. First reading - Baseline")
                    print("2. Second reading - Breathing")
                    
                    # First reading - Baseline
                    if not self._handle_sensor_measurement("BME", "baseline", "BME", sensor_extractor):
                        print("Failed to complete the baseline reading of BME sensor.")
                        continue # Repeat the while loop, back to the test selection menu
                    
                    # Second reading - Breathing
                    if not self._handle_sensor_measurement("BME", "breathing", "BME", sensor_extractor):
                        print("Failed to complete the breathing reading of BME sensor.")
                        continue # Repeat the while loop, back to the test selection menu
                    continue # Return to test selection menu
                    
                elif choice == "3":  # Limit switches
                    # The following code is for testing all Limit Switches.
                    for ls_num in range(1, 5):
                        if not self._handle_sensor_measurement(f"LS{ls_num}", "unpressed -> pressed -> unpressed", f"Limit Switch {ls_num}", sensor_extractor):
                            print(f"Failed to complete the test for LS{ls_num}. Please try again.")
                            break # Exits the for loop completely
                    else:
                        print("All Limit Switches tests completed successfully.")
                    continue # Return to test selection menu
                            
                elif choice == "4":  # Servo
                    if not self._handle_sensor_measurement("SERVO1", "home -> hit left LS -> hit right LS", "SERVO1", sensor_extractor):
                        print("Failed to complete Servo Motor 1 testing")
                        continue # Repeat the while loop, back to the test selection menu
                    
                    if not self._handle_sensor_measurement("SERVO2", "home -> hit left LS -> hit right LS", "SERVO2", sensor_extractor):
                        print("Failed to complete Servo Motor 2 testing")
                        continue # Repeat the while loop, back to the test selection menu
                    continue # Return to test selection menu
                            
                elif choice == "5":  # LEDs
                    for led_num in range(1, 3): #Testing LED 1 and LED 2
                        if not self._handle_sensor_measurement(f"LED{led_num}", "blinking sequence", f"LED {led_num}", sensor_extractor):
                            break # Exits the for loop completely
                    continue # Return to test selection menu
                
                elif choice == "6":  # Sensor Board
                    print("\nThe program will collect 10 rounds of raw sensor data and analyze each of them. But only the second valid reading will be used for the test.")
                    if not self._handle_sensor_measurement("sensor board", "reading", "Sensor Board", sensor_extractor):
                        print("Failed to complete the test for Sensor Board. Please try again.")
                        continue # Repeat the while loop, back to the test selection menu
                    continue # Return to test selection menu
                
            else:
                print("Invalid test number. Please follow the instruction menu and try again.")
                continue # Repeat the while loop, back to the test selection menu
                            
        return True
    
    def _handle_device_level_test(self, table, sensor_extractor, mfc):
        self.current_table = table
        # sensor_type, field_prefix = test_types[choice]
        test_types = {
            "1": ("CO2", "Co2 concen."),
            "2": ("BME", "Humidity"),
            "3": ("LS", "Limit Switch"),
            "4": ("Servo", "Servo"),
            "5": ("LED", "LED"),
            "6": ("Sensor Board", "Sensor Board")
        }

        while True:
            print("\nAvailable tests:")
            print("1. CO2 Sensor")
            print("2. BME Sensor")
            print("3. Limit Switches")
            print("4. Servo Motors")
            print("5. LEDs")
            print("6. Sensor Board")
            print("7. Complete Testing")
            
            choice = input("Enter test number (or 'q' to quit): ").strip().lower()
            if choice == 'q':
                break # Exits the while loop completely and ask user to input their name, date, MB serial number, remark
                
            if choice == "7":
                # Except name, date, MB serial number, remark, all other fields must be filled
                all_fields_filled = all(
                    field.get("user_entry")
                    for field in table["fields"]
                    if field["name"] not in ["Name", "Date", "Motherboard Serial Number", "Remark"]
                )
                if all_fields_filled:
                    print("Congratulations! All system functionality tests completed successfully. You can either choose to continue the rest of the tests or quit the program to fix the issues.")
                    break # Exits the while loop completely and ask user to input their name, date, MB serial number, remark
                print("Not all tests have been completed. Please complete all tests.")
                continue # Repeat the while loop, back to the test selection menu

            if choice in test_types:
                sensor_type, field_prefix = test_types[choice]
                
                if choice == "1":  # CO2 sensor
                    # First do baseline measurement
                    if not self._handle_sensor_measurement(sensor_type, "baseline", field_prefix, sensor_extractor):
                        print("Failed to complete the baseline measurement of CO2 sensor.")
                        continue # Repeat the while loop, back to the test selection menu
                    
                    while True:
                        #Ask user to proceed with the breath sample selection
                        proceed = input("Do you want to proceed with the breath sample selection? (y/n): ").strip().lower()
                        if proceed == "y":
                            # Ask user to select the breath sample
                            self.handle_two_mfc_test(mfc)
                            break # Exits the while loop completely and goto CO2 flow and return baseline test
                        elif proceed == "n":
                            print("Just remaind you that you choose not to use any analyte for the CO2 sensor testing. Your test will continue without using any people's breath sample analytes.")
                            break # Exits the while loop completely and goto CO2 flow and return baseline test
                        else:
                            print("Invalid input. Please enter 'y' for Yes or 'n' for No.")
                            continue # Repeat the while loop
                    
                    for measurement in ["CO2 flow", "return baseline"]:
                        if not self._handle_sensor_measurement(sensor_type, measurement, field_prefix, sensor_extractor):
                            break # Exits the for loop completely and back to the test selection menu
                    continue # Return to test selection menu
                        
                elif choice == "2":  # BME sensor
                    print("\nBME Sensor Testing:")
                    print("1. First reading - Baseline")
                    print("2. Second reading - Breathing")
                    
                    # First reading - Baseline
                    if not self._handle_sensor_measurement("BME", "baseline", "BME", sensor_extractor):
                        print("Failed to complete the baseline reading of BME sensor.")
                        continue # Repeat the while loop, back to the test selection menu
                    
                    # Ask user to proceed with the breath sample selection
                    while True:
                        proceed = input("Do you want to proceed with the breath sample selection? (y/n): ").strip().lower()
                        if proceed == "y":
                            # Ask user to select the breath sample
                            self.handle_two_mfc_test(mfc)
                            break
                        elif proceed == "n":
                            print("Just remaind you that you choose not to use any analyte for the BME sensor testing. Your test will continue without using any people's breath sample analytes.")
                            break
                        else:
                            print("Invalid input. Please enter 'y' for Yes or 'n' for No.")
                            continue
                    
                    # Second reading - Breathing
                    if not self._handle_sensor_measurement("BME", "breathing", "BME", sensor_extractor):
                        print("Failed to complete the breathing reading of BME sensor.")
                        continue # Repeat the while loop, back to the test selection menu (we not using break because there is no for loop)
                    continue # Return to test selection menu
                    
                elif choice == "3":  # Limit switches
                    # The following code is for testing all Limit Switches.
                    for ls_num in range(1, 5):
                        if not self._handle_sensor_measurement(f"LS{ls_num}", "unpressed -> pressed -> unpressed", f"Limit Switch {ls_num}", sensor_extractor):
                            print(f"Failed to complete the test for LS{ls_num}. Please try again.")
                            break # Exits the for loop completely
                    else:
                        print("All Limit Switches tests completed successfully.")
                    continue # Return to test selection menu
                            
                elif choice == "4":  # Servo
                    if not self._handle_sensor_measurement("SERVO1", "home -> hit left LS -> hit right LS", "SERVO1", sensor_extractor):
                        print("Failed to complete Servo Motor 1 testing")
                        continue # Repeat the while loop, back to the test selection menu
                    
                    if not self._handle_sensor_measurement("SERVO2", "home -> hit left LS -> hit right LS", "SERVO2", sensor_extractor):
                        print("Failed to complete Servo Motor 2 testing")
                        continue # Repeat the while loop, back to the test selection menu
                    continue # Return to test selection menu
                            
                elif choice == "5":  # LEDs
                    for led_num in range(1, 3): #Testing LED 1 and LED 2
                        if not self._handle_sensor_measurement(f"LED{led_num}", "blinking sequence", f"LED {led_num}", sensor_extractor):
                            break # Exits the for loop completely
                    continue # Return to test selection menu
                
                elif choice == "6":  # Sensor Board
                    print("\nThe program will collect 10 rounds of raw sensor data and analyze each of them. But only the second valid reading will be used for analysis.")
                    if not self._handle_sensor_measurement("sensor board", "reading", "Sensor Board", sensor_extractor):
                        print("Failed to complete the test for Sensor Board. Please try again.")
                        continue # Repeat the while loop, back to the test selection menu
                    continue # Return to test selection menu, back to the test selection menu
                
            else:
                print("Invalid test number. Please follow the instruction menu and try again.")
                continue # Repeat the while loop, back to the test selection menu
                            
        return True
    
    def handle_two_mfc_test(self, mfc):
        try:
            # Define file paths
                file_paths = {
                    "a": "C:/Users/jiawei.yang/Desktop/Noze/projects/product testing/product-testing/Breath_Sample_Data/Updated_samples_data/FM input/Alex_breath_1.csv",
                    "b": "C:/Users/jiawei.yang/Desktop/Noze/projects/product testing/product-testing/Breath_Sample_Data/Updated_samples_data/FM input/Nizar_breath_1.csv",
                    "c": "C:/Users/jiawei.yang/Desktop/Noze/projects/product testing/product-testing/Breath_Sample_Data/Updated_samples_data/FM input/Aarya_breath_1.csv",
                    "d": "C:/Users/jiawei.yang/Desktop/Noze/projects/product testing/product-testing/Breath_Sample_Data/Updated_samples_data/FM input/Robert_breath_1.csv"
                }
                
                # only this table will be printed seperately in the display_completion.py file. Other tables will be printed by using the display_table function in the main python file also in the same format as the previous tests.
                print("\nAvailable breath sample files:")
                print(tabulate([[option['name'], option['code']] for option in input_FM_sample_record_table["options"]], 
                                headers=["Sample Name", "Code"], 
                                tablefmt="grid"))
                
                file_path = None # Initialize the file path variable
                
                while not file_path:
                    sample_choice = input("Please enter the code of the breath sample you want to use or directly copy paste the path of the input CSV file here: ").strip()
                    
                    print(f"User input: '{sample_choice}'")  # Debugging
                    
                    if sample_choice in file_paths:
                        file_path = file_paths[sample_choice]
                    elif os.path.isfile(sample_choice):# Check if the input is a valid file path
                        file_path = os.path.abspath(sample_choice) # Get the absolute path for consistency
                    else:
                        print(f"Invalid code or file path: : {sample_choice}. Please try again.")
                        if not os.path.exists(sample_choice):
                            print(f"The file path '{sample_choice}' does not exist.")

                # Generate output filename with timestamp
                output_file = f"2MFCs_breath_sample_output.csv"
                
                # Read flow rates and timestamps from the file
                flow_rates, FM_timestamps = read_flow_rates_from_csv(file_path)
                
                # Run MFC with input data
                mfc.run(flow_rates, FM_timestamps, output_file)
        except Exception as e:
            print(f"Error during two MFCs test: {e}")
            return
    
    # Function to display a table and capture user inputs
    def display_table(self, table, check_test_type, mfc, flow_meter):
        # Store the current devices
        self.current_mfc = mfc
        self.current_flow_meter = flow_meter
        
        updated = False
        print(f"\n{table['title']}")
        
        if table['title'] == "Device Level Test Table":
            try:
                sensor_extractor = SensorDataExtractor()
                updated = self._handle_device_level_test(table, sensor_extractor, mfc)
            except Exception as e:
                print(f"Error during device level test: {e}")
                return
            
            for field in table["fields"]:
                if field["name"] not in [
                    "Co2 concen.(baseline)",
                    "Co2 concen.(CO2 flow)",
                    "Co2 concen.(return baseline)",
                    "Humidity(baseline)",
                    "Temperature(baseline)",
                    "Humidity(breathing)",
                    "Temperature(breathing)",
                    "Sensor Board Serial Number",
                    "Sensor Board Functionality",
                    "BME in Sensor Board Temperature",
                    "BME in Sensor Board Humidity",
                    "Limit Switch 1",
                    "Limit Switch 2",
                    "Limit Switch 3",
                    "Limit Switch 4",
                    "Servo Motor 1 (Home Position)",
                    "Servo Motor 1 (Hit Left LS)",
                    "Servo Motor 1 (Hit Right LS)",
                    "Servo Motor 2 (Home Position)",
                    "Servo Motor 2 (Hit Left LS)",
                    "Servo Motor 2 (Hit Right LS)",
                    "LED 1 functionality",
                    "LED 2 functionality"
                    ]:
                    if "prompt" in field:
                        field["user_entry"] = input(field["prompt"])
                    else:
                        field["user_entry"] = input(f"Enter value for {field['name']}: ")
                updated = True
        
        elif table['title'] == "System Functionality Test Table":
            try:
                sensor_extractor = SensorDataExtractor()
                updated = self._handle_system_functionality_test(table, sensor_extractor)
            except Exception as e:
                print(f"Error during system functionality test: {e}")
                return
            
            for field in table["fields"]:
                if field["name"] not in [
                    "Co2 concen.(baseline)",
                    "Co2 concen.(CO2 flow)",
                    "Co2 concen.(return baseline)",
                    "Humidity(baseline)",
                    "Temperature(baseline)",
                    "Humidity(breathing)",
                    "Temperature(breathing)",
                    "Sensor Board Serial Number",
                    "Sensor Board Functionality",
                    "BME in Sensor Board Temperature",
                    "BME in Sensor Board Humidity",
                    "Limit Switch 1",
                    "Limit Switch 2",
                    "Limit Switch 3",
                    "Limit Switch 4",
                    "Servo Motor 1 (Home Position)",
                    "Servo Motor 1 (Hit Left LS)",
                    "Servo Motor 1 (Hit Right LS)",
                    "Servo Motor 2 (Home Position)",
                    "Servo Motor 2 (Hit Left LS)",
                    "Servo Motor 2 (Hit Right LS)",
                    "LED 1 functionality",
                    "LED 2 functionality"
                    ]:
                    if "prompt" in field:
                        field["user_entry"] = input(field["prompt"])
                    else:
                        field["user_entry"] = input(f"Enter value for {field['name']}: ")
                updated = True

        else:       
            if table['title'] in [
                "Leakage of MP+BPV Table",
                "Capnogram Leakage Test Table",
                "Flow Diversion Valve Leakage Test Table",
                "BFU Test Table",
                "System Leakage Test Table"
                ]:
                # Ask the user to input the desired flow rate for the MFC
                while True:
                    try:
                        flow_rate = int(input("Enter the desired flow rate for the MFC (in ccm): "))
                        if flow_rate < 0:
                            print("Flow rate must be non-negative. Please try again.")
                            continue
                        break
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                # Ask the user to input the desired duration for data collection
                while True:
                    try:
                        duration = float(input("Enter the desired duration for data collection (in seconds): "))
                        if duration <= 0:
                            print("Duration must be a positive number. Please try again.")
                            continue
                        break
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
                
                # Ask the user to confirm the setup before outputing the flow rate of the MFC
                while True:
                    setup_ready = input("Please ensure that the setup is ready. Is the setup ready? (y/n): ").strip().lower()
                    if setup_ready not in ['y', 'n']:
                        print("Invalid input. Please enter 'y' for Yes or 'n' for No.")
                        continue
                    if setup_ready == 'n':
                        print("Please ensure that the setup is ready before continuing.")
                        continue
                    break
                
                # Set the flow rate on the MFC
                print(f"Setting MFC to output a flow rate of {flow_rate} ccm...")
                try:
                    mfc.set_value(flow_rate)
                except Exception as e:
                    print(f"Failed to set flow rate on the MFC: {e}")
                    sys.exit(1)

                # File to save flow meter data
                filename = "flow_meter_data.csv"

                # Collect data from the flow meter
                try:
                    print(f"Collecting data for {duration} seconds")
                    flow_rates_1, flow_rates_2 = flow_meter.collect_flow_data_with_duration(filename, duration)
                    # Calculate the average flow rate
                    average_flow_rate_1 = flow_meter.calculate_average_flow_rate(flow_rates_1)
                    average_flow_rate_2 = flow_meter.calculate_average_flow_rate(flow_rates_2)
                    
                    print(f"The average flow rate recorded by FM 1 during the duration is: {average_flow_rate_1:.2f} sccm")
                    print(f"The average flow rate recorded by FM 2 during the duration is: {average_flow_rate_2:.2f} sccm")
                    
                    true_false_cal = abs((1 - (average_flow_rate_2 / average_flow_rate_1)) * 100)
                    # Find the field with the leakage percentage and get its expected_result
                    for field in table["fields"]:
                        if field["name"] in [
                            "MP + BPV Leakage %",
                            "Leakage of Capnogram in %",
                            "Leakage of Flow Diversion Valve in %",
                            "Pump Flow Rate in ccm",
                            "Leakage of BFU in %",
                            "Leakage of System in %"
                            ]:
                            if field["name"] != "Pump Flow Rate in ccm":
                                expected_result = field.get("expected_result", "N/A")
                                expected_result_value = float(expected_result.split('(')[0])
                                status = "P" if 0 <= true_false_cal <= expected_result_value else "F"
                                print(f"Expected Result in {table['title']} for {field['name']}: {expected_result}, and the value that we get is: {true_false_cal:.2f} in percentage, it is considered as {status}")
                            else:
                                expected_result = field.get("expected_result", "N/A")
                                expected_result_value = float(expected_result.split('(')[0])
                                status = "P" if (expected_result_value - 10) <= average_flow_rate_1 <= (expected_result_value + 10) else "F"
                                print(f"Expected Result in {table['title']} for {field['name']}: {expected_result}, and the value that we get is: {average_flow_rate_1:.2f} in ccm, it is considered as {status}")
                                
                    # Turn off the MFC after data collection
                    try:
                        mfc.set_value(0)  # Set the flow rate to 0 to turn off the MFC
                    except Exception as e:
                        print(f"Failed to shut down the MFC: {e}")
                    print(f"Data collection complete. Data saved to {filename}.")

                    # Automatically set the true_false_cal in the user_entry field and status in the status field
                    for field in table["fields"]:
                        # Check if the field is not a leakage percentage field
                        if field["name"] not in [
                            "MP + BPV Leakage %",
                            "Leakage of Capnogram in %",
                            "Leakage of Flow Diversion Valve in %",
                            "Leakage of BFU in %",
                            "Pump Flow Rate in ccm",
                            "Leakage of System in %"
                            ]:
                            # Prompt for name, date, and remark
                            if "prompt" in field:
                                field["user_entry"] = input(field["prompt"])
                            else:
                                field["user_entry"] = input(f"Enter value for {field['name']}: ")
                            updated = True
                        else:
                            if "expected_result" in field:
                                # Extract and convert the expected_result to a float
                                expected_result_value = float(field["expected_result"].split('(')[0])
                                # Compare true_false_cal with the expected result
                                field["status"] = "P" if 0 <= true_false_cal <= expected_result_value else "F"
                                field["user_entry"] = f"{true_false_cal:.2f}"
                                
                                if field["name"] in ["Pump Flow Rate in ccm"]:
                                    expected_result_value = float(field["expected_result"].split('(')[0])
                                    field["status"] = "P" if (expected_result_value - 10) <= average_flow_rate_1 <= (expected_result_value + 10) else "F"
                                    field["user_entry"] = f"{average_flow_rate_1:.2f}"       
                            updated = True
                except Exception as e:
                    print(f"Error during flow meter data recording: {e}")
                    sys.exit(1)
        
            else:
                for field in table["fields"]:
                    # Use "prompt" to show the message to the user
                    if "user_entry" in field:
                        prompt_message = field.get("prompt") or f"Enter value for {field['name']}: "
                        entry = input(prompt_message)
                        if entry:
                            field["user_entry"] = entry
                            updated = True

                    # If there's a status (like Pass/Fail), prompt for it separately
                    if "status" in field:
                        status_input = input(f"Enter 'P' for Pass or 'F' for Fail for {field['name']}: ").strip().upper()
                        if status_input in ["P", "F"]:  # Only update for valid inputs
                            field["status"] = status_input
                            updated = True

        # If the table was updated, add it to the list of updated tables
        if updated:
            self.updated_tables.append({
                "title": table['title'],
                "fields": table["fields"]
            })

        print("\nUpdated Table:")
        for field in table["fields"]:
            if field.get("status"):
                print(f"{field['name']}: {field.get('user_entry', '')} | Status: {field.get('status', '')}")
            else:
                print(f"{field['name']}: {field.get('user_entry', '')}")

        # Mark the table as completed in all_test_status
        self.all_test_status[table["title"]] = True

        if check_test_type == "1":
            completion_summary = self.check_all_tests_completion_1()
        elif check_test_type == "2":
            completion_summary = self.check_all_tests_completion_2()
        else:
            raise ValueError("Invalid check_test_type. Use '1' for new device or '2' for reprocessing.")

        # Ask the user if they want to end the test
        whether_end_test = input("Do you want to end the test? (Y/N): ").strip().lower()
        if whether_end_test == 'y':
            chart_filename = self.get_all_charts()
            create_pdf("testbench_results.pdf", self.updated_tables, self.device_serial_number, completion_summary, self.previous_completed_tests, self.previous_test_note, chart_filename)
            print("Ending the test. PDF generated successfully")
            self.cleanup_devices()  # Clean up before exiting
            exit()

        # Clean up devices when done with the table
        self.cleanup_devices()

    def check_all_tests_completion_1(self):
        not_completed = [name for name, completed in self.all_test_status.items() if not completed]
        completed = [name for name, completed in self.all_test_status.items() if completed]

        if not not_completed:
            completion_summary = "You finished all tests"
        else:
            completed_message = "You have completed the following tests: " + ", ".join(completed) if completed else "You have not completed any tests."
            pending_message = "\nThe following tests are still pending: " + ", ".join(not_completed)
            completion_summary = completed_message + "\n" + pending_message
        print(completion_summary)
        return completion_summary
            
    def check_all_tests_completion_2(self):
        completed = [name for name, completed in self.all_test_status.items() if completed]

        if completed:
            completed_message = "You have completed the following tests: " + ", ".join(completed) if completed else "You have not completed any tests."
        else:
            print("You have not completed any tests.")
        print(completed_message)
        return completed_message

    def generate_co2_chart(self):
        if not any(self.co2_values.values()):
            return None

        chart_filenames = []
        
        # Clean up the data structure by removing duplicate keys
        cleaned_values = {
            'baseline': self.co2_values.get('baseline', []),
            'CO2 flow': self.co2_values.get('CO2 flow', []) or self.co2_values.get('co2_flow', []),
            'return baseline': self.co2_values.get('return baseline', []) or self.co2_values.get('return_baseline', [])
        }
        
        # Make sure these keys match exactly with the cleaned data structure
        filename_mapping = {
            'baseline': 'baseline',
            'CO2 flow': 'co2_flow',
            'return baseline': 'return_baseline'
        }
        
        colors = {
            'baseline': 'blue',
            'CO2 flow': 'red',
            'return baseline': 'green'
        }
        
        # First generate individual charts
        for measurement_type, values in cleaned_values.items():
            if not values:
                continue
        
            plt.figure(figsize=(10, 5))
            plt.plot(range(len(values)), values, marker='o', linestyle='-')
            
            # Add value annotations to each point
            for i, value in enumerate(values):
                plt.annotate(f'{value:.0f}',
                             (i, value),
                             textcoords="offset points",
                             xytext=(0,10),
                             ha='center')
        
            title = measurement_type.replace('_', ' ').title()
            plt.title(f'CO2 Sensor {title} Data')
            plt.xlabel(f'Sample Number during {title.lower()} period')
            plt.ylabel('CO2 Value (ppm)')
            
            plt.xlim(0, len(values) - 1)
            plt.xticks(range(len(values)))
            plt.grid(True)
            plt.tight_layout()
            
            filename = f"co2_sensor_{filename_mapping[measurement_type]}_chart.png"
            plt.savefig(filename)
            plt.close()
            chart_filenames.append(filename)

        # Generate combined chart
        plt.figure(figsize=(12, 6))
        
        for measurement_type, values in cleaned_values.items():
            if not values:
                continue
        
            plt.plot(range(len(values)), values, 
                    marker='o', 
                    linestyle='-', 
                    label=measurement_type.replace('_', ' ').title(),
                    color=colors[measurement_type])

            # Add value annotations to each point
            for i, value in enumerate(values):
                plt.annotate(f'{value:.0f}',
                             (i, value),
                             textcoords="offset points",
                             xytext=(0,10),
                             ha='center',
                             color=colors[measurement_type])
        
        plt.title('Combined CO2 Sensor including baseline, CO2 flow, and return baseline')
        plt.xlabel('Sample Number')
        plt.ylabel('CO2 Value (ppm)')
        # Check for labeled artists before adding a legend
        if plt.gca().get_legend_handles_labels()[0]:
            plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        combined_filename = "co2_sensor_combined_chart.png"
        plt.savefig(combined_filename)
        plt.close()
        
        chart_filenames.append(combined_filename)
        
        return chart_filenames
    
    def generate_sensing_elements_chart(self, sensing_elements):
        if not sensing_elements:
            return None
        
        plt.figure(figsize=(14, 7))
        x_values = range(1, len(sensing_elements) + 1)
        
        # Create bar chart
        bars = plt.bar(x_values, sensing_elements)
        
        # Customize the chart
        plt.title('Sensing Elements Data Summary')
        plt.xlabel('Sensing Element Number')
        plt.ylabel('Value')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Set x-axis ticks to show all element numbers
        plt.xticks(x_values)
        
        # Rotate x labels for better readability
        plt.xticks(rotation=45)
        
        # Format the y-axis to show numbers directly without scientific notation
        ax = plt.gca()  # Get current axis
        ax.get_yaxis().set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))  # Format with commas and no decimals
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Add data annotations on each bar
        for bar, value in zip(bars, sensing_elements):
            plt.text(
                bar.get_x() + bar.get_width() / 2, # Center the text horizontally
                bar.get_height() + 0.02 * max(sensing_elements), # Position above the bar
                f'{value:.1f}',
                ha = 'center', # Horizontal alignment
                va = 'bottom', # Vertical alignment
                fontsize=7,  # Font size for the annotations
                color='black',  # Text color
                rotation=45 if len(sensing_elements) > 20 else 0  # Rotate annotations if many bars
            )
        
        # Save the chart
        chart_filename = "sensing_elements_chart.png"
        plt.savefig(chart_filename)
        plt.close()
        
        return chart_filename
    
    def generate_T_H_from_seperate_BME_chart(self):
        # Check for the presence of data
        if not hasattr(self, 'temperature') or not hasattr(self, 'humidity'):
            print("Temperature or Humidity data attributes are missing.")
            return None
        
        if not self.temperature and self.humidity:
            print("Temperature or Humidity data is empty.")
            return None

        chart_filenames = []
        
        # Clean up the data structure by removing duplicate keys
        data = {
            'temperature_baseline': self.temperature.get('baseline', []),
            'temperature_breathing': self.temperature.get('breathing', []),
            'humidity_baseline': self.humidity.get('baseline', []),
            'humidity_breathing': self.humidity.get('breathing', [])
        }
        
        # Debug: Print data structure
        # print("Data being processed for charts:")
        # for key, values in data.items():
            #print(f"{key}: {values[:5]}{'...' if len(values) > 5 else ''}")  # Print first 5 values for brevity
        
        colors = {
            'temperature_baseline': 'blue',
            'temperature_breathing': 'red',
            'humidity_baseline': 'green',
            'humidity_breathing': 'orange'
        }
        
        # First generate individual charts
        for key, values in data.items(): # key should be 'temperature_baseline', 'temperature_breathing', 'humidity_baseline', 'humidity_breathing'
            if not values:
                # print(f"No data for {key}, skipping chart generation.")
                continue
        
            try:
                plt.figure(figsize=(10, 5))
                
                offset = 10 if 'temperature' in key else -10  # +10 offset for temperature graphs; -10 offset for humidity graphs
                
                plt.plot(range(len(values)), values, marker='o', linestyle='-', color=colors[key])
                
                # Add value annotations to each point
                for i, value in enumerate(values):
                    plt.annotate(f'{value:.2f}',
                                (i, value),
                                textcoords="offset points",
                                xytext=(0,offset),
                                ha='center')
            
                title = key.replace('_', ' ').title()
                plt.title(f'{title} Data')
                plt.xlabel(f'Sample Number during {title.lower()} period')
                plt.ylabel('Value')
                
                plt.xlim(0, len(values) - 1)
                plt.xticks(range(len(values)))
                plt.grid(True)
                plt.tight_layout()
                
                filename = f"{key}_chart.png"
                plt.savefig(filename)
                plt.close()
                chart_filenames.append(filename)
            except Exception as e:
                print(f"Error generating chart for {key}: {e}")

        # Generate combined chart
        try:
            combined_filename = "temperature_humidity_combined_chart.png"
            has_combined_chart = False
            
            plt.figure(figsize=(12, 6))

            offsets = { # Define offsets to prevent overlaps
                'temperature_baseline': 10, # shifted 10 points above
                'temperature_breathing': -10, # 10 points below
                'humidity_baseline': 15,
                'humidity_breathing': -15
            }
            
            for key, values in data.items():
                if not values:
                    continue
            
                plt.plot(range(len(values)), values, 
                        marker='o', 
                        linestyle='-', 
                        label=key.replace('_', ' ').title(),
                        color=colors[key])
                has_combined_chart = True  # At least one dataset exists

                '''
                # Add value annotations to each point with offset
                for i, value in enumerate(values):
                    plt.annotate(f'{value:.2f}',
                                (i, value),
                                textcoords="offset points",
                                xytext=(0,offsets[key]),
                                ha='center',
                                color=colors[key])
                '''
            if has_combined_chart:
                if plt.gca().get_legend_handles_labels()[0]:
                    plt.legend()
                    
                plt.title('Combined Temperature and Humidity Data')
                plt.xlabel('Sample Number')
                plt.ylabel('value')
                plt.grid(True)
                plt.tight_layout()
            
                plt.savefig(combined_filename)
                print(f"Combined chart saved: {combined_filename}")  # Confirm combined file saved
                plt.close()
                chart_filenames.append(combined_filename)
            
        except Exception as e:
            print(f"Error generating combined chart: {e}")
        
        return chart_filenames
    
    
    def get_all_charts(self):
        chart_filenames = []
        co2_charts = self.generate_co2_chart()
        if co2_charts:
            chart_filenames.extend(co2_charts)
            
        # Get sensing elements chart if it exists
        if hasattr(self, 'sensing_elements_chart') and self.sensing_elements_chart:
            chart_filenames.append(self.sensing_elements_chart)
            
        T_H_charts = self.generate_T_H_from_seperate_BME_chart()
        # Get Temp_Humi chart if them exist
        if T_H_charts:
            chart_filenames.extend(T_H_charts)
             
        return chart_filenames
