# Self-awareness

The aeriOS self-awareness module is one of the 4 essential modules within the aeriOS self-* capabilities set. This component analyses and obtains information from the node (CPU, RAM, disk, real-time characteristic, net traffic, net speed, power consumption, etc.), continuously monitoring its health status and workload. Due to the need to offer real-time information on the status of the IE, this module is subdivided into two components, which are executed continuously. One (*power_consumption*) is in charge of obtaining the power consumption (which requires more computing time). The other (*hardware_info*) is responsible for obtaining the rest of the parameters instantly. The component that obtains the power consumption needs an average of 20-25 seconds per execution to obtain new valid values and the other only needs about 10-15 seconds to update its information. The purpose is to provide updated information to the rest of the self-* capabilities as fast as possible to modify the operation of the IE, if necessary.

## Relationships with another self-* capabilities

The following figure describe the self-awareness module inside the IE and the relationships with another self-* modules.

<figure>
  <img src="self_capabilities_relationships.png" alt="Self-* capabilities relationships"/>
  <figcaption><b>Figure 1. Self-* capabilities relationships</b></figcaption>
</figure>

## Getting started

> ⚠️**Warning** \
>  Remember to create the necessary entities related to Domain, LLOs, etc. in the Orion-LD of the Domain.
>
>  For the *power_consumption* submodule the Docker images are split according to architecture (AMD64 and ARM64). Therefore, when launching them in Kubernetes or Docker, the deployment files must be modified to select the architecture.

## Features

Currently, the module is able to obtain the following information from each IE in the aeriOS computing continuum:

- **domain**: indicates the aeriOS Domain where the IE is located.
- **hostname**: internal name, it's the hostname of the machine.
- **internalIpAddress**: internal IP address.
- **macAddress**: MAC address.
- **cpuCores**: number of processor cores.
- **cpuFreqMax**: maximum CPU frequency (in Megahertzs).
- **currentCpuUsage**: current percentage of CPU usage.
- **ramCapacity**: maximum RAM memory capacity (in Megabytes).
- **availableRam**: currently available RAM memory (in Megabytes).
- **currentRamUsage**: RAM memory currently in use (in Megabytes).
- **currentRamUsagePct**: percentage of RAM memory currently in use.
- **diskType**: indicates the type of the storage medium (HDD or SSD).
- **diskCapacity**: maximum capacity of the storage medium (in Megabytes).
- **availableDisk**: current available capacity of the storage medium (in Megabytes).
- **currentDiskUsage**: current used capacity of the storage medium (in Megabytes).
- **currentDiskUsagePct**: percentage of current capacity utilisation of the storage medium.
- **netSpeedUp**: current upload speed of the network interface (in Megabits per second).
- **netSpeedDown**: current download speed of the network interface (in Megabits per second).
- **netTrafficUp**: current upload traffic of the network interface (in Megabytes per second).
- **netTrafficDown**: current download traffic of the network interface (in Megabytes per second).
- **netLostPackages**: indicates the number of packages lost from network traffic.
- **avgPowerConsumption**: average electrical energy consumption (in Watts).
- **currentPowerConsumption**: current electrical energy consumption (in Watts).
- **realTimeCapable**: indicates whether the IE is capable of executing tasks that require the real-time constraint.
- **cpuArchitecture**: indicates processor architecture (AMD64, ARM64, etc.).
- **operatingSystem**: indicates the operating system installed (e.g. GNU/Linux).
- **infrastructureElementTier**: indicates the tier in the continuum (e.g. Cloud, Edge, FarEdge, IoT, ...) of the IE.
- **infrastructureElementStatus**: indicates the status of the IE.

## Environment variables

- AERIOS_VERBOSE: indicates whether or not the module provides information through the Docker container log.
  - Value: true/false.
- AERIOS_AUTHORIZATION: indicates whether KrakenD shall be used to communicate with Orion-LD.
  - Value: true/false.
- AERIOS_KEYCLOAK_URL: the URL where Keycloak is running.
  - Value: protocol, IP and port (e.g. "http://IP:port").
  - *Optional (if AERIOS_AUTHORIZATION is false)*.
- AERIOS_KEYCLOAK_REALM: the Keycloak realm.
  - Value: string.
  - *Optional (if AERIOS_AUTHORIZATION is false)*.
- AERIOS_KRAKEND_URL: the URL where KrakenD is running.
  - Value: protocol, IP and port (e.g. "http://IP:port").
  - *Optional (if AERIOS_AUTHORIZATION is false)*.
- AERIOS_CB_CLIENT_ID: the ID of the client provided to the Auth server.
  - *Optional (if AERIOS_AUTHORIZATION is false)*.
- AERIOS_CB_CLIENT_SECRET: the secret of the client provided to the Auth server.
  - *Optional (if AERIOS_AUTHORIZATION is false)*.
- AERIOS_ORION_URL: the URL where Orion-LD is running.
  - Value: protocol, IP and port (e.g. "http://IP:port").
  - *Optional (if AERIOS_AUTHORIZATION is true)*.
- AERIOS_CONTAINER_TECHNOLOGY: the container technology of the execution environment.
  - Value: Kubernetes/Docker.
- AERIOS_IE_GPU: indicates whether the IE has a GPU.
  - Value: true/false.
  - *Optional*.
- AERIOS_IE_GPU_MEMORY: indicates the IE's GPU memory, in Megabytes (MB).
  - Value: integer.
  - *Optional*.
- AERIOS_IE_NET_SPEED_TEST: indicates whether an IE network speed test should be performed. This could consume network resources.
  - Value: true/false.
- AERIOS_POWER_SOURCE: entity ID of the power source (energy production source) that feeds the IE.
  - Value: NGSI-LD relationship format.
  - *Optional*.
- AERIOS_ENERGY_EFFICIENCY_RATIO: energy efficiency of an IE based on the resources it uses or its computing capacity.
  - Value: float.
  - *Optional*.
- AERIOS_IE_LOCATION: the vector of coordinates (longitude, latitude) of the physical location of the IE.
  - Value: [float,float]
- AERIOS_IE_IP: the IP of the IE where is running the self-awareness module.
  - Value: IP.

## Local deployment (*hardware_info*)

To test the code locally:

1) Download [script.py](./hardware_info/script.py) file.

2) Run the following commands to install the necessary dependencies:

```bash
apt update
apt install -y iproute2
pip3 install getmac psutil quart requests speedtest-cli
```

3) In the same directory where the file was downloaded, run the following command to launch the self-awareness (*hardware_info*):

```bash
python3 script.py
```

## Local deployment (*power_consumption*)

To test the code locally:

1) Download [script.py](./power_consumption/script.py) file.

2) Run the following commands to install the necessary dependencies:

```bash
apt update
apt install -y powertop
pip3 install getmac pandas quart requests
```

3) In the same directory where the file was downloaded, run the following command to launch the self-awareness (*power_consumption*):

```bash
python3 script.py
```

## Sampling frequency

To change the sampling rate at which data is updated in Orion for each Infrastructure Element, one server has been enabled on port 8002 for *hardware_info* and another on port 8003 for *power_consumption*. The operation of both is the same.

The following is an example using *cURL* to update the *hardware_info* sample frequency (in seconds):

```bash
curl -X 'POST' 'http://[AERIOS_IE_IP]:8002/sampling_frequency' -H 'Content-Type: application/json' -d '{ "value": 10 }'
```

A [swagger.yaml](./hardware_info/swagger.yaml) file is available for consultation.

The following is an example using *cURL* to update the *power_consumption* sample frequency (in seconds):

```bash
curl -X 'POST' 'http://[AERIOS_IE_IP]:8003/sampling_frequency' -H 'Content-Type: application/json' -d '{ "value": 10 }'
```

A [swagger.yaml](./power_consumption/swagger.yaml) file is available for consultation.
