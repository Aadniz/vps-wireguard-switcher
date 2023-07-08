import json
import CloudFlare
from settings import Settings


class Cloudflare(CloudFlare.CloudFlare):
    #signed_in = False
    hosts = []
    """
    cloudflare_hosts from ./settings.py
    """

    # During creation of extended cloudflare class, we will pull the API key from settings.py if set
    def __init__(self):
        if Settings.cloudflare_key is None:
            return
        super().__init__(token=Settings.cloudflare_key)
        self.hosts = Settings.cloudflare_hosts

    def switch_dns(self, content, dns_type=None, hosts=None):
        """
        Switch cloudflare DNS
        :param content: The value to be changed
        :param dns_type: The type to change, like "A", "AAAA", "TXT" etc...
        :param hosts: The hosts this applies to. If not set, will use the settings.json hosts. If neither are set, it will update EVERYTHING!
        :return:
        """
        if hosts is None:
            hosts = self.hosts

        # Get the DNS config for the queried hosts
        dns_settings = self.get_dns_settings(hosts, dns_type)

        # Then switch the ones with incorrect content
        updated_anything = False
        for setting in dns_settings:
            for record in setting:
                tmp_dns_type = dns_type if dns_type is not None else record["type"]
                if record["content"] != content:
                    res = self.update_dns_setting(record["zone_id"], record["id"], record["name"], tmp_dns_type, content, True)
                    if updated_anything == False and res == True:
                        updated_anything = True
        if updated_anything == False:
            print("Cloudflare DNS values not changed")

    def update_dns_setting(self, zone_id, dns_id: str, name: str, dns_type: str, content: str, proxied: bool, comment: str = None, tags: list = None, ttl: int = None):
        data = {
            'name': name,
            'type': dns_type,
            'content': content,
            'proxied': proxied
        }

        if comment is not None:
            data["comment"] = comment
        if tags is not None:
            data["tags"] = tags
        if ttl is not None:
            data["ttl"] = ttl

        print(f"Updating {name} cloudflare DNS...", end="")
        try:
            r = self.zones.dns_records.put(zone_id, dns_id, data=data)
            print(r)
        except self.exceptions.CloudFlareAPIError as e:
            print("\n/zones.dns_records.put %s - %d %s - api call failed" % (name, e, e))
            return False
        except Exception as e:
            print("\n/zones.dns_records.put %s - %s - api call failed" % (name, e))
            return False

        return True

    def get_dns_settings(self, query: str | list = None, dns_type=None):
        if query is None:
            query = []

        zones = self.query_zones(query)

        # request the DNS records from that zones
        dnss = []
        for zone in zones:
            try:
                if dns_type == None:
                    dns_records = self.zones.dns_records.get(zone["id"])
                else:
                    dns_records = self.zones.dns_records.get(zone["id"], params={'type': dns_type})
                dnss.append(dns_records)
            except self.exceptions.CloudFlareAPIError as e:
                print('/zones/dns_records.get %d %s - api call failed' % (e, e))
                continue
        return dnss

    def query_zones(self, query: str | list = None):
        """
        Function to query the zones that fits the query.
        :param query: We can only query 1 or more values of zone_id or name. If the query is an empty array, it will give everything in response
        :return: Returns the array of zones that matches the query
        """
        if query is None:
            query = []

        try:
            zones = self.zones.get(params={'per_page': 50})
        except self.exceptions.CloudFlareAPIError as e:
            print('/zones.get %d %s - api call failed' % (e, e))
            return None
        except Exception as e:
            print('/zones.get - %s - api call failed' % e)
            return None
        if len(zones) == 0:
            print('No zones found')
            return None

        if not query:
            return zones
        elif type(query) == str:
            query = [query]

        queried_zones = []
        for zone in zones:
            if zone["id"] in query or zone["name"] in query:
                queried_zones.append(zone)

        return queried_zones
