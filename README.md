# Complementary-tools

## VIP platform complete installation

### Introduction

This procedure will explain how to install the whole vip infrastructure on 2 machines.
The first machine (called `vip-machine` is composed of the VIP-portal and of the services it needs to run (grida, sma).
The second machine (called `moteur-machine` is composed of moteur-server, its plugins and few others necessary plugins.

The installed infrastucture is meant to run only local jobs (on the moteur machine) and to use only local files.
To use dirac, additional changes not documented here (yet) are necessary.

The procedure is described for centos machines but should be adaptable to any major linux distribution without much effort.

### Prerequisites

As the whole infrastucture is installed on 2 machines, some things must be done to allow the services to communicate and share things.

1. Install `apache` (`httpd`) on both machines through the system package manager

2. Create the `/var/www/html/workflows` folder on both machines

3. A NFS share must be established on the `/var/www/html/workflows` path on the 2 machines.
It is advised to use the `moteur-machine` as the NFS server and the `vip-machine` as a NFS client.

4. The `9092` port must be opened on the `moteur-machine` and accessible from the `vip-machine`.
   The `3306` port must be opened on the `vip-machine` and accessible from the `moteur-machine`.

5. A SMTP server must be accessible from the `vip-machine`

### `vip-machine` installation

The installation must be done as the `root` user.

1. Install needed Tools

       yum -y install wget unzip nmap vim java-1.8.0-openjdk-devel python-pip git
       pip install --upgrade pip
       
    Python version 3.x is necessary, if your system is using python2, you must install `python3` and use `pip3`.

2. Add VIP user

       useradd -m -d /vip vip
       
3. Install MariaDB

    Do the folowing command and choose the root password for the mariadb server.
    
        yum -y -q install mariadb mariadb-server
        systemctl enable mariadb.service
        systemctl start mariadb.service
        mysqladmin password $MARIADB_ROOT_PASSWORD

4. Configure MariaDB

    Create the users/rights init file in `/vip/db_init.sql`.
    Choose a password for the mariadb user (different from root) and change `MOTEUR_HOST` by `moteur-machine`'s hostname.
                    
       # The following is mysql_secure_installation
       DELETE FROM mysql.user WHERE User='';
       DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
       DROP DATABASE test;
       DELETE FROM mysql.db WHERE Db='test' OR Db='test\_%';
       # VIP user
       CREATE USER 'vip'@'localhost' IDENTIFIED BY '<DB_VIP_PASSWORD>';
       CREATE USER 'vip'@'<MOTEUR_HOST>' IDENTIFIED BY '<DB_VIP_PASSWORD>';
       # Create the databases for VIP
       # Charset cannot be utf8 characters as it takes 3 times the space (max
       # DB row size is 64 kB)
       CREATE DATABASE vip;
       ALTER DATABASE vip CHARACTER SET=latin1;
       GRANT ALL PRIVILEGES ON vip.* TO 'vip'@'localhost';
       GRANT ALL PRIVILEGES ON vip.* TO 'vip'@'<MOTEUR_HOST>';
       CREATE DATABASE workflowsdb;
       ALTER DATABASE workflowsdb CHARACTER SET=latin1;
       GRANT ALL PRIVILEGES ON workflowsdb.* TO 'vip'@'localhost';
       GRANT ALL PRIVILEGES ON workflowsdb.* TO 'vip'@'<MOTEUR_HOST>';

    Init the database (using the root password)

       mysql --user=root --password=$MARIADB_ROOT_PASSWORD < /vip/db_init.sql
       wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/workflowsdb_init.sql -P /vip
       mysql --user=root --password=$MARIADB_ROOT_PASSWORD < /vip/workflowsdb_init.sql
       rm /vip/db_init.sql /vip/workflowsdb_init.sql

5. Tomcat

       wget https://downloads.apache.org/tomcat/tomcat-9/v9.0.44/bin/apache-tomcat-9.0.44.tar.gz -P /vip
       tar xzvf /vip/apache-tomcat-9.0.44.tar.gz -C /vip
       rm -rf /vip/apache-tomcat-9.0.44/webapps/*

    Add the folowing lines before `</Context>` `$TOMCAT_HOME/conf/context.xml` (database jndi configuration):

             <Resource name="jdbc/vip"
                 auth="Container"
                 type="javax.sql.DataSource"
                 username="vip"
                 password="<DB_VIP_PASSWORD>"
                 driverClassName="org.mariadb.jdbc.Driver"
                 url="jdbc:mysql://localhost:3306/vip"
                 validationQuery="select 1"
                 testOnBorrow="true"
                 maxTotal="100"
                 maxIdle="50" />
    
    Adapt the password with the one chosen in the mariadb installation.

6. VIP

       mkdir /vip/.vip /vip/.moteur2
       wget https://github.com/axlbonnet/VIP-portal/raw/local-installation/vip-portal/src/main/resources/default-vip.conf -O /vip/.vip/vip.conf
       wget https://github.com/axlbonnet/VIP-portal/raw/local-installation/vip-portal/src/main/resources/default-vip-api.conf -O /vip/.vip/vip-api.conf
       wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/conf/prod/.moteur2/moteur2plugins.conf -O /vip/.moteur2/moteur2plugins.conf
       wget https://github.com/axlbonnet/VIP-portal/releases/download/2.1-alpha/vip-portal-2.1-alpha.war -O /vip/apache-tomcat-9.0.44/webapps/ROOT.war

7. Configure vip.conf

    There are things to change in `/vip/.vip/vip.conf`.
    
    At the beginning, you can change all the `admin.*` properties as you desires. 
    This are the information automatically created for the admin user on the first start.
    
    Change `boutiques.application.rootFolder` to `/vip/Support (group)/Applications`
    
    Change `grida.server.host` to `vip-machine`'s hostname
    
    Change `datamanager.path` to `/vip/grida`
    
    Change `datamanager.users.home` to `/var/www/html/workflows/SharedData/users` 
    and `datamanager.groups.home` to `/var/www/html/workflows/SharedData/groups`
    and `vo.root` to `/var/www/html/workflows/SharedData`
    
    Change `myproxy.min.hours` to `0`
    
    Change `workflows.directory` to `/var/www/html/workflows`
    
    Change `workflows.db.host` to `moteur-machine`'s hostname
    
    Change `truststore.file` to `/vip/apache-tomcat-9.0.44/conf/truststore.jks`
    
    Add the line `workflows.inputs.useLocalFiles = true` at the end

8. Other configuration

    In `/vip/.vip/vip-api.conf`, edit `carmin.platform.name`, `carmin.platform.description` and `carmin.platform.email` to your platform information.
    
    In `/vip/.moteur2/moteur2plugins.conf`, 
    put `org.mariadb.jdbc.Driver` in `moteur2.plugins.workflowsdb.connection.driver_class`, 
    put `vip` in `moteur2.plugins.workflowsdb.connection.username`, 
    put the vip mariadb password in `moteur2.plugins.workflowsdb.connection.password`, 
    and add `localhost:3306` in `moteur2.plugins.workflowsdb.connection.url`
     

7. GRIDA

       mkdir /vip/grida
       mkdir /vip/grida/downloads  
       mkdir /vip/grida/uploads  
       wget -q  https://github.com/axlbonnet/GRIDA/releases/download/2.1.0-alpha/grida-server-2.1.0-alpha.jar -O /vip/grida/grida-server-2.0.1.jar

    Copy https://github.com/virtual-imaging-platform/GRIDA#server-configuration in `/vip/grida/grida-server.conf` and change `commands.type` to `local`. 

8.  SMA
 
        mkdir /vip/sma
        wget -q https://github.com/virtual-imaging-platform/SMA/releases/download/r_0_1/sma-server-0.1.zip -P /vip/sma 
        unzip -q /vip/sma/sma-server-0.1.zip  -d /vip/sma
        rm -f /vip/sma/sma-server-0.1.zip  

    Copy in the `/vip/sma/sma-server.conf` the following content :

        sma.port = 8084
        sma.retrycount = 5
        mail.host = TOCHANGE
        mail.transport.protocol = smtp
        mail.from = TOCHANGE
        mail.from.name = TOCHANGE
        mail.max.simultaneous.runs = 5
        sma.max.history = 90
    
    Edit `mail.host` to your SMTP host, `mail.from` to your service email adress, and `mail.from.name` to your service name.
    
9. Install Boutiques

    `pip` should run with python3, on python2 systems, `pip3` must be used.

        pip install boutiques

10. Finalize installation

        sudo chown -R vip:vip /vip
        sudo chown -R apache:apache /vip/grida
        sudo chown -R vip:vip /vip/grida/uploads
        sudo chmod g+rx /vip
        sudo usermod -a -G vip apache
    
11. Start Grida and SMA

    Grida must be started with the apache user with the command `java -jar grida-server-2.0.1.jar` in the `/vip/grida` folder.
    SMA must be started with the vip user with the command `java -jar /vip/sma/sma-server-0.1.jar` in the `/vip/sma` folder.
    It is advised to configure grida and sma as a system services and make them start automatically on machine boot.

10. Start tomcat as vip with `/vip/apache-tomcat-9.0.44/bin/startup.sh`
    It is advised to configure tomcat as a system service to make it start automatically on system startup.
    It is also advised to make tomcat restart once a day through a cron entry.
    Also, tomcat should be configured to respond to HTTPS requests and no HTTP requests,
    this could be done in tomcat or by setting up a reverse proxy.

### `moteur-machine` installation

1. Every folder/file created on the `moteur-machine` must belong to the apache user.
       The installation must be done as root.

3. If it isn't already done, `apache` (`httpd`) must be installed through the system package manager

2. Stop the apache server (`service httpd stop`)

3. Install Java JDK 8 through the system package manager (`yum install java-1.8.0-openjdk-devel`)

4. `mkdir -p /var/www/cgi-bin/m2Server-gasw3; export MOTEUR_HOME=/var/www/cgi-bin/m2Server-gasw3`

5. Install the moteur server.

    It is a small c++ server already compiled and available for CentOS 7.
    For other any other system, please adapt the compilation instuctions from https://github.com/virtual-imaging-platform/moteur_server to your needs and use the produced executable.

       cd $MOTEUR_HOME
       wget https://github.com/virtual-imaging-platform/moteur_server/releases/download/v1.1/moteur_server-v1.1-centos7.tar.gz
       tar xzf moteur_server-*-centos7.tar.gz
       rm -rf moteur_server-*-centos7*

6. Install moteur server scripts
 
       export MOTEUR_SERVER_RAW_FILES=https://github.com/virtual-imaging-platform/moteur_server/raw/v1.1
       wget -q ${MOTEUR_SERVER_RAW_FILES}/env.sh -O ${MOTEUR_HOME}/env.sh
       wget -q ${MOTEUR_SERVER_RAW_FILES}/killWorkflow.sh -O ${MOTEUR_HOME}/killWorkflow.sh
       wget -q ${MOTEUR_SERVER_RAW_FILES}/submitWorkflow.sh -O ${MOTEUR_HOME}/submitWorkflow.sh
       chmod +x ${MOTEUR_HOME}/killWorkflow.sh ${MOTEUR_HOME}/submitWorkflow.sh

7. Install h2 server

       mkdir /var/www/prod
       export H2_ZIP=h2-2012-05-23.zip
       wget -q https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/h2database/${H2_ZIP} -O /var/www/prod/${H2_ZIP}
       cd /var/www/prod && unzip -q /var/www/prod/${H2_ZIP}
       rm -f /var/www/prod/${H2_ZIP}
       unset H2_ZIP
       chown -R apache:apache /var/www/prod/h2

8. Start the h2 server

   The h2 service must be started with the apache user with the command `java -cp /var/www/prod/h2/bin/h2-1.3.167.jar org.h2.tools.Server -tcpAllowOthers`.
   It is advised to configure it as a system service and make it start automatically on machine boot.

9. Install grida

       mkdir /var/www/prod/grida
       wget -q  https://github.com/axlbonnet/GRIDA/releases/download/2.1.0-alpha/grida-server-2.1.0-alpha.jar -O /var/www/prod/grida/grida-server-2.0.1.jar
       mkdir /var/www/.cache
       chown apache:apache /var/www/prod/grida /var/www/.cache

10. Configure and start grida

    Copy https://github.com/virtual-imaging-platform/GRIDA#server-configuration in `/var/www/prod/grida/grida-server.conf` and change `commands.type` to `local`.

    Grida must be started with the apache user with the command `java -jar grida-server-2.0.1.jar` in the `/var/www/prod/grida` folder.
    It is advised to configure it as a system service and make it start automatically on machine boot.

11. Install moteur2 jars

        cd $MOTEUR_HOME
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/moteur/moteur2.jar 
        mkdir worflow-agent-0.2
        cd worflow-agent-0.2
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/moteur/worflow-agent-0.2/workflow-agent-0.2.jar
        cd ..
        mkdir libs plugins
        cd libs
        wget https://github.com/virtual-imaging-platform/GASW/releases/download/v3.6.0/gasw-3.6.0.jar
        wget https://github.com/virtual-imaging-platform/GRIDA/releases/download/2.0.1/grida-client-2.0.1.jar
        wget https://github.com/virtual-imaging-platform/GRIDA/releases/download/2.0.1/grida-common-2.0.1.jar
        wget https://github.com/virtual-imaging-platform/Moteur2-Grida/releases/download/1.1/moteur2-grida-1.1.jar
        cd ../plugins
        wget https://github.com/virtual-imaging-platform/GASW-Dirac-Plugin/releases/download/V3.5.0/gasw-dirac-plugin-3.5.0-jar-with-dependencies.jar
        wget https://github.com/virtual-imaging-platform/GASW-Healing-Plugin/releases/download/v3.3.1/gasw-healing-plugin-3.3.1-jar-with-dependencies.jar
        wget https://github.com/virtual-imaging-platform/Moteur2-WorkflowsDB-Plugin/releases/download/v1.5/moteur2-workflowsdb-plugin-1.5-jar-with-dependencies.jar
        wget https://github.com/virtual-imaging-platform/GASW-Stats-Plugin/releases/download/v3.2.0/gasw-stats-plugin-3.2.0-jar-with-dependencies.jar
        wget https://github.com/virtual-imaging-platform/GASW-H2-Plugin/releases/download/3.0/gasw-h2-plugin-3.0-jar-with-dependencies.jar
        wget https://github.com/virtual-imaging-platform/GASW-Local-Plugin/releases/download/3.0/gasw-local-plugin-3.0-jar-with-dependencies.jar

12. Add moteur2 configuration

        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/moteur/worflow-agent-0.2/workflow-agent.conf -O $MOTEUR_HOME/worflow-agent-0.2/workflow-agent.conf
        mkdir $MOTEUR_HOME/.moteur2 $MOTEUR_HOME/conf
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/conf/.moteur2/moteur2.conf -O $MOTEUR_HOME/.moteur2/moteur2.conf
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/moteur/conf/default.conf -O $MOTEUR_HOME/conf/default.conf
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/moteur/conf/override.conf -O $MOTEUR_HOME/conf/override.conf
        mkdir /var/www/.moteur2
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/conf/.moteur2/moteur2-grida.conf -O /var/www/.moteur2/moteur2-grida.conf
        mkdir /var/www/prod/.moteur2 /var/www/prod/.jgasw
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/conf/prod/.jgasw/jgasw.properties -O /var/www/prod/.jgasw/jgasw.properties
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/conf/prod/.moteur2/moteur2plugins.conf -O /var/www/prod/.moteur2/moteur2plugins.conf
        wget https://github.com/virtual-imaging-platform/Complementary-tools/raw/develop/conf/prod/.moteur2/moteur2server.conf -O /var/www/prod/.moteur2/moteur2server.conf

13. Edit moteur2 Configurations
    1. In `$MOTEUR_HOME/workflow-agent-0.2/workflow-agent.conf`, put `localhost` in `db.h2.server` and `9092` in `db.h2.port`
    2. In `$MOTEUR_HOME/.moteur2/moteur2.conf`, do nothing
    3. In `$MOTEUR_HOME/conf/default.conf`, update the paths in `plugin.db`, `plugin.executor` and `plugin.listener`.
       Put `false` in `minorstatus.service.enabled`
       Put `localhost` in `plugin.h2.server.host`, `9092` in `plugin.h2.server.port`, and `gasw` in `plugin.h2.user` and `plugin.h2.password`
    4. In `$MOTEUR_HOME/conf/override.conf`, do nothing
    5. In `$MOTEUR_HOME/env.sh`, update `JAVA_HOME` to `/usr/lib/jvm/jre-1.8.0` or to the right JRE path on your system.
    6. In `/var/www/prod/.moteur2/moteur2plugins.conf `, 
       put `vip` in `moteur2.plugins.workflowsdb.connection.username`, 
       put the vip mariadb password in `moteur2.plugins.workflowsdb.connection.password`, 
       and add the `vip-machine` hostname and the `3306` port in `moteur2.plugins.workflowsdb.connection.url`
    7. In `/var/www/.moteur2/moteur2-grida.conf`, 
       put `moteur-machine`'s hostname in `grida.server.host`,
       put `9006` in `grida.server.port`,
       and put `/var/www/.moteur2/moteur2-grida.conf` in `proxy.path`
    8. In `/var/www/prod/.moteur2/moteur2server.conf`, update `configuration/plugins/plugin/location` to the real path of `moteur2-workflowsdb-plugin`


14. Install boutiques

    `pip` should run with python3, on python2 systems, `python3` should be installed and `pip3` should be used.

        yum -y install python-pip
        pip install --upgrade pip
        pip install boutiques

15. Change rights

        chown -R apache:apache $MOTEUR_HOME /var/www/prod /var/www/.moteur2
        sudo setenforce Permissive

16. Start apache

### Finalization and tests

VIP should be working on the vip machine on the `8080` port (or another port if you changed the tomcat port).
You can access it with the admin/password configured in the vip.conf file.
You should then :
* Create the engine corresponding to `moteur-machine`
* Create a class
* Import an application (**Warning** The application automatically imported will not work at the moment and needs manual editing from a VIP expert)

## cloud-init (old method)

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

### vip.te

This is the SELinux security configuration of the server installed by
the cloud-init file.

## zenodo
The two scripts, **replayer.py** and **uploader.py**, were developed to address reproducibility concerns.

The *uploader.py script* is designed to be used by an administrator of a **VIP instance** to upload a summary (with or without results) of an execution to Zenodo.

The *replayer.py script* is then used to replay an execution previously uploaded to Zenodo.
