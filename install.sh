# install script for ucg-dash.service
#
# v1.6 :  treat current directory as install directory
#
cp ucg-dash.service.template ucg-dash.service
sed -i "s|WORK_DIR|$(pwd)|g"  ucg-dash.service
cp -v ucg-dash.service /etc/systemd/system/ucg-dash.service
#
systemctl daemon-reload
systemctl enable ucg-dash.service
systemctl start ucg-dash.service
systemctl status ucg-dash.service
#
