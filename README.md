# vps-manager

Script to manage VPS switching and cloudflare settings.
The script is meant to automate switching between a main VPS and a backup VPS.

### Configuring `settings.json`

settings.json is the config file to tune this application. Here you can specify the VPS servers and their information,
and also the possibility to update the DNS records on cloudflare.

***If this application is meant to be run by multiple peers, only 1 peer should have control over cloudflare!***

Template/Example:
```json
{
  "check_interval": 600,
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
      "local_ip": "10.0.0.1"
    },
    {
      "name": "Backup VPS",
      "ip": "123.201.24.12",
      "port": 51820,
      "public_key": "qwertyuiopasdfghjklzxcvbnm/1234567890QWERTY=",
      "priority": 2,
      "subnet": "10.0.1.0/24",
      "local_ip": "10.0.1.1"
    }
  ],
  "tests": [
    {
      "hostname": "example.org",
      "path": "/_matrix/federation/v1/version",
      "response_code": 200
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