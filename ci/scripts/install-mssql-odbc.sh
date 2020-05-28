#!/usr/bin/env bash
set -xe

apt-get update --yes
apt-get install --yes --no-install-recommends \
        gpg-agent gnupg2 apt-transport-https curl

export ACCEPT_EULA=Y

curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/10/prod.list -o /etc/apt/sources.list.d/mssql-release.list

apt-get update --yes
apt-get install --yes --no-install-recommends msodbcsql17
