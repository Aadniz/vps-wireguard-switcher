import json
import os
import hashlib


class Settings:
    check_interval: int = 300
    """
    The interval between each check in seconds
    """

    max_switches_a_day: int = 8
    """
    To prevent hanging on to 1st priority with a probable unstable connection, we set a limit
    """

    max_ms: int = 750
    """
    Maximum allowed ping ms before result in failure for checking
    """

    max_http_ms: int = 8000
    """
    Maximum allowed HTTP curl ms timing before result in failure for checking
    """

    success_rate: float = 0.6
    """
    Minimum success rate for allowing a pass
    """

    double_checks: int = 3
    """
    When a failure occurs, the script will skip the check_interval and double check x amount of times before switching
    """

    healthy_switching_checks: int = 16
    """
    If both hosts are up and running, but the active route is not set to the highest priority,
    this is how many loops needed to pass before switching
    """

    servers: list = []
    """
    The server dict objects provided in settings.json in vps_servers.
    For each server, these keys must be set: "ip", "port", "public_key", "subnet" and "local_ip"
    """

    tests: list = []
    """
    HTTP test urls. For each test provided, it will add 1/len(tests) to the checks.
    For each test object, these keys must be set: "hostname" and "path"
    """

    self_test_addresses: list | str = ["1.1.1.1"]
    """
    External hosts to test external internet connection. It will ping the hosts to verify it works.
    """

    self_test_success_rate: float = 0.7
    """
    The amount of success rate to determine if external internet is working.
    In some cases, 1 or more hosts may have an outage, therefore can confirm that the internet is working using a success rate
    """

    wireguard_interface: str = None
    """
    Wireguard interface, eg: wg0, wg1 etc...
    """

    cloudflare_key: str = None
    """
    The cloudflare Bearer token key. If not set or incorrect, cloudflare API will remain untouched
    """

    cloudflare_hosts: dict | list | str = []
    """
    The hosts, or zone ids that determines which domains to control.
    It can also contain a dict or a list of dicts explaining dns_type and proxied.
    For example
    ```
    [
      {
        "name": "domain.com",
        "dns_type": "A",
        "proxied": false
      }
    ]
    ```
    IF cloudflare_key IS SET AND cloudflare_hosts IS EMPTY, IT WILL CONTROL ALL ZONES
    """

    highest_priority: int = None
    lowest_priority: int = None

    __has_init: bool = False
    __checksum: str = None
    __file_path: str = None
    __dir_path: str = None

    @staticmethod
    def init():
        if Settings.__has_init:
            return
        Settings.__load()

    @staticmethod
    def reload():
        Settings.__load()

    @staticmethod
    def updated():
        """
        Check if settings has been updated since last checked.
        :return:
        """
        return Settings.__hash_file(Settings.__file_path) != Settings.__checksum

    @staticmethod
    def __load():
        """
        Here we load all the settings
        """
        Settings.__has_init = True

        # See if settings file exists
        Settings.__dir_path = os.path.dirname(os.path.realpath(__file__))
        Settings.__file_path = Settings.__dir_path + "/settings.json"
        if not os.path.isfile(Settings.__file_path):
            print(f"Settings file not found: {Settings.__file_path}")
            print("Please copy paste the example shown in README.MD")
            exit(1)

        f = open(Settings.__file_path, "rb")
        jsonObject = json.load(f)
        f.close()

        Settings.__checksum = Settings.__hash_file(Settings.__file_path)

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
                test["port"] = 80
                test["scheme"] = "http" if "scheme" not in test else test["scheme"]
                if "://" in test["hostname"]:
                    test["scheme"] = test["hostname"].split("://")[0]
                    test["hostname"] = test["hostname"].split("://")[1]
                if ":" in test["hostname"]:
                    test["port"] = int(test["hostname"].split(":")[1])
                    test["hostname"] = test["hostname"].split(":")[0]
                if test["port"] == 443 or test["port"] == 8443:
                    test["scheme"] = "https"
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

        if "healthy_switching_checks" in jsonObject:
            if jsonObject["healthy_switching_checks"] >= 0:
                Settings.healthy_switching_checks = jsonObject["healthy_switching_checks"]
            else:
                print("WARNING: healthy_switching_checks can't be negative.")

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

        if "cloudflare_key" in jsonObject:
            Settings.cloudflare_key = jsonObject["cloudflare_key"]

        if "cloudflare_hosts" in jsonObject:
            if type(jsonObject["cloudflare_hosts"]) == str and jsonObject["cloudflare_hosts"].strip() != "":
                Settings.cloudflare_hosts = [jsonObject["cloudflare_hosts"]]
            elif type(jsonObject["cloudflare_hosts"]) == list and len(jsonObject["cloudflare_hosts"]) > 0:
                Settings.cloudflare_hosts = jsonObject["cloudflare_hosts"]
            elif Settings.cloudflare_key is not None:
                print("WARNING: no cloudflare hosts specified! The DNS switching will apply to all domains within the account!")
                Settings.cloudflare_hosts = []

    @staticmethod
    def __hash_file(filename):
        """
        This function returns the SHA-1 hash of the file passed into it
        https://www.programiz.com/python-programming/examples/hash-file
        """

        # make a hash object
        h = hashlib.sha1()

        # open file for reading in binary mode
        with open(filename, 'rb') as file:
            # loop till the end of the file
            chunk = 0
            while chunk != b'':
                # read only 1024 bytes at a time
                chunk = file.read(1024)
                h.update(chunk)

        # return the hex representation of digest
        return h.hexdigest()