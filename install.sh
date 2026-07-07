# install script for ucg-dash.service
#
# v1.0
#
mkdir /root/ucg-dash
mv -v index.html chart.js server.py /root/ucg-dash/
mv -v ucg-dash.service.txt /etc/systemd/system/ucg-dash.service
#
systemctl daemon-reload
systemctl enable ucg-dash.service
systemctl start ucg-dash.service
systemctl status ucg-dash.service
#
