# install script for ucg-dash.service
#
# v1.1 : keep files in /tmp/ucg-dash
#
cp -v ucg-dash.service.txt /etc/systemd/system/ucg-dash.service
#
systemctl daemon-reload
systemctl enable ucg-dash.service
systemctl start ucg-dash.service
systemctl status ucg-dash.service
#
