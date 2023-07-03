import time

from settings import Settings
from server import Server

if __name__ == '__main__':

    # Init the settings class
    Settings.init()

    # Init the server class
    Server.init()

    while True:
        for host in Server.hosts:
            # Check if there is connection to the host
            print("Checking " + host["name"] + " ...")
            Server.check(host)

        time.sleep(Settings.check_interval)
