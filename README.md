# vps-manager

Program to manage VPS switching and cloudflare settings.
The program is meant to automate switching between the main VPS and backup VPS.

### Configuring `settings.json`

settings.json is the config file to tune this application. Here you can specify the VPS servers and their information,
and also the possibility to update the DNS records on cloudflare.

***If this application is meant to be run by multiple peers only 1 peer should have control over cloudflare!***

Template/Example:
```json
{
  "vps_servers": [
    {
      "ip": "123.123.123.123",
      "port": 51820,
      "public_key": "abcdefghijklmnop/qrstuv+wxyz1234567890ABCDE=",
      "priority": 1,
      "subnet": "10.0.0.0/24"
    },
    {
      "ip": "123.201.24.12",
      "port": 51820,
      "public_key": "qwertyuiopasdfghjklzxcvbnm/1234567890QWERTY=",
      "priority": 2,
      "subnet": "10.0.1.0/24"
    }
  ]
}
```