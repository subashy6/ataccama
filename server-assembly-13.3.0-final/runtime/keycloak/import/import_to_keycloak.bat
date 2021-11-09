@echo off

set MY_DIR=%~dp0

set SOURCE_DIR=%1
set KC_HOME=%MY_DIR%\..\..\..\keycloak
set KC_URL=http://localhost:8083/auth
set KC_ADMIN_USER=admin
set KC_ADMIN_PASSWORD=admin
set REALM_NAME=ataccamaone

call "%KC_HOME%\bin\kcadm.bat" config credentials --server %KC_URL% --realm master --user %KC_ADMIN_USER% --password %KC_ADMIN_PASSWORD%

setlocal EnableDelayedExpansion

rem USERS
rem user_name
FOR /F %%U IN (%SOURCE_DIR%\users_to_add.txt) do (
	echo Creating user %%U
	call "%KC_HOME%\bin\kcadm.bat" create users -r %REALM_NAME% -s username=%%U 2> err.txt
 	set /p err_txt=<err.txt
	for /f "delims=' tokens=2" %%T in ("!err_txt!") do set user_uid=%%T
	set users[%%U]=!user_uid!
	echo Created new user with id !user_uid!
	del err.txt
)

rem ROLES
rem role_name;role_desc
FOR /F "delims=" %%R IN (%SOURCE_DIR%\roles_to_add.txt) do (
	for /f "delims=; tokens=1" %%T in ("%%R") do set role=%%T
	for /f "delims=; tokens=2" %%T in ("%%R") do set desc=%%T
	echo Creating role !role!
	call "%KC_HOME%\bin\kcadm.bat" create roles -r %REALM_NAME% -s name=!role! -s "description=!desc!"
)

rem GROUPS
rem group_name
FOR /F %%G IN (%SOURCE_DIR%\groups_to_add.txt) do (
	echo Creating group %%G
	call "%KC_HOME%\bin\kcadm.bat" create groups -r %REALM_NAME% -s name=%%G 2> err.txt
	set /p err_txt=<err.txt
	for /f "delims=' tokens=2" %%T in ("!err_txt!") do set grp_uid=%%T
	set groups[%%G]=!grp_uid!
	echo Created new group with id !grp_uid!
	del err.txt
)

rem USER-ROLE
rem user_name;role_name
FOR /F %%R IN (%SOURCE_DIR%\usr_role.txt) do (
	for /f "delims=; tokens=1" %%T in ("%%R") do set user=%%T
	for /f "delims=; tokens=2" %%T in ("%%R") do set role=%%T
	echo Adding role !role! to user !user!
	call "%KC_HOME%\bin\kcadm.bat" add-roles -r %REALM_NAME% --uusername !user! --rolename !role!
)

rem USER-GROUP
rem user_name;group_name
FOR /F %%G IN (%SOURCE_DIR%\usr_grp.txt) do (
	for /f "delims=; tokens=1" %%T in ("%%G") do set user=%%T
	for /f "delims=; tokens=2" %%T in ("%%G") do set group=%%T
	call set user_uid=%%users[!user!]%%
	call set grp_uid=%%groups[!group!]%%
	echo Adding user !user! to group !group!
	call "%KC_HOME%\bin\kcadm.bat" update -r %REALM_NAME% users/!user_uid!/groups/!grp_uid! -s userId=!user_uid! -s groupId=!grp_uid! -n
)

rem GROUP-ROLE
rem group_name;role_name
FOR /F %%R IN (%SOURCE_DIR%\grp_role.txt) do (
	for /f "delims=; tokens=1" %%T in ("%%R") do set group=%%T
	for /f "delims=; tokens=2" %%T in ("%%R") do set role=%%T
	call set grp_uid=%%groups[!group!]%%
	echo Adding role !role! to group !group!
	call "%KC_HOME%\bin\kcadm.bat" add-roles -r %REALM_NAME% --gid !grp_uid! --rolename !role!
)

rem GROUP-GROUP
rem owner_group_name;member_group_name
FOR /F %%G IN (%SOURCE_DIR%\grp_grp.txt) do (
	for /f "delims=; tokens=1" %%T in ("%%G") do set owner=%%T
	for /f "delims=; tokens=2" %%T in ("%%G") do set member=%%T
	call set owner_uid=%%groups[!owner!]%%
	echo Adding member group !member! to group !owner!
	call "%KC_HOME%\bin\kcadm.bat" create -r %REALM_NAME% groups/!owner_uid!/children -s name=!member!
)
	
endlocal