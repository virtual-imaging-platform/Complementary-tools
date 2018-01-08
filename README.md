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

#### Machine certificate

An auto-signed certificate has been created, used by apache https.  It
must be replaced by a correct certificate.  The files must be replaced
in the directories:
```shell
/etc/pki/tls/private/<hostname>.key
/etc/pki/tls/certs/<hostname>.crt
```

#### Final commands

Create a proxy with the voms extension:
```shell
/root/sbin/renew_voms_for_moteur.sh >> /root/cron-renew-voms.log 2>&1
```

Configure dirac vomsdir.  Replace `<VO_NAME>` with the name of the VO
that you have configured in the `cloud_init_vip.yaml` file, eg
`biomed`.
```shell
cd /var/www/cgi-bin/m2Server-gasw3/dirac
export X509_USER_PROXY=/var/www/html/workflows/dirac-robot-<VO_NAME>
scripts/dirac-configure defaults-gridfr.cfg
```

Initialise myproxy the first time:
```shell
/home/vip/robotcert/uploadRobot.sh
```
