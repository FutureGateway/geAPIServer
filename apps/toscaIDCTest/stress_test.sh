#!/bin/bash
APP_ID=<app_id> # Place here the appId
USER=brunor
SUBMIT_COUNT=1
SUBMIT_DELAY=10 
TOKEN=$1
if [ "$TOKEN" != "" ]; then
  CURL_AUTH="-H \"Authorization: Bearer $TOKEN\""
else
  CURL_AUTH=""
fi

if [ "$APP_ID" = "" ]; then
  echo "Unable to identify application '"$APP_NAME"'"
  exit 1
fi


for i in $(seq 1 $SUBMIT_COUNT)
do
  echo "Submitting job #$i"
  TMP=$(mktemp /tmp/stresstest_XXXXXXXX)
  CMD="curl -H \"Content-Type: application/json\" $CURL_AUTH  -X POST -d '{\"application\":\""$APP_ID"\",\"description\":\"tosca test run\"}' http://localhost:8888/v1.0/tasks | tee $TMP"
  eval $CMD
  id=$(cat $TMP | jq '.id' | xargs echo)
  if [ "$id" != "" ]; then
    echo "id for job $i = $id"
    CMD="curl -H \"Content-Type: application/json\" $CURL_AUTH  -X POST http://localhost:8888/v1.0/tasks/$id/input | tee $TMP"
    eval $CMD
  fi
  rm -f $TMP
  if [ $i -ne $SUBMIT_COUNT ]; then
    sleep $SUBMIT_DELAY
  fi
done

