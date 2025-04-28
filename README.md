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

#### Myproxy certificates (deprecated)

myproxy is no more used, as all proxy files are updated with the
script `update_proxy_for_vip_moteur_dirac.sh`.  This part is
deprecated.

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

The following commands need that the file `/tmp/dirac-robot` exists
and is the valid proxy that will be used.

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

## Description of some files and folders

(Most of) all these files are downloaded by the cloud-init script
during installation.

### conf

Configuration files for moteur.

### dirac_services

Python scripts to add to default dirac installation, to add some
services needed by moteur.

### lcg-gfal

Contains shell-scripts for some lcg executables, and runs the
equivalent gfal command, effectively transforming a lcg command into a
gfal command.  The lcg executables delivered with dirac don't work, so
this is a workaround.

### moteur

Many jars to install moteur, and some associated configuration files.

### cloud_init_vip.yaml

This file can be used to instantiate a VM running all the services
needed to run a VIP server.  It must be configured at the start of the
file to adapt to your environment (administrator, VO tu use, …).

### vip.te

This is the SELinux security configuration of the server installed by
the cloud-init file.

## zenodo
The two scripts, **replayer.py** and **uploader.py**, were developed to address reproducibility concerns.

The *uploader.py script* is designed to be used by an administrator of a **VIP instance** to upload a summary (with or without results) of an execution to Zenodo.

The *replayer.py script* is then used to replay an execution previously uploaded to Zenodo.