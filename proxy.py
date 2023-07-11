from settings import Settings


class Proxy:
    __proxy = None
    """
    Proxy configuration when doing the tests and/or update cloudflare DNS

    * route: **1|2|3** - 1: checks only, 2: external network (cloudflare) only, 3: everything
    * strict: true|false - If set to false, it will try without proxy if it fails
    * type: socks5|socks4|http - The type of proxy
    * host: domain, hostname, ip address
    * port: The port
    * username: Username if any
    * password: Password if any
    """

    __has_inited = False
    """
    Can only run the init function once
    """

    @staticmethod
    def init():
        if Proxy.__has_inited:
            return
        Settings.init()
        Proxy.__proxy = Settings.proxy
        Proxy.__has_inited = True

    @staticmethod
    def get_requests_proxies(route: int) -> dict | None:
        f"""
        Returns the proxies dict that we want to put in the requests parameter
        :param route: 1 - checking, 2 - cloudflare communication, 3 - everything
        :return: {dict(http= "url", https= "url")}
        """
        Proxy.init()
        if Proxy.__proxy is None:
            return None
        if Proxy.__proxy["route"] != 3 and Proxy.__proxy["route"] != route:
            return None

        url = f"{Proxy.__proxy['type']}://"
        if "username" in Proxy.__proxy and "password" in Proxy.__proxy:
            url += f"{Proxy.__proxy['username']}:{Proxy.__proxy['password']}@"
        elif "username" in Proxy.__proxy:
            url += f"{Proxy.__proxy['username']}@"

        url += f"{Proxy.__proxy['host']}:{Proxy.__proxy['port']}"

        return {
            "http": url,
            "https": url
        }

