# Complementary-tools

## cloud-init

The cloud init file can be used to instantiate a VM running all the
services needed to run vip.  It must be tailored to your environment
at the start of the file.

### Manual configuration

Once the VM has been instanciated using the cloud-init file, several
certificates must be manually copied to the VM:

#### Robot certificate used for vip / moteur / dirac

Upload the file:
```shell
/tmp/dirac-robot
```

This file must be regularly updated so that the proxy never expires.
It is used through cron files to creates the proxies used by vip, moteur
and dirac.

#### Machine certificate

An auto-signed certificate has been created, used by apache https.  It
must be replaced by a correct certificate.  The files must be replaced
in the directories:
```shell
/etc/pki/tls/private/<hostname>.key
/etc/pki/tls/certs/<hostname>.crt
```

#### Proxy generation

The following commands must be done :
- at the first startup
- every time the `/tmp/dirac-robot` is not valid (or with a validity duration too short) and VIP fails to start because of that
They need that the file `/tmp/dirac-robot` exists and is the valid proxy that will be used.

Create a proxy with the voms extension.  This is done regularly via
cron, but must be done once, so that the proxies can be used
immediately.  This is the first run of the script, with the option
`--no-dirac`, as dirac has not yet been initialised.
```shell
/root/sbin/update_proxy_for_vip_moteur_dirac.sh --no-dirac >> /root/cron-update-proxy.log 2>&1
```

Configure dirac vomsdir.  Replace `<VO_NAME>` with the name of the VO
that you have configured in the `cloud_init_vip.yaml` file, eg
`biomed`.  This can only be done with a correct proxy.
```shell
cd /var/www/cgi-bin/m2Server-gasw3/dirac
export X509_USER_PROXY=/var/www/html/workflows/dirac-robot-<VO_NAME>
scripts/dirac-configure defaults-gridfr.cfg
```

Now that dirac has been configured, run again the creation of the
proxies, but this time without the `--no-dirac` option, to update also
the dirac proxy.
```shell
/root/sbin/update_proxy_for_vip_moteur_dirac.sh >> /root/cron-update-proxy.log 2>&1
```

And finally restart tomcat.
```shell
systemctl restart tomcat
```

#### SQL commands

In the current version, the database build automatically by VIP contains some errors. This won't be necessary in the next VIP version, but with the 1.27 version, the folowing commands must be done to correct that (`$DB_ROOT_PASSWD` comes from the `/root/global_configuration.txt` file):

```
mysql --user=root --password=$DB_ROOT_PASSWD -e "use vip;ALTER TABLE VIPEngines ADD COLUMN status VARCHAR(255) DEFAULT NULL;"
mysql --user=root --password=$DB_ROOT_PASSWD -e "use vip;ALTER TABLE VIPApplications ADD COLUMN lfn varchar(255) DEFAULT NULL;"
mysql --user=root --password=$DB_ROOT_PASSWD -e "use vip;INSERT INTO VIPEngines (name, endpoint, status) VALUES ('local','http://${HOSTNAME}/cgi-bin/m2Server-gasw3/moteur_server','enabled');"
```

### SE Linux

The `vip.te` file is the SELinux security configuration of the server installed by
the cloud-init file. The rules it contains allow to run VIP in a secure environment,
but in the current state, several SELinux rules are broken by moteur. So SELinux needs
to be in `Permissive` mode for the whole platform to run properly.

## Description of some files and folders

(Most of) all these files are downloaded by the cloud-init script
during installation.

### conf

Configuration files for moteur.

### dirac_services

Python scripts to add to default dirac installation, to add some
services needed by moteur.

### moteur

Many jars to install moteur, and some associated configuration files.

### cloud_init_vip.yaml

This file can be used to instantiate a VM running all the services
needed to run a VIP server.  It must be configured at the start of the
file to adapt to your environment (administrator, VO tu use, …).
