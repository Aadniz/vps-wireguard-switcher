import time

from settings import Settings

if __name__ == '__main__':

    # Init the settings
    Settings.init()

    while True:

        time.sleep(Settings.check_interval)
