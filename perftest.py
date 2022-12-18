import json
import subprocess
import telegram_send

# Settings
runs = 5
time_between_runs = 360
server_ip = "speedtest.shinternet.ch"
base_ports = {
 "iperf": 5001,
 "iperf3": 5201
}


def craftCommand(binary, settings):
    command = binary + " " + settings["flags"]

    # handle server IP
    if binary == "iperf3" or binary == "iperf":
        command = command + " -c " + server_ip
    
    # handle multithreading
    base_command = command
    if settings["threads"] > 1:
        command = command + " -p " + str(base_ports[binary]) + " | grep receiver"
        for i in range(1, settings["threads"]):
            if binary == "iperf3" or binary == "iperf":
                port = base_ports[binary] + i
                command = command + " & " + base_command + " -p " + str(port) + " | grep receiver"
    else:
        command = command
    return command

#def ParseOutput:
    ## MAIN

data = ""

with open('tests.json') as f:
   data = json.load(f)

for i,test in enumerate(data):
    c = craftCommand(test["binary"], test["binary_settings"])
    data[i]["command"] = c
    data[i]["output"] = subprocess.check_output(c, shell=True).decode("utf-8") 

print(data)
result = ""
# Parse Output
with open("my_file.txt", "a+") as f:
    for test in data:
        f.write("\n########################\n")
        f.write("Starting: " + test["command"])
        f.write("\n########################\n")
        f.write(test["output"])


#telegram_send.send(conf="./conf",messages=[result])