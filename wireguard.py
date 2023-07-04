import subprocess
import psutil

class Wireguard:
    __up = False
    __root = False

    def __init__(self):
        self.self_test()
        self.__up = True

    def self_test(self):
        # Check if wg commands are accessible
        output = subprocess.run(["wg", "show"], stderr=subprocess.PIPE, timeout=45)
        addrs = psutil.net_if_addrs()
        print(addrs.keys())