#!/bin/bash
#
# patch_0.0.3.sh
#
# This patch includes the following features: 
#
# - Virtual infrastructure 
# - Application outcome field and not null contraints on name, description
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.3"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

# infrastructure.virtual
out "Checking infrastructure.virtual"
NEWCOL=$(asdb_cmd "select count(virtual) from infrastructure;" 2>/dev/null)
if [ "$NEWCOL" = "" ]; then
  out "infrastructure.virtual missing; patching db"
  echo "alter table infrastructure add virtual boolean default false not null;" > $SQLTMP
  asdb_file $SQLTMP
  out "infrastructure.virtual created"
else
  out "infrastructure.virtual already exists"
fi

out "Modifying application table"
cat >$SQLTMP <<EOF
alter table application add outcome varchar(32) default "JOB" not null;
alter table application modify name varchar(64) not null;
alter table application modify description varchar(256) not null;
EOF
asdb_file $SQLTMP
out "Application table changed"

# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "virtual infrastructure, application name, description change"
out "patch registered"

