
# Table of Contents

1.  [Client Tutorial](#org13ec6a0)
    1.  [Install wireguard](#org251f646)
    2.  [Setting up the keys](#orgeb88faa)
    3.  [Configuring wg0.conf](#org6f5f2b6)
    4.  [Adding peer to the server(s)](#org89becf1)
    5.  [Starting the service](#orgbb6507c)
    6.  [Switching from one to another VPS](#org29ed7df)
    7.  [Automate the VPS switching](#orgc0d0e9e)
        1.  [settings.json](#org186d7f5)
        2.  [Systemd service](#org66392ee)

\newpage


<a id="org13ec6a0"></a>

# Client Tutorial

We are assuming that the client is running a Debian 12 instance. We will ensure this setup is possible to achieve over SSH throughout the steps.


<a id="org251f646"></a>

## Install wireguard

    sudo apt update
    sudo apt upgrade
    sudo apt install wireguard


<a id="orgeb88faa"></a>

## Setting up the keys

Generate the public and private keys by running the following commands

    wg genkey | sudo tee /etc/wireguard/private.key
    sudo chmod go= /etc/wireguard/private.key
    sudo cat /etc/wireguard/private.key | wg pubkey | sudo tee /etc/wireguard/public.key


<a id="org6f5f2b6"></a>

## Configuring wg0.conf

The configuration file is located at \textit{/etc/wireguard/wg0.conf}

    [Interface]
    Address = 10.0.0.205/16
    ListenPort = 51820
    PrivateKey = hZ46R....tsNy=
    
    [Peer]
    PublicKey = 9vxKz...IWns=
    AllowedIPs = 0.0.0.0/0
    Endpoint = 18.52.125.212:51820
    PersistentKeepalive = 25
    
    [Peer]
    PublicKey = 6PsUS...wbxBY=
    Endpoint = 93.122.227.117:51820
    PersistentKeepalive = 25

In the configuration we want to set the ip address within the subnet of the wireguard network, with the same ending numbers. So having 192.168.1.205, set the wireguard ip of 10.0.0.205.

You can&rsquo;t set the private key to link to the private.key file. We have to copy paste the value of the file into the configuration.

The peer that has \textit{AllowedIPs} is the peer that gets the gateway priority.


<a id="org89becf1"></a>

## Adding peer to the server(s)

Copy the content of \textit{/etc/wireguard/public.key} from the client, and paste in the following command on the server

    sudo wg set wg0 peer PeUm3...29hg= allowed-ips 10.0.0.204 persistent-keepalive 25


<a id="orgbb6507c"></a>

## Starting the service

    sudo systemctl start wg-quick@wg0.service
    sudo journalctl -fu wg-quick@wg0.service


<a id="org29ed7df"></a>

## Switching from one to another VPS

When switching from one wireguard VPS to another, it is important to never overlap the Allowed-IPs.

Given the active VPS1 public key being \textit{9vxKz...IWns=} and the other VPS2 public key being \textit{6PsUS...wbxBY}, the order of switching should look like this:

    # Cut off gateway to VPS1
    sudo wg set wg0 peer 9vxKz...IWns= allowed-ips 10.0.0.0/24
    # Start gateway to VPS2
    sudo wg set wg0 peer 6PsUS...wbxBY allowed-ips 0.0.0.0/0


<a id="orgc0d0e9e"></a>

## Automate the VPS switching

For the last couple of days, I have made a python script that should automatically switch to the working VPS server during interruptions.
Privacy VPS services such as Njalla or 1984 Hosting are bound to be unreliable at times, therefore requires such configuration.

Github link: <https://github.com/D3faIt/vps-wireguard-switcher>


<a id="org186d7f5"></a>

### settings.json

Looking at the github link, we need to set our settings.json configuration inside the project folder.
When tuning the settings, we can test it&rsquo;s working by running the following commands to run:

    python3 -m venv venv
    source venv/bin/activate
    ./venv/bin/pip3 install -r requirements.txt
    sudo venv/bin/python3 main.py


<a id="org66392ee"></a>

### Systemd service

Create a systemd serivce that runs this script under \textit{/etc/systemd/system/}.
Paste this content

    [Unit]
    Description=VPS manager
    After=network.target
    
    [Service]
    WorkingDirectory=/home/pi/Documents/vps-manager
    ExecStart=/home/user/Documents/vps-manager/venv/bin/python3 /home/user/Documents/vps-manager/main.py
    RestartSec=5
    Restart=always
    Environment=PYTHONUNBUFFERED=1
    
    [Install]
    WantedBy=multi-user.target

Now run the systemd service, and monitor it. Assuming the systemd serivce is called \textit{vps-manager.service}, we will run this command:

    sudo systemctl start vps-manager && sudo journalctl -fu vps-manager --all

If everything are working as expected, we can enable it:

    sudo systemctl enable vps-manager

