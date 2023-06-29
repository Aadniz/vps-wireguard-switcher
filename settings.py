import json
import os


class Settings:
    check_interval = 300
    servers = []
    active = 0

    __has_init = False

    @staticmethod
    def init():
        if Settings.__has_init:
            return
        Settings.__has_init = True
        # See if settings file exists
        file_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = file_dir + "/settings.json"
        if not os.path.isfile(file_path):
            print("Settings file not found: " + file_path)
            print("Please copy paste the example shown in README.MD")
            exit(1)

        f = open(file_path, "rb")
        jsonObject = json.load(f)
        f.close()

        if "vps_servers" not in jsonObject:
            print("Missing setting \"vpn_servers\" in settings.json")
            exit(1)

        if 2 > len(jsonObject["vps_servers"]):
            print("Settings needs to have more than 2 VPS servers in settings.json")
            exit(1)

        # Checking if vps_servers has the correct format
        required_keys = ["ip", "port", "public_key", "priority", "subnet", "local_ip"]

        has_failed = False
        for server in jsonObject["vps_servers"]:
            missing_keys = [key for key in required_keys if key not in server]
            if missing_keys:
                print(f"Missing key(s) {', '.join(missing_keys)} in server array config in settings.json")
                has_failed = True

        if has_failed:
            exit(1)

        Settings.__servers = jsonObject["vps_servers"]

        if "check_interval" in jsonObject:
            if jsonObject["check_interval"] > 5:
                Settings.check_interval = jsonObject["check_interval"]