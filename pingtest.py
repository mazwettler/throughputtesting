
import time
import datetime
import telegram_send
import os
import traceback

server_ip = "192.168.178.41"
# states:
# 0 init
# 1 up
# 2 down

state = 0


def ping():
    online = os.system("ping -c 1 -i 1 " + server_ip)
    if (online == 0):
        print("Availabe with ", online)
        return True
    else:
        print("Offline with ", online)
        return False


try:
    while True:
        time.sleep(1)
        result = ping()
        date = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(date)*1000
        if (result and state == 0):
            # telegram_send.send(conf="/opt/script/conf", messages=[
            #                   "FW finished booting")
            # break
            print("Server initialized!")
            print(unix_timestamp)
            state = 1
        elif (not result and state == 1):
            down_stamp = unix_timestamp
            print("Server went down! (" + str(down_stamp) + ")")
            state = 2
        elif (result and state == 2):
            up_stamp = unix_timestamp
            print("Server came up! (" + str(up_stamp) + ")")
            downtime = up_stamp - down_stamp
            print("Server has been down for " +
                  str(round(downtime/1000, 3)) + " seconds")
            state = 1
except KeyboardInterrupt:
    print('interrupted!')
