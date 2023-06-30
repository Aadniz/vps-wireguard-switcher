import json
import os


class Settings:
    check_interval = 300
    max_switches_a_day = 8
    max_ms = 750
    servers = []

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
        required_keys = ["ip", "port", "public_key", "subnet", "local_ip"]

        has_failed = False
        pri = 1
        c = 0
        for server in jsonObject["vps_servers"]:
            missing_keys = [key for key in required_keys if key not in server]
            if missing_keys:
                print(f"Missing key(s) {', '.join(missing_keys)} in server array config in settings.json")
                has_failed = True
                continue

            if "priority" in server:
                pri = server["priority"] + 1
            else:
                jsonObject["vps_servers"][c]["priority"] = pri
                pri += 1

            if not "name" in server:
                jsonObject["vps_servers"][c]["name"] = server["ip"] + ":" + server["port"] + "-" + server["public_key"]

            c += 1

        if has_failed:
            exit(1)

        Settings.servers = jsonObject["vps_servers"]

        # Optional settings
        if "check_interval" in jsonObject:
            if jsonObject["check_interval"] > 5:
                Settings.check_interval = jsonObject["check_interval"]

        if "max_switches_a_day" in jsonObject:
            if jsonObject["max_switches_a_day"] > 1:
                Settings.max_switches_a_day = jsonObject["max_switches_a_day"]

        if "max_ms" in jsonObject:
            if jsonObject["max_ms"] > 1:
                Settings.max_ms = jsonObject["max_ms"]
