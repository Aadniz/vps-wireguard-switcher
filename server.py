import urllib.request
from ping3 import ping, verbose_ping
import requests

from settings import Settings


class Server:
    hosts = []
    active = 0

    @staticmethod
    def init():
        # Init settings if it hasn't been run yet
        Settings.init()
        Server.hosts = Settings.servers

    @staticmethod
    def check(query):
        """
        Here we will do atleast 3 tests. For the check to be successfully it must pass 2 of 3 (or 60%)
        :param query: Match one value in JSON settings, or be equal to the host
        :return:
        """
        server = Server.__resolve_query(query)
        tests = 2
        successes = 0

        if len(Settings.paths) > 0:
            tests += 1

        # First try to ping
        res = ping(server["ip"], 4, "ms")
        if res is not None:
            if Settings.max_ms > res:
                successes += 1
            print("["+str(successes)+"/"+str(tests)+"] Ping:\t" + str(int(res*100)/100) + " ms")
        else:
            print("["+str(successes)+"/"+str(tests)+"] Ping:\tFailed")

        # Check if HTTP is working
        req = urllib.request.Request("http://" + server["ip"], data=None, method="HEAD", headers={'User-Agent': 'VPS Manager - server.py'})
        try:
            res = urllib.request.urlopen(req, timeout=Settings.max_http_ms/1000)
            res_code = res.status
            if 500 > res_code:
                successes += 1
            print("[" + str(successes) + "/" + str(tests) + "] HTTP:\tStatus Code " + str(res_code))
        except TimeoutError:
            print("[" + str(successes) + "/" + str(tests) + "] HTTP:\tTIMEOUT")
        except Exception as e:
            print("[" + str(successes) + "/" + str(tests) + "] HTTP:\t", e)

        # Now test reverse proxy directly
        extra_tests = len(Settings.paths)
        if len(Settings.paths) > 0:
            for path in Settings.paths:
                hostnames = []
                if type(path["hostname"]) == list:
                    hostnames = path["hostname"]
                    extra_tests += len(path["hostname"])
                else:
                    hostnames = [path["hostname"]]
                    extra_tests += 1
                for hostname in hostnames:
                    response = requests.get(f'http://{server["ip"]}{path["path"]}', headers={'Host': hostname})
                    status_code = response.status_code
                    if "response_code" in path and path["response_code"] == status_code:
                        successes += 1/extra_tests
                        print("[" + str(int(successes)) + "/" + str(tests) + "] HTTP:\tStatus Code " + str(status_code))
                    elif "response_code" not in path and 500 > status_code:
                        successes += 1/extra_tests
                        print("[" + str(int(successes)) + "/" + str(tests) + "] HTTP:\tStatus Code " + str(status_code))
                    else:
                        print("[" + str(int(successes)) + "/" + str(tests) + "] HTTP:\tStatus Code " + str(status_code))

    @staticmethod
    def __resolve_query(query) -> dict:
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
