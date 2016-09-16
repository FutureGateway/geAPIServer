#!/bin/bash
#
# setup_app.sh - Script to install an application on FutureGateway
#
USER=brunor
APPNAME="repast@DFA.CT"
APPDESC="amber tester application with docker"
OUTCOME="JOB"
INFRANAME="repast_test@CT_DFA_stack01"
INFRADESC="Repast tester application"
FILESPATH="$FGLOCATION/fgAPIServer/apps/repast"


APPDEFJSONFILE=$(mktemp)
cat >$APPDEFJSONFILE <<EOF
{
  "outcome": "${OUTCOME}",
  "description": "${APPDESC}",
  "name": "${APPNAME}",
  "enabled": true,
  "input_files": [
    {
      "name": "pilot_script.sh",
      "path": "${FILESPATH}",
      "override": false
    }
  ],
  "parameters": [
    {
      "description": "",
      "value": "GridEngine",
      "name": "target_executor"
    },
    {
      "description": "",
      "value": "/bin/bash",
      "name": "jobdesc_executable"
    },
    {
      "description": "",
      "value": "pilot_script.sh",
      "name": "jobdesc_arguments"
    },
    {
      "description": "",
      "value": "myRepast-infection-Output.txt",
      "name": "jobdesc_output"
    },
    {
      "description": "",
      "value": "myRepast-infection-Error.txt",
      "name": "jobdesc_error"
    }
  ],
  "infrastructures": [
    {
      "name": "${INFRANAME}",
      "virtual": false,
      "enabled": true,
      "parameters": [
        {
          "value": "rocci://stack-server-01.cloud.dfa.unict.it:8787",
          "name": "jobservice"
        },
        {
          "value": "3fb9e799-0d4f-41ab-ac7a-b6939f5b81c4",
          "name": "os_tpl"
        },
        {
          "value": "repast",
          "name": "resource_tpl"
        },
        {
          "value": "REPAST_Analysis",
          "name": "attributes_title"
        },
        {
          "value": "etokenserver2.ct.infn.it",
          "name": "eToken_host"
        },
        {
          "value": "8082",
          "name": "eToken_port"
        },
        {
          "value": "bc681e2bd4c3ace2a4c54907ea0c379b",
          "name": "eToken_id"
        },
        {
          "value": "vo.africa-grid.org",
          "name": "voms"
        },
        {
          "value": "vo.africa-grid.org",
          "name": "voms_role"
        },
        {
          "value": "true",
          "name": "rfc_proxy"
        },
        {
          "value": "false",
          "name": "disable-voms-proxy"
        },
        {
          "value": "false",
          "name": "proxy-renewal"
        },
        {
          "value": "true",
          "name": "secured"
        },
        {
          "value": "/network/public",
          "name": "link"
        },
        {
          "value": "22",
          "name": "sshport"
        }
      ],
      "description": "${INFRADESC}"
    }
  ]
}
EOF

# Setup application, retrieve id and sets stress_test app_id
TMP=$(mktemp)
CMD="curl -H \"Content-Type: application/json\" -X POST -d '"$(cat $APPDEFJSONFILE)"' http://localhost:8888/v1.0/applications?user=$USER" 
# echo $CMD
eval $CMD | tee $TMP
#APPID=$(cat $TMP | grep "\"id\"" | awk -F":" '{ print $2 }' | xargs echo | sed s/,//g)
APPID=$(cat $TMP | jq .id | xargs echo)
sed -i -e "s/<app_id>/$APPID/" stress_test.sh
rm -f $TMP
rm -f $APPDEFJSONFILE
echo ""
echo "Installation done"
