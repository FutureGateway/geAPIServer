#!/usr/bin/python

import os
import sys
import pycurl
import json
import argparse


def get_png(output_pointers, name, pwd, dst_output):

    from urllib import urlencode

    """
    Given base url, username and password,
    provides the output file
    """

    outfile = open(dst_output, 'w')
    base_url = output_pointers['base_url'].replace('http', 'https')
    workflow_id = output_pointers['workflow_id']
    session_id = output_pointers['session']

    pwd = pwd.rstrip('\n')
    export_path = "/export/misc/"
    png_name = "/precip_trend_analysis.png"
    cookie_string = ""

    png_url = base_url + '/sessions.php/' + \
        session_id + export_path + workflow_id + png_name
    print png_url

    post_data = {'username': name, 'password': pwd, 'submit': '"login"'}
    postfields = urlencode(post_data)

    target = pycurl.Curl()
    target.setopt(target.URL, str(png_url))
    target.setopt(target.WRITEFUNCTION, outfile.write)
    target.setopt(target.POSTFIELDS, postfields)
    target.setopt(pycurl.COOKIEJAR, 'ophidia_cookie')
    target.setopt(pycurl.COOKIEFILE, 'ophidia_cookie')
    # target.setopt(target.FOLLOWLOCATION, True)
    target.setopt(target.SSL_VERIFYPEER, 0)

    try:
        target.perform()
        result = target.getinfo(pycurl.HTTP_CODE)
        target.close()

    except pycurl.error as e:
        err_msg = "Failed download on %s (pycurl %s) !\n-----\n" % (png_url, e)
        sys.stderr.write(err_msg)
        print err_msg
        result = "-1"

    os.remove('ophidia_cookie')

    if result == 200:
        return 0
    else:
        return 1


def grab_workflow(fileStream):
    """
    Parses json stream, to grab workflow and marker IDs
    """
    json_data = json.loads(fileStream)
    response = json_data["response"]["response"]
    values = {'base_url': "", 'session': -1,
              'workflow_id': -1, 'marker_id': -1}

    workflow_status = response[0]['objcontent'][0]['message']
    if workflow_status == "OPH_STATUS_COMPLETED":

        workflow_responses = response[2]
        content = workflow_responses["objcontent"]
        rows = content[0]['rowvalues']

        for r in rows:
            if r[5] == "Create map":

                values['base_url'] = r[0].split('/sessions')[0]
                values['session'] = r[1]
                values['workflow_id'] = r[2]
                values['marker_id'] = r[3]

    return values

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=('This script parses Ophidia JSON output'
                     ' and grabs the png image'))
    parser.add_argument('json_input', help='Path to the json input file')
    parser.add_argument(
        'oph_credentials', help=('Path to the file containing username '
                                 'and password for Ophidia server'))
    parser.add_argument('output_file', help='Path to the png output file')
    args = parser.parse_args()

    credentials = open(args.oph_credentials, 'r').read()

    # this can be better refined
    cred = credentials.split(':')
    user = cred[0]
    pwd = cred[1]

    json_input = open(args.json_input, 'r')

    output_pointers = grab_workflow(json_input.read())

    exit_code = get_png(output_pointers, user, pwd, args.output_file)
    sys.exit(exit_code)
