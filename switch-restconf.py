#!/usr/bin/python
#
# Copyright (c) 2018
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# ---------------------------------------------------------------------------

import requests
import sys
import json

# Ignore warnning from certificates
requests.packages.urllib3.disable_warnings()

# Import Environment file which contains all the host and sensitve data.
# Purposly part of the git ignore.
import env_lab

# TO CHANGE THE ENVIRONMENT just CHANGE THE NAME HERE !!! ------------
HOST_ENV = env_lab.HM_SW01

# Host name or IP address of yor network device and restconf port.
HOST = HOST_ENV['host']
PORT = HOST_ENV['restconf_port']

# Restconf credentials
USER = HOST_ENV['username']
PASS = HOST_ENV['password']

# Not sure why I did this tbh... just lazy to write "" 
GET = "GET"
POST = "POST"
PATCH = "PATCH"
DELETE = "DELETE"
PUT = "PUT"

# DISCLAIMER: This is just a code I did in my spare time and is for fun only.
# Please don't judge my bad coding style - this was done on the fly, and I still need to refactor.
# Ejoy...

def makeApiCall(method, resource, payload):
    """
        General funtion that executes the RESTCONF call based on the method, resource uri and payload.
    """

    url = "https://{h}:{p}/restconf/{r}".format(h=HOST, p=PORT, r=resource)
    # print("\n ... Debug: {} ---\n".format(url))

    # Specify headers for the RESTCONF
    headers = {'Content-Type': 'application/yang-data+json',
               'Accept': 'application/yang-data+json'}

    # Simply does the API call
    response = requests.request(method, url, auth=(USER, PASS), data=payload, headers=headers, verify=False)

    try:
        return (response.json())
    except:
        print(response)
        return ""


def ppJSON(parsed):
    """ Pretty Print JSON so it's visible better """
    print(json.dumps(parsed, indent=4, sort_keys=True))

# --------------------

def validateRestconf():
    """ Validate that we can reach RESTCONF and display available resources """

    response = makeApiCall(GET, resource="", payload="")
    print(ppJSON(response))

    # Display available yang models for this device
    resource = "data/netconf-state/capabilities"
    response = makeApiCall(GET, resource, payload="")
    print(ppJSON(response))


def getInterfaceOper():

    # ---- Get detailed interface info - Detailed information about the traffic that is seen on a port.
    # ---- We can monitor all sorts of traffic on all ports
    # resource = "data/Cisco-IOS-XE-interfaces-oper:interfaces"
    # response = makeApiCall(GET, resource, payload="")
    # print(ppJSON(response))

    # ---- Get detailed of a SPECIFIC interface info - Detailed information about the traffic that is seen on a port.
    # ---- We can monitor all sorts of traffic on all ports
    resource = "data/Cisco-IOS-XE-interfaces-oper:interfaces/interface=GigabitEthernet1%2F0%2F15"
    response = makeApiCall(GET, resource, payload="")
    print(ppJSON(response))


def setInterfaceOper():

    data = {
            "Cisco-IOS-XE-interfaces-oper:interface": {
            "description" :  "Modified from a RESTCONF",
            "ether-state" : {
                "auto-negotiate" : "false",
                "negotiated-duplex-mode" : "1000"
            }
        }   
    }

    payload = json.dumps(data)

    # ---- Set detailed of a SPECIFIC interface
    resource = "data/Cisco-IOS-XE-interfaces-oper:interfaces/interface=GigabitEthernet1%2F0%2F17"
    response = makeApiCall(PATCH, resource, payload)
    print(ppJSON(response))


def getVLAN():
    """
        Simlar to "show vlan" command in the CLI.
    """

    print("Fatching VLAN information...")

    # ---- GET details of all VLANs ----
    resource = "data/Cisco-IOS-XE-vlan-oper:vlans/vlan"
    response = makeApiCall(GET, resource, payload="")
    print(ppJSON(response))


def getInterface(name="", int_id=""):
    """
        If interface name and id (i.e. number) are specified, return info for that interface.
        Othwerise, return all interfaces.
    """

    if name and int_id: # ---- Get a specific interface
        print("Fatching info for interface {n} {i} ...".format(n=name, i=int_id))
        resource = "data/Cisco-IOS-XE-native:native/interface/{n}={i}".format(n=name, i=int_id)
    else: # ---- Get ALL interfaces
        print("Fatching info for all interfaces ...")
        resource = "data/Cisco-IOS-XE-native:native/interface"

    response = makeApiCall(GET, resource, payload="")
    print(ppJSON(response))


def setInterfaceStatus(name, id, status):
    """
        Sets the interface status to shut or no shut.

        TODO: Adjust so it is generic and can take any interface name and number.
    """

    print("Changing interface status...")

    if status == "shut":
        data = {
            "Cisco-IOS-XE-native:GigabitEthernet": {
                "name": "1/0/16",
                "shutdown": [""]
            }
        }
    elif status == "no shut":
        data = {
            "Cisco-IOS-XE-native:GigabitEthernet": {
                "name": "1/0/16"
            }
        }
    else:
        print("Use 'shut' or 'no shut' as the status")
        return

    payload = json.dumps(data)

    resource = "data/Cisco-IOS-XE-native:native/interface/{n}={i}".format(n=name, i=id)
    # For Cisco native, we need to use PUT, as "shutdown" is only displayed if port is admin down
    response = makeApiCall(PUT, resource, payload)
    print(ppJSON(response))


def setInterfaceVlan(name, int_id, vlan_id):
    """
        NOTE: data body uses forward-slash to identify interface name (e.g. 1/0/22), while
        url path uses back-slash (e.g. 1\0\22), so some parsing might be needed to automate this part.'

        TODO: Adjust so it is generic and can take any interface name and number. 
    """

    print("Changing VLAN assignment...")

    # Create new data      
    data = {
        "Cisco-IOS-XE-native:GigabitEthernet": {
            "name": "1/0/22",
            "switchport-config": {
            "switchport": {
                "Cisco-IOS-XE-switch:access": {
                    "vlan": {
                        "vlan": vlan_id
                    }
                },
                "Cisco-IOS-XE-switch:mode": {
                    "access": {}
                }
            }
        }
        },
    }

    payload = json.dumps(data)

    resource = "data/Cisco-IOS-XE-native:native/interface/{n}={i}".format(n=name, i=int_id)
    # Use patch to just adjust the values, no need to re-add the entry
    response = makeApiCall(PATCH, resource, payload)
    print(ppJSON(response))


def assignVlan():
    """
        TODO: Cmplete the function
    """

    data = {
        "Cisco-IOS-XE-vlan-oper:vlan": [
            {
                "id": 40,
                "name": "VLAN0040",
                "status": "active",
                "vlan-interfaces": [
                    {
                        "interface": "GigabitEthernet1/0/7",
                        "subinterface": 0
                    },
                ]
            }
        ]
    }

    # resource = "data/Cisco-IOS-XE-vlan-oper:vlans"
    # response = makeApiCall(PATCH, resource, payload="")
    # print(ppJSON(response))


# ----------------------------- Using IETF Yang Models ------------------------

def createInterfaceIETF():

    data = {
        "ietf-interfaces:interface": {
            "name": "Loopback100",
            "description": "Configured by RESTCONF",
            "type": "iana-if-type:softwareLoopback",
            "enabled": "true",
            "ietf-ip:ipv4": {
                "address": [
                    {
                        "ip": "172.16.100.2",
                        "netmask": "255.255.255.0"
                    }
                ]
            }
        }
    }

    payload = json.dumps(data)

    resource = "data/ietf-interfaces:interfaces"
    response = makeApiCall(POST, resource, payload)

    print("--- Using IETF Standard ---")
    print(ppJSON(response))


def setInterfaceConfigIETF():
    """ Set interface 
    """

    # ---- Loopback Example
    # data = {
    #     "ietf-interfaces:interface": {
    #         "name": "Loopback100",
    #         "description": "Configured by RESTCONF",
    #         "type": "iana-if-type:softwareLoopback",
    #         "enabled": "false",
    #         "ietf-ip:ipv4": {
    #             "address": [
    #                 {
    #                     "ip": "172.16.100.3",
    #                     "netmask": "255.255.255.0"
    #                 }
    #             ]
    #         }
    #     }
    # }
    
    # resource = "data/ietf-interfaces:interfaces/interface=Loopback100"
    
    # ---- GigabitEthernet Example
    data = {
        "ietf-interfaces:interface": {
            "enabled": "false"
        }
    }

    resource = "data/ietf-interfaces:interfaces/interface=GigabitEthernet1%2F0%2F15"
    
    payload = json.dumps(data)
    response = makeApiCall(PATCH, resource, payload)

    print("--- Using IETF Standard ---")
    print(ppJSON(response))


def getInterfaceIETF(interface=""):

    print("--- Using IETF Standard ---")

    if interface:
        # ---- get a SPECIFIC interface
        # ---- e.g. interface=Loopback100, GigabitEthernet1%2F0%2F15
        resource = "data/ietf-interfaces:interfaces/interface={}".format(interface)
        print(resource)
    else:
        # ---- get ALL interfaces
        resource = "data/ietf-interfaces:interfaces"
        
    response = makeApiCall(GET, resource, payload="")
    print(ppJSON(response))


def getArpTable():
    """
        Displays the ARP table. Note: only works with L3 interface.
    """

    resource = "data/Cisco-IOS-XE-arp-oper:arp-data"
    response = makeApiCall(GET, resource, payload="")
    print(ppJSON(response))


def getPortBasedOnMAC(end_mac):
    """
        Display the prort number for the endpoint connected to it, based on the endpoint MAC address.
    """

    resource = "data/Cisco-IOS-XE-matm-oper:matm-oper-data/"
    response = makeApiCall(GET, resource, payload="")

    # Filter the response to get the MAC table
    mac_table = response["Cisco-IOS-XE-matm-oper:matm-oper-data"]["matm-table"][0]["matm-mac-entry"]

    # Check if endpoint is in this MAC table (i.e. can you see the requested MAC address)
    for mac in mac_table:
        if mac["mac"] == end_mac:
            print(ppJSON(mac))
            return

    print("No client with this MAC address here...")
    print("Check the full output: ")
    print(ppJSON(response))


# create a main() method2
def main():
    """
        Main method...
    """

    # validateRestconf()

    # ---- 'show vlan'
    # getVLAN()

    # ---- User Cisco Native yang to dipslay info about interface and vlans
    # getInterface("Loopback", "200")
    # getInterface()
    # getInterface("GigabitEthernet", "1%2F0%2F15")
    # getInterface("GigabitEthernet", "1%2F0%2F17")
    # ---- Show that VLAN is displayed for interface - Note default VLAN is not displayed
    # getInterface("GigabitEthernet", "1%2F0%2F21")

    # ---- Set VLAN for a port
    # getInterface("GigabitEthernet", "1%2F0%2F22")
    # setInterfaceVlan("GigabitEthernet", "1%2F0%2F22", "30")
    # getInterface("GigabitEthernet", "1%2F0%2F22")

    # ---- Detailed Interface info
    # getInterfaceOper()

    # ---- Seach port based on the MAC address
    # getPortBasedOnMAC("00:1e:de:f9:f3:98")
    # getPortBasedOnMAC("f0:1e:34:13:3d:6d")

    # ---- Set interface status : enable/disable
    # getInterface("GigabitEthernet", "1%2F0%2F16")
    # setInterfaceStatus("GigabitEthernet", "1%2F0%2F16", "shut")
    # getInterface("GigabitEthernet", "1%2F0%2F16")


    # ---- IETF Commands
    # createInterfaceIETF()
    # setInterfaceConfigIETF()
    # getInterfaceIETF("GigabitEthernet1%2F0%2F15")
    # getInterfaceIETF("Loopback100")
    

if __name__ == '__main__':
    sys.exit(main())
