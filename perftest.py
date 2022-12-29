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
    "iperf": r"\[(...)\].+?\s([0-9.]+)\s(Gbits\/sec|Mbits\/sec|Kbits\/sec).*",
    "iperf -u": r"\[(...)\].+?\s([0-9.]+)\s(Gbits\/sec|Mbits\/sec|Kbits\/sec).*",
    "iperf3": r"\[(...)\].+?\s([0-9.]+)\s(Gbits\/sec|Mbits\/sec|Kbits\/sec).*",
    "streams": r"\-P\s(\d*)\s*"
}


def parseOutput(binary, command, filename):
    r = ""
    speed = ""
    with open(output_dir + filename, 'r') as f:
        line = ""
        if binary == "iperf3":
            line = f.readlines()[-3]

        elif binary == "iperf":
            if " -u " in command:
                for l in (f.readlines()[-2:]):
                    line = line + l
                binary = "iperf -u"
            else:
                line = f.readlines()[-1]
        # Get fields
        result = re.search(regex[binary], line)

        # parse speed to Mbps/sec
        try:
            speed = float(result.group(2))
            print("\tParsed Speed: " + str(speed) + " " +
                  result.group(3) + " from file " + filename)
        except AttributeError:
            print("\tERROR on parsing in file: " +
                  filename + " on line: " + line)
            traceback.print_exc()
    return speed


def ping():
    online = os.system("ping -w 10 -c 1 " + server_ip)
    if (online == 0):
        print("Availabe with ", online)
        return True
    else:
        print("Offline with ", online)
        return False


def craftCommand(test, index):

    streams = 1
    threads = 1
    bandwidth = info["bandwidth"]
    binary = test["binary"]
    settings = test["binary_settings"]
    # generate command
    command = binary + " " + settings["flags"]

    # generate Output file name
    base_filename = output_dir + str(index) + "_" + binary

    # handle binary specific settings
    if binary == "iperf3" or binary == "iperf":
        # report only in Mbits
        command = command + " -f m"
        # add server IP
        command = command + " -c " + server_ip
        # get parallel stream count
        regex_streams = re.search(regex["streams"], settings["flags"])
        try:
            streams = regex_streams.group(1)
        except AttributeError:
            streams = 1
        if "-u" in settings["flags"]:
            test["protocol"] = "UDP"
        else:
            test["protocol"] = "TCP"
    # handle multithreading
    base_command = command
    try:
        if settings["threads"] > 1:
            threads = settings["threads"]
            command = command + " -p " + \
                str(base_ports[binary]) + " > " + base_filename + ".log"
            for i in range(1, threads):
                if binary == "iperf3":
                    port = base_ports[binary] + i
                    filename = base_filename + "-" + str(port)
                    command = command + " & " + base_command + \
                        " -p " + str(port) + " > " + filename + ".log"
        else:
            # Redirect Output
            command = command + " > " + base_filename + ".log"
    except KeyError:
        # Redirect Output
        command = command + " > " + base_filename + ".log"

    if binary == "iperf3":
        # bandwidth limitter
        bandwidth = int(info["bandwidth"])/(int(streams)*int(threads))
    command = command.replace(
        "$BANDWIDTH", str(bandwidth))
    test["command"] = command
    test["threads"] = int(threads)
    test["streams_per_thread"] = int(streams)
    test["streams_total"] = int(streams)*int(threads)
    test["expected_speed"] = int(info["bandwidth"])/1000000
    return test


data = ""
info = ""
result = '"cloud","iperf_vm_size","fw_vendor","fw_size","protocol","binary","excpected_throughput","throughput","threads","streams_per_thread","total_streams","short_name","test_name","init_time","command"\n'

with open('/opt/script/tests.json') as f:
    data = json.load(f)

with open('/opt/script/info') as f:
    info = json.load(f)

while True:
    time.sleep(1)
    if (ping()):
        telegram_send.send(conf="/opt/script/conf", messages=[
                           "iPerf server is reachable, starting benchmarks. (FW_SIZE: {}, FW_VENDOR: {}, IPERF_SIZE: {})".format(info["fwsize"], info["vendor"], info["vmsize"])])
        break
    time.sleep(1)


for i, test in enumerate(data):
    try:
        time.sleep(5)
        data[i] = craftCommand(test, i)
        c = data[i]["command"]
        print("\n# Running test: " + c)
        data[i]["output"] = subprocess.check_output(
            c, shell=True).decode("utf-8")
        time.sleep(2)
        files = os.listdir(output_dir)
        speed = 0.0
        for file in files:
            if file.startswith(str(i)+"_"):
                speed = speed + float(parseOutput(data[i]["binary"], c, file))
        if binary == "iperf3":
            shortname = "{}_{}T_{}S".format(
                data[i]["protocol"], data[i]["threads"], data[i]["streams_per_thread"])
        elif binary == "iperf":
            shortname = "{}_{}T_1S".format(
                data[i]["protocol"], data[i]["streams_per_thread"])
        result = result + "\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",{},{},{},{},{},\"{}\",\"{}\",{},\"{}\"\n".format(
            info["cloud"], info["vmsize"], info["vendor"], info["fwsize"], data[i]["protocol"], data[i]["binary"], data[i]["expected_speed"], speed, data[i]["threads"], data[i]["streams_per_thread"], data[i]["streams_total"], shortname, data[i]["name"], info["runtime"], c)
    except:
        telegram_send.send(conf="/opt/script/conf", messages=["Test failed: \n ```\n" + json.dumps(
            data[i]) + "``` \n\n Details: \n ```\n" + traceback.format_exc() + "```"], parse_mode="markdown")

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
html = template % df.to_html(classes=classes)

# html = df.to_html()
hti = Html2Image(custom_flags=["--headless", "--no-sandbox"],
                 output_path=output_dir, browser_executable="/usr/bin/google-chrome-stable")
hti.screenshot(html_str=html, save_as='result.png', size=(2560, 1440))

with open(output_dir + 'result.html', "w+") as f:
    f.write(html)

with open(output_dir + 'result.png', "rb") as f:
    telegram_send.send(conf="/opt/script/conf", images=[f])
