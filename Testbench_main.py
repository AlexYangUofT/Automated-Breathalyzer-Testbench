# Author: Alex Yang; Date: 2024-12
# You should always run this main.py program
# Please remember to change the port number in the "initialize_devices" function
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import textwrap
from reportlab.lib import colors
from all_tables import (first_menu, previous_test_table, second_menu, third_menu, mp_bpv, voc, rh, capnogram, bfu, 
                        flow_diversion_valve, system_leakage, system_functionality, device_testing, input_FM_sample_record_table)
from one_mfc_control import one_MFC
from flow_meter_record import FlowSensorSFM6000
from display_completion import TestManager
from create_pdf import create_pdf
import sys
from time import sleep
from two_MFCs_control_sampling_generator import two_MFCs
import serial.tools.list_ports as list_ports
# Initialize TestManager
test_manager = TestManager() # test again

def get_available_ports(): # List all available COM ports
    return [port.device for port in list_ports.comports()]

def initialize_devices(test_choice): # Initialize MFCs and Flow Meters based on requirements
    try:
        available_ports = get_available_ports()
        print(f"Available COM ports: {available_ports}")
        
        # Define the ports you want to use
        mfc1_port = "COM18"
        mfc2_port = "COM10"
        fm1_port = "COM12"
        fm2_port = "COM16"
        
        # Verify ports exist
        required_ports = [mfc1_port]
        if test_choice == "7":
            required_ports.append(mfc2_port)
        required_ports.extend([fm1_port, fm2_port])
        
        missing_ports = [port for port in required_ports if port not in available_ports]
        if missing_ports:
            raise Exception(f"The following required ports are not available: {missing_ports}")
        
        # Initialize devices with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                mfc = None
                flow_meter = None
                
                try:
                    if test_choice == "7":
                        print(f"Attempting to initialize two MFCs (attempt {attempt + 1}/{max_retries})")
                        mfc = two_MFCs(port1_mfc=mfc1_port, port2_mfc=mfc2_port)
                    else:
                        print(f"Attempting to initialize one MFC (attempt {attempt + 1}/{max_retries})")
                        mfc = one_MFC(port=mfc1_port)
                    
                    # Add a small delay before initializing flow meters
                    sleep(1)
                    
                    # Initialize Flow Meters
                    print(f"Attempting to initialize flow meters (attempt {attempt + 1}/{max_retries})")
                    flow_meter = FlowSensorSFM6000(port1=fm1_port, port2=fm2_port)
                    
                    return mfc, flow_meter
                    
                except Exception as e:
                    # Clean up if initialization fails
                    if mfc:
                        mfc.cleanup()
                    if flow_meter:
                        flow_meter.cleanup()
                    raise e
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    sleep(retry_delay)
                else:
                    raise Exception(f"Failed to initialize devices after {max_retries} attempts")
                    
    except Exception as e:
        print(f"Error initializing devices: {e}")
        print("Please check:")
        print("1. All devices are properly connected")
        print("2. All devices are powered on")
        print("3. The correct COM ports are being used")
        print("4. No other program is using these COM ports, especially dont open Sensirion app when running this program")
        sys.exit(1)


def main_menu():
    while True:
        device_serial_number = input("Please enter the device serial number: ").strip()
        if device_serial_number:
            break
        else:
            print("Device serial number cannot be empty. Please try again.")
    test_manager.set_device_serial_number(device_serial_number)
    # New device or old device reprocessing table
    print(tabulate([[option['name'], option['code']] for option in first_menu["options"]], headers=["Test Type", "Code"], tablefmt="grid"))
    while True:
        choice = input("Select 1 for New Device Test or 2 for Device Reprocessing: ").strip()
        if choice in ["1", "2"]: # The main menu table (contain 7 components)  
            if choice == "1":
                print("This is the test for new device, you must complete all of ULT before moving to LLT. Lastly DLT")
            elif choice == "2":
                print("This is the old device reprocessing, you can select whatever test that you want to do")
                
            while True:
                previous_completed_tests = [] # Create a list to store previous completed tests
                note = "" # Initialize the note
                previous_completed_test_yes_or_no = input("Did you do any of the testing before related to this device serial number? (y/n): ").strip().lower()
                if previous_completed_test_yes_or_no in ["y", "n"]:
                    if previous_completed_test_yes_or_no == "y":
                        print(tabulate([[opt["name"], f"code: {opt["code"]}"] for opt in previous_test_table["options"]], headers=["Test Type", "Code Number"], tablefmt="grid"))
                        valid_codes_in_list = [opt["code"].lower() for opt in previous_test_table["options"]]
                        while True:
                            previous_completed_tests_choice = input("The table above shows all main components that need to be done. Please enter the code number that indicates the test that you have done, seperated by commas: ").strip().lower()
                            # Split the input by commas to get individual codes
                            chosen_codes = [code.strip() for code in previous_completed_tests_choice.split(",")]
                            # Seperate valid and invalid code
                            invalid_enter_codes = [code for code in chosen_codes if code not in valid_codes_in_list]
                            valid_enter_codes = [code for code in chosen_codes if code in valid_codes_in_list]
                            # If there are invalid codes being prompt, reset note and prompt again
                            if invalid_enter_codes:
                                print(f"Invalid codes entered: {", ".join(invalid_enter_codes)}. Please look at the table and re-enter the code again")
                                continue # Restart the loop
                            
                            # process valid codes:
                            for code in valid_enter_codes:
                                previous_completed_tests_name = next (opt["name"] for opt in previous_test_table["options"] if opt["code"].lower() == code)
                                previous_completed_tests.append(previous_completed_tests_name)
                                print(f"Recorded completion of: {previous_completed_tests_name}")
                            if not invalid_enter_codes: # If all codes are valid, break the loop
                                note = input("Please enter a note regarding the previous tests (e.g., you should specify the exact date that you did the test, reason): ").strip()
                                break
                        if previous_completed_tests:
                            print("\nThe following tests have been recorded as completed: ")
                            for tests in previous_completed_tests:
                                print(f"- {tests}")
                        else:
                            print("No valid test codes being entered")
                    else:
                        print("Nothing has been completed previously.")
                    test_manager.set_previous_completed_tests(previous_completed_tests)
                    test_manager.set_previous_test_note(note)
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
        
        
            while True:
                print(tabulate([[section["section_name"]] + [[opt["name"], f"code: {opt["code"]}"] for opt in section["options"]] for section in second_menu["sections"]], 
                                headers=["Section", "'Test Type', 'Code Number'","'Test Type', 'Code Number'","'Test Type', 'Code Number'", "'Test Type', 'Code Number'"], tablefmt="grid"))
                test_choice = input("Right now you are in the main menu, which contains 7 sub-tests that you can do. Please enter the code to indicate which test are you planning to do: ").strip()
                
                if test_choice == "1":
                    print(tabulate([[option['name'], option['code']] for option in third_menu["options"]], headers=["Test Name", "Code"], tablefmt="grid"))
                    print("Right now you are in the details of MP+BPV section")
                    third_choice = input("Enter the code to do leakage, VOC, or RH: ").strip()
                    
                    if third_choice == "a":
                        mfc, flow_meter = initialize_devices(test_choice)
                        test_manager.display_table(mp_bpv, check_test_type=choice, mfc=mfc, flow_meter=flow_meter)
                    elif third_choice == "b":
                        test_manager.display_table(voc, check_test_type=choice, mfc=None, flow_meter=None)
                    elif third_choice == "c":
                        test_manager.display_table(rh, check_test_type=choice, mfc=None, flow_meter=None)
                    else:
                        print("Leakage(a), voc(b), or rh(c) can only be test, your entry doesn't make sense, you will be directed to main menu.")

                elif test_choice in ["2", "3", "4", "5", "7"]:
                    mfc, flow_meter = initialize_devices(test_choice)
                    if test_choice == "2":
                        test_manager.display_table(capnogram, check_test_type=choice, mfc=mfc, flow_meter=flow_meter)
                    elif test_choice == "3":
                        test_manager.display_table(flow_diversion_valve, check_test_type=choice, mfc=mfc, flow_meter=flow_meter)
                    elif test_choice == "4":
                        test_manager.display_table(bfu, check_test_type=choice, mfc=mfc, flow_meter=flow_meter)
                    elif test_choice == "5":
                        test_manager.display_table(system_leakage, check_test_type=choice, mfc=mfc, flow_meter=flow_meter)
                    elif test_choice == "7":
                        test_manager.display_table(device_testing, check_test_type=choice, mfc=mfc, flow_meter=flow_meter)
                elif test_choice == "6":
                    test_manager.display_table(system_functionality, check_test_type=choice, mfc=None, flow_meter=None)
                else:
                    print("There are only 7 tests that can be done. Ensure you enter a valid component code.")
        else:
            print("Stupid mistake! Seems like you dont want to do test! Only enter 1 or 2.")

# Calling the main function
main_menu()





