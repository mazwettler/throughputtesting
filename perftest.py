import json
import subprocess
import telegram_send
import time
import os
import tarfile
import re

# Settings
runs = 5
time_between_runs = 360
server_ip = "10.0.1.10"
base_ports = {
 "iperf": 5001,
 "iperf3": 5201
 }

regex = {
 "iperf": r"^\[(...)\].+?\s([0-9.]+)\s(Gbits/sec|Mbits/sec|Kbits/sec).*$",
 "iperf3": r"^\[(...)\].+?\s([0-9.]+)\s(Gbits/sec|Mbits/sec|Kbits/sec).*$"
}

def parseOutput(binary, filename):
    r = ""
    with open(filename, 'r') as f:
        line=""
        if binary == "iperf3":
            line = f.readlines()[-3]
        
        elif binary == "iperf":
            line = f.readlines()[-1]
        # Get fields
        result = re.search(regex[binary],filename)
        # convert speed to Mbps/sec
        speed = float(result.groups(2))
        if result.groups(2).contains("Gbps"):
            speed = speed * 1000
    return speed

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

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
    base_filename = "/opt/output/" + str(index) + "_" + binary

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

result = "test,binary,throughput"

for i,test in enumerate(data):
    c = craftCommand(test["binary"], test["binary_settings"], i)
    data[i]["command"] = c
    data[i]["output"] = subprocess.check_output(c, shell=True).decode("utf-8")
    files = os.listdir("/opt/output")
    for file in files:
        if file.startswith(str(i)+"_"):
            speed = parseOutput(test["binary"] , file)
            result = result + "{},{},{}\n".format(test["name"],test["binary"],speed)

print(result)

make_tarfile("output.tar", "/opt/output")
# Parse Output
#with open("output.txt", "a+") as f:
#    for test in data:
#        f.write("\n#######################################\n")
#        f.write("###### Starting: " + test["command"])
#        f.write("\n#######################################\n")
#        f.write(test["test.log"])
        #if(test["binary"] == "iperf3"):
            


# telegram_send.send(conf="./conf",messages=[result])