# Complementary-tools

## cloud-init

The cloud init file can be used to instantiate a VM running all the
services needed to run vip.  It must be tailored to your environment
at the start of the file.

### Manual configuration

Once the VM has been instanciated using the cloud-init file, several
certifacates must be manually copied to the VM:

#### Dirac robot certificate

Upload the file:
```shell
/tmp/dirac-robot
```

#### Myproxy certificates

Upload the files:
```shell
/etc/grid-security/myproxy/hostcert.pem
/etc/grid-security/myproxy/hostkey.pem
```

Run the commands:
```shell
cd /etc/grid-security/myproxy
chown myproxy:root * && chmod 600 hostkey.pem
systemctl restart myproxy-server
```

#### Globus certificates

Upload the files:
```shell
/home/vip/.globus/usercert.pem
/home/vip/.globus/userkey.pem
```

Run the commands:
```shell
chown -R vip:vip /home/vip/.globus
chmod 700 /home/vip/.globus
```

#### Final commands

Run the command as root:
```shell
/root/sbin/renew_voms_for_moteur.sh >> /root/cron-renew-voms.log 2>&1
```

Run the command as vip:
```shell
/home/vip/robotcert/uploadRobot.sh
```
