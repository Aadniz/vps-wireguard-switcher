import time

from datetime import datetime

from wireguard import Wireguard
from settings import Settings
from server import Server


def get_date_today():
    return datetime.today().strftime('%Y-%m-%d')


if __name__ == '__main__':

    # Init the needed classes
    Settings.init()
    Server.init()
    Wireguard.init()

    date_today = get_date_today()

    double_checks_counter = 0
    """
    Double checks to make sure the server is down actually, instead of jumping to the conclusion right away and switching
    """

    healthy_double_checks_counter = 0
    """
    The counter for when both VPS servers are up and running, but we want to switch because the active is not the one with highest priority
    """

    while True:
        if Settings.updated():
            print("Settings changed, reloading...")
            Settings.reload()
            Server.reload()

        # Reset date if not equal
        if date_today != get_date_today():
            Server.reset_max_switches()
            date_today = get_date_today()

        # Self-test first
        print("Running self-test ...")
        res = Server.self_test()
        if not res:
            print("The Server has no WAN internet!!")

        for host in Server.hosts:
            # Check if there is connection to the host
            print(f'Checking {host["name"]} ...')
            # The server.check returns a [local success, external success, total tests]
            res = Server.check(host)
            print("[local, external, total] = ", end="")
            print(res)

            host["status"] = res

        # Either local or external failure needed to switch
        if Settings.success_rate > Wireguard.active_server["status"][0] / Wireguard.active_server["status"][2] or Settings.success_rate > Wireguard.active_server["status"][1] / Wireguard.active_server["status"][2]:
            double_checks_counter += 1

            # Only switch once double_checks are more than Settings.double_checks
            if Settings.double_checks > double_checks_counter:
                print(f"[{double_checks_counter}/{Settings.double_checks}] Active server failed, switching in {(Settings.double_checks - double_checks_counter)} loops")
                continue

            for host in Server.hosts:
                if host == Wireguard.active_server:
                    continue
                # Switch to anything that has successes on local tests
                if not Server.WAN and host["status"][0] / host["status"][2] >= Settings.success_rate:
                    print(f'Switching to {host["name"]}')
                    Server.switch(host)
                    break
                # Switch to anything that has successes on both local and external
                if Server.WAN and host["status"][0] / host["status"][2] >= Settings.success_rate and host["status"][1] / host["status"][2] >= Settings.success_rate:
                    print(f'Switching to {host["name"]}')
                    Server.switch(host)
                    break

            time.sleep(10)
            print("Running self-test, checking that the server has WAN now ...", end="")
            res = Server.self_test()
            if res:
                print(" OK")
            else:
                print("\nCRITICAL! The Server STILL has no WAN internet!!")
                Wireguard.up = False
            double_checks_counter = 0

        # Pick the host with the highest score
        highest_score_host = None
        highest_score = 0
        for host in Server.hosts:
            multiplier = Settings.lowest_priority + Settings.highest_priority - host["priority"]
            score = (host["status"][0] + host["status"][1]) * multiplier
            if score > highest_score:
                highest_score = score
                highest_score_host = host

        if Wireguard.up and Wireguard.active_server is not None and Server.WAN:  # Check if active server is the highest priority one
            if Wireguard.active_server == highest_score_host:  # Should land here 99.9% of the time
                healthy_double_checks_counter = 0
            elif healthy_double_checks_counter >= Settings.healthy_switching_checks:
                # Switch
                print(f"Switching to {highest_score_host['name']}")
                Server.switch(highest_score_host)
                healthy_double_checks_counter = 0
            else:
                print(f"Want to switch to higher priority route {highest_score_host['name']}")
                print(f"Switching in {round((Settings.healthy_switching_checks - healthy_double_checks_counter) * Settings.check_interval / 60, 1)} minutes ({Settings.healthy_switching_checks - healthy_double_checks_counter} loops)")
                healthy_double_checks_counter += 1
        else:  # Kickstart wireguard again
            if Settings.double_checks > double_checks_counter:
                double_checks_counter += 1
                print(f"[{double_checks_counter}/{Settings.double_checks}] Active server failed, Resetting wireguard settings in {(Settings.double_checks - double_checks_counter)} loops")
                continue
            print("Resetting wireguard settings ...")
            Server.switch(highest_score_host)
            if Wireguard.up:
                continue
            if Wireguard.active_server is None:
                print("Could not find active server!")
                print(f"zzzzzzzzzZZZZZZZZZZZZzzzzzz... ({Settings.check_interval}s)")
                time.sleep(Settings.check_interval)
                continue

        print(f"\nActive route through {Wireguard.active_server['name']}\n")
        print(f"zzzzzzzzzZZZZZZZZZZZZzzzzzz... ({Settings.check_interval}s)")
        time.sleep(Settings.check_interval)
