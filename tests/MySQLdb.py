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


#
# MySQLdb.py emulates the MySQL module returning configurable outputs
#            accordingly to pre-defined queries (see queries variable)
#

__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.2-30-g37540b8-37540b8-37"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"


# export PYTHONPATH=\
# $PYTHONPATH:/Users/Macbook/Documents/fgAPIServer_codestyle_changes/tests/..
# from fgapiserver import fgapiserver
queries = [
    {'query': 'SELECT VERSION()',
     'result': [['test', ], ]},
    {'query': 'select max(version) from db_patches;',
     'result': [['0.0.6'], ]},
    {'query': ('select  id\n'
               ',status\n'
               ',date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               ',date_format(last_change, \'%%Y-%%m-%%dT%%TZ\') last_change\n'
               ',app_id\n'
               ',description\n'
               ',status\n'
               ',user\n'
               ',iosandbox\n'
               'from task where id=%s;'),
     'result': [['1',
                 'DONE',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00',
                 '1',
                 'test task',
                 'DONE',
                 'test user',
                 '/tmp/test']], },
    {'query': ('select argument\n'
               'from task_arguments\n'
               'where task_id=%s\n'
               'order by arg_id asc;'),
     'result': [['argument'], ]},
    {'query': ('select file\n'
               '      ,if(path is null or length(path)=0,'
               '          \'NEEDED\','
               '          \'READY\') status\n'
               'from task_input_file\n'
               'where task_id=%s\n'
               'order by file_id asc;'),
     'result': [['input_file_1', 'NEEDED'], ['input_file_2', 'READY'], ]},
    {'query': ('select file\n'
               '      ,if(path is NULL,\'\',path)\n'
               'from task_output_file\n'
               'where task_id=%s\n'
               'order by file_id asc;'),
     'result': [['output_file_1', '/tmp'], ['output_file_2', '/tmp'], ]},
    {'query': ('select '
               '  data_name\n'
               ' ,data_value\n'
               ' ,data_desc\n'
               ' ,data_type\n'
               ' ,data_proto\n'
               ' ,date_format(creation,'
               '              \'%%Y-%%m-%%dT%%TZ\') creation\n'
               ' ,date_format(last_change,'
               '              \'%%Y-%%m-%%dT%%TZ\') last_change\n'
               'from runtime_data\n'
               'where task_id=%s\n'
               'order by data_id asc;'),
     'result': [['userdata_name_1',
                 'userdata_value_1',
                 'userdata_desc_1',
                 'NULL',
                 'NULL',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'],
                ['userdata_name_2',
                 'userdata_value_2',
                 'userdata_desc_2',
                 'NULL',
                 'NULL',
                 '1970-01-01T00:00:00',
                 '1970-01-01T00:00:00'],
                ]},
    {'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,outcome\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,enabled\n'
               'from application\n'
               'where id=%s;'),
     'result': [['1',
                 'test application',
                 'test application description',
                 'JOB',
                 '1970-01-01T00:00:00',
                 '1'],
                ]},
    {'query': ('select pname\n'
               '      ,pvalue\n'
               'from application_parameter\n'
               'where app_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_param_1', 'test_param_value_1'],
                ['test_param_2', 'test_param_value_2'], ]},
    {'query': ('select id\n'
               '      ,name\n'
               '      ,description\n'
               '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
               '      ,if(enabled,\'enabled\',\'disabled\') status\n'
               '      ,if(vinfra,\'virtual\',\'real\') status\n'
               'from infrastructure\n'
               'where app_id=%s;'),
     'result': [['1',
                 'test infra',
                 'test infrastructure for test application',
                 '1970-01-01T00:00:00',
                 'enabled',
                 'real'], ]},
    {'query': ('select pname, pvalue\n'
               'from infrastructure_parameter\n'
               'where infra_id=%s\n'
               'order by param_id asc;'),
     'result': [['test_infra_param_name_1', 'test_infra_param_value_1'],
                ['test_infra_param_name_2', 'test_infra_param_value_2'], ]},
    {'query': ('select task_id '
               'from task_output_file '
               'where file=%s and path=%s;'),
     'result': ['1']},
    {'query': ('select if((creation+expiry)-now()>0,user_id,NULL) user_id\n'
               '      ,(select name from fg_user where id=user_id) name\n'
               'from fg_token\n'
               'where token=%s;'),
     'result': [['1', 'test_user'], ]},
]


class cursor:

    position = 0
    cursor_results = None

    def __getitem__(self, i):
        return self.cursor_results[i]

    def __len__(self):
        return len(self.cursor_results)

    def execute(self, sql, sql_data=None):
        print "Executing: %s" % sql
        self.position = 0
        self.cursor_results = None
        for query in queries:
            if query['query'] == sql:
                self.cursor_results = query['result']
                print "Test query found!"
                print "result: '%s'" % self.cursor_results
        if self.cursor_results is None:
            print "Test query not found!"

    def fetchone(self):
        if self.cursor_results is None:
            return ''
        else:
            res = self.cursor_results[self.position]
            self.position += 1
            print "fetchone: %s" % res
            return res

    def close(self):
        print "cursor close"
        return None


class MySQLError(Exception):
    pass


class Error:
    pass


def connect(*args, **kwargs):
    db = MySQLdb()
    return db


class MySQLdb:

    Error = None

    def __init__(self, *args, **kwargs):
        Error = MySQLError()

    def cursor(self):
        cr = cursor()
        return cr

    def close(self):
        print "MySQLdb.close"
        return None

    def commit(self):
        print "MySQLdb.commit"
        return None
