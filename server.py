from ping3 import ping, verbose_ping

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
        server = Server.__resolve_query(query)
        # First try to ping

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
