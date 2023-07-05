import subprocess
import psutil

from server import Server


class Wireguard:
    up = False
    root = False

    interface = None
    address = None  # 10.0.0.204
    netmask = None  # 255.255.0.0

    active_server = None

    def __init__(self):
        self.self_test()
        if self.up is False:
            print("WARNING: Wireguard failed to initialize! There is no VPN control!")
            return

    def self_test(self):
        # Check if wg commands are accessible
        output = subprocess.run(["wg", "show"], capture_output=True, text=True, timeout=45)
        result = output.stdout.strip()

        if output.returncode != 0:
            if output.stderr.strip() != "":
                print(output.stderr.strip())
            else:
                print("Wireguard controls failed")
            self.up = False
            return
        if result == "" and output.stderr.strip() == "":
            print("Wireguard controls gave no output. Most likely are not running")
            self.up = False
            return
        if output.stderr.strip() != "":
            print(output.stderr.strip())

        # Now to find the interface
        peer_focus = None
        for line in result.split("\n"):
            line = line.strip()
            if "interface:" in line:
                print(line)
                self.interface = line.split(" ")[1].strip()
            if "peer" in line:
                peer_focus = line.split(" ")[1].strip()
            if "allowed ips" in line and "0.0.0.0/0" in line and peer_focus != None:
                self.active_server = Server.get_server(peer_focus)
        if self.interface is None:
            print("No wireguard interface found?")
            self.up = False
            return
        if self.active_server is None:
            print("No gateway?")
            self.up = False
            return

        # Now compare with ip addr
        addrs = psutil.net_if_addrs()
        found = False
        for addr in addrs.keys():
            if addr.lower().strip() == self.interface:
                self.address = addrs[addr][0].address
                self.netmask = addrs[addr][0].netmask
                found = True
                break
        if not found:
            print(self.interface + " instance not found in ip addr")
            self.up = False
            return

        self.up = True
