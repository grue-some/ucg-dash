# ucg-dash

Unifi Cloud Gateway System Monitor: CPU temperature, CPU \& Memory Utilization
- latest update:
    - version v3.0
    - date 2026-8-11 
    - rewrite, to keep stats on server side, and add threat rate statistics

- Written by Google AI with some prodding \& manual edits by grue-some
- Tested on UCG Ultra running Unifi OS v5.1.19 to v5.1.28

- Installs a service named 'ucg-dash' on a Unifi Cloud Gateway. 
The service generates an auto-updating web page at port 38083 
showing CPU temperature, CPU utilization, and memory utilization, 
and a 5 minute and 24hr graph for all three variables. 

## Installation instructions:
- Pick a directory, e.g. /opt .
- Then, either git clone the project,
or download and unzip the release .zip file.
- Verify install script is executable.
- Run the install script: ./install.sh .

## Update instructions:
- Stop the service: systemctl stop ucg-dash.service
- Run the install script

## Removal instructions:
- Stop the service: systemctl stop ucg-dash.service
- Disable the service: systemctl disable ucg-dash.service
- Delete the service file: rm /etc/systemd/system/ucg-dash.service
- Delete the install directory: rm -r ucg-dash-*version number*; e.g. rm -r ucg-dash-1.9
- Delete the zip file: rm v*version number*.zip; e.g. rm v1.9.zip
