from datetime import datetime
from getmac import get_mac_address
from os.path import exists
from quart import Quart, request
import asyncio
import json
import math
import os
import pandas
import re
import requests
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
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the access token in Keycloak. Aborting execution...', flush=True)
                print('Keycloak error:', response.text, sep='\n', flush=True)

            sys.exit(1)
    except Exception as e:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the access token in Keycloak. Aborting execution...', flush=True)
            print('Keycloak error:', e, sep='\n', flush=True)

        sys.exit(1)

async def self_task():
    mac_address = get_mac_address()

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
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to get the entity Domain from Orion. It is not possible to update the entity associated with this Infrastructure Element in Orion. Aborting execution...', flush=True)
                print('Orion error:', response.text, sep='\n', flush=True)

            sys.exit(1)
    except Exception as e:
        if os.environ['AERIOS_VERBOSE'] == "true":
            print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to get the entity Domain from Orion. It is not possible to update the entity associated with this Infrastructure Element in Orion. Aborting execution...', flush=True)
            print('Orion error:', e, sep='\n', flush=True)

        sys.exit(1)

    orion_headers['Content-Type'] = 'application/json'

    while True:
        try:
            subprocess.run(['powertop', '--csv=powertop.csv'])
        except:
            if os.environ['AERIOS_VERBOSE'] == "true":
                print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the power consumption of the Infrastructure Element. Using an empty value...', flush=True)

        if exists('powertop.csv'):
            with open('powertop.csv', 'r') as f:
                for i, line in enumerate(f):
                    if 'Overview of Software Power Consumers' in line:
                        skip_rows = i + 2
                        break

            try:
                dataframe = pandas.read_csv('powertop.csv', sep=';', header=0, index_col=['Description'],
                                            usecols=['Description', 'PW Estimate'], skipinitialspace=True,
                                            skiprows=skip_rows, nrows=99)
                current_power_consumption = 0.0

                for i in range(len(dataframe.index)):
                    data = dataframe['PW Estimate'].iloc[i].split()

                    if data[1] == 'W':
                        current_power_consumption += float(data[0])
                    elif data[1] == 'mW':
                        current_power_consumption += float(data[0]) / 1000
                    else:
                        current_power_consumption += float(data[0]) / 1000000

                current_power_consumption = math.ceil(current_power_consumption)
            except:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the current power consumption of the Infrastructure Element. Using an empty value...', flush=True)

                current_power_consumption = -1

            try:
                with open('powertop.csv', 'r') as f:
                    for line in f:
                        if 'The system baseline power is estimated at:' in line:
                            avg_power_consumption = re.compile(r'(\d+)').findall(line)

                            if (len(avg_power_consumption) == 1):
                                avg_power_consumption = int(avg_power_consumption[0])
                            else:
                                avg_power_consumption = float(avg_power_consumption[0] + '.' + avg_power_consumption[1])

                            if line.rstrip().endswith("  W;"):
                                avg_power_consumption = math.ceil(avg_power_consumption)
                            elif line.rstrip().endswith("m W;"):
                                avg_power_consumption = math.ceil(avg_power_consumption / 1000)
                            else:
                                avg_power_consumption = math.ceil(avg_power_consumption / 1000000)

                            break

                avg_power_consumption
            except:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to obtain the average power consumption of the Infrastructure Element. Using an empty value...', flush=True)

                avg_power_consumption = -1
        else:
            current_power_consumption = -1
            avg_power_consumption = -1

        orion_payload = {}

        if avg_power_consumption != -1:
            orion_payload['avgPowerConsumption'] = {
                'value': avg_power_consumption
            }

        if current_power_consumption != -1:
            orion_payload['currentPowerConsumption'] = {
                'value': current_power_consumption
            }

        if len(orion_payload) > 0:
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
                            print(datetime.now().isoformat()[:19] + ' - An authorization error occurred while trying to update the entity InfrastructureElement in Orion. Aborting execution...', flush=True)
                            print('Orion error:', response.text, sep='\n', flush=True)

                        sys.exit(1)
                    elif response.status_code != 204 and os.environ['AERIOS_VERBOSE'] == "true":
                        print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the entity InfrastructureElement in Orion.', flush=True)
                        print('Orion error:', response.text, sep='\n', flush=True)
                elif response.status_code != 204 and os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the entity InfrastructureElement in Orion.', flush=True)
                    print('Orion error:', response.text, sep='\n', flush=True)
            except Exception as e:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the entity InfrastructureElement in Orion.', flush=True)
                    print('Orion error:', e, sep='\n', flush=True)

        self_payload = {
            'id': 'urn:ngsi-ld:InfrastructureElement:' + domain[domain.rfind(':') + 1 : ] + ':' + mac_address.replace(':', '')
        }

        if avg_power_consumption != -1:
            self_payload['avgPowerConsumption'] = avg_power_consumption

        if current_power_consumption != -1:
            self_payload['currentPowerConsumption'] = current_power_consumption

        if len(self_payload) > 1:
            try:
                response = requests.post(url='http://' + os.environ['AERIOS_IE_IP'] + ':8001/data', data=json.dumps(self_payload), headers=self_headers, timeout=5)

                if response.status_code != 201 and os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the facts through the Self-orchestrator.', flush=True)
            except:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the facts through the Self-orchestrator.', flush=True)

            try:
                response = requests.post(url='http://' + os.environ['AERIOS_IE_IP'] + ':8090/optimize/powerConsumption', data=json.dumps(self_payload), headers=self_headers, timeout=30)

                if response.status_code != 200 and os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the data in the Self-optimisation and adaptation.', flush=True)
            except:
                if os.environ['AERIOS_VERBOSE'] == "true":
                    print(datetime.now().isoformat()[:19] + ' - An error occurred while trying to update the data in the Self-optimisation and adaptation.', flush=True)

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
    await app.run_task(host='0.0.0.0', port=8003)

asyncio.run(run_self())
