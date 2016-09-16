#!/usr/bin/env python
# Copyright (c) 2015:
# Istituto Nazionale di Fisica Nucleare (INFN), Italy
# Consorzio COMETA (COMETA), Italy
#
# See http://www.infn.it and and http://www.consorzio-cometa.it for details on
# the copyright holders.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import fgapiserver
from mklogtoken import token_encode, token_decode, token_info

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


class Test_fgAPIServer(unittest.TestCase):

    def banner(self, test_name):
        print ""
        print "------------------------------------------------"
        print " Testing: %s" % test_name
        print "------------------------------------------------"

    #
    # fgapiserver
    #

    def test_User(self):
        self.banner("User class")
        user = fgapiserver.User(2, 'test')
        self.assertEqual(2, user.get_id())
        self.assertEqual('test', user.get_name())

    def test_paginate_reposnse(self):
        self.banner("paginate_response(txt,'2','3')")
        response = ['111111111111111111111111111\n',
                    '222222222222222222222222222\n',
                    '333333333333333333333333333\n',
                    '444444444444444444444444444\n',
                    '555555555555555555555555555\n',
                    '666666666666666666666666666\n',
                    '777777777777777777777777777\n',
                    '888888888888888888888888888\n',
                    '999999999999999999999999999\n',
                    '000000000000000000000000000\n',
                    'AAAAAAAAAAAAAAAAAAAAAAAAAAA\n',
                    'BBBBBBBBBBBBBBBBBBBBBBBBBBB\n', ]
        expected_page = ['444444444444444444444444444\n',
                         '555555555555555555555555555\n',
                         '666666666666666666666666666\n', ]
        received_page = fgapiserver.paginate_response(response, '1', '3')
        self.assertEqual(expected_page, received_page)

    def test_checkDbVer(self):
        self.banner("checkDbVer()")
        self.assertEqual('0.0.6', fgapiserver.check_db_ver())

    def test_fgapiserver(self):
        self.banner("get_task_app_id(1)")
        self.assertEqual('1', fgapiserver.get_task_app_id(1))

    def test_get_file_task_id(self):
        self.banner("get_file_task_id('test_file','/tmp')")
        task_id = fgapiserver.get_file_task_id('test_file', '/tmp')
        print task_id
        self.assertEqual(task_id, '1')

    def test_verify_session_token(self):
        self.banner("verify_session_token("
                    "'AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKK')")
        result = fgapiserver.verify_session_token(
            'AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKK')
        self.assertEqual(result[0], '1')
        self.assertEqual(result[1], 'test_user')

    #
    # mklogtoken
    #
    def test_mklogtoken(self):
        self.banner("Testing tokenEncode/tokenDecode/tokenInfo")
        key = "0123456789ABCDEF"
        username = 'test'
        password = 'testpwd'
        token = token_encode(key, username, password)
        tinfo = token_decode(key, token)
        print ("Token with key: '%s'; "
               "encoding: 'username:=%s:"
               "password=%s:"
               "timestamp=<issue_time>' is '%s'"
               % (key, username, password, token))
        print "Decoded token: '%s' -> '%s'" % (token, tinfo)
        username2, password2, timestamp2 = token_info(token)
        print ("Token info: 'username=%s:password=%s:timestamp=%s'"
               % (username2, password2, timestamp2))
        self.assertEqual("%s:%s" % (username, password), "%s:%s" % (username2,
                                                                    password2))
if __name__ == '__main__':
    print "----------------------------------"
    print "Starting unit tests ..."
    print "----------------------------------"
    unittest.main()
    print "Tests completed"
