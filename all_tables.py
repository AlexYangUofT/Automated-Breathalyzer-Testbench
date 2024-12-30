# Author: Alex Yang; Date: 2024-12
# This program contains all of the table that needs in the pdf
# Dictionary-based tables
# First Menu
first_menu = {
    "title": "First Menu",
    "options": [
        {"name": "New Device Test", "code": "1"},
        {"name": "Device Reprocessing", "code": "2"}
    ]
}

previous_test_table = {
    "options": [
        {"name": "Leakage of MP+BPV Table", "code": "1a"},
        {"name": "MP+BPV VOC Loss Table", "code": "1b"},
        {"name": "MP+BPV RH Reduction Table", "code": "1c"},
        {"name": "Capnogram Leakage Test Table", "code": "2"},
        {"name": "Flow Diversion Valve Leakage Test Table", "code": "3"},
        {"name": "BFU Test Table", "code": "4"},
        {"name": "System Leakage Test Table", "code": "5"},
        {"name": "System Functionality Test Table", "code": "6"},
        {"name": "Device Level Test Table", "code": "7"}
    ]
}

# Second Menu
second_menu = {
    "title": "Second Menu",
    "sections": [
        {
            "section_name": "Unit Level Testing",
            "options": [
                {"name": "Mouthpiece + BPV", "code": "1"},
                {"name": "Capnogram", "code": "2"},
                {"name": "Flow Diversion Valve", "code": "3"},
                {"name": "BFU", "code": "4"}
            ]
        },
        {
            "section_name": "Logic Level Testing",
            "options": [
                {"name": "System Leakage", "code": "5"},
                {"name": "System Functionality", "code": "6"}
            ]
        },
        {
            "section_name": "Device Level Testing",
            "options": [
                {"name": "Device Level Test", "code": "7"}
            ]
        }
    ]
}


# Define third menu data
third_menu = {
    "title": "Third Menu",
    "options": [
        {"name": "Leakage of MP+BPV %", "code": "a"},
        {"name": "VOC loss %", "code": "b"},
        {"name": "RH reduction %", "code": "c"}
    ]
}


# Define MP+BPV Test Table using Dictionary
mp_bpv = {
    "title": "Leakage of MP+BPV Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "MP + BPV Leakage %", "expected_result": "3 (From assembly doc)", "user_entry": "", "status": "P or F"}, # expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}



# Define VOC Loss Table using Dictionary
voc = {
    "title": "MP+BPV VOC Loss Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "VOC loss of MP + BPV (8 trials average for acetone) in %", "expected_result": "5 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "VOC loss of MP + BPV (8 trials average for isoprene) in %", "expected_result": "5 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}


# Define RH Reduction Table using Dictionary
rh = {
    "title": "MP+BPV RH Reduction Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "RH of MP + BPV (8 trials average) in %", "expected_result": "10 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define capnogram leakage data using Dictionary
capnogram = {
    "title": "Capnogram Leakage Test Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "Leakage of Capnogram in %", "expected_result": "3 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define Flow Diversion Valve leakage data using Dictionary
flow_diversion_valve = {
    "title": "Flow Diversion Valve Leakage Test Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "Leakage of Flow Diversion Valve in %", "expected_result": "3 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define BFU data using Dictionary
bfu = {
    "title": "BFU Test Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "Pump Flow Rate in ccm", "expected_result": "150 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Leakage of BFU in %", "expected_result": "3 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define system leakage data using Dictionary
system_leakage = {
    "title": "System Leakage Test Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "Leakage of System in %", "expected_result": "20 (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define system functionality data using Dictionary
system_functionality = {
    "title": "System Functionality Test Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "Motherboard Serial Number", "prompt": "Enter the MB serial number: ", "user_entry": ""},
        
        # CO2 sensor
        {"name": "Co2 concen.(baseline)", "expected_result": "500ppm (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Co2 concen.(CO2 flow)", "expected_result": "3300ppm (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Co2 concen.(return baseline)", "expected_result": "500ppm (From assembly doc)", "user_entry": "", "status": "P or F"},
        
        # BME sensor
        {"name": "Humidity(baseline)", "expected_result": "25% (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Temperature(baseline)", "expected_result": "27C (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Humidity(breathing)", "expected_result": "30% (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Temperature(breathing)", "expected_result": "30C (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        
        # Sensor Board
        {"name": "Sensor Board Serial Number", "expected_result": "", "user_entry": "", "status": ""},
        {"name": "Sensor Board Functionality", "expected_result": "36, 32, 2 (# of total values read, # of sensing elements, # of saturated values)", "user_entry": "", "status": "P or F"},
        {"name": "BME in Sensor Board Temperature", "expected_result": "21C (From assembly doc)", "user_entry": "", "status": "P or F"},
        {"name": "BME in Sensor Board Humidity", "expected_result": "30% (From assembly doc)", "user_entry": "", "status": "P or F"},
        
        # Limit switches
        {"name": "Limit Switch 1", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Limit Switch 2", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Limit Switch 3", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Limit Switch 4", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        
        # Servo motors
        {"name": "Servo Motor 1 (Home Position)", "expected_result": "90° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 1 (Hit Left LS)", "expected_result": "135° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 1 (Hit Right LS)", "expected_result": "45° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 2 (Home Position)", "expected_result": "90° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 2 (Hit Left LS)", "expected_result": "135° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 2 (Hit Right LS)", "expected_result": "45° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        
        # LEDs
        {"name": "LED 1 functionality", "expected_result": "PASS", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "LED 2 functionality", "expected_result": "PASS", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define device testing data using Dictionary
device_testing = {
    "title": "Device Level Test Table",
    "fields": [
        {"name": "Name", "prompt": "Type your name: ", "user_entry": ""},
        {"name": "Date", "prompt": "Enter the date (format: mm-dd-yyyy): ", "user_entry": ""},
        {"name": "Motherboard Serial Number", "prompt": "Enter the MB serial number: ", "user_entry": ""},
        
        # CO2 sensor
        {"name": "Co2 concen.(baseline)", "expected_result": "500ppm (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Co2 concen.(CO2 flow)", "expected_result": "3300ppm (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Co2 concen.(return baseline)", "expected_result": "500ppm (From assembly doc)", "user_entry": "", "status": "P or F"},
        
        # BME sensor
        {"name": "Humidity(baseline)", "expected_result": "25% (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Temperature(baseline)", "expected_result": "27C (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Humidity(breathing)", "expected_result": "30% (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Temperature(breathing)", "expected_result": "30C (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        
        # Sensor Board
        {"name": "Sensor Board Serial Number", "expected_result": "", "user_entry": "", "status": ""},
        {"name": "Sensor Board Functionality", "expected_result": "36, 32, 2 (# of total values read, # of sensing elements, # of saturated values)", "user_entry": "", "status": "P or F"},
        {"name": "BME in Sensor Board Temperature", "expected_result": "21C (From assembly doc)", "user_entry": "", "status": "P or F"},
        {"name": "BME in Sensor Board Humidity", "expected_result": "30% (From assembly doc)", "user_entry": "", "status": "P or F"},
        
        # Limit switches
        {"name": "Limit Switch 1", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Limit Switch 2", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Limit Switch 3", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Limit Switch 4", "expected_result": "0 1 0 (Unpressed, Pressed, Unpressed)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        
        # Servo motors
        {"name": "Servo Motor 1 (Home Position)", "expected_result": "90° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 1 (Hit Left LS)", "expected_result": "135° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 1 (Hit Right LS)", "expected_result": "45° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 2 (Home Position)", "expected_result": "90° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 2 (Hit Left LS)", "expected_result": "135° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Servo Motor 2 (Hit Right LS)", "expected_result": "45° (From assembly doc)", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        
        # LEDs
        {"name": "LED 1 functionality", "expected_result": "PASS", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "LED 2 functionality", "expected_result": "PASS", "user_entry": "", "status": "P or F"},# expected_result can be changed accordingly
        {"name": "Remark", "prompt": "Please comment: ", "user_entry": ""}
    ]
}

# Define input FM sample record data
# Keep in mind, only this table will be printed seperately in the display_completion.py file. Other tables will be printed by using the display_table function in the main python file also in the same format as the previous tests.
input_FM_sample_record_table = {
    "options": [
        {"name": "Alex_best_breath_sample", "code": "a"},
        {"name": "Nizar_best_breath_sample", "code": "b"},
        {"name": "Aarya_best_breath_sample", "code": "c"},
        {"name": "Robert_best_breath_sample", "code": "d"}
    ]
}