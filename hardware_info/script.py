from datetime import datetime
from getmac import get_mac_address
from os.path import exists
from quart import Quart, request
import ast
import asyncio
import json
import math
import os
import platform
import psutil
import requests
import socket
import speedtest
import subprocess
import sys

app = Quart('self_server')
sampling_frequency = 5

def get_token():
    keycloak_payload = {
        'grant_type': 'client_credentials',
        'client_id': os.environ['AERIOS_CB_CLIENT_ID'],
        'client_secret': os.environ['AERIOS_CB_CLIENT_SECRET']
    }

    keycloak_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(url=os.environ['AERIOS_KEYCLOAK_URL'] + '/auth/realms/' + os.environ['AERIOS_KEYCLOAK_REALM'] + '/protocol/openid-connect/token', data=keycloak_payload, headers=keycloak_headers, timeout=3)

        if response.status_code == 200:
            return json.loads(response.text)['access_token']
        else:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the access token in Keycloak. Aborting execution...')
                print('Keycloak error:', response.text, sep='\n')

            sys.exit(1)
    except Exception as e:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the access token in Keycloak. Aborting execution...')
            print('Keycloak error:', e, sep='\n')

        sys.exit(1)

async def self_task():
    cpu_count = psutil.cpu_count()
    cpu_cores = -1 if cpu_count is None else cpu_count
    cpu_freq = psutil.cpu_freq()

    if cpu_freq is None:
        cpu_freq_max = -1
    else:
        cpu_freq_max = math.ceil(cpu_freq.current) if cpu_freq.max == 0.0 else math.ceil(cpu_freq.max)

    ram_capacity = math.ceil(psutil.virtual_memory().total / 1000000)
    mac_address = get_mac_address()
    disk = None

    try:
        devices = json.loads(subprocess.run(['lsblk', '-J', '-a', '-o', 'TYPE,ROTA'], capture_output=True, text=True).stdout)['blockdevices']
        disk = next((device for device in devices if device['type'] == 'disk'), None)
    except:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the disk type of the Infrastructure Element. Using an empty value...')

    if disk is None:
        disk_type = ''
    elif disk['rota']:
        disk_type = 'HDD'
    else:
        disk_type = 'SSD'

    gpu = os.environ['AERIOS_IE_GPU'] if 'AERIOS_IE_GPU' in os.environ else False

    if 'AERIOS_IE_GPU_MEMORY' in os.environ:
        try:
            gpu_memory = int(os.environ['AERIOS_IE_GPU_MEMORY'])
        except:
            gpu_memory = -1
    else:
        gpu_memory = -1

    physical_interfaces = []

    try:
        for interface in json.loads(subprocess.run(['ip', '-s', '-j', 'link', 'show'], capture_output=True, text=True).stdout):
            if any(interface['ifname'].startswith(pattern) for pattern in ['eth', 'enp', 'ens', 'wlan', 'wlp']):
                physical_interfaces.append(interface['ifname'])
    except:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the physical interfaces of the Infrastructure Element. Using an empty value...')

    power_source = os.environ['AERIOS_POWER_SOURCE'] if 'AERIOS_POWER_SOURCE' in os.environ else 'urn:ngsi-ld:none'

    if 'AERIOS_ENERGY_EFFICIENCY_RATIO' in os.environ:
        try:
            energy_efficiency_ratio = int(os.environ['AERIOS_ENERGY_EFFICIENCY_RATIO'])
        except:
            energy_efficiency_ratio = 0
    else:
        energy_efficiency_ratio = 0

    self_headers = {
        'Content-Type': 'application/json'
    }

    if os.environ['AERIOS_AUTHORIZATION'] == "true":
        orion_headers = {
            'aerOS': 'true',
            'Authorization': 'Bearer ' + get_token()
        }
    else:
        orion_headers = {
            'aerOS': 'true'
        }

    try:
        if os.environ['AERIOS_AUTHORIZATION'] == "true":
            response = requests.get(url=os.environ['AERIOS_KRAKEND_URL'] + '/entities?type=Domain&local=true', headers=orion_headers, timeout=3)
        else:
            response = requests.get(url=os.environ['AERIOS_ORION_URL'] + '/ngsi-ld/v1/entities?type=Domain&local=true', headers=orion_headers, timeout=3)

        if response.status_code == 200:
            domain = json.loads(response.text)[0]['id']
        else:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to get the entity Domain from Orion. It is not possible to create the entity associated with this Infrastructure Element in Orion. Aborting execution...')
                print('Orion error:', response.text, sep='\n')

            sys.exit(1)
    except Exception as e:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to get the entity Domain from Orion. It is not possible to create the entity associated with this Infrastructure Element in Orion. Aborting execution...')
            print('Orion error:', e, sep='\n')

        sys.exit(1)

    exists_ie = False

    try:
        if os.environ['AERIOS_AUTHORIZATION'] == "true":
            response = requests.get(url=os.environ['AERIOS_KRAKEND_URL'] + '/entities/urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', '') + '?local=true', headers=orion_headers, timeout=3)
        else:
            response = requests.get(url=os.environ['AERIOS_ORION_URL'] + '/ngsi-ld/v1/entities/urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', '') + '?local=true', headers=orion_headers, timeout=3)

        if response.status_code == 200:
            exists_ie = True
        elif os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to get the entity InfrastructureElement from Orion. The entity does not exist. Creating a new one...')
            print('Orion error:', response.text, sep='\n')
    except Exception as e:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to get the entity InfrastructureElement from Orion. The entity does not exist. Creating a new one...')
            print('Orion error:', e, sep='\n')

    orion_headers['Content-Type'] = 'application/json'

    if not exists_ie:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sckt:
                sckt.connect(('8.8.8.8', 80))
                internal_ip_address = sckt.getsockname()[0]
        except:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the internal IP address of the Infrastructure Element. Using an empty value...')

            internal_ip_address = ''

        cpu_architecture = platform.machine()

        if cpu_architecture == 'x86_64':
            cpu_architecture = 'AMD64'
            infrastructureElementTier = 'Cloud'
        elif cpu_architecture == 'aarch64':
            cpu_architecture = 'ARM64'
            infrastructureElementTier = 'Edge'
        elif cpu_architecture == 'riscv64':
            cpu_architecture = 'RISC-V'
            infrastructureElementTier = 'Edge'
        else:
            infrastructureElementTier = 'Edge'

        orion_payload = {
            'id': 'urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', ''),
            'type': 'InfrastructureElement',
            'domain': {
                'type': 'Relationship',
                'object': domain
            },
            'hostname': {
                'type': 'Property',
                'value': socket.gethostname()
            },
            'containerTechnology': {
                'type': 'Property',
                'value': os.environ['AERIOS_CONTAINER_TECHNOLOGY']
            },
            'internalIpAddress': {
                'type': 'Property',
                'value': internal_ip_address
            },
            'macAddress': {
                'type': 'Property',
                'value': mac_address
            },
            'lowLevelOrchestrator': {
                'type': 'Relationship',
                'object': 'urn:ngsi-ld:LowLevelOrchestrator:' + domain[domain.rfind(':') + 1 : ] + ':' + os.environ['AERIOS_CONTAINER_TECHNOLOGY']
            },
            'cpuCores': {
                'type': 'Property',
                'value': cpu_cores
            },
            'cpuFreqMax': {
                'type': 'Property',
                'value': cpu_freq_max,
                'unitCode': 'Megahertzs (MHz)'
            },
            'currentCpuUsage': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Percentage (%)'
            },
            'gpu': {
                'type': 'Property',
                'value': gpu
            },
            'gpuMemory': {
                'type': 'Property',
                'value': gpu_memory,
                'unitCode': 'Megabytes (MB)'
            },
            'ramCapacity': {
                'type': 'Property',
                'value': ram_capacity,
                'unitCode': 'Megabytes (MB)'
            },
            'availableRam': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabytes (MB)'
            },
            'currentRamUsage': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabytes (MB)'
            },
            'currentRamUsagePct': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Percentage (%)'
            },
            'diskType': {
                'type': 'Property',
                'value': disk_type
            },
            'diskCapacity': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabytes (MB)'
            },
            'availableDisk': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabytes (MB)'
            },
            'currentDiskUsage': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabytes (MB)'
            },
            'currentDiskUsagePct': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Percentage (%)'
            },
            'netSpeedUp': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabits per second (Mb/s)'
            },
            'netSpeedDown': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Megabits per second (Mb/s)'
            },
            'netTrafficUp': {
                'type': 'Property',
                'value': -1.0,
                'unitCode': 'Megabytes per second (MB/s)'
            },
            'netTrafficDown': {
                'type': 'Property',
                'value': -1.0,
                'unitCode': 'Megabytes per second (MB/s)'
            },
            'netLostPackages': {
                'type': 'Property',
                'value': -1
            },
            'avgPowerConsumption': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Watts (W)'
            },
            'currentPowerConsumption': {
                'type': 'Property',
                'value': -1,
                'unitCode': 'Watts (W)'
            },
            'powerSource': {
                'type': 'Relationship',
                'object': power_source
            },
            'energyEfficiencyRatio': {
                'type': 'Property',
                'value': energy_efficiency_ratio
            },
            'realTimeCapable': {
                'type': 'Property',
                'value': False
            },
            'trustScore': {
                'type': 'Property',
                'value': -1
            },
            'cpuArchitecture': {
                'type': 'Relationship',
                'object': 'urn:ngsi-ld:CpuArchitecture:' + cpu_architecture
            },
            'operatingSystem': {
                'type': 'Relationship',
                'object': 'urn:ngsi-ld:OperatingSystem:' + platform.system()
            },
            'infrastructureElementTier': {
                'type': 'Relationship',
                'object': 'urn:ngsi-ld:InfrastructureElementTier:' + infrastructureElementTier
            },
            'infrastructureElementStatus': {
                'type': 'Relationship',
                'object': 'urn:ngsi-ld:InfrastructureElementStatus:Ready'
            },
            'location': {
                'type': 'GeoProperty',
                'value': {
                    'type': 'Point',
                    'coordinates': ast.literal_eval(os.environ['AERIOS_IE_LOCATION'])
                }
            }
        }

        try:
            if os.environ['AERIOS_AUTHORIZATION'] == "true":
                response = requests.post(url=os.environ['AERIOS_KRAKEND_URL'] + '/entities?local=true', data=json.dumps(orion_payload), headers=orion_headers, timeout=3)
            else:
                response = requests.post(url=os.environ['AERIOS_ORION_URL'] + '/ngsi-ld/v1/entities?local=true', data=json.dumps(orion_payload), headers=orion_headers, timeout=3)

            if response.status_code != 201:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to create the entity InfrastructureElement in Orion. Aborting execution...')
                    print('Orion error:', response.text, sep='\n')

                sys.exit(1)
        except Exception as e:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to create the entity InfrastructureElement in Orion. Aborting execution...')
                print('Orion error:', e, sep='\n')

            sys.exit(1)

        self_payload = {
            'id': 'urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', ''),
            'cpuCores': cpu_cores,
            'cpuFreqMax': cpu_freq_max,
            'currentCpuUsage': -1,
            'gpu': gpu,
            'gpuMemory': gpu_memory,
            'ramCapacity': ram_capacity,
            'availableRam': -1,
            'currentRamUsage': -1,
            'currentRamUsagePct': -1,
            'diskType': disk_type,
            'diskCapacity': -1,
            'availableDisk': -1,
            'currentDiskUsage': -1,
            'currentDiskUsagePct': -1,
            'netSpeedUp': -1,
            'netSpeedDown': -1,
            'netTrafficUp': -1.0,
            'netTrafficDown': -1.0,
            'netLostPackages': -1,
            'avgPowerConsumption': -1,
            'currentPowerConsumption': -1,
            'energyEfficiencyRatio': energy_efficiency_ratio,
            'realTimeCapable': False
        }

        try:
            response = requests.post(url='http://' + os.environ['AERIOS_IE_IP'] + ':8001/data', data=json.dumps(self_payload), headers=self_headers, timeout=5)

            if response.status_code != 201 and os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the facts through the Self-orchestrator.')
        except:
            if os.environ['AERIOS_VERBOSE'] == "true":
               print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the facts through the Self-orchestrator.')

    while True:
        current_cpu_usage = math.ceil(psutil.cpu_percent(interval=1))
        available_ram = math.ceil(psutil.virtual_memory().available / 1000000)
        current_ram_usage = ram_capacity - available_ram
        current_ram_usage_pct = math.ceil((current_ram_usage * 100) / ram_capacity)
        real_time_capable = exists('/proc/self-realtimeness')

        if physical_interfaces:
            net_lost_packages = 0

            try:
                for interface in json.loads(subprocess.run(['ip', '-s', '-j', 'link', 'show'], capture_output=True, text=True).stdout):
                    if interface['ifname'] in physical_interfaces:
                        net_lost_packages += interface['stats64']['rx']['errors'] + interface['stats64']['tx']['errors']
            except:
                net_lost_packages = -1

            net_io_counters = psutil.net_io_counters(pernic=True, nowrap=True)
            initial_sent = net_io_counters[physical_interfaces[0]].bytes_sent
            initial_recv = net_io_counters[physical_interfaces[0]].bytes_recv
            await asyncio.sleep(1)
            net_io_counters = psutil.net_io_counters(pernic=True, nowrap=True)
            final_sent = net_io_counters[physical_interfaces[0]].bytes_sent
            final_recv = net_io_counters[physical_interfaces[0]].bytes_recv
            net_traffic_up = round((final_sent - initial_sent) / 1000000, 2)
            net_traffic_down = round((final_recv - initial_recv) / 1000000, 2)
        else:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the network traffic of the Infrastructure Element. Using an empty value...')

            net_lost_packages = -1
            net_traffic_up = -1.0
            net_traffic_down = -1.0

        if os.environ['AERIOS_IE_NET_SPEED_TEST'] == "true":
            try:
                speed_test = speedtest.Speedtest()
                speed_test.get_best_server()
                net_speed_up = round(speed_test.upload(threads=1) / 1000000)
                net_speed_down = round(speed_test.download(threads=1) / 1000000)
            except:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the network speed of the Infrastructure Element. Using an empty value...')

                net_speed_up = -1
                net_speed_down = -1

        try:
            disk_usage = psutil.disk_usage('/')
        except:
            disk_usage = None

        if disk_usage is not None:
            disk_capacity = math.ceil(disk_usage.total / 1000000)
            available_disk = math.ceil(disk_usage.free / 1000000)
            current_disk_usage = math.ceil(disk_usage.used / 1000000)
            current_disk_usage_pct = math.ceil(disk_usage.percent)
        else:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the disk usage of the Infrastructure Element. Using an empty value...')

            disk_capacity = -1
            available_disk = -1
            current_disk_usage = -1
            current_disk_usage_pct = -1

        orion_payload = {
            'currentCpuUsage': {
                'value': current_cpu_usage
            },
            'availableRam': {
                'value': available_ram
            },
            'currentRamUsage': {
                'value': current_ram_usage
            },
            'currentRamUsagePct': {
                'value': current_ram_usage_pct
            },
            'realTimeCapable': {
                'value': real_time_capable
            }
        }

        if disk_usage is not None:
            orion_payload['diskCapacity'] = {
                'value': disk_capacity
            }

            orion_payload['availableDisk'] = {
                'value': available_disk
            }

            orion_payload['currentDiskUsage'] = {
                'value': current_disk_usage
            }

            orion_payload['currentDiskUsagePct'] = {
                'value': current_disk_usage_pct
            }

        if net_lost_packages != -1:
            orion_payload['netLostPackages'] = {
                'value': net_lost_packages
            }

        if net_traffic_up != -1.0:
            orion_payload['netTrafficUp'] = {
                'value': net_traffic_up
            }

        if net_traffic_down != -1.0:
            orion_payload['netTrafficDown'] = {
                'value': net_traffic_down
            }

        if os.environ['AERIOS_IE_NET_SPEED_TEST'] == "true":
            if net_speed_up != -1:
                orion_payload['netSpeedUp'] = {
                    'value': net_speed_up
                }

            if net_speed_down != -1:
                orion_payload['netSpeedDown'] = {
                    'value': net_speed_down
                }

        try:
            if os.environ['AERIOS_AUTHORIZATION'] == "true":
                response = requests.patch(url=os.environ['AERIOS_KRAKEND_URL'] + '/entities/urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', '') + '?local=true', data=json.dumps(orion_payload), headers=orion_headers, timeout=3)
            else:
                response = requests.patch(url=os.environ['AERIOS_ORION_URL'] + '/ngsi-ld/v1/entities/urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', '') + '?local=true', data=json.dumps(orion_payload), headers=orion_headers, timeout=3)

            if os.environ['AERIOS_AUTHORIZATION'] == "true" and response.status_code == 401:
                orion_headers = {
                    'aerOS': 'true',
                    'Authorization': 'Bearer ' + get_token(),
                    'Content-Type': 'application/json'
                }

                response = requests.patch(url=os.environ['AERIOS_KRAKEND_URL'] + '/entities/urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', '') + '?local=true', data=json.dumps(orion_payload), headers=orion_headers, timeout=3)

                if response.status_code == 401:
                    if os.environ['AERIOS_VERBOSE'] == "true":
                        print(datetime.now().isoformat()[:19] + ' - An authorization error occurred while trying to update the entity InfrastructureElement in Orion. Aborting execution...')
                        print('Orion error:', response.text, sep='\n')

                    sys.exit(1)
                elif response.status_code != 204 and os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the entity InfrastructureElement in Orion.')
                    print('Orion error:', response.text, sep='\n')
            elif response.status_code != 204 and os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the entity InfrastructureElement in Orion.')
                print('Orion error:', response.text, sep='\n')
        except Exception as e:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the entity InfrastructureElement in Orion.')
                print('Orion error:', e, sep='\n')

        self_payload = {
            'id': 'urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', ''),
            'currentCpuUsage': current_cpu_usage,
            'availableRam': available_ram,
            'currentRamUsage': current_ram_usage,
            'currentRamUsagePct': current_ram_usage_pct,
            'realTimeCapable': real_time_capable
        }

        if disk_usage is not None:
            self_payload['diskCapacity'] = disk_capacity
            self_payload['availableDisk'] = available_disk
            self_payload['currentDiskUsage'] = current_disk_usage
            self_payload['currentDiskUsagePct'] = current_disk_usage_pct

        if net_lost_packages != -1:
            self_payload['netLostPackages'] = net_lost_packages

        if net_traffic_up != -1.0:
            self_payload['netTrafficUp'] = net_traffic_up

        if net_traffic_down != -1.0:
            self_payload['netTrafficDown'] = net_traffic_down

        if os.environ['AERIOS_IE_NET_SPEED_TEST'] == "true":
            if net_speed_up != -1:
                self_payload['netSpeedUp'] = net_speed_up

            if net_speed_down != -1:
                self_payload['netSpeedDown'] = net_speed_down

        try:
            response = requests.post(url='http://' + os.environ['AERIOS_IE_IP'] + ':8001/data', data=json.dumps(self_payload), headers=self_headers, timeout=5)

            if response.status_code != 201 and os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the facts through the Self-orchestrator.')
        except:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the facts through the Self-orchestrator.')

        self_payload = {
            'id': 'urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', ''),
            'availableRam': available_ram,
            'currentCpuUsage': current_cpu_usage,
            'currentRamUsage': current_ram_usage,
            'currentRamUsagePct': current_ram_usage_pct,
            'ramCapacity': ram_capacity,
            'realTimeCapable': real_time_capable
        }

        if cpu_cores != -1:
            self_payload['cpuCores'] = cpu_cores

        if disk_usage is not None:
            self_payload['diskCapacity'] = disk_capacity
            self_payload['availableDisk'] = available_disk
            self_payload['currentDiskUsage'] = current_disk_usage
            self_payload['currentDiskUsagePct'] = current_disk_usage_pct

        try:
            response = requests.post(url='http://' + os.environ['AERIOS_IE_IP'] + ':8090/optimize', data=json.dumps(self_payload), headers=self_headers, timeout=30)

            if response.status_code != 200 and os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the data in the Self-optimisation and adaptation.')
        except:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the data in the Self-optimisation and adaptation.')

        await asyncio.sleep(sampling_frequency)

@app.route('/sampling_frequency', methods=['POST'])
async def handle_post():
    data = await request.get_json()

    if 'value' in data:
        if isinstance(data['value'], int):
            global sampling_frequency
            sampling_frequency = data['value']

            return 'The value has been received correctly.', 200
        else:
            return 'The value must be an integer.', 400
    else:
        return 'No value provided.', 400

async def run_self():
    asyncio.create_task(self_task())
    await app.run_task(host='0.0.0.0', port=8002)

asyncio.run(run_self())
