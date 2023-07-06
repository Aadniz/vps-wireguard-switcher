import json
import os


class Settings:
    check_interval = 300
    max_switches_a_day = 8
    max_ms = 750
    max_http_ms = 8000
    success_rate = 0.6
    double_checks = 3
    servers = []
    tests = []
    self_test_addresses = ["1.1.1.1"]
    self_test_success_rate = 0.7
    wireguard_interface = None

    highest_priority = None
    lowest_priority = None

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
        for server in jsonObject["vps_servers"]:
            missing_keys = [key for key in required_keys if key not in server]
            if missing_keys:
                print(f"Missing key(s) {', '.join(missing_keys)} in server array config in settings.json")
                has_failed = True
                continue

            if "priority" in server:
                pri = server["priority"] + 1
            else:
                server["priority"] = pri
                pri += 1

            if Settings.highest_priority is None or Settings.highest_priority > server["priority"]:
                Settings.highest_priority = server["priority"]
            if Settings.lowest_priority is None or server["priority"] > Settings.lowest_priority:
                Settings.lowest_priority = server["priority"]

            if "name" not in server:
                server["name"] = server["ip"] + ":" + server["port"] + "-" + server["public_key"]
            if "persistent_keepalive" not in server or 5 > server["persistent_keepalive"]:
                server["persistent_keepalive"] = 25

        if has_failed:
            exit(1)

        Settings.servers = jsonObject["vps_servers"]

        # Checking paths in settings
        if "tests" in jsonObject:
            for test in jsonObject["tests"]:
                if "hostname" not in test:
                    print("Missing hostname in one or more paths!")
                    exit(1)
                if "path" not in test:
                    print("Missing path in one or more paths!")
                    exit(1)
            Settings.tests = jsonObject["tests"]

        # Optional settings
        if "check_interval" in jsonObject:
            if jsonObject["check_interval"] > 5:
                Settings.check_interval = jsonObject["check_interval"]
            else:
                print("WARNING: check_interval is smaller than 5!")

        if "max_switches_a_day" in jsonObject:
            if jsonObject["max_switches_a_day"] > 1:
                Settings.max_switches_a_day = jsonObject["max_switches_a_day"]
            else:
                print("WARNING: max_switches_a_day must be more than 1")

        if "max_ms" in jsonObject:
            if jsonObject["max_ms"] > 1:
                Settings.max_ms = jsonObject["max_ms"]
            else:
                print("WARNING: Who looks for max_ms less than 1? Trade servers? Anyways, 1 > max_ms is not supported")

        if "success_rate" in jsonObject:
            if jsonObject["success_rate"] > 0:
                Settings.success_rate = jsonObject["success_rate"]
            else:
                print("WARNING: if success_rate is less than 0, it means it will succeed if everything fails. Comon give it some more thought!")

        if "double_checks" in jsonObject:
            if jsonObject["double_checks"] >= 0:
                Settings.double_checks = jsonObject["double_checks"]
            else:
                print("WARNING: double_checks can't be negative.")

        if "wireguard_interface" in jsonObject:
            Settings.wireguard_interface = jsonObject["wireguard_interface"]

        if "self_test_success_rate" in jsonObject:
            if jsonObject["self_test_success_rate"] > 0:
                Settings.self_test_success_rate = jsonObject["self_test_success_rate"]
            else:
                print("WARNING: if self_test_success_rate is less than 0, it means it will succeed if everything fails. Comon give it some more thought!")

        if "max_http_ms" in jsonObject:
            if jsonObject["max_http_ms"] > Settings.max_ms:
                Settings.max_http_ms = jsonObject["max_http_ms"]
            else:
                print("WARNING: max_http_ms must be greater than max_ms. It doesn't make sense for a HTTP protocol to be quicker than a ping")

        if "self_test_addresses" in jsonObject:
            if type(jsonObject["self_test_addresses"]) == str:
                Settings.self_test_addresses = [jsonObject["self_test_addresses"]]
            elif type(jsonObject["self_test_addresses"]) == list:
                Settings.self_test_addresses = jsonObject["self_test_addresses"]
            else:
                print("WARNING: self_test_addresses is neither a string or a list?")
