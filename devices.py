import socket
from crontab import CronTab
from netifaces import interfaces, ifaddresses, AF_INET
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)
nmap_output = 'devices.txt'
devices = {}

def cron_job(ip_mask):
    cron = CronTab()
    job = cron.new(command='nmap -sn {}'.format(ip_mask))  
    job.minute.every(1)
    cron.write()

def get_ip4_mask():
    iplist = [ifaddresses(face)[AF_INET][0]["addr"] for face in interfaces() if AF_INET in ifaddresses(face)]
    ip_mask = '.'.join(iplist[1].split('.')[:3]) + '.0/24'
    return ip_mask

def update_connected_devs():
    global devices
    with open(nmap_output, 'r') as f:
        for line in f:
            # if 'Starting Nmap' in line:
            #     date_time = ' '.join((line.split()[7:]))
                # print('Time updated: {}'.format(date_time))
            if 'Nmap scan report for' in line:
                ip_addr = line.split()[4]
            elif 'MAC Address:' in line:
                mac_addr = str(line.split()[2])
                host_name = ' '.join(line.split()[3:])[1:-1]
                devices[mac_addr] = {'ip': ip_addr, 'host': host_name}
    return devices

# cron_job(get_ip4_mask)

try:
    update_connected_devs()
    for dev, value in devices.items():
        print(value['ip'], value['host'])
except IOError:
    print("Error opening file: {}".format(nmap_output))


@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices), 200

app.run('0.0.0.0', port = 5000)