import json
import CloudFlare
from settings import Settings

class Cloudflare(CloudFlare.CloudFlare):
    # signed_in = False
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

    def switch_dns(self, content, dns_type=None, hosts=None) -> bool:
        """
        Switch cloudflare DNS
        :param content: The value to be changed
        :param dns_type: The type to change, like "A", "AAAA", "TXT" etc...
        :param hosts: The hosts this applies to. If not set, will use the settings.json hosts. If neither are set, it will update EVERYTHING!
        :return: True if any updates happened at all
        """
        if hosts is None:
            hosts = self.hosts
        if type(hosts) == dict and "name" in hosts:  # Transform {...} to [{...}]
            hosts = [hosts]

        # Get the DNS config for the queried hosts
        dns_settings = self.get_dns_settings(hosts, dns_type)

        # Then switch the ones with incorrect content
        updated_anything = False
        for setting in dns_settings:
            for record in setting:
                tmp_dns_type = dns_type if dns_type is not None else record["type"]
                proxied = True
                if type(hosts) == list and len(hosts) != 0 and type(hosts[0]) == dict and "name" in hosts[0]:
                    for host in hosts:
                        if host["name"].strip().lower() == record["name"]:
                            if "dns_type" in host:
                                tmp_dns_type = host["dns_type"]
                            if "proxied" in host:
                                proxied = host["proxied"]
                        break
                if record["content"] != content:
                    res = self.update_dns_setting(record["zone_id"], record["id"], record["name"], tmp_dns_type, content, proxied)
                    if updated_anything == False and res == True:
                        updated_anything = True
        return updated_anything

    def update_dns_setting(self, zone_id, dns_id: str, name: str, dns_type: str, content: str, proxied: bool, comment: str = None, tags: list[str] = None, ttl: int = None) -> bool:
        """
        Function to update the DNS record, do the API query towards Cloudflare
        https://developers.cloudflare.com/api/operations/dns-records-for-a-zone-update-dns-record
        :param zone_id: Each zone (or domain if you will) has their own zone id. Required
        :param dns_id: Need to know what DNS row we are talking about. That's when we use the dns_id
        :param name: The domain name, or more general the DNS record name
        :param dns_type: The type, being A, AAAA, MX, TXT etc...
        :param content: The content of the DNS record. Like an ip address
        :param proxied: Whenever to proxy the ip through cloudflare or reveal the real IP behind the hood (SHOULD ALWAYS BE TRUE)
        :param comment: If you feel spicy you can add a comment
        :param tags: Custom array[string] tags for the DNS record. This field has no effect on DNS responses.
        :param ttl: Time To Live (TTL) of the DNS record in seconds. Setting to 1 means 'automatic'. Value must be between 60 and 86400, with the minimum reduced to 30 for Enterprise zones.
        :return: True on success, false on failure with the error in the cout

        """
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

    def get_dns_settings(self, query: dict | list[dict] | str | list[str] = None, dns_type=None) -> list:
        """
        Get the DNS settings from cloudflare specifying the Query and DNS Type
        :param query: Query 1 or more values of zone_id or name. If the query is an empty array, it will give everything in response
        :param dns_type: The type, being A, AAAA, MX, TXT etc...
        :return: A multidimensional list of the dns settings. zone[][] where each zone has setting[]
        """
        if query is None:
            query = []
        elif type(query) == dict and "name" in query:  # Transform {...} to [{...}]
            query = [query]

        zones = self.query_zones(query)

        # request the DNS records from that zones
        dnss = []
        for zone in zones:
            try:
                if type(query) == list and len(query) != 0 and type(query[0]) == dict and "name" in query[0] and "dns_type" in query[0]:  # If cloudflare_hosts: [{"name": "blarg", "dns_type": "blarg"}, {...}, ...]
                    found = False
                    for host in query:
                        if host["name"].lower().strip() == zone["name"]:
                            dns_records = self.zones.dns_records.get(zone["id"], params={'type': host["dns_type"]})
                            dnss.append(dns_records)
                            found = True
                            break
                    if not found:
                        print(f"No host found for zone {zone['name']}")
                    continue
                elif dns_type != None:
                    dns_records = self.zones.dns_records.get(zone["id"], params={'type': dns_type})
                else:
                    dns_records = self.zones.dns_records.get(zone["id"])
                dnss.append(dns_records)
            except self.exceptions.CloudFlareAPIError as e:
                print('/zones/dns_records.get %d %s - api call failed' % (e, e))
                continue
        return dnss

    def query_zones(self, query: dict | list[dict] | str | list[str] = None) -> list | None:
        """
        Function to query the zones that fits the query.
        :param query: Query 1 or more values of zone_id or name. If the query is an empty array, it will give everything in response
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

        if type(query) == dict and "name" in query:  # If cloudflare_hosts: {"name": "blarg", "dns_type": "blarg"}
            query = [query["name"]]
        elif type(query) == list and len(query) != 0 and type(query[0]) == dict and "name" in query[0]:  # If cloudflare_hosts: [{"name": "blarg", "dns_type": "blarg"}, {...}, ...]
            query = [item["name"] for item in query]
        elif type(query) == list and len(query) != 0 and type(query[0]) == str:
            pass
        elif type(query) == str:
            query = [query]
        else:
            print(f"invalid query for query_zones", query)
            exit(1)

        queried_zones = []
        for zone in zones:
            if zone["id"] in query or zone["name"] in query:
                queried_zones.append(zone)

        return queried_zones
