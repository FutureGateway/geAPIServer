#!/bin/bash
#
# patch_0.0.6.sh
#
# This patch includes the following features: 
#
# - Adding runtime_data fields: data_type, data_proto
#

# Include functions
. ./patch_functions.sh

PATCH="0.0.6"
check_patch $PATCH

# Create a temporary SQL file
SQLTMP=$(mktemp /tmp/patch_${PATCH}_XXXXXX)

#
# Missing columns/tables
#

out "Modifying runtime_data table"
cat >$SQLTMP <<EOF
alter table runtime_data add data_proto varchar(128);
alter table runtime_data add data_type varchar(128);
EOF
asdb_file $SQLTMP
out "Database changed"
out ""
# Removing SQL file
rm -f $SQLTMP

#
# VO: vo.indigo-datacloud.eu
#
# This change requires sudo or root privileges so that
# it will be only reported as change to apply
#
out ""
out "!!! IMPORTANT !!!"
out "Patch script cannot apply changes with sudo or root privileges so that"
out "please execute with sudo or as root user the following code lines in"
out "order to support the vo.indigo-datacloud.eu VO."
out ""
out "echo '\"vo.indigo-datacloud.eu\" \"voms01.ncg.ingrid.pt\" \"40101\" \"/C=PT/O=LIPCA/O=LIP/OU=Lisboa/CN=voms01.ncg.ingrid.pt\" \"vo.indigo-datacloud.eu\" > /etc/vomses/indigo-voms01.ncg.ingrid.pt"
out "mkdir -p /etc/grid-security/vomsdir/vo.indigo-datacloud.eu"
out "cat > /etc/grid-security/vomsdir/vo.indigo-datacloud.eu/voms01.ncg.ingrid.pt.lsc <<EOF"
out "/C=PT/O=LIPCA/O=LIP/OU=Lisboa/CN=voms01.ncg.ingrid.pt"
out "/C=PT/O=LIPCA/CN=LIP Certification Authority"
out "EOF"
out ""

out "registering patch $PATCH"
register_patch "$PATCH" "patch_${PATCH}.sh" "Add runtime_data fields: proto and type"
out "patch registered"

