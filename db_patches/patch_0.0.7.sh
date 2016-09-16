#!/bin/bash
#
# patch_0.0.7.sh
#
# This patch includes the following features: 
#
# - Increasing the field length for token field in fg_token table (1024)
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.7"
PATCH_DESC="Increasing the field length for token field in fg_token table"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

out "Modifying fg_token table"
cat >$SQLTMP <<EOF
alter table fg_token modify token varchar(1024);
EOF
asdb_file $SQLTMP
out "Database changed"
out ""
# Removing SQL file
rm -f $SQLTMP

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "$PATCH_DESC"
out "patch registered"

