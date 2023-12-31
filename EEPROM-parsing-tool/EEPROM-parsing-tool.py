import csv, json
import argparse
from math import comb
from pathlib import Path
from textwrap import wrap

parser = argparse.ArgumentParser()
parser.add_argument("file_path", type=Path)

p = parser.parse_args()

if p.file_path.exists():
    filepath = p.file_path
else:
    print("Error: file not found")
    programPause = input('Press <ENTER> to quit')
    exit()

temp_list = []
combined_list = []

with open(filepath) as tsv:
    for line in tsv:
        if line.split():    #Make sure line isn't empty
            temp_list.append(wrap(line, 2))      #split removes all white space characters and converts remaining to a list of two characters per item            

if all(line[0] == format(i, 'X').ljust(2, '0') for i, line in enumerate(temp_list)):  #if all of the lines have a value at the beginning that matches the line number, they are probably line numbers so drop them
    for line in temp_list:
        line.pop(0)     #Drop first value that contains the line number


for line in temp_list:
    combined_list += line

falsecount = 0
for item in combined_list[1::2]:        #Check if all odd items are zero, indicating hex data has zeros between each byte
    if bool(int(item, 16)) == False:
        falsecount += 1

if falsecount == len(combined_list[1::2]):
    print("all odd values are zero")
    for i, item in enumerate(combined_list[1::2]):
        combined_list.pop(i+1)          #This is kind of weird but it works. Deletes all the odd items after confirming they are all zero


firmware_version_hex = ''.join(combined_list[:24]) 
firmware_version = bytearray.fromhex(firmware_version_hex).decode()
output_data = {}
output_data["Firmware"] = firmware_version

total_runtime_hex = ''.join(combined_list[28:32]) 
total_runtime_seconds = round(int(total_runtime_hex, 16)* .032, 3)  #32ms per tick
output_data["Total_Runtime_Seconds"] = total_runtime_seconds

combined_list = combined_list[32:]

fault_list = []
for i in range(len(combined_list)//6):
    timestamp_ticks = ''.join(combined_list[2:6]) 
    timestamp_seconds = round(int(timestamp_ticks, 16)* .032, 3)  #32ms per tick

    error_code_hex = ''.join(combined_list[:2]),
    error_code_hex = error_code_hex[0]
    error_code_binary = str(bin(int(error_code_hex, 16)))[2:].zfill(16)
    error_bits = list(error_code_binary)

    error_meaning = []
    if error_bits[0] == "1":
        error_meaning.append("ISL_INT_OVERTEMP_FLAG")
    if error_bits[1] == "1":
        error_meaning.append("ISL_EXT_OVERTEMP_FLAG")
    if error_bits[2] == "1":
        error_meaning.append("ISL_INT_OVERTEMP_PICREAD")
    if error_bits[3] == "1":
        error_meaning.append("THERMISTOR_OVERTEMP_PICREAD")
    if error_bits[4] == "1":
        error_meaning.append("UNDERTEMP_FLAG")
    if error_bits[5] == "1":
        error_meaning.append("CHARGE_OC_FLAG")
    if error_bits[6] == "1":
        error_meaning.append("DISCHARGE_OC_FLAG")
    if error_bits[7] == "1":
        error_meaning.append("DISCHARGE_SC_FLAG")

    if error_bits[8] == "1":
        error_meaning.append("DISCHARGE_OC_SHUNT_PICREAD")
    if error_bits[9] == "1":
        error_meaning.append("CHARGE_ISL_INT_OVERTEMP_PICREAD")
    if error_bits[10] == "1":
        error_meaning.append("CHARGE_THERMISTOR_OVERTEMP_PICREAD")
    if error_bits[11] == "1":
        error_meaning.append("TEMP_HYSTERESIS")
    if error_bits[12] == "1":
        error_meaning.append("ISL_BROWN_OUT")
    if error_bits[13] == "1":
        error_meaning.append("CRITICAL_I2C_ERROR")

    detect_mode = (''.join(error_bits[14:])),
    detect_mode = int(detect_mode[0], 2)
    if detect_mode == 0:
        detect_mode_text = "None"
    elif detect_mode == 1:
        detect_mode_text = "Trigger"
    elif detect_mode == 2:
        detect_mode_text = "Charger"
    else:
        detect_mode_text = ""


    error_dict = {
        "index": i,
        #"error_code": error_code_hex,
        "error_meaning": error_meaning,
        "detect_mode": detect_mode_text,
        "timestamp": timestamp_seconds
    }
    combined_list = combined_list[6:]
    if timestamp_ticks != "FFFFFFFF":
        fault_list.append(error_dict)


output_data["Faults"] = fault_list

print(json.dumps(output_data, indent=4))

programPause = input('Press <ENTER> to continue')