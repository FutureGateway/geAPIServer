#!/bin/bash
#
# patch_0.0.8.sh
#
# This patch includes the following features: 
#
# - ToscaIDC interface uses its own table tosca_idc 
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.8"
PATCH_DESC="ToscaIDC interface uses its own table tosca_idc"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

out "Creating ToscaIDC executor interface table: tosca_idc"
cat >$SQLTMP <<EOF
create table tosca_idc (
    id             int unsigned  not null
   ,task_id        int unsigned  not null
   ,tosca_id       varchar(1024) not null
   ,tosca_status   varchar(32)   not null
   ,tosca_endpoint varchar(1024) not null
   ,creation       datetime      not null -- When the action is enqueued
   ,last_change    datetime      not null -- When the record has been modified by the GridEngine last time
   ,primary key(id)
);
EOF
asdb_file $SQLTMP
out "Database changed"
out ""
# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

