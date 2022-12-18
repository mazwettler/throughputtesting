import json
import subprocess
import telegram_send
import time
import os
import tarfile

# Settings
runs = 5
time_between_runs = 360
server_ip = "10.0.1.10"
base_ports = {
 "iperf": 5001,
 "iperf3": 5201
 }

def ping():
    online = os.system("ping -w 10 -c 1 " + server_ip)
    if(online == 0):
         print("Avilabe with ",online)
         return True
    else:
         print("Offline with ",online)
         return False
    

def craftCommand(binary, settings, index):
    command = binary + " " + settings["flags"]

    # generate Output file name
    base_filename = "output_" + str(index) + "_" + binary

    # handle server IP
    if binary == "iperf3" or binary == "iperf":
        command = command + " -c " + server_ip + " > " + base_filename + ".log"
    
    # handle multithreading
    base_command = command
    if settings["threads"] > 1:
        command = command + " -p " + str(base_ports[binary])
        for i in range(1, settings["threads"]):
            if binary == "iperf3" or binary == "iperf":
                port = base_ports[binary] + i
                filename = base_filename + "-" + str(port)
                command = command + " & " + base_command + " -p " + str(port) + " > " + filename + ".log"
    else:
        command = command
    return command

#def ParseOutput:
    ## MAIN

while True:
    time.sleep(1)
    if( ping()):
        telegram_send.send(conf="./conf",messages=["iPerf server is reachable, starting benchmarks."])
        break
    time.sleep(1)

data = ""

with open('tests.json') as f:
   data = json.load(f)

for i,test in enumerate(data):
    c = craftCommand(test["binary"], test["binary_settings"], i)
    data[i]["command"] = c
    data[i]["output"] = subprocess.check_output(c, shell=True).decode("utf-8") 

result = ""
# Parse Output
#with open("output.txt", "a+") as f:
#    for test in data:
#        f.write("\n#######################################\n")
#        f.write("###### Starting: " + test["command"])
#        f.write("\n#######################################\n")
#        f.write(test["test.log"])
        #if(test["binary"] == "iperf3"):
            


# telegram_send.send(conf="./conf",messages=[result])