#!/usr/bin/env sh
## SETUP
defaultUsername=`who am i | awk '{print $1}'`
serviceName="mmm-ws-web-server"
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
serviceConfigPath="$dir/$serviceName.service"
defaultInstallPath="/etc/systemd/system/$serviceName.service"

check_permission() {
	local FILE=`readlink $1 -f`
	local USER=$2
	local MODE=$3

	if [ "$MODE" == "-r" ]; then
		local PERMISSION_NAME="read"
	else
		local PERMISSION_NAME="write"
	fi

	echo
	echo -n "Checking $PERMISSION_NAME permission to '$FILE' for user $USER..."
	if sudo -u $USER [ $MODE "$FILE" ] ; then
		echo "[OK]"
		return 1
	else
		echo "[not accesible]"
		echo "Please, make sure that user $USER has $PERMISSION_NAME permission to following folder"
		ls -ld $FILE
		return 0
	fi
}

## RESOLVE USER
read -p "Username of account that runs the service [$defaultUsername]: " username
username=${username:-$defaultUsername}
until id "$username" > /dev/null 2>&1; do
	read -p "User '$username' does not exist. Try again or press x to exit [$defaultUsername]: " username
	if [ "$username" == "x" ]; then
	    exit 0
	fi
	username=${username:-$defaultUsername}
done

## RESOLVE INSTALL PATH
read -p "Where to put service config file [$defaultInstallPath]: " installPath
installPath=${installPath:-$defaultInstallPath}

## CHECK PERMISSIONS
permission_check=0
check_permission $dir $username -r && permission_check=1
check_permission "$dir/../lib" $username -r && permission_check=1
check_permission "$dir/../plugin" $username -r && permission_check=1
check_permission "$dir/../etc" $username -r && permission_check=1

check_permission "$dir/../tmp" $username -w && permission_check=1
check_permission "$dir/../log" $username -w && permission_check=1
check_permission "$dir/../storage" $username -w && permission_check=1

if ((permission_check)); then
	echo "Unable to complete installation";
	exit 1
fi

## CREATE CONFIG FILE AND LINK IT TO INSTALL PATH

read -r -d '' serviceConfig << EOM
[Unit]
Description=Service wrapper for java application 'mmm-ws-web-server'
After=syslog.target

[Service]
User=_USERNAME_
Environment="JAVA_OPTS="
ExecStart="$dir/$serviceConfigPath.sh"
WorkingDirectory=$dir
SuccessExitStatus=143

[Install]
WantedBy=multi-user.target
EOM

serviceConfig="${serviceConfig/_USERNAME_/$username}"
echo "$serviceConfig" > $serviceConfigPath
ln -sf $serviceConfigPath $installPath

echo "Installation complete."
read -n 1 -s -r -p "Press any key to continue"
echo