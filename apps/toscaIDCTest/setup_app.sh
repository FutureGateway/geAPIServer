#!/bin/bash
#
# setup_app.sh - Script to install an application on FutureGateway
#
APPNAME="hostname@toscaIDC"
APPDESC="hostname tester application on toscaIDC"
OUTCOME="JOB"
TOSCA_ENDPOINT="http://localhost:8889/orchestrator/deployments"
TOSCA_IP=$(echo $TOSCA_ENDPOINT | sed s/[a-z][A-Z]*//g | tr '/' ' ' | sed s/': '// | xargs echo)
INFRADESC="Tosca test at $TOSCA_ENDPOINT"
INFRANAME="tosca_Test@$TOSCA_IP"
FILESPATH="$FGLOCATION/fgAPIServer/apps/toscaTest"
TOKEN=$1
if [ "$TOKEN" != "" ]; then
  CURL_AUTH="-H \"Authorization: Bearer $TOKEN\""
else
  CURL_AUTH=""
fi

# Prepare data section for curl command
CURLDATA=$(mktemp /tmp/curldata_XXXXXXXX)
cat >$CURLDATA <<EOF
{
  "infrastructures": [
    {
      "description": "${INFRADESC}",
      "parameters": [
        {
          "name": "tosca_endpoint",
          "value": "${TOSCA_ENDPOINT}"
        },
        {
          "name": "tosca_template",
          "value": "tosca_template.yaml"
        },
        {
          "name": "tosca_parameters",
          "value": "params=parameters.json"
        }
      ],
      "enabled": true,
      "virtual": false,
      "name": "${INFRANAME}"
    }
  ],
  "parameters": [
    {
      "name": "target_executor",
      "value": "ToscaIDC",
      "description": ""
    },
    {
      "name": "jobdesc_executable",
      "value": "tosca_test.sh",
      "description": "unused"
    },
    {
      "name": "jobdesc_output",
      "value": "stdout.txt",
      "description": "unused"
    },
    {
      "name": "jobdesc_error",
      "value": "stderr.txt",
      "description": "unused"
    }
  ],
  "enabled": true,
  "input_files": [
    {
      "override": false,
      "path": "${PWD}",
      "name": "tosca_template.yaml"
    },
    {
      "override": false,
      "path": "${PWD}",
      "name": "tosca_test.sh"
    },
    {
      "override": false,
      "path": "${PWD}",
      "name": "parameters.json"
    }
  ],
  "name": "${APPNAME}",
  "description": "${APPDESC}",
  "outcome": "${OUTCOME}"
}
EOF

# Setup application, retrieve id and sets stress_test app_id
CURLOUT=$(mktemp /tmp/curlout_XXXXXXXX)
CURLDATA_CONTENT=$(cat $CURLDATA)
CMD="curl -H \"Content-Type: application/json\" $CURL_AUTH -X POST -d '"$CURLDATA_CONTENT"' http://localhost:8888/v1.0/applications | tee $CURLOUT" 
echo "Executing: "
echo $CMD
eval $CMD 
echo ""
echo "Retrieving AppId and modifying stress_test.sh"
APPID=$(cat $CURLOUT | jq '.id' | xargs echo)
sed -i -e "s/<app_id>/$APPID/" stress_test.sh
rm -f $CURLDATA
rm -f $CURLOUT

