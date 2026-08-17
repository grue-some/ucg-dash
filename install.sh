# install script for ucg-dash2.service
#
# v3.1 :  treat current directory as install directory; 
#         move chart.js and index.html to /static subdirectory
#
mkdir -p static
mv index.html chart.js favicon.ico static/
#
cp ucg-dash2.service.template ucg-dash2.service
sed -i "s|WORK_DIR|$(pwd)|g"  ucg-dash2.service
cp -v ucg-dash2.service /etc/systemd/system/ucg-dash2.service
#
systemctl daemon-reload
systemctl enable ucg-dash2.service
systemctl start ucg-dash2.service
systemctl status ucg-dash2.service
#
