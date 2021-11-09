# Repo with openssl11
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

# Packaged python is compiled against openssl 1.1.1
yum -y install \
  openssl11 \
  curl

# Install Oracle client and its dependencies
yum install -y https://download.oracle.com/otn_software/linux/instantclient/oracle-instantclient-basic-linuxx64.rpm

# Install MS SQL driver
curl -s https://packages.microsoft.com/config/rhel/7/prod.repo > /etc/yum.repos.d/mssql-release.repo
ACCEPT_EULA=Y yum install -y msodbcsql17

yum clean all
