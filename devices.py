import socket
from netifaces import interfaces, ifaddresses, AF_INET
import subprocess
from flask import Flask, jsonify
from threading import Timer

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

app = Flask(__name__)
nmap_output = 'devices.txt'
devices = {}

def nmap_job(ip_mask):
    global devices
    command = 'sudo nmap -sn {} > {}'.format(ip_mask, nmap_output)
    print(command)
    subprocess.run([command], shell = True)
    try:
        devices = update_connected_devs()
    except IOError:
        print("Error opening file: {}".format(nmap_output))

def get_ip4_mask():
    iplist = [ifaddresses(face)[AF_INET][0]["addr"] for face in interfaces() if AF_INET in ifaddresses(face)]
    ip_mask = '.'.join(iplist[1].split('.')[:3]) + '.0/24'
    return ip_mask

def update_connected_devs():
    con_devices = {}
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
                con_devices[mac_addr] = {'ip': ip_addr, 'host': host_name}
    return con_devices

ip_mask = get_ip4_mask()
nmap = RepeatedTimer(60, nmap_job, ip_mask)

@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices), 200

app.run('0.0.0.0', port = 5000)