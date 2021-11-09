dnf install -y curl

# Install Oracle client and its dependencies
dnf install -y https://download.oracle.com/otn_software/linux/instantclient/oracle-instantclient-basic-linuxx64.rpm

# Install MS SQL driver
curl -s https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
ACCEPT_EULA=Y dnf install -y msodbcsql17

dnf clean all
