FROM python:3.13.6-slim-bullseye
WORKDIR /self-awareness/power_consumption
COPY script.py ./
RUN apt update
RUN apt install -y powertop
RUN pip3 install getmac pandas quart requests
EXPOSE 8003
ENTRYPOINT [ "python3", "-u", "script.py" ]
