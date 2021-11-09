apt-get update

# Packaged python is compiled against openssl 1.1.1
# libaio is needed for Oracle client
apt-get install -y \
  curl \
  alien \
  libssl1.1 \
  sqlite3 \
  libaio1

# Install Oracle client libraries
curl -s https://download.oracle.com/otn_software/linux/instantclient/oracle-instantclient-basic-linuxx64.rpm > oracle_client.rpm
alien -i ./oracle_client.rpm

# Install MS SQL driver
curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl -s https://packages.microsoft.com/config/ubuntu/18.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17

apt-get clean
rm -rf /var/cache/apt/*
