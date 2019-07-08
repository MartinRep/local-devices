import socket
from netifaces import interfaces, ifaddresses, AF_INET
import subprocess
from flask import Flask, jsonify
from threading import Timer

app = Flask(__name__)
devices = {}

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

def nmap_job(ip_mask):
    command = 'sudo nmap -sn {}'.format(ip_mask)
    nmap = subprocess.run([command], shell = True, stdout = subprocess.PIPE)
    nmap_output = nmap.stdout.decode("utf-8")
    update_connected_devs(nmap_output)    

def get_ip4_mask():
    iplist = [ifaddresses(face)[AF_INET][0]["addr"] for face in interfaces() if AF_INET in ifaddresses(face)]
    ip_mask = '.'.join(iplist[1].split('.')[:3]) + '.0/24'
    return ip_mask

def update_connected_devs(nmap_output):
    global devices
    con_devices = {}
    for line in nmap_output.splitlines():
        # if 'Starting Nmap' in line:
        #     date_time = ' '.join((line.split()[7:]))
            # print('Time updated: {}'.format(date_time))
        if 'Nmap scan report for' in line:
            ip_addr = line.split()[4]
        elif 'MAC Address:' in line:
            mac_addr = str(line.split()[2])
            con_devices[mac_addr] = {}
            if mac_addr in devices:
                devices[mac_addr]['uptime'] += 1
                devices[mac_addr]['downtime'] = 0
            else: 
                host_name = ' '.join(line.split()[3:])[1:-1]
                devices[mac_addr] = {'ip': ip_addr, 'host': host_name, 'uptime': 1, 'downtime': 0}
    offline_devs = set(devices.keys()) ^ set(con_devices.keys())
    for dev in offline_devs:
        devices[dev]['uptime'] = 0
        if 'downtime' in devices[dev]:
            devices[dev]['downtime'] += 1
        else:
            devices[dev]['downtime'] = 1

def main():
    ip_mask = get_ip4_mask()
    nmap = RepeatedTimer(30, nmap_job, ip_mask)
    app.run('0.0.0.0', port = 5000)

@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices), 200

if __name__ == "__main__":
    main()