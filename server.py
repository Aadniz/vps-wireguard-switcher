import urllib.request
from ping3 import ping, verbose_ping
from urllib.parse import urlparse
import requests

from settings import Settings
from proxy import Proxy
from cloudflare import Cloudflare
import wireguard


class Server:
    hosts = []
    WAN = False

    __switches_today = 0
    """
    The amount of times the server has switched VPS server today
    """

    @staticmethod
    def init():
        # Init settings if it hasn't been run yet
        Settings.init()
        Server.hosts = Settings.servers

    @staticmethod
    def check(query) -> list:
        """
        Here we will check both local connection and external connection to the servers.
        It will include the tests in settings.json if any is provided. It will test for reverse proxy connections
        :param query: Match one value in JSON settings, or be equal to the host
        :return: [local success, external success, total tests]
        """
        server = Server.get_server(query)

        # local, external, total
        l_e_successes = [0, 0, 0]

        for i in range(2):
            if i == 0:
                ip = server["local_ip"]
            else:
                ip = server["ip"]

            tests = 2
            successes = 0

            if len(Settings.tests) > 0:
                tests += 1

            # First try to ping
            res = None
            try:
                res = ping(ip, 4, "ms")
            except PermissionError as e:
                print(" No permission to ping. Please run as root or check https://github.com/robfox92/ping3/blob/c18fb2a23fe601356cba69e6881d92605c875b79/TROUBLESHOOTING.MD")
            except OSError as e:
                print(f" Pinging address {ip} is not possible with the active network interfaces.")

            if res is not None and res != 0:
                if Settings.max_ms > res:
                    successes += 1
                print(f" [{successes}/{tests}]\t{ip:<15} ping:\t{int(res*100)/100} ms")
            else:
                print(f" [{successes}/{tests}]\t{ip:<15} ping:\tFailed")

            # Set proxy
            proxy = Proxy.get_requests_proxies(1)
            print(proxy)
            res = requests.request("HEAD", "http://" + ip, proxies=proxy, timeout=Settings.max_http_ms / 1000, headers={'User-Agent': 'VPS Manager - server.py'})
            try:
                res = requests.request("HEAD", "http://" + ip, proxies=proxy, timeout=Settings.max_http_ms/1000, headers={'User-Agent': 'VPS Manager - server.py'})

                res_code = res.status_code
                if 500 > res_code:
                    successes += 1
                print(f" [{successes}/{tests}]\t{ip:<15} HTTP:\tStatus Code {res_code}\t{res.url}")
            except TimeoutError:
                print(f" [{successes}/{tests}]\t{ip:<15} HTTP:\tTIMEOUT\t{res.url}")
            except Exception as e:
                print(f" [{successes}/{tests}]\t{ip:<15} HTTP:\t", e)

            # Now test reverse proxy directly
            extra_tests = 0
            if len(Settings.tests) > 0:
                # Count the amount of extra tasks
                for test in Settings.tests:
                    if type(test["hostname"]) == list:
                        extra_tests += len(test["hostname"])
                    else:
                        extra_tests += 1
                for test in Settings.tests:
                    hostnames = []
                    if type(test["hostname"]) == list:
                        hostnames = test["hostname"]
                    else:
                        hostnames = [test["hostname"]]
                    for hostname in hostnames:
                        try:
                            response = requests.get(f'{test["scheme"]}://{ip}:{test["port"]}{test["path"]}', headers={'Host': hostname}, timeout=Settings.max_http_ms/1000)
                            # Alter the URL to include the hostname
                            o = urlparse(response.url)
                            port = (":" + str(o.port)) if o.port is not None else ""
                            query_string = ("?" + o.query) if o.query != "" else ""
                            fragment = ("#" + o.fragment) if o.fragment != "" else ""
                            url = f"{o.scheme}://{hostname.split(':')[0] + port}{o.path}{query_string}{fragment}"

                            status_code = response.status_code
                            if "response_code" in test and test["response_code"] == status_code:
                                successes += 1/extra_tests
                                print(f" ({int(successes / tests*100)}%)\t{ip:<15} HTTP:\tStatus Code {status_code}\t{url}")
                            elif "response_code" not in test and 500 > status_code:
                                successes += 1/extra_tests
                                print(f" ({int(successes / tests*100)}%)\t{ip:<15} HTTP:\tStatus Code {status_code}\t{url}")
                            else:
                                print(f" ({int(successes / tests*100)}%)\t{ip:<15} HTTP:\tStatus Code {status_code}\t{url}")
                        except Exception as e:
                            print(f" ({int(successes / tests*100)}%)\t{ip:<15} HTTP:\t", e)

            l_e_successes[2] = round(tests)
            l_e_successes[i] = round(successes, 2)

        return l_e_successes

    @staticmethod
    def switch(query):
        server = Server.get_server(query)
        if Server.__switches_today >= Settings.max_switches_a_day:
            print(f"Reached maximum switches today of {Server.__switches_today}/{Settings.max_switches_a_day}")
            return

        wireguard.Wireguard.reset_or_switch(server)
        cf = Cloudflare()
        cf.switch_dns(server["ip"], dns_type="A")
        Server.__switches_today += 1

    @staticmethod
    def self_test() -> bool:
        """
        This function will check if there is any network connection at all
        :return: returns true if it has network connection
        """
        tests = len(Settings.self_test_addresses)
        successes = 0
        for host in Settings.self_test_addresses:
            # First try to ping
            res = None
            try:
                res = ping(host, 4, "ms")
            except PermissionError as e:
                print("No permission to ping. Please run as root or check https://github.com/robfox92/ping3/blob/c18fb2a23fe601356cba69e6881d92605c875b79/TROUBLESHOOTING.MD")
            except OSError as e:
                print(f"Pinging address {host} is not possible with the active network interfaces.")
            if res is not None and res != 0:
                successes += 1

        Server.WAN = successes/tests > Settings.self_test_success_rate
        return Server.WAN

    @staticmethod
    def get_server(query) -> dict:
        """
        Function to resolve query and return a server object
        :param query: In case query is a number, it will check the priority. Otherwise it will match on the strings
        :return: returns the server object
        """
        for host in Server.hosts:
            if host == query:
                return host
            for key, value in host.items():
                if type(query) == int:
                    if query == host["priority"]:
                        return host
                if query == value:
                    return host

        print("Query failed!")
        exit(1)

    @staticmethod
    def reset_max_switches():
        Server.__switches_today = 0
