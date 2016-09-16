#!/bin/bash
#
# patch_0.0.4.sh
#
# This patch includes the following features: 
#
# - User membership, groups and roles
# - Login and session token managemen 
# - Protected API calls
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.4"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

out "Users Groups and Roles definition"
cat >$SQLTMP <<EOF
create table fg_user (
    id           int unsigned not null auto_increment
   ,name         varchar(128)  not null
   ,password     varchar(4096) not null
   ,first_name   varchar(128)  not null
   ,last_name    varchar(128)  not null
   ,institute    varchar(256)  not null
   ,mail         varchar(1024) not null
   ,creation     datetime      not null
   ,modified     datetime      not null
   ,primary key(id,name)
);
insert into fg_user (id,name,password,first_name,last_name,institute,mail,creation,modified)
values (1,'futuregateway',password('futuregateway'),'FutureGateway','FutureGateway','INFN','sgw-admin@lists.indigo-datacloud.eu',now(),now());
insert into fg_user (id,name,password,first_name,last_name,institute,mail,creation,modified)
values (2,'test',password('test'),'Test','Test','INFN','sgw-admin@lists.indigo-datacloud.eu',now(),now());
insert into fg_user (id,name,password,first_name,last_name,institute,mail,creation,modified)
values (3,'brunor',password('brunor'),'Riccardo','Bruno','INFN','riccardo.bruno@ct.infn.it',now(),now());
create table fg_group (
    id           int unsigned not null auto_increment
   ,name         varchar(128)  not null
   ,creation     datetime      not null
   ,modified     datetime      not null
   ,primary key(id)
);
insert into fg_group (id,name,creation,modified) values (1,'administrator',now(),now());
insert into fg_group (id,name,creation,modified) values (2,'test',now(),now());
insert into fg_group (id,name,creation,modified) values (3,'generic user',now(),now());
create table fg_role (
    id           int unsigned not null auto_increment
   ,name         varchar(128)  not null
   ,creation     datetime      not null
   ,modified     datetime      not null
   ,primary key(id)
);
insert into fg_role (id,name,creation,modified) values ( 1,'app_install',now(),now());
insert into fg_role (id,name,creation,modified) values ( 2,'app_change',now(),now());
insert into fg_role (id,name,creation,modified) values ( 3,'app_delete',now(),now());
insert into fg_role (id,name,creation,modified) values ( 4,'app_view',now(),now());
insert into fg_role (id,name,creation,modified) values ( 5,'app_run',now(),now());
insert into fg_role (id,name,creation,modified) values ( 6,'infra_add',now(),now());
insert into fg_role (id,name,creation,modified) values ( 7,'infra_change',now(),now());
insert into fg_role (id,name,creation,modified) values ( 8,'infra_delete',now(),now());
insert into fg_role (id,name,creation,modified) values ( 9,'infra_view',now(),now());
insert into fg_role (id,name,creation,modified) values (10,'infra_attach',now(),now());
insert into fg_role (id,name,creation,modified) values (11,'infra_detach',now(),now());
insert into fg_role (id,name,creation,modified) values (12,'task_delete',now(),now());
insert into fg_role (id,name,creation,modified) values (13,'task_view',now(),now());
insert into fg_role (id,name,creation,modified) values (14,'task_userdata',now(),now());
insert into fg_role (id,name,creation,modified) values (15,'user_add',now(),now());
insert into fg_role (id,name,creation,modified) values (16,'user_del',now(),now());
insert into fg_role (id,name,creation,modified) values (17,'user_change',now(),now());
insert into fg_role (id,name,creation,modified) values (18,'group_change',now(),now());      
insert into fg_role (id,name,creation,modified) values (19,'role_change',now(),now());      
insert into fg_role (id,name,creation,modified) values (20,'user_impersonate',now(),now());
insert into fg_role (id,name,creation,modified) values (21,'group_impersonate',now(),now());

create table fg_user_group (
    user_id     int unsigned not null
   ,group_id    int unsigned not null
   ,creation    datetime     not null
   ,foreign key (user_id) references fg_user(id)
   ,foreign key (group_id) references fg_group(id)
);
insert into fg_user_group (user_id,group_id,creation) values (1,1,now());
insert into fg_user_group (user_id,group_id,creation) values (2,2,now());
insert into fg_user_group (user_id,group_id,creation) values (3,3,now());
create table fg_group_role (
    group_id    int unsigned not null
   ,role_id     int unsigned not null
   ,creation    datetime     not null
   ,foreign key (group_id) references fg_group(id)
   ,foreign key (role_id) references fg_role(id)
);
insert into fg_group_role (group_id,role_id,creation)
select 1,id,now() from fg_role;
insert into fg_group_role (group_id,role_id,creation) values (2, 4, now());
insert into fg_group_role (group_id,role_id,creation) values (2, 5, now());
insert into fg_group_role (group_id,role_id,creation) values (2,12, now());
insert into fg_group_role (group_id,role_id,creation) values (2,13, now());
insert into fg_group_role (group_id,role_id,creation) values (2,14, now());
insert into fg_group_role (group_id,role_id,creation) values (3, 4, now());
create table fg_group_apps (
    group_id    int unsigned not null
   ,app_id      int unsigned not null
   ,creation    datetime     not null
   ,foreign key (group_id) references fg_group(id)
   ,foreign key (app_id) references application(id)
);
insert into fg_group_apps (group_id, app_id, creation)
	select 1,id,now() from application;                                 
insert into fg_group_apps (group_id, app_id, creation) values (2,1,now());
insert into fg_group_apps (group_id, app_id, creation) values (2,2,now());
create table fg_token (
    token    varchar(64)  not null
   ,user_id  int unsigned not null
   ,creation datetime     not null
   ,expiry   integer
);
EOF
asdb_file $SQLTMP
out "Database changed"
out ""
out "(!) IMPORTANT"
out "This patch implies the installation of two different python packages:"
out "   flask-login"
out "   pycrypto"
out "The installation of these packages may vary accordingly to the destination OS"
out "MACOSX:"
out "  sudo pip install flask-login"
out "  sudo pip install pycrypto"
out "DEB: (Ubuntu)"
out "  sudo apt-get install python-flask-login"
out "  sudo apt-get install python-python-crypto"
out "  (!) WARNING"
out "  On Ubuntu 14.04 Server LTS flask-login is not updated;"
out "  you may require to execute the following commands instead:"
out "     sudo apt-get install python-pip"
out "     pip install flask-login"
out "EL6/7: (CentOS)"
out "  yum install python-flask-login.noarch"
out "  yum insall python-crypto"
out ""
# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "User membership with log and session tokens and API call restrictions"
out "patch registered"

