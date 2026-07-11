# ucg-dash
  Unifi Cloud Gateway System Monitor: CPU temperature, CPU &amp; Memory Utilization

  Written by Google AI with some prodding & manual edits by grue-some

  Tested on UCG Ultra running v5.1.19

  Installs a service named 'ucg-dash' on a Unifi Cloud Gateway. 
  The service generates an auto-updating web page at port 38083 
  showing CPU temperature, CPU utilization, and memory utilization,
  and a 5 minute graph for all three variables.

  Installation instructions: 

  Pick a directory, e.g. /opt .
  
  Then, either git clone the project,
  or download and unzip the release .zip file.
          
  Verify install script is executable.
  
  Run the install script: ./install.sh .
