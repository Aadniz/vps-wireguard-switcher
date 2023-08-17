import subprocess
import psutil
import time
import glob
import os

from server import Server
from settings import Settings
from systemd import Systemd


class Wireguard:
    up = False
    root = False

    interface = None
    address = None  # 10.0.0.204
    netmask = None  # 255.255.0.0

    active_server = None

    __fails = 0
    __config_path = "/etc/wireguard/"

    @staticmethod
    def init():
        Wireguard.self_test()
        if Wireguard.up is False:
            print("WARNING: Wireguard failed to initialize! There is no VPN control!")
            return

    @staticmethod
    def self_test():
        # Check if wg commands are accessible
        output = subprocess.run(["wg", "show"], capture_output=True, text=True, timeout=45)
        result = output.stdout.strip()

        if output.returncode != 0:
            if output.stderr.strip() != "":
                print(output.stderr.strip())
            else:
                print("Wireguard controls failed")
            Wireguard.up = False
            return
        if result == "" and output.stderr.strip() == "":
            print("Wireguard controls gave no output. Most likely are not running")
            Wireguard.up = False
        if output.stderr.strip() != "":
            print(output.stderr.strip())

        # Now to find the interface
        peer_focus = None
        for line in result.split("\n"):
            line = line.strip()
            if "interface:" in line:
                print(line)
                Wireguard.interface = line.split(" ")[1].strip()
            if "peer" in line:
                peer_focus = line.split(" ")[1].strip()
            if "allowed ips" in line and "0.0.0.0/0" in line and peer_focus != None:
                Wireguard.active_server = Server.get_server(peer_focus)
        if Settings.wireguard_interface is not None:
            Wireguard.interface = Settings.wireguard_interface
        if Wireguard.interface is None:
            Wireguard.try_get_interface()
            if Wireguard.interface is None:
                print("No wireguard interface found?")
                Wireguard.up = False
                return
        if Wireguard.active_server is None:
            print("No gateway?")
            Wireguard.up = False
            return

        # Now compare with ip addr
        addrs = psutil.net_if_addrs()
        found = False
        for addr in addrs.keys():
            if addr.lower().strip() == Wireguard.interface:
                Wireguard.address = addrs[addr][0].address
                Wireguard.netmask = addrs[addr][0].netmask
                found = True
                break
        if not found:
            print(f"{Wireguard.interface} instance not found in ip addr")
            Wireguard.up = False
            return

        Wireguard.__fails = 0
        Wireguard.up = True

    @staticmethod
    def try_get_interface():
        if not os.access(Wireguard.__config_path, os.R_OK):
            print(f"No access to read {Wireguard.__config_path}")
            return

        files = glob.glob(Wireguard.__config_path + "*.conf")
        if len(files) > 0:
            for file in files:
                interface = file.split(Wireguard.__config_path)[1].split(".conf")[0]
                Wireguard.interface = interface
                return

    @staticmethod
    def reset_or_switch(focus_host: dict = None, force=False):
        """
        Here we switch or restart the wireguard settings. May be used when there is no interface, or gateway
        :param focus_host: A host object
        :param force: Force restart the systemd service without looping 3 times
        :return:
        """
        if focus_host is None:
            focus_host = Server.hosts[0]

        # Try to get the interface or else we can't really continue
        if Wireguard.interface is None:
            Wireguard.try_get_interface()
            if Wireguard.interface is None:
                print("Failed to get interface. Recommend checking out the issue manually!")
                return

        service_name = f"wg-quick@{Wireguard.interface}.service"
        service_status = Systemd.state(service_name)
        if force or (service_status != "active" and Wireguard.__fails >= 3):
            Systemd.restart(service_name)
            status = Systemd.state(service_name)
            while status != "active":
                print(status + " ", end="")
                status = Systemd.state(service_name)
                time.sleep(1)
            print()

        # Now run the command for each host. The focus host will look a bit different
        # We need to make sure the 0.0.0.0/0 never overlaps, thus the reason for the array joining and c counting
        c = 0
        for host in Server.hosts + [focus_host]:
            allowed_ips = host["subnet"]
            if host == focus_host and len(Server.hosts) > c:
                c += 1
                continue
            if host == focus_host and c >= len(Server.hosts):
                print("> " + host["name"])
                allowed_ips = "0.0.0.0/0"
            else:
                print("< " + host["name"])

            output = subprocess.run([
                "wg", "set", Wireguard.interface, "peer", host["public_key"],
                "endpoint", host["ip"] + ":" + str(host["port"]),
                "allowed-ips", allowed_ips,
                "persistent-keepalive", str(host["persistent_keepalive"])
            ], capture_output=True, text=True, timeout=45)
            result = output.stdout.strip()

            if output.returncode != 0:
                print(f"({host['name']})", "ERROR: ", output.stderr)
                time.sleep(2)
                c += 1
                continue
            elif result != "":
                print(f"({host['name']})", result)
            else:
                print(f"({host['name']})", "wg", "set", Wireguard.interface, "peer", host["public_key"], "endpoint", host["ip"] + ":" + str(host["port"]), "allowed-ips", allowed_ips, "persistent-keepalive", str(host["persistent_keepalive"]))

            time.sleep(8)
            c += 1

        # Now do a self test to hopefully update the class to up = True
        Wireguard.self_test()
        if not Wireguard.up:
            # When fails reaches 3, we will restart the systemd service
            Wireguard.__fails += 1
