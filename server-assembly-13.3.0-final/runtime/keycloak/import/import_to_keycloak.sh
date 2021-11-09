#!/bin/bash

MY_DIR=${0%/*}
SOURCE_DIR=${1:-.}
KC_HOME=${KC_HOME:-$MY_DIR/../../../keycloak}
KC_URL=${KEYCLOAK_URL:-http://localhost:8083/auth}
KC_ADMIN_USER=${KC_ADMIN_USER:-admin}
KC_ADMIN_PASSWORD=${KC_ADMIN_PASSWORD:-admin}
REALM_NAME=${REALM_NAME:-ataccamaone}

"$KC_HOME/bin/kcadm.sh" config credentials --server $KC_URL --realm master --user $KC_ADMIN_USER --password $KC_ADMIN_PASSWORD

declare -A users
declare -A groups

# USERS
#user_name
while read username; do
	echo "Creating user "$username
	user_uid=`"$KC_HOME/bin/kcadm.sh" create users -r $REALM_NAME -s username=$username 2>&1 | tee err.txt | grep "'" | sed "s/.*'\(.*\)'.*/\1/"`
	users[$username]=$user_uid
	echo "Created new user with id $user_uid"
done < $SOURCE_DIR/users_to_add.txt

#ROLES
#role_name;role_desc
while read role; do
	desc=${role#*;}
	role=${role%;*}
	echo "Creating role "$role
	"$KC_HOME/bin/kcadm.sh" create roles -r $REALM_NAME -s name=$role -s "description=$desc"
done < $SOURCE_DIR/roles_to_add.txt

#GROUPS
#group_name
while read group; do
	echo "Creating group "$group
	grp_uid=`"$KC_HOME/bin/kcadm.sh" create groups -r $REALM_NAME -s name=$group 2>&1 | tee err.txt | grep "'" | sed "s/.*'\(.*\)'.*/\1/"`
	groups[$group]=$grp_uid
	echo "Created new group with id $grp_uid"
done < $SOURCE_DIR/groups_to_add.txt

#USER-ROLE
#user_name;role_name
while read user_role; do
	user=${user_role%%;*}
	role=${user_role#*;}
	echo "Adding role $role to user $user"
	"$KC_HOME/bin/kcadm.sh" add-roles -r $REALM_NAME --uusername $user --rolename $role
done < $SOURCE_DIR/usr_role.txt

#USER-GROUP
#user_name;group_name
while read user_group; do
	user=${user_group%%;*}
	group=${user_group#*;}
	user_uid=${users[$user]}
	grp_uid=${groups[$group]}
	echo "Adding user $user to group $group"
	"$KC_HOME/bin/kcadm.sh" update -r $REALM_NAME users/$user_uid/groups/$grp_uid -s userId=$user_uid -s groupId=$grp_uid -n
done < $SOURCE_DIR/usr_grp.txt

#GROUP-ROLE
#user_name;role_name
while read group_role; do
	group=${group_role%%;*}
	role=${group_role#*;}
	echo "Adding role $role to group $group"
	"$KC_HOME/bin/kcadm.sh" add-roles -r $REALM_NAME --gid ${groups[$group]} --rolename $role
done < $SOURCE_DIR/grp_role.txt


#GROUP-GROUP
#owner_group_name;member_group_name
while read owner_mamber; do
	owner=${owner_mamber%%;*}
	member=${owner_mamber#*;}
	echo "Adding member group $member to group $owner"
	"$KC_HOME/bin/kcadm.sh" create -r $REALM_NAME groups/${groups[$owner]}/children -s name=$member
done < $SOURCE_DIR/grp_grp.txt