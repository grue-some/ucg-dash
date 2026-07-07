# ucg-dash
  Unifi Cloud Gateway System Monitor: CPU temperature, CPU &amp; Memory Utilization

  Written by Google AI with some prodding & manual edits by grue-some

  Tested on UCG Ultra running v5.1.19

  Installs a service named 'ucg-dash' on a Unifi Cloud Gateway. 
  The service generates an auto-updating web page at port 38083 
  showing CPU temperature, CPU utilization, and memory utilization,
  and a 5 minute graph for all three variables.

  Installation instructions: 

  Either 
          git clone the project to /tmp/ucg-dash,
  Or
          download release .zip file, unzip and 
          move to /tmp/ucg-dash (mv <unzip directory> /tmp/ucg-dash )
  
  (in order to use a different install directory, modify the file locations in ucg-dash.service and server.py)
  
  Make install script executable: chmod a+x install.sh
  Source install script: ./install.sh
