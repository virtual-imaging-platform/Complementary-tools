# Complementary-tools

## cloud-init

The cloud init file can be used to instantiate a VM running all the
services needed to run vip.  It must be tailored to your environment
at the start of the file.

### Manual configuration

Once the VM has been instanciated using the cloud-init file, several
certifacates must be manually copied to the VM:

#### Robot certificate used for vip / moteur / dirac

Upload the file:
```shell
/tmp/dirac-robot
```

This file must be regularly updated so that the proxy never expires.
It is used throu cron files to creates the proxies used by vip, moteur
and dirac.

#### Myproxy certificates ???

myproxy is no more used.  This part is probably useless.

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

#### Machine certificate

An auto-signed certificate has been created, used by apache https.  It
must be replaced by a correct certificate.  The files must be replaced
in the directories:
```shell
/etc/pki/tls/private/<hostname>.key
/etc/pki/tls/certs/<hostname>.crt
```

#### Final commands

Configure dirac vomsdir.  Replace `<VO_NAME>` with the name of the VO
that you have configured in the `cloud_init_vip.yaml` file, eg
`biomed`.
```shell
cd /var/www/cgi-bin/m2Server-gasw3/dirac
export X509_USER_PROXY=/var/www/html/workflows/dirac-robot-<VO_NAME>
scripts/dirac-configure defaults-gridfr.cfg
```

Create a proxy with the voms extension.  It must be done after the
above dirac configuration.  This is done regularly via cron, but must
be done once, so that the proxies can be used immediately.
```shell
/root/sbin/update_proxy_for_vip_moteur_dirac.sh >> /root/cron-update-proxy.log 2>&1
```
