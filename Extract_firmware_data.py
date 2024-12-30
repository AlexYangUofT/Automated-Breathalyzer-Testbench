# Author: Alex Yang; Date: 2024-12
# This program is going to extract all necessary data from the Motherboard. Remainder: please flush the motherboard using the main.cpp code in the github. You can find this code in the seperate folder called "Testbench_firmware_individule_components"
# Please remember to change the port number in the "__init__" function
import serial
import time

class SensorDataExtractor:
    def __init__(self, port="COM14", baudrate=115200, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.co2_values = []  # Store individual CO2 values
        self.humidity = [] # Store 30 humidity readings from BME sensor
        self.temperature = [] # Store 30 temperature readings from BME sensor

    def send_command(self, command):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
                print(f"Opening serial port: {self.port} at {self.baudrate} baud")
                print(f"Sending command: {command}")
                ser.write((command + '\r\n').encode('utf-8'))
                
                if command.upper() == "CO2":
                    time.sleep(30)
                elif command.upper() == "BME":
                    time.sleep(40)
                elif command.upper() == "SERVO1" or command.upper() == "SERVO2":
                    time.sleep(3)
                elif command.upper() == "LS1" or command.upper() == "LS2" or command.upper() == "LS3" or command.upper() == "LS4":
                    time.sleep(2)
                elif command.upper() == "LED1" or command.upper() == "LED2":
                    time.sleep(6)
                elif command.lower() == "sensor board":
                    time.sleep(15)
                else:
                    time.sleep(2)
                
                try:
                    response = ser.read_all().decode('utf-8', errors='replace')
                    return response.strip()
                except UnicodeDecodeError:# If UTF-8 fails, try with latin-1
                    ser.reset_input_buffer()
                    response = ser.read_all().decode('latin-1')
                    print(f"Encoding error in serial data: {e}")
                    return response.strip()
                
        except serial.SerialException as e:
            print(f"Serial exception: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error sending command: {e}")
            return None

    def read_co2_data(self, command):
        # Here we need to properly parse and return the CO2 values
        if command.upper() == "CO2":
            print("Requesting CO2 data...")
            try:
                response = self.send_command(command)
                if response and response.strip():
                    print("CO2 Data Received:")
                    print(response)
                    try:
                        lines = response.split('\n')
                        self.co2_values = []  # Reset the list for new readings
                        average_co2_values = None
                        
                        for line in lines:
                            if "CO2 Value:" in line:
                                try:
                                    co2_value = float(line.split("CO2 Value:")[1].strip())
                                    self.co2_values.append(co2_value)
                                except ValueError:
                                    print(f"Could not convert CO2 value to float: {line}")
                                    continue
                                
                            elif "CO2 Average" in line:
                                try:
                                    average_co2_values = float(line.split("CO2 Average:")[1].strip())
                                except ValueError:
                                    print(f"Could not convert CO2 value to float: {line}")
                                    continue
                                
                        if self.co2_values:
                            return {
                                "values": self.co2_values,
                                "average": average_co2_values
                            }
                        else:
                            print("No valid CO2 average readings received.")
                            return None
                        
                    except (IndexError, ValueError) as e:
                        print(f"Error parsing CO2 data: {e}")
                        print(f"Raw response: {response}")
                        return None
                else:
                    print("No response received. Check if the device is connected and powered on.")
                    return None
                
            except UnicodeDecodeError as e:
                print(f"Encoding error in serial data: {e}")
                try:
                    response = self.port.read_all().decode('latin-1')
                    print(f"Attempting to parse with alternative encoding...")
                    lines = response.split('\n')
                    for line in lines:
                        if "CO2 Value:" in line:
                            try:
                                co2_value = float(line.split("CO2 Value:")[1].strip())
                                self.co2_values.append(co2_value)
                            except ValueError:
                                print(f"Could not convert CO2 value to float: {line}")
                                continue
                        elif "CO2 Average" in line:
                            try:
                                average_co2_values = float(line.split("CO2 Average:")[1].strip())
                            except ValueError:
                                print(f"Could not convert CO2 value to float: {line}")
                                continue
                        if self.co2_values:
                            return {
                                "values": self.co2_values,
                                "average": average_co2_values
                            }
                        else:
                            print("No valid CO2 average readings received.")
                            return None
                except Exception as e2:
                    print(f"Failed to parse with alternative encoding: {e2}")
                    return None
                
            except Exception as e:
                print(f"Unexpected error reading CO2 data: {e}")
                return None
        else:
            print("Invalid command. Please enter 'CO2' to test CO2 readings.")
            return None
            
    def read_BME_data(self, command):
        if command.upper() == "BME":
            print("Requesting BME data...")
            try:
                response = self.send_command(command)
                if response and response.strip():
                    print("BME Data Received:")
                    print(response)
                    try:
                        lines = response.split('\n')
                        self.humidity = []  # Reset the list for new readings
                        self.temperature = [] # Reset the list for new readings
                        avg_temp = None
                        avg_hum = None
                        
                        # Then look for the average values
                        for line in lines:
                            # streamline parsing both temperature and humidity
                            if "Reading:" in line and "Temperature:" in line and "Humidity:" in line:
                                try:
                                    # Extract temperature
                                    temp_str = line.split("Temperature:")[1].split("Humidity:")[0].strip()
                                    temp = float(temp_str)
                                    self.temperature.append(temp)
                                    # Extract humidity
                                    hum_str = line.split("Humidity:")[1].strip()
                                    hum = float(hum_str)
                                    self.humidity.append(hum)
                                except (IndexError, ValueError) as e:
                                    print(f"Error parsing 30 temperatures or 30 humidity: {e}")
                            
                            if "Average Temperature of 30 readings:" in line:
                                try:
                                    avg_temp = float(line.split("readings:")[1].strip())
                                except (IndexError, ValueError) as e:
                                    print(f"Error parsing average temperature: {e}")
                                    
                            elif "Average Humidity of 30 readings:" in line:
                                try:
                                    avg_hum = float(line.split("readings:")[1].strip())
                                except (IndexError, ValueError) as e:
                                    print(f"Error parsing average humidity: {e}")
                        
                        print(f"Extracted Temperatures: {self.temperature}")
                        print(f"Extracted Humidities: {self.humidity}")
                        
                        if self.temperature and self.humidity and avg_temp is not None and avg_hum is not None:
                            return {
                                "temperature_32": self.temperature,
                                "humidity_32": self.humidity,
                                "temperature": round(avg_temp, 2),
                                "humidity": round(avg_hum, 2)
                            }
                        else:
                            print(f"Incomplete data: Average Temp={avg_temp}, Average Humidity={avg_hum}")
                            return None
                        
                    except (IndexError, ValueError) as e:
                        print(f"Error parsing BME data: {e}")
                        print(f"Raw response: {response}")
                        return None
                else:
                    print("No response received. Check if the device is connected and powered on.")
                    return None
                
            except Exception as e:
                print(f"Unexpected error reading BME data: {e}")
                return None
        else:
            print("Invalid command. Please enter 'BME' to test BME readings.")
            return None
    
    def read_Servos_data(self, command):
        if command.upper() == "SERVO1" or command.upper() == "SERVO2":
            print(f"Requesting {command} data...")
            response = self.send_command(command)
            if response:
                print(f"{command} Data Received:")
                print(response)
                try:
                    # Look for the last line containing "Servo moved to angle"
                    lines = response.split('\n')
                    for line in reversed(lines):
                        if "Servo moved to angle" in line:
                            angle = float(line.split("angle:")[-1].strip())
                            return angle
                    print(f"Could not find angle value in response: {response}")
                    return None
                except (IndexError, ValueError) as e:
                    print(f"Error parsing servo data: {e}")
                    return None
            else:
                print("No response received. Check if the device is connected and powered on.")
                return None
        else:
            print(f"Invalid command. Please enter '{command}' to test servo readings.")
            return None
            
    def read_limit_switches_data(self, command):
        if command.upper() in ["LS1", "LS2", "LS3", "LS4"]:
            print(f"Requesting {command} data...")
            count = 0
            last_state = None
            attempts = 0
            max_attempts = 10  # Maximum number of attempts to prevent infinite loop
            
            # Continue until we've recorded 3 state changes or reached max attempts
            while count < 3 and attempts < max_attempts:
                response = self.send_command(command)
                if response:
                    try:
                        # Extract the last line of the response, which should contain the numeric state
                        lines = response.splitlines()
                        current_state = int(lines[-1].strip())
                        
                        # If this is a new state or our first reading
                        if last_state is None or current_state != last_state:
                            count += 1
                            last_state = current_state
                            print(f"State change {count}: Switch state is {current_state}")
                        
                    except ValueError as e:
                        print(f"Error parsing Limit Switch data: {e}")
                        return None, None
                else:
                    print("No response received. Check if the device is connected and powered on.")
                    return None, None
                
                attempts += 1

            return attempts, count # Return both attempts and count regardless of success or failure
        else:
            print("Invalid command. Please enter 'LS1', 'LS2', 'LS3', or 'LS4' to test Limit Switches readings.")
            return None, None
            
    def read_LEDs_data(self, command):
        if command.upper() == "LED1" or command.upper() == "LED2":
            print(f"Sending {command} command to toggle LEDs...")
            self.send_command(command)
            print(f"{command} command sent successfully")
            return True
        else:
            print("Invalid command. Please enter 'LED1' or 'LED2' to control LEDs.")
            return False
        
    def read_Sensor_Board_data(self, command):
        if command.lower() == "sensor board":
            print(f"Sending {command} command to request Sensor Board data...")
            response = self.send_command(command)
            if response and response.strip():
                print("Sensor Board Data Received:")
                print(response)
                
                # Split response into individual readings
                readings = [line for line in response.split('\n') if 'Sensor Data:' in line]
                valid_readings = []
                all_values = []
                
                print(f"\nProcessing {len(readings)} readings...")
                
                for reading in readings:
                    try:
                        # Extract the data part after "Sensor Data:"
                        data_part = reading.split('Sensor Data:')[1].strip()
                        values = [v for v in data_part.split() if v.strip()]
                        
                        # Debug output
                        print(f"\nAnalyzing reading with {len(values)} values:")
                        print(values)
                        
                        # Validation criteria
                        if len(values) == 36:
                            try:
                                all_values.append(values) # all_values has 36 values
                                
                                # Check if all values except last are numeric
                                numeric_values = [] 
                                for i in range(len(values) - 1):
                                    numeric_values.append(float(values[i])) # This numeric_values doesn't include the last value, which is the serial number. So it should has 35 values
                                
                                # Check if last value contains required format
                                if 'bsi-nz' in values[-1]: # values[-1] is the serial number
                                    valid_readings.append(numeric_values) # So the valid_readings should also have 35 values
                                    print("✓ Valid reading found")
                                else:
                                    print("✗ Invalid: Last value missing 'bsi-nz' format")
                            except ValueError:
                                print("✗ Invalid: Non-numeric values found")
                                
                        else:
                            print(f"✗ Invalid: Wrong number of values ({len(values)})")
                            
                    except Exception as e:
                        print(f"Error processing reading: {e}")
                        continue
                
                if valid_readings:
                    # Get the first valid reading (or average multiple readings if needed)
                    reading_values = valid_readings[1]  # Using second valid reading, this only contain 35 values (without serial number)
                    
                    # Extract the serial number from the last value
                    serial_number = all_values[1][-1]  # (index 1): using second valid reading; (index -1): ends at the last element
                    # Return structured data
                    
                    sensing_elements = reading_values[1:-2] #1: starts from the second element (index 1), -2: ends at the 2nd last element (index -2)
                    
                    print(f"Serial Number: {serial_number}")
                    print(f"Total Values Read: {len(all_values[1])}")
                    print(f"Total Sensing Elements: {len(all_values[1]) - 4}")
                    print(f"Actual Sensing Elements: {sensing_elements}")
                    print(f"Total Saturated Values: {sum(1 for x in reading_values[:-4] if x >= 2000000)}")
                    print(f"Temperature: {reading_values[-2]}")
                    print(f"Humidity: {reading_values[-1]}")
                    
                    return {
                        'sensor_board_serial_number': serial_number,  # Serial number
                        'total_values_read': len(all_values[1]),  # Total number of values in a valid reading
                        'total_sensing_elements': len(all_values[1]) - 4,  # Number of sensing elements (excluding temp & humidity & serial number & first value)
                        'actual_sensing_elements': sensing_elements,  # Sensing elements
                        'total_saturated_values': sum(1 for x in reading_values[:-4] if x >= 2000000),  # Count values >= 2000000
                        'temperature': reading_values[-2],  # Second to last value
                        'humidity': reading_values[-1]  # Last value
                    }
                else:
                    print("\nNo valid readings found in the response")
                    return None
            else:
                print("No response received. Check if the device is connected and powered on.")
                return None
        else:
            print("Invalid command. Please use 'sensor board' to request sensor data.")
            return None