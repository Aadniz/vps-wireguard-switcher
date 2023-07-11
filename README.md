# vps-manager

Script to manage VPS switching and cloudflare settings.
The script is meant to automate switching between a main VPS and a backup VPS.

### Setting up
When setting up the project, we first need to clone the repository, and enter the directory
```bash
git clone https://github.com/D3faIt/vps-wireguard-switcher.git
cd vps-wireguard-switcher
```
Now we need to create the virtual environment.
```bash
python3 -m venv venv
```
Now that it is created, we source the `venv/bin/activate` file
```bash
source venv/bin/activate
```
Lastly install the `requirements.txt` using the pip environment
```bash
./venv/bin/pip3 install -r requirements.txt
```

### Configuring `settings.json`

settings.json is the config file to tune this application. Here you can specify the VPS servers and their information,
and also the possibility to update the DNS records on cloudflare.

***If this application is meant to be run by multiple peers, only 1 peer should have control over cloudflare!***

Template/Example:
```json
{
  "cloudflare_key": "abcdefghijklmnopqrstuvwxyz1234567890ABCD",
  "cloudflare_hosts": ["example.org", "test.com"],
  "check_interval": 600,
  "healthy_switching_checks": 16,
  "wireguard_interface": "wg0",
  "max_switches_a_day": 8,
  "max_ms": 750,
  "max_http_ms": 8500,
  "success_rate": 0.6,
  "double_checks": 3,
  "self_test_addresses": ["1.1.1.1", "8.8.8.8", "1.0.0.1"],
  "self_test_success_rate": 0.7,
  "vps_servers": [
    {
      "name": "Main VPS",
      "ip": "123.123.123.123",
      "port": 51820,
      "public_key": "abcdefghijklmnop/qrstuv+wxyz1234567890ABCDE=",
      "priority": 1,
      "subnet": "10.0.0.0/24",
      "local_ip": "10.0.0.1",
      "persistent_keepalive": 25
    },
    {
      "name": "Backup VPS",
      "ip": "123.201.24.12",
      "port": 51820,
      "public_key": "qwertyuiopasdfghjklzxcvbnm/1234567890QWERTY=",
      "priority": 2,
      "subnet": "10.0.1.0/24",
      "local_ip": "10.0.1.1",
      "persistent_keepalive": 25
    }
  ],
  "tests": [
    {
      "hostname": "example.org:443",
      "path": "/_matrix/federation/v1/version",
      "response_code": 200,
      "scheme": "https"
    },
    {
      "hostname": "example.org",
      "path": "/.well-known/matrix/client",
      "response_code": 200
    },
    {
      "hostname": "example.com",
      "path": "/.well-known/matrix/server",
      "response_code": 200
    }
  ]
}
```
| Attribute                | Type               | Default value | Required | Comment                                                                                                                                                                                             |
|--------------------------|--------------------|---------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| cloudflare_key           | string             | (None)        | No       | The cloudflare Bearer token key. If not set or incorrect, cloudflare API will remain untouched                                                                                                      |
| cloudflare_hosts         | string \| string[] | (None)        | No       | The hosts, or zone ids that determines which domains to control. **NOTE:** IF cloudflare_key IS SET AND cloudflare_hosts IS EMPTY, IT WILL CONTROL ALL ZONES                                        |
| check_interval           | int                | 300           | No       | The interval between each check in seconds                                                                                                                                                          |
| healthy_switching_checks | int                | 16            | No       | If hosts are up and running, but the active route is not set to the highest priority, this is how many loops needed to pass before switching                                                        |
| wireguard_interface      | string             | (None)        | No       | Wireguard interface, eg: wg0, wg1 etc...                                                                                                                                                            |
| max_switches_a_day       | int                | 8             | No       | To prevent hanging on to 1st priority with a probable unstable connection, we set a limit                                                                                                           |
| max_ms                   | int                | 750           | No       | Maximum allowed ping ms before result in failure for checking                                                                                                                                       |
| max_http_ms              | int                | 8000          | No       | Maximum allowed HTTP ms timing before result in failure for checking                                                                                                                                |
| success_rate             | int<0,1>           | 0.6           | No       | Minimum success rate for allowing a pass                                                                                                                                                            |
| double_checks            | int                | 3             | No       | When a failure occurs, the script will skip the check_interval and double check x amount of times before switching                                                                                  |
| self_test_addresses      | string \| string[] | 1.1.1.1       | No       | External hosts to test external internet connection. It will ping the hosts to verify it works.                                                                                                     |
| self_test_success_rate   | float              | 0.7           | No       | The amount of success rate to determine if external internet is working. In some cases, 1 or more hosts may have an outage, therefore can confirm that the internet is working using a success rate |
| vps_servers              | dict[]             | (None)        | **YES**  | For each server, these keys must be set: "ip", "port", "public_key", "subnet" and "local_ip"                                                                                                        |
| tests                    | dict[]             | (None)        | No       | HTTP test urls. For each test object, these keys must be set: "hostname" and "path".                                                                                                                |


### Running and testing
Once the setup is done, you should be able to run the program like so
```bash
venv/bin/python3 main.py
```

### Setting up systemd service
When setting up the systemd service, we can create the service below under `/etc/systemd/system/`,
and change the values to fit our needs. Change the paths to the correct directory.

```
[Unit]
Description=VPS manager
After=network.target

[Service]
WorkingDirectory=/home/user/Documents/vps-wireguard-switcher
ExecStart=/home/user/Documents/vps-wireguard-switcher/venv/bin/python3 /home/user/Documents/vps-wireguard-switcher/main.py
RestartSec=5
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Assuming we call the service `vps-manager.service`, start and test the service like so:
```bash
sudo systemctl start vps-manager.service && sudo journalctl -fu vps-mamager.service
```

Lastly, if everything works like it should, start the service at startup
```bash
sudo systemctl enable vps-manager.service
```