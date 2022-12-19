import json
import subprocess
import telegram_send
import time
import os
import re
import traceback
import pandas as pd
from html2image import Html2Image

# Settings
runs = 5
time_between_runs = 360
server_ip = "10.0.1.10"
output_dir = "/opt/output/"
base_ports = {
 "iperf": 5001,
 "iperf3": 5201
 }

regex = {
 "iperf": r"\[(...)\].+?\s([0-9.]+)\s(Gbits/sec|Mbits/sec|Kbits/sec).*",
 "iperf3": r"\[(...)\].+?\s([0-9.]+)\s(Gbits/sec|Mbits/sec|Kbits/sec).*"
}

def parseOutput(binary, filename):
    r = ""
    speed = ""
    with open(output_dir + filename, 'r') as f:
        line=""
        if binary == "iperf3":
            line = f.readlines()[-3]
        
        elif binary == "iperf":
            line = f.readlines()[-1]
        # Get fields
        result = re.search(regex[binary],line)

        # convert speed to Mbps/sec
        try:
            speed = float(result.group(2))
            print("\tParsed Speed: " + str(speed) + " " + result.group(3) + " from file " + filename)
            if "Gbits" in result.group(3):
                speed = speed * 1000
            elif "Kbits" in result.group(3):
                speed = speed / 1000
        except AttributeError:
            print("\tERROR on parsing in file: " + filename + " on line: " + line)
            traceback.print_exc()
    return speed

def ping():
    online = os.system("ping -w 10 -c 1 " + server_ip)
    if(online == 0):
         print("Availabe with ",online)
         return True
    else:
         print("Offline with ",online)
         return False
    

def craftCommand(binary, settings, index):
    # generate command
    command = binary + " " + settings["flags"]

    # generate Output file name
    base_filename = output_dir + str(index) + "_" + binary

    # handle server IP
    if binary == "iperf3" or binary == "iperf":
        command = command + " -c " + server_ip + " > " + base_filename + ".log"
    
    # handle multithreading
    base_command = command
    try:
        if settings["threads"] > 1:
            command = command + " -p " + str(base_ports[binary])
            for i in range(1, settings["threads"]):
                if binary == "iperf3":
                    port = base_ports[binary] + i
                    filename = base_filename + "-" + str(port)
                    command = command + " & " + base_command + " -p " + str(port) + " > " + filename + ".log"
    except KeyError:
        return command

    return command

data = ""
info = ""
result = "fw_vendor,fw_size,test,binary,throughput,command\n"

with open('/opt/script/tests.json') as f:
   data = json.load(f)

with open('/opt/script/info') as f:
   info = json.load(f)

while True:
    time.sleep(1)
    if( ping()):
        telegram_send.send(conf="/opt/script/conf",messages=["iPerf server is reachable, starting benchmarks. (FW_SIZE: {}, FW_VENDOR: {})".format(info["vendor"],info["fwsize"])])
        break
    time.sleep(1)


   
for i,test in enumerate(data):
    try:
        time.sleep(5)
        c = craftCommand(test["binary"], test["binary_settings"], i)
        data[i]["command"] = c
        print("\n# Running test: " + c)
        data[i]["output"] = subprocess.check_output(c, shell=True).decode("utf-8")
        time.sleep(2)
        files = os.listdir(output_dir)
        speed = 0.0
        for file in files:
            if file.startswith(str(i)+"_"):
                speed = speed + parseOutput(test["binary"] , file)

        result = result + "\"{}\",\"{}\",{},{},\"{}\"\n".format(info["vendor"],info["fwsize"],test["name"],test["binary"],speed,c)
    except:
        telegram_send.send(conf="/opt/script/conf",messages=["Test failed: \n ```\n" + json.dumps(test) +  "``` \n\n Details: \n ```\n" + traceback.format_exc() + "```"],parse_mode="markdown")

f = open(output_dir + "result.csv", "a+")
f.write(result)
f.close()

df = pd.read_csv(output_dir + "result.csv")

template = """"
<link href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
<style>
th {
    background: #2d2d71;
    color: white;
    text-align: left;
}
</style>
<body>
%s
</body>
"""

classes = 'table table-striped table-bordered table-hover table-sm'
html= template % df.to_html(classes=classes)

#html = df.to_html()
hti = Html2Image(custom_flags=["--headless", "--no-sandbox"],output_path=output_dir,browser_executable="/usr/bin/google-chrome-stable")
hti.screenshot(html_str=html, save_as='result.png')

with open(output_dir + 'result.png', "rb") as f:
    telegram_send.send(conf="/opt/script/conf",images=[f])