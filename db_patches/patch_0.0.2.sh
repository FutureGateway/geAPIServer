#!/bin/bash
#
# patch_0.0.2.sh
#
# A complex script that updates an existing futuregteway
# with no patching mechanism to the 0.0.2 version (startup of patch)
#
# - 0.0.2 Features
# - SimpleTosca
# - as_queue checks
# - runtime_data
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.2"
check_patch $PATCH

# 1st setup DBUtils
FGENV=$FGLOCATION/setenv.sh
ASDBCHK=$(cat $FGENV | grep asdb | wc -l)
UTDBCHK=$(cat $FGENV | grep utdb | wc -l)

if [ $ASDBCHK -eq 0 ]; then
  TMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)
  out "asdb and utdb tools not existing; installing them"
  cat >$TMP <<EOF
# DB functions
asdb() {
  cmd=\$(echo "\$*" | sed s/\$0//)
  if [ "\$cmd" != "" ]; then
    cmd="-e \\"\$cmd\\""
  fi
  eval "mysql -h localhost -P 3306 -u fgapiserver -pfgapiserver_password \$ASDB_OPTS fgapiserver \$cmd"
}
EOF
  cat $TMP >> $FGENV
  source $TMP
  rm -f $TMP
else
  out "asdb utility already defined"
fi

if [ $UTDBCHK -eq 0 ]; then
  TMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)
  out "utdb tool not existing; installing it"
  cat >> $TMP <<EOF
utdb() {
  cmd=\$(echo "\$*" | sed s/\$0//)
    if [ "\$cmd" != "" ]; then
    cmd="-e \\"\$cmd\\""
  fi
  eval "mysql -h localhost -P 3306 -u tracking_user -pusertracking \$UTDB_OPTS userstracking \$cmd"
}
EOF
  cat $TMP >> $FGENV
  source $TMP
  rm -f $TMP
else
  out "utdb utility already defined"
fi

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

# Check for runtime_data
RUNTIMEDATA=$(asdb_cmd "desc runtime_data;" 2>/dev/null)
if [ "$RUNTIMEDATA" = "" ]; then
  cat >$SQLTMP <<EOF
create table runtime_data (
   task_id      int unsigned  not null      -- id of the task owning data
  ,data_id      int unsigned  not null      -- data identifier (a progressive number)
  ,data_name    varchar(128)  not null      -- name of data field
  ,data_value   varchar(1024) not null      -- value of data field
  ,data_desc    varchar(2048)               -- value of data description
  ,creation     datetime      not null      -- When data has been written the first time
  ,last_change  datetime      not null      -- When data has been updated
  ,primary key(task_id,data_id)
  ,foreign key (task_id) references task(id)
);
EOF
  asdb_file $SQLTMP
fi

#
# Missing columns/tables
#

# as_queue.retry
out "Checking as_queue.retry"
NEWCOL=$(asdb_cmd "select count(retry) from as_queue;" 2>/dev/null)
if [ "$NEWCOL" = "" ]; then
  out "as_queue.retry missing; patching db"
  echo "alter table as_queue add retry int unsigned not null default 0;" > $SQLTMP
  asdb_file $SQLTMP
  out "as_queue.retry created"
else
  out "as_queue.retry column already exists"
fi

# as_queue.check_ts
NEWCOL=$(asdb_cmd "select count(check_ts) from as_queue;" 2>/dev/null)
if [ "$NEWCOL" = "" ]; then
  out "as_queue.check_ts missing; patching db"
  echo "alter table as_queue add check_ts datetime;"              > $SQLTMP
  echo "update as_queue set check_ts=last_change;"               >> $SQLTMP
  echo "alter table as_queue modify check_ts datetime not null;" >> $SQLTMP
  asdb_file $SQLTMP
  out "as_queue.check_ts created"
else
  out "as_queue.check_ts column already exists"
fi

# application_parameter.pdesc
NEWCOL=$(asdb_cmd "select count(pdesc) from application_parameter;" 2>/dev/null)
if [ "$NEWCOL" = "" ]; then
  out "application_parameter.pdesc missing; patching db"
  echo "alter table application_parameter add pdesc varchar(1024);" > $SQLTMP
  asdb_file $SQLTMP
  out "application_parameter.pdesc created"
else
  out "application_parameter.pdesc already exists"
fi

# simple_tosca
NEWTAB=$(asdb_cmd "select count(*) from simple_tosca;" 2>/dev/null)
if [ "$NEWTAB" = "" ]; then
  out "simple_tosca table missing; creating it"
  cat >$SQLTMP <<EOF
create table simple_tosca (
    id           int unsigned not null
   ,task_id      int unsigned not null
   ,tosca_id     varchar(256) not null
   ,tosca_status varchar(32)  not null
   ,creation     datetime     not null -- When the action is enqueued
   ,last_change  datetime     not null -- When the record has been modified by the GridEngine last time
   ,primary key(id)
);
EOF
  asdb_file $SQLTMP
  out "simple_tosca table created"
else
  out "simple_tosca table already exists"
fi

# db_patch table
NEWTAB=$(asdb_cmd "select count(*) from db_patches;" 2>/dev/null)
if [ "$NEWTAB" = "" ]; then
  out "db_patch table missing; patching db"
  cat >$SQLTMP <<EOF
create table db_patches (
    id           int unsigned not null -- Patch Id
   ,version      varchar(32)  not null -- Current database version
   ,name         varchar(256) not null -- Name of the patch (it describes the involved feature)
   ,file         varchar(256) not null -- file refers to fgAPIServer/db_patches directory
   ,applied      datetime              -- Patch application timestamp
   ,primary key(id)
);
insert into db_patches (id,version,name,file,applied) values (1,'0.0.1','baseline setup','../fgapiserver_db.sql',now())
EOF
  asdb_file $SQLTMP
  out "db_patch table created"
else
  out "db_patch table already exists"
fi

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "adding patching mechanism, simple_tosca, check on as_queue table"
out "patch registered"

