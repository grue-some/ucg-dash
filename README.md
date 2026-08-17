# ucg-dash2

Unifi Cloud Gateway System Monitor: CPU temperature, CPU \& Memory Utilization, and Threats Rate
- latest update:
    - version v3.3
    - date 2026-8-17 
    - updated to include a web page icon; indentation fix in server.py

- Written by Google AI with some prodding \& manual edits by grue-some
- Tested on UCG Ultra running Unifi OS v5.1.19 to v5.1.30

- Installs a service named 'ucg-dash2' on a Unifi Cloud Gateway. 
The service generates an auto-updating web page at port 5000
showing CPU temperature, CPU utilization, memory utilization, and
the hourly and daily rate of threats in /var/log/ulog/threat.log,  
with a history graph below. 

## Installation instructions:
- Pick a directory, e.g. /opt .
- Then, either git clone the project,
or download and unzip the release .zip file.
- Verify install script is executable.
- Run the install script: ./install.sh .

## Update instructions:
- Stop the service: systemctl stop ucg-dash2.service
- Run the install script

## Removal instructions:
- Stop the service: systemctl stop ucg-dash2.service
- Disable the service: systemctl disable ucg-dash2.service
- Delete the service file: rm /etc/systemd/system/ucg-dash2.service
- Delete the install directory: rm -r ucg-dash-*version number*; e.g. rm -r ucg-dash-1.9
- Delete the zip file: rm v*version number*.zip; e.g. rm v1.9.zip

