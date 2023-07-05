import time

from wireguard import Wireguard
from settings import Settings
from server import Server

if __name__ == '__main__':

    # Init the settings class
    Settings.init()

    # Init the server class
    Server.init()

    # Init the wireguard class
    wireguard = Wireguard()

    while True:
        # Self-test first
        print("Running self-test ...")
        res = Server.self_test()
        if not res:
            print("CRITICAL: Self-test failed! Doing nothing")
            time.sleep(Settings.check_interval)
            continue

        for host in Server.hosts:
            # Check if there is connection to the host
            print("Checking " + host["name"] + " ...")
            res = Server.check(host)
            print(res)

        print(wireguard.active_server)

        time.sleep(Settings.check_interval)
