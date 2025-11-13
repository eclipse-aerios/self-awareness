FROM python:3.14.0a3-slim-bookworm
WORKDIR /self-awareness/hardware_info
COPY script.py ./
RUN apt update
RUN apt install -y iproute2
RUN pip3 install getmac psutil quart requests speedtest-cli
EXPOSE 8002
ENTRYPOINT [ "python3", "script.py" ]
