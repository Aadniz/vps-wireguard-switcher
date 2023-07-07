import time

from datetime import datetime

from cloudflare import Cloudflare
from wireguard import Wireguard
from settings import Settings
from server import Server


def get_date_today():
    return datetime.today().strftime('%Y-%m-%d')


if __name__ == '__main__':

    # Init the settings class
    Settings.init()

    # Init the server class
    Server.init()

    # Init the wireguard class
    Wireguard.init()

    # Get the date today
    date_today = get_date_today()

    double_checks = 0

    while True:
        # Reset date if not equal
        if date_today != get_date_today():
            Server.reset_max_switches()

        # Self-test first
        print("Running self-test ...")
        res = Server.self_test()
        if not res:
            print("The Server has no WAN internet!!")

        for host in Server.hosts:
            # Check if there is connection to the host
            print("Checking " + host["name"] + " ...")
            # The server.check returns a [local success, external success, total tests]
            res = Server.check(host)
            print("[local, external, total] = ", end="")
            print(res)

            host["status"] = res

        # Kickstart wireguard again
        if not Wireguard.up:
            # Pick the host with the highest score
            highest_score_host = None
            highest_score = 0
            for host in Server.hosts:
                multiplier = Settings.lowest_priority + Settings.highest_priority - host["priority"]
                score = (host["status"][0] + host["status"][1]) * multiplier
                if score > highest_score:
                    highest_score = score
                    highest_score_host = host
            print("Resetting wireguard settings ...")
            Wireguard.reset_or_switch(highest_score_host)
            if Wireguard.up:
                continue
            if Wireguard.active_server is None:
                print("Could not find active server!")
                print("zzzzzzzzzZZZZZZZZZZZZzzzzzz... (" + str(Settings.check_interval) + "s)")
                time.sleep(Settings.check_interval)
                continue

        # Either local or external failure needed to switch
        if Settings.success_rate > Wireguard.active_server["status"][0] / Wireguard.active_server["status"][2] or Settings.success_rate > Wireguard.active_server["status"][1] / Wireguard.active_server["status"][2]:
            double_checks += 1
            print("["+str(double_checks)+"/"+str(Settings.double_checks)+"] Active server failed, switching in " + str(Settings.double_checks - double_checks) + " loops")
            # Only switch once double_checks are more than Settings.double_checks
            if Settings.double_checks > double_checks:
                continue

            for host in Server.hosts:
                if host == Wireguard.active_server:
                    continue
                # Switch to anything that has successes on local tests
                if not Server.WAN and host["status"][0] / host["status"][2] >= Settings.success_rate:
                    print("Switching to " + host["name"])
                    Server.switch(host)
                    break
                # Switch to anything that has successes on both local and external
                if Server.WAN and host["status"][0] / host["status"][2] >= Settings.success_rate and host["status"][1] / host["status"][2] >= Settings.success_rate:
                    print("Switching to " + host["name"])
                    Server.switch(host)
                    break


            double_checks = 0

        print("zzzzzzzzzZZZZZZZZZZZZzzzzzz... ("+str(Settings.check_interval)+"s)")
        time.sleep(Settings.check_interval)
