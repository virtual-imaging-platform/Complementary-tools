#!/bin/sh

#      ADMIN_EMAIL=pascal.wassong@iphc.cnrs.fr
#      MYPROXY_USER="/O=GRID-FR/C=FR/O=CNRS/OU=IPHC/CN=Pascal Wassong"
#      MYPROXY_PASSWORD=tototo
#      LFC_VIP_ROOT_DIR=/grid/biomed/pwassong/vip/data
#      DB_VIP_PASSWORD=davipdbadminpiwee

#    ssh_authorized_keys:
#      - MODIFY

rm -f cloud_init_vip_pw.yaml

sed \
    -e 's/ADMIN_EMAIL=MODIFY/ADMIN_EMAIL=pascal.wassong@iphc.cnrs.fr/' \
    -e 's#MYPROXY_USER=MODIFY#MYPROXY_USER="/O=GRID-FR/C=FR/O=CNRS/OU=IPHC/CN=Pascal Wassong"#' \
    -e 's/MYPROXY_PASSWORD=MODIFY/MYPROXY_PASSWORD=tototo/' \
    -e 's#LFC_VIP_ROOT_DIR=MODIFY#LFC_VIP_ROOT_DIR=/grid/biomed/pwassong/vip/data#' \
    -e 's/DB_VIP_PASSWORD=MODIFY/DB_VIP_PASSWORD=davipdbadminpiwee/' \
    -e 's#- MODIFY#- ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGMc6IUHXFpUSL0wOVd6/CtcKPmqilFt3CbQhv6R7chrjga01a4w0yv2HjALxVPMtB+2Xj4W/raq3CiHFe8cvtAy3oKy6SnwRNwgCiSjK63eqQNM5Cz250v3DxH3HZ8UEpLCmYRU4+Cirv/17jAocT19TlU7RlGq7PHYcsK0F++SIQ9hM1YJmoSIXH8QwjgEriE4Tz1WmH37b8KfasbrcEaxRYaRNz62CgQqAgwNLmItLatsG5jfJcoqZ5NKgh/R7lnrLohcUvR2os6c9aJbs3NoUSlkIaBP/NQzfMx38uqHqShxFEzT4flZ07SmQvCdXoZbTGA6aPAfx/89cDsezz pwassong@sbgat401#' \
    -e 's#https://github.com/virtual-imaging-platform/Complementary-tools/archive/master.zip#https://github.com/wassong-iphc/Complementary-tools/archive/cloud-init-dev.zip#' \
    cloud_init_vip.yaml > cloud_init_vip_pw.yaml
