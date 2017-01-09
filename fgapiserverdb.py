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

import MySQLdb
import uuid
import os
import random
import urllib
import shutil
import logging
import json

"""
  GridEngine API Server database
"""
__author__ = "Riccardo Bruno"
__copyright__ = "2015"
__license__ = "Apache"
__version__ = "v0.0.1-15-g1527c76-1527c76-22"
__maintainer__ = "Riccardo Bruno"
__email__ = "riccardo.bruno@ct.infn.it"

"""
 Database connection default settings
"""
def_db_host = 'localhost'
def_db_port = 3306
def_db_user = 'fgapiserver'
def_db_pass = 'fgapiserver_password'
def_db_name = 'fgapiserver'

"""
 Task sandboxing will be placed here Sandbox directories
 will be generated as UUID names generated during task creation
"""
def_iosandbbox_dir = '/tmp'
def_geapiserverappid = '10000'  # GridEngine sees API server as an application

"""
  fgapiserver_db Class contain any call interacting with fgapiserver database
"""


class FGAPIServerDB:

    """
     API Server Database connection settings
    """
    db_host = None
    db_port = None
    db_user = None
    db_pass = None
    db_name = None
    iosandbbox_dir = def_iosandbbox_dir
    geapiserverappid = def_geapiserverappid

    """
        Error Flag and messages filled up upon failures
    """
    err_flag = False
    err_msg = ''
    message = ''

    """
      FGAPIServerDB - Constructor may override default
                      values defined at the top of the file
    """

    def __init__(self, *args, **kwargs):
        self.db_host = kwargs.get('db_host', def_db_host)
        self.db_port = kwargs.get('db_port', def_db_port)
        self.db_user = kwargs.get('db_user', def_db_user)
        self.db_pass = kwargs.get('db_pass', def_db_pass)
        self.db_name = kwargs.get('db_name', def_db_name)
        self.iosandbbox_dir = kwargs.get('iosandbbox_dir', def_iosandbbox_dir)
        self.geapiserverappid = kwargs.get(
            'geapiserverappid', def_geapiserverappid)
        logging.debug(
            "[DB settings]\n"
            " host: '%s'\n"
            " port: '%s'\n"
            " user: '%s'\n"
            " pass: '%s'\n"
            " name: '%s'\n"
            " iosandbox_dir: '%s'\n"
            " geapiserverappid: '%s'\n" %
            (self.db_host,
             self.db_port,
             self.db_user,
             self.db_pass,
             self.db_name,
             self.iosandbbox_dir,
             self.geapiserverappid))

    """
      catchDBError - common operations performed upon database
                     query/transaction failure
    """

    def catch_db_error(self, e, db, rollback):
        logging.debug("[ERROR] %d: %s" % (e.args[0], e.args[1]))
        # print "[ERROR] %d: %s" % (e.args[0], e.args[1])
        if rollback is True:
            db.rollback()
        self.err_flag = True
        self.err_msg = "[ERROR] %d: %s" % (e.args[0], e.args[1])

    """
      close_db - common operatoins performed closing DB query/transaction
    """

    def close_db(self, db, cursor, commit):
        if cursor is not None:
            cursor.close()
        if db is not None:
            if commit is True:
                db.commit()
            db.close()

    """
      connect Connects to the fgapiserver database
    """

    def connect(self):
        return MySQLdb.connect(
            host=self.db_host,
            user=self.db_user,
            passwd=self.db_pass,
            db=self.db_name,
            port=self.db_port)

    """
     test - DB connection tester function
    """

    def test(self):
        db = None
        cursor = None
        try:
            db = self.connect()
            # prepare a cursor object using cursor() method
            cursor = db.cursor()
            # execute SQL query using execute() method.
            cursor.execute("SELECT VERSION()")
            # Fetch a single row using fetchone() method.
            data = cursor.fetchone()
            self.err_flag = False
            self.err_msg = 'Database version : %s' % data[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)

    """
      get_db_version - Return the database version
    """

    def get_db_version(self):
        db = None
        cursor = None
        dbver = ''
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select max(version) from db_patches;')
            sql_data = ()
            cursor.execute(sql, sql_data)
            dbver = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return dbver

    """
      get_state returns the status and message of the last action on the DB
    """

    def get_state(self):
        return (self.err_flag, self.err_msg)

    """
      create_session_token - Starting from the given triple
                            (username,password,timestamp) produce a
                            valid access token
    """

    def create_session_token(self, username, password, logts):
        # logtimestamp is currently ignored; old timestamps should not be
        # considered
        db = None
        cursor = None
        sestoken = ''
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select if(count(*)>0,uuid(),NULL) acctoken \n'
                   'from fg_user \n'
                   'where name=%s and fg_user.password=password(%s);')
            sql_data = (username, password)
            cursor.execute(sql, sql_data)
            sestoken = cursor.fetchone()[0]
            if sestoken is not None:
                sql = ('insert into fg_token \n'
                       '  select %s, id, now() creation, 24*60*60 \n'
                       '  from  fg_user \n'
                       '  where name=%s \n'
                       '    and fg_user.password=password(%s);')
                sql_data = (sestoken, username, password)
                cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return sestoken

    """
      verify_session_token - Check if the passed token is valid and return
                           the user id and its name
    """

    def verify_session_token(self, sestoken):
        db = None
        cursor = None
        user_id = ''
        user_name = ''
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = (
                'select if((creation+expiry)-now()>0,user_id,NULL) user_id\n'
                '      ,(select name from fg_user where id=user_id) name\n'
                'from fg_token\n'
                'where token=%s;')
            sql_data = (sestoken,)
            cursor.execute(sql, sql_data)
            user_rec = cursor.fetchone()
            if user_rec is not None:
                user_id = user_rec[0]
                user_name = user_rec[1]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return user_id, user_name

    """
      register_token - Register the incoming and valid token into the token
                       table. This is used by PTV which bypass APIServer
                       session tokens. The record will be written only once
    """
    def register_token(self, userid, token, subject):
        db = None
        cursor = None
        sestoken = ''
        try:
            db = self.connect()
            cursor = db.cursor()
            if token is not None:
                sql = ('insert into \n'
                       'fg_token (token, subject, user_id, creation, expiry)\n'
                       'select %s, %s, %s, now(), NULL\n'
                       'from dual\n'
                       'where (select count(*)\n'
                       '       from fg_token\n'
                       '       where token=%s) = 0;')
                sql_data = (token, subject, userid, token)
                cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return

    """
      verify_user_role - Verify if the given user has the given role
    """

    def verify_user_role(self, user_id, role_name):
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select count(*)>0      \n'
                   'from fg_user        u  \n'
                   '    ,fg_group       g  \n'
                   '    ,fg_user_group ug  \n'
                   '    ,fg_group_role gr  \n'
                   '    ,fg_role        r  \n'
                   'where u.id=%s          \n'
                   '  and u.id=ug.user_id  \n'
                   '  and g.id=ug.group_id \n'
                   '  and g.id=gr.group_id \n'
                   '  and r.id=gr.role_id  \n'
                   '  and r.name = %s;')
            sql_data = (user_id, role_name)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return result

    """
      verify_user_app - Verify if the given user has the given app in its roles
    """

    def verifyUserApp(self, user_id, app_id):
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select count(*)>0      \n'
                   'from fg_user        u  \n'
                   '    ,fg_group       g  \n'
                   '    ,application    a  \n'
                   '    ,fg_user_group ug  \n'
                   '    ,fg_group_apps ga  \n'
                   'where u.id=%s          \n'
                   '  and u.id=ug.user_id  \n'
                   '  and a.id=%s          \n'
                   '  and a.id=ga.app_id   \n'
                   '  and g.id=ug.group_id \n'
                   '  and g.id=ga.group_id;')
            sql_data = (user_id, app_id)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return result

    """
      same_group - Return True if given users belong to the same group
    """

    def same_group(self, user_1, user_2):
        db = None
        cursor = None
        result = ''
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select count(*)>1               \n'
                   'from fg_user_group              \n'
                   'where user_id = (select id      \n'
                   '                 from fg_user   \n'
                   '                 where name=%s) \n'
                   '   or user_id = (select id      \n'
                   '                 from fg_user   \n'
                   '                 where name=%s) \n'
                   'group by group_id               \n'
                   'having count(*) > 1;')
            sql_data = (user_1, user_2)
            cursor.execute(sql, sql_data)
            record = cursor.fetchone()
            if record is not None:
                result = record[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return result

    """
      get_user_info_by_name - Return full user info from the given username
    """

    def get_user_info_by_name(self, name):
        db = None
        cursor = None
        user_info = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select id        \n'
                   '      ,name      \n'
                   '      ,password  \n'
                   '      ,first_name\n'
                   '      ,last_name \n'
                   '      ,institute \n'
                   '      ,mail      \n'
                   '      ,creation  \n'
                   '      ,modified  \n'
                   'from fg_user     \n'
                   'where name=%s;')
            sql_data = (name,)
            cursor.execute(sql, sql_data)
            record = cursor.fetchone()
            if record is not None:
                user_info = {
                    "id": record[0],
                    "name": record[1],
                    "password": record[2],
                    "first_name": record[3],
                    "last_name": record[4],
                    "institute": record[5],
                    "mail": record[6],
                    "creation": record[7],
                    "modified": record[8]}
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return user_info

    """
      task_exists - Return True if the given task_id exists False otherwise
    """

    def task_exists(self, task_id):
        db = None
        cursor = None
        count = 0
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from task\n'
                   'where id = %s;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return count > 0

    """
       get_task_record - Retrieve the whole task information
    """

    def get_task_record(self, task_id):
        db = None
        cursor = None
        task_record = {}
        try:
            db = self.connect()
            cursor = db.cursor()
            # Task record
            sql = (
                'select '
                ' id\n'
                ',status\n'
                ',date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
                ',date_format(last_change, \'%%Y-%%m-%%dT%%TZ\') last_change\n'
                ',app_id\n'
                ',description\n'
                ',status\n'
                ',user\n'
                ',iosandbox\n'
                'from task\n'
                'where id=%s\n'
                '  and status != "PURGED";')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            task_dbrec = cursor.fetchone()
            if task_dbrec is not None:
                task_dicrec = {
                    "id": str(
                        task_dbrec[0]),
                    "status": task_dbrec[1],
                    "creation": str(
                        task_dbrec[2]),
                    "last_change": str(
                        task_dbrec[3]),
                    "application": task_dbrec[4],
                    "description": task_dbrec[5],
                    "status": task_dbrec[6],
                    "user": task_dbrec[7],
                    "iosandbox": task_dbrec[8]}
            else:
                return {}
            # Task arguments
            sql = ('select argument\n'
                   'from task_arguments\n'
                   'where task_id=%s\n'
                   'order by arg_id asc;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            task_args = []
            for arg in cursor:
                task_args += [arg[0], ]
            # Task input files
            sql = (
                'select file\n'
                '      ,if(path is null or length(path)=0,'
                '          \'NEEDED\','
                '          \'READY\') status\n'
                '      ,if(path is NULL,\'\',path)\n'
                'from task_input_file\n'
                'where task_id=%s\n'
                'order by file_id asc;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            task_ifiles = []
            for ifile in cursor:
                if ifile[1] == 'NEEDED':
                    ifile_entry = {
                        "name": ifile[0],
                        "status": ifile[1],
                    }
                else:
                    ifile_entry = {
                        "name": ifile[0],
                        "status": ifile[1],
                        "url": 'file?%s'
                        % urllib.urlencode({"path": ifile[2],
                                            "name": ifile[0]}),
                    }
                task_ifiles += [ifile_entry, ]
            # Task output files
            sql = ('select file\n'
                   '      ,if(path is NULL,\'\',path)\n'
                   'from task_output_file\n'
                   'where task_id=%s\n'
                   'order by file_id asc;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            task_ofiles = []
            for ofile in cursor:
                ofile_entry = {"name": ofile[0],
                               "url": 'file?%s'
                               % urllib.urlencode({"path": ofile[1],
                                                   "name": ofile[0]})}
                task_ofiles += [ofile_entry, ]
            # runtime_data
            sql = (
                'select '
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
                'order by data_id asc;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            runtime_data = []
            for rtdata in cursor:
                rtdata_entry = {
                    "name": rtdata[0],
                    "value": rtdata[1],
                    "description": rtdata[2],
                    "type": rtdata[3],
                    "proto": rtdata[4],
                    "creation": str(
                        rtdata[5]),
                    "last_change": str(
                        rtdata[6])}
                runtime_data += [rtdata_entry, ]
            # Prepare output
            task_record = {
                "id": str(
                    task_dicrec['id']),
                "status": task_dicrec['status'],
                "creation": str(
                    task_dicrec['creation']),
                "last_change": str(
                    task_dicrec['last_change']),
                "application": str(
                    task_dicrec['application']),
                "description": task_dicrec['description'],
                "user": task_dicrec['user'],
                "arguments": task_args,
                "input_files": task_ifiles,
                "output_files": task_ofiles,
                "runtime_data": runtime_data,
                "iosandbox": task_dicrec['iosandbox']}
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return task_record

    """
      get_task_status - Return the status of a given Task
    """

    def get_task_status(self, task_id):
        return self.get_task_record(task_id).get('status', None)

    """
      get_task_input_files - Return info about input files of a given Task
    """

    def get_task_input_files(self, task_id):
        db = None
        cursor = None
        task_ifiles = ()
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,if(path is null,\'NEEDED\',\'READY\') status\n'
                   'from task_input_file\n'
                   'where task_id = %s;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            for ifile in cursor:
                file_info = {
                    "name": ifile[0], "status": ifile[1]
                }
                task_ifiles += (file_info,)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return task_ifiles

    """
      get_task_output_files - Return info about output files of a given Task
    """

    def get_task_output_files(self, task_id):
        db = None
        cursor = None
        task_ifiles = ()
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,if(path is null,\'waiting\',\'ready\')\n'
                   'from task_output_file\n'
                   'where task_id = %s;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            for ifile in cursor:
                file_info = {
                    "name": ifile[0], "status": ifile[1]
                }
                task_ifiles += (file_info,)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return task_ifiles

    """
      get_app_detail - Return details about a given app_id
    """

    def get_app_detail(self, app_id):
        db = None
        cursor = None
        app_detail = {}
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = (
                'select id\n'
                '      ,name\n'
                '      ,description\n'
                '      ,outcome\n'
                '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
                '      ,enabled\n'
                'from application\n'
                'where id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            app_record = cursor.fetchone()
            app_detail = {
                "id": str(
                    app_record[0]),
                "name": app_record[1],
                "description": app_record[2],
                "outcome": app_record[3],
                "creation": str(
                    app_record[4]),
                "enabled": app_record[5]}
            # Add now app parameters
            sql = ('select pname\n'
                   '      ,pvalue\n'
                   'from application_parameter\n'
                   'where app_id=%s\n'
                   'order by param_id asc;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            app_parameters = []
            for param in cursor:
                parameter = {
                    "param_name": param[0], "param_value": param[1]
                }
                app_parameters += [parameter, ]
            app_detail['parameters'] = app_parameters
            # Get now application ifnrastructures with their params
            infrastructures = ()
            sql = (
                'select id\n'
                '      ,name\n'
                '      ,description\n'
                '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
                '      ,if(enabled,\'enabled\',\'disabled\') status\n'
                '      ,if(vinfra,\'virtual\',\'real\') status\n'
                'from infrastructure\n'
                'where app_id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            infrastructures = []
            for infra in cursor:
                infra_details = {
                    "id": str(
                        infra[0]),
                    "name": infra[1],
                    "description": infra[2],
                    "creation": str(
                        infra[3]),
                    "status": infra[4],
                    "virtual": infra[5]}
                infrastructures += [infra_details, ]
            # Now loop over infrastructures to get their parameters
            for infra in infrastructures:
                sql = ('select pname, pvalue\n'
                       'from infrastructure_parameter\n'
                       'where infra_id=%s\n'
                       'order by param_id asc;')
                sql_data = (str(infra['id']),)
                cursor.execute(sql, sql_data)
                infra_parameters = []
                for param in cursor:
                    param_details = {
                        "name": param[0], "value": param[1]
                    }
                    infra_parameters += [param_details, ]
                infra['parameters'] = infra_parameters
            app_detail['infrastructures'] = infrastructures
            return app_detail
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)

    """
      get_task_app_detail - Return application details of a given Task
    """

    def get_task_app_detail(self, task_id):
        task_record = self.get_task_record(task_id)
        return self.get_app_detail(str(task_record['application']))

    """
      get_task_info - Retrieve full information about given task_id
    """

    def get_task_info(self, task_id):
        task_record = self.get_task_record(task_id)
        task_record.get('id', None)
        if task_record.get('id', None) is None:
            self.err_flag = True
            self.err_msg = "[ERROR] Did not find task id: %s" % task_id
            return {}
        task_app_details = self.get_task_app_detail(task_id)
        task_info = task_record
        del task_info['application']
        task_info['application'] = task_app_details
        return task_info

    """
        get_app_files - Retrieve from application_files table the application
                        specific files associated to the given application
    """

    def get_app_files(self, app_id):
        db = None
        cursor = None
        app_files = []
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select file\n'
                   '      ,path\n'
                   '      ,override\n'
                   'from application_file\n'
                   'where app_id=%s\n'
                   'order by file_id asc;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            for app_file in cursor:
                app_files += [{"file": app_file[0],
                               "path": app_file[1], "override": app_file[2]}, ]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return app_files

    """
      init_task - initialize a task from a given application id
    """

    def init_task(
            self,
            app_id,
            description,
            user,
            arguments,
            input_files,
            output_files):
        # Get app defined files
        app_files = self.get_app_files(app_id)
        # Start creating task
        db = None
        cursor = None
        task_id = -1
        try:
            # Create the Task IO Sandbox
            iosandbox = '%s/%s' % (self.iosandbbox_dir, str(uuid.uuid1()))
            os.makedirs(iosandbox)
            # Insert new Task record
            db = self.connect()
            cursor = db.cursor()
            sql = ('insert into task (id\n'
                   '                 ,creation\n'
                   '                 ,last_change\n'
                   '                 ,app_id\n'
                   '                 ,description\n'
                   '                 ,status\n'
                   '                 ,user\n'
                   '                 ,iosandbox)\n'
                   'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
                   '      ,now()                           -- creation date\n'
                   '      ,now()                           -- last change\n'
                   '      ,%s                              -- app_id\n'
                   '      ,%s                              -- description\n'
                   '      ,\'WAITING\'                     -- status WAITING\n'
                   '      ,%s                              -- user\n'
                   '      ,%s                              -- iosandbox\n'
                   'from task;\n'
                   )
            sql_data = (app_id, description, user, iosandbox)
            cursor.execute(sql, sql_data)
            sql = 'select max(id) from task;'
            sql_data = ''
            cursor.execute(sql)
            task_id = cursor.fetchone()[0]
            # Insert Task arguments
            if arguments != []:
                for arg in arguments:
                    sql = (
                        'insert into task_arguments (task_id\n'
                        '                           ,arg_id\n'
                        '                           ,argument)\n'
                        'select %s\n'
                        '      ,if(max(arg_id) is NULL,1,max(arg_id)+1)\n'
                        '      ,%s\n'
                        'from task_arguments\n'
                        'where task_id=%s')
                    sql_data = (task_id, arg, task_id)
                    cursor.execute(sql, sql_data)
            # Insert Task input_files
            # Process input files specified in the REST URL (input_files)
            # producing a new vector called inp_file having the same structure
            # of app_files: [ { "name": <filname>
            #                  ,"path": <path to file> },...]
            # except for the 'override' key not necessary in this second array.
            # For each file specified inside input_file, verify if it exists
            # alredy in the app_file vector. If the file exists there are two
            # possibilities:
            # * app_file['override'] flag is true; then user inputs are
            #   ignored, thus the file will be skipped
            # * app_file['override'] flag is false; user input couldn't be
            #   ignored, thus the path to the file will be set to NULL waiting
            #   for user input
            inp_file = []
            for file in input_files:
                skip_file = False
                for app_file in app_files:
                    if file['name'] == app_file['file']:
                        skip_file = True
                        if app_file['override'] is True:
                            break
                        else:
                            app_file['path'] = None
                            break
                if not skip_file:
                    # The file is not in app_file
                    inp_file += [{"path": None, "file": file['name']}, ]
            # Files can be registered in task_input_files
            for inpfile in app_files + inp_file:
                # Not None paths having not empty content refers to an
                # existing app_file that could be copied into the iosandbox
                # task directory and path can be modifies with the iosandbox
                # path
                if inpfile['path'] is not None and len(inpfile['path']) > 0:
                    shutil.copy(
                        '%s/%s' %
                        (inpfile['path'], inpfile['file']), '%s/%s' %
                        (iosandbox, inpfile['file']))
                    inpfile['path'] = iosandbox
                sql = (
                    'insert into task_input_file (task_id\n'
                    '                            ,file_id\n'
                    '                            ,path\n'
                    '                            ,file)\n'
                    'select %s\n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
                    '      ,%s\n'
                    '      ,%s\n'
                    'from task_input_file\n'
                    'where task_id=%s')
                sql_data = (task_id, inpfile['path'], inpfile['file'], task_id)
                cursor.execute(sql, sql_data)
            # Insert Task output_files specified by application settings
            # (default)
            sql = ('select pvalue\n'
                   'from application_parameter\n'
                   'where app_id=%s\n'
                   ' and (   pname=\'jobdesc_output\'\n'
                   '      or pname=\'jobdesc_error\');')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            for out_file in cursor:
                output_files += [{"name": out_file[0]}, ]
            # Insert Task output_files specified by user
            for outfile in output_files:
                sql = (
                    'insert into task_output_file (task_id\n'
                    '                             ,file_id\n'
                    '                             ,file)\n'
                    'select %s\n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)\n'
                    '      ,%s\n'
                    'from task_output_file\n'
                    'where task_id=%s')
                sql_data = (task_id, outfile['name'], task_id)
                cursor.execute(sql, sql_data)
        except IOError as xxx_todo_changeme:
            (errno, strerror) = xxx_todo_changeme.args
            self.err_flag = True
            self.err_msg = "I/O error({0}): {1}".format(errno, strerror)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)

        # Accordingly to specs: input_files -
        # If omitted the task is immediately ready to start
        # If the inputsandbox is ready the job will be triggered for execution
        if self.is_input_sandbox_ready(task_id):
            # The input_sandbox is completed; trigger the Executor for this
            # task only if the completed sandbox consists of overridden files
            # or no files are specified in the application_file table for this
            # app_id
            if self.is_overridden_sandbox(app_id):
                self.submit_task(task_id)

        return task_id

    """
      get_task_io_sandbox - Get the assigned IO Sandbox folder of the
                            given task_id
    """

    def get_task_io_sandbox(self, task_id):
        db = None
        cursor = None
        iosandbox = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = 'select iosandbox from task where id=%s;'
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            result = cursor.fetchone()
            if result is None:
                self.err_flag = True
                self.err_msg = "[ERROR] Unable to find task id: %s" % task_id
            else:
                iosandbox = result[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return iosandbox

    """
      update_iniput_sandbox_file - Update input_sandbox_table with the fullpath
      of a given (task,filename)
    """

    def update_iniput_sandbox_file(self, task_id, filename, filepath):
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('update task_input_file\n'
                   'set path=%s\n'
                   'where task_id=%s\n'
                   '  and file=%s;')
            sql_data = (filepath, task_id, filename)
            cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return

    """
      is_input_sandbox_ready - Return true if all input_sandbox files have been
                               uploaded for a given (task_id)
                               True if all files have a file path registered
                               or the task does not contain any input file
    """

    def is_input_sandbox_ready(self, task_id):
        db = None
        cursor = None
        sandbox_ready = False
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = (
                'select '
                '  sum(if(path is NULL,0,1))=count(*) or count(*)=0 sb_ready\n'
                'from task_input_file\n'
                'where task_id=%s;')
            sql_data = (task_id,)
            cursor.execute(sql, sql_data)
            sandbox_ready = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return 1 == int(sandbox_ready)

    """
      submit_task - Trigger the GridEngine to submit the given task
                    This function takes care of all APIServerDaemon needs to
                    properly submit the applciation
    """

    def submit_task(self, task_id):
        # Get task information
        task_info = self.get_task_info(task_id)
        app_info = task_info['application']
        app_params = app_info['parameters']
        # Retrieve only enabled infrastructures
        app_infras = ()
        for infra in app_info['infrastructures']:
            if bool(infra['status']):
                app_infras += (infra,)
        if app_infras is None or len(app_infras) == 0:
            self.err_flag = True
            self.err_msg = ('No suitable infrastructure found for task_id: %s'
                            % task_id)
            return False
        # Proceed only if task comes form a WAITING state
        task_status = task_info.get('status', '')
        if task_status != 'WAITING':
            self.err_flag = True
            self.err_msg = ('Wrong status (\'%s\') '
                            'to ask submission for task_id: %s') % (
                task_status, task_id)
            return False
        # Application must be also enabled
        if not bool(app_info['enabled']):
            self.err_flag = True
            self.err_msg = ('Unable submit task_id: %s,'
                            ' because application is disabled') % task_id
            return False
        # Infrastructures must exist for this application
        enabled_infras = []
        for infra in app_infras:
            if infra['status'] == 'enabled':
                enabled_infras += [infra, ]
        if len(enabled_infras) == 0:
            self.err_flag = True
            self.err_msg = ('No suitable infrastructures found for task_id: %s'
                            % task_id)
            return False
        # All checks have been done, it is possible to enqueue the Task request
        return self.enqueue_task_request(task_info)

    """
      enqueue_task_request - Place a request into the queue
    """
    def enqueue_task_request(self, task_info):
        db = None
        cursor = None
        self.err_flag = False
        try:
            # Save native APIServer JSON file, having the format:
            # <task_iosandbox_dir>/<task_id>.json
            as_file = open('%s/%s.json' %
                           (task_info['iosandbox'], task_info['id']), "w")
            as_file.write(json.dumps(task_info))
            # Determine the application target executor (default GridEngine)
            target_executor = 'GridEngine'
            for app_param in task_info['application']['parameters']:
                if app_param['param_name'] == 'target_executor':
                    target_executor = app_param['param_value']
                    break
            try:
                # Insert task record in the APIServerDaemon' queue
                db = self.connect()
                cursor = db.cursor()
                sql = (
                    'insert into as_queue (\n'
                    '   task_id       \n'
                    '  ,target_id     \n'
                    '  ,target        \n'
                    '  ,action        \n'
                    '  ,status        \n'
                    '  ,target_status \n'
                    '  ,creation      \n'
                    '  ,last_change   \n'
                    '  ,check_ts      \n'
                    '  ,action_info   \n'
                    ') values (%s,'
                    '          NULL,'
                    '          %s,'
                    '          \'SUBMIT\','
                    '          \'QUEUED\','
                    '          NULL,'
                    '          now(),'
                    '          now(),'
                    '          now(),'
                    '          %s);')
                sql_data = (task_info['id'],
                            target_executor, task_info['iosandbox'])
                cursor.execute(sql, sql_data)
                sql = (
                    'update task set status=\'SUBMIT\', \n'
                    'last_change=now() where id=%s;')
                sql_data = (str(task_info['id']),)
                cursor.execute(sql, sql_data)
            except MySQLdb.Error as e:
                self.catch_db_error(e, db, True)
            finally:
                self.close_db(db, cursor, True)
                if as_file is not None:
                    as_file.close()
        except IOError as xxx_todo_changeme1:
            (errno, strerror) = xxx_todo_changeme1.args
            self.err_flag = True
            self.err_msg = "I/O error({0}): {1}".format(errno, strerror)
        finally:
            as_file.close()
        return not self.err_flag

    """
      get_task_list - Get the list of tasks associated to a user and/or app_id
    """

    def get_task_list(self, user, app_id):
        db = None
        cursor = None
        task_ids = []
        try:
            # Get Task ids preparing the right query (user/*,@
            # wildcards/app_id)
            db = self.connect()
            cursor = db.cursor()
            app_clause = ''
            sql_data = ()
            user_filter = user[0]
            if user_filter == '*':
                user_name = user[1:]
                user_clause = ''
            elif user_filter == '@':
                user_name = user[1:]
                user_clause = ('  and user in (select distinct(u.name)      \n'
                               '               from fg_user        u        \n'
                               '                  , fg_group       g        \n'
                               '                  , fg_user_group ug        \n'
                               '               where u.id=ug.user_id        \n'
                               '                 and g.id=ug.group_id       \n'
                               '                 and g.id in                \n'
                               '                   (select g.id             \n'
                               '                    from fg_user_group ug   \n'
                               '                        ,fg_user        u   \n'
                               '                        ,fg_group       g   \n'
                               '                     where ug.user_id=u.id  \n'
                               '                       and ug.group_id=g.id \n'
                               '                       and u.name=%s))')
                sql_data += (user_name,)
            else:
                user_name = user
                user_clause = '  and user = %s\n'
                sql_data += (user_name,)
            if app_id is not None:
                app_clause = '  and app_id = %s\n'
                sql_data += (app_id,)
            sql = ('select id\n'
                   'from task\n'
                   'where status != "PURGED"\n'
                   '%s%s;'
                   ) % (user_clause, app_clause)
            cursor.execute(sql, sql_data)
            for task_id in cursor:
                task_ids += [task_id[0], ]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return task_ids

    """
      delete - Delete a given task
    """

    def delete(self, task_id):
        db = None
        cursor = None
        status = False
        # Get task information
        task_info = self.get_task_info(task_id)
        try:
            # Insert task record in the GridEngine' queue
            db = self.connect()
            cursor = db.cursor()
            sql = (
                'insert into as_queue (\n'
                '   task_id\n'
                '  ,target_id\n'
                '  ,target\n'
                '  ,action\n'
                '  ,status\n'
                '  ,target_status\n'
                '  ,creation\n'
                '  ,last_change\n'
                '  ,check_ts\n'
                '  ,action_info\n'
                ') values (%s,\n'
                '          NULL,\n'
                '         \'GridEngine\',\n'
                '         \'CLEAN\',\n'
                '         \'QUEUED\',\n'
                '          NULL,\n'
                '          now(),\n'
                '          now(),\n'
                '          now(),\n'
                '          %s);')
            sql_data = (task_info['id'], task_info['iosandbox'])
            cursor.execute(sql, sql_data)
            sql = (
                'update task set status=\'CANCELLED\', '
                'last_change=now() where id=%s;')
            sql_data = (str(task_info['id']),)
            cursor.execute(sql, sql_data)
            status = True
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return status

    """
      patch_task - Patches a given task with provided runtime_data values
    """

    def patch_task(self, task_id, runtime_data):
        db = None
        cursor = None
        status = False
        try:
            db = self.connect()
            cursor = db.cursor()
            for rtdata in runtime_data:
                data_name = rtdata['data_name']
                data_value = rtdata['data_value']
                data_desc = rtdata.get('data_desc', '')
                data_type = rtdata.get('data_type', '')
                data_proto = rtdata.get('data_proto', '')
                # Determine if dataname exists for this task
                sql = ('select count(*)\n'
                       'from runtime_data\n'
                       'where data_name=%s\n'
                       '  and task_id=%s;')
                sql_data = (data_name, task_id)
                cursor.execute(sql, sql_data)
                result = cursor.fetchone()
                if result is None:
                    self.err_flag = True
                    self.err_msg = ("[ERROR] Unable to patch task id: %s"
                                    % task_id)
                else:
                    data_count = result[0]
                if data_count == 0:
                    # First data insertion
                    sql = (
                        'insert into runtime_data (task_id\n'
                        '                         ,data_id\n'
                        '                         ,data_name\n'
                        '                         ,data_value\n'
                        '                         ,data_desc\n'
                        '                         ,data_type\n'
                        '                         ,data_proto\n'
                        '                         ,creation\n'
                        '                         ,last_change)\n'
                        'select %s\n'
                        '      ,(select '
                        '          if(max(data_id) is NULL,1,max(data_id)+1)\n'
                        '        from runtime_data\n'
                        '        where task_id=%s)\n'
                        '      ,%s\n'
                        '      ,%s\n'
                        '      ,%s\n'
                        '      ,%s\n'
                        '      ,%s\n'
                        '      ,now()\n'
                        '      ,now();\n')
                    sql_data = (task_id, task_id,
                                data_name,
                                data_value,
                                data_desc,
                                data_type,
                                data_proto)
                    cursor.execute(sql, sql_data)
                    status = True
                else:
                    sql = ('update runtime_data\n'
                           'set data_value = %s\n'
                           '   ,last_change = now()\n'
                           'where data_name=%s\n'
                           '  and task_id=%s;')
                    sql_data = (data_value, data_name, task_id)
                    cursor.execute(sql, sql_data)
                    status = True
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return status

    """
    is_overridden_sandbox - True if all files of the specified application
                            have the override flag True
                            If no files are specified in application_file the
                            function returns True
    """

    def is_overridden_sandbox(self, app_id):
        db = None
        cursor = None
        no_override = False
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = (
                'select '
                '  if(sum(override) is NULL,'
                '     TRUE,'
                '     count(*)=sum(override)) override\n'
                'from application_file\n'
                'where app_id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            no_override = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return 1 == int(no_override)

    """
      get_file_task_id - Get the task id related to the given file and path
    """

    def get_file_task_id(self, file_name, file_path):
        db = None
        cursor = None
        task_id = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select task_id from task_output_file\n'
                   'where file=%s and path=%s\n'
                   'union all\n'
                   'select task_id from task_input_file\n'
                   'where file=%s and path=%s;')
            sql_data = (file_name, file_path, file_name, file_path)
            cursor.execute(sql, sql_data)
            task_id = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return task_id

    """
      status_change - Add a task status change command in as_queue
                      this causes the EIs to handle the change properly
    """

    def status_change(self, task_id, new_status):
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('insert into as_queue (task_id,'
                   '                      action,'
                   '                      status,'
                   '                      target,'
                   '                      target_status,'
                   '                      creation,'
                   '                      last_change,'
                   '                      check_ts)'
                   'values (%s,'
                   '        "STATUSCH",'
                   '        "QUEUED",'
                   '        (select target '
                   '         from as_queue '
                   '         where task_id=%s '
                   '         and action="SUBMIT"),'
                   '         %s,'
                   '         now(),'
                   '         now(),'
                   '         now());')
            sql_data = (task_id, task_id, new_status)
            cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return
#
# Application
#
    """
      app_exists - Return True if the given app_id exists False otherwise
    """

    def app_exists(self, app_id):
        db = None
        cursor = None
        count = 0
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = ('select count(*)\n'
                   'from application\n'
                   'where id = %s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            count = cursor.fetchone()[0]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return count > 0

    """
      get_app_list - Get the list of applications
    """

    def get_app_list(self):
        db = None
        cursor = None
        app_ids = []
        try:
            # Get Task ids preparing the right query (user/app_id)
            db = self.connect()
            cursor = db.cursor()
            sql_data = ()
            sql = ('select id\n'
                   'from application;')
            cursor.execute(sql)
            for app_id in cursor:
                app_ids += [app_id[0], ]
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, False)
        finally:
            self.close_db(db, cursor, False)
        return app_ids

    """
       get_app_record - Get application record
    """

    def get_app_record(self, app_id):
        db = None
        cursor = None
        app_record = {}
        try:
            db = self.connect()
            cursor = db.cursor()
            # Task record
            sql = (
                'select name\n'
                '      ,description\n'
                '      ,outcome\n'
                '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
                '      ,enabled\n'
                'from application\n'
                'where id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            app_dbrec = cursor.fetchone()
            if app_dbrec is not None:
                app_dicrec = {
                    "id": str(app_id),
                    "name": app_dbrec[0],
                    "description": app_dbrec[1],
                    "outcome": app_dbrec[2],
                    "creation": str(
                        app_dbrec[3]),
                    "enabled": app_dbrec[4]}
            else:
                return {}
            # Application parameters
            sql = ('select pname\n'
                   '      ,pvalue\n'
                   'from application_parameter\n'
                   'where app_id=%s\n'
                   'order by param_id asc;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            app_params = []
            for param in cursor:
                app_params += [{"name": param[0],
                                "value": param[1], "description": ""}, ]
            # Application input files
            sql = ('select file\n'
                   '      ,path\n'
                   '      ,override\n'
                   'from application_file\n'
                   'where app_id=%s\n'
                   'order by file_id asc;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            app_ifiles = []
            for ifile in cursor:
                ifile_entry = {
                    "name": ifile[0], "path": ifile[1], "override": ifile[2]
                }
                app_ifiles += [ifile_entry, ]
            # Application infrastructures
            sql = (
                'select id\n'
                '      ,name\n'
                '      ,description\n'
                '      ,date_format(creation, \'%%Y-%%m-%%dT%%TZ\') creation\n'
                '      ,enabled\n'
                'from infrastructure\n'
                'where app_id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            app_infras = []
            for app_infra in cursor:
                app_infra_entry = {"id": str(app_infra[0]),
                                   "name": app_infra[1],
                                   "description": app_infra[2],
                                   "creation": str(app_infra[3]),
                                   "enabled": app_infra[4],
                                   "vinfra": False}
                #                 ,"parameters"     : []}
                app_infras += [app_infra_entry, ]
            for app_infra in app_infras:
                sql = ('select pname\n'
                       '      ,pvalue\n'
                       'from infrastructure_parameter\n'
                       'where infra_id=%s\n'
                       'order by param_id asc;')
                sql_data = (app_infra['id'],)
                cursor.execute(sql, sql_data)
                infra_params = []
                for infra_param in cursor:
                    infra_params += [{
                        "name": infra_param[0], "value": infra_param[1]
                    }, ]
                app_infra["parameters"] = infra_params
            # Prepare output
            app_record = {
                "id": str(app_id),
                "name": app_dicrec['name'],
                "description": app_dicrec['description'],
                "outcome": app_dicrec['outcome'],
                "creation": str(
                    app_dicrec['creation']),
                "enabled": app_dicrec['enabled'],
                "parameters": app_params,
                "input_files": app_ifiles,
                "infrastructures": app_infras}
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return app_record

    """
      init_app - initialize an application
                 from the given parameters: name
                                           ,description
                                           ,enabled
                                           ,parameters
                                           ,inp_files
                                           ,infrastructures
    """

    def init_app(
            self,
            name,
            description,
            outcome,
            enabled,
            parameters,
            inp_files,
            infrastructures):
        # Start creating app
        db = None
        cursor = None
        app_id = -1
        try:
            # Insert new application record
            db = self.connect()
            cursor = db.cursor()
            sql = ('insert into application (id\n'
                   '                        ,name\n'
                   '                        ,description\n'
                   '                        ,outcome\n'
                   '                        ,creation\n'
                   '                        ,enabled)\n'
                   'select if(max(id) is NULL,1,max(id)+1) -- new id\n'
                   '      ,%s                              -- name\n'
                   '      ,%s                              -- description\n'
                   '      ,%s                              -- outcome\n'
                   '      ,now()                           -- creation\n'
                   '      ,%s                              -- enabled\n'
                   'from application;\n'
                   )
            sql_data = (name, description, outcome, enabled)
            cursor.execute(sql, sql_data)
            # Get inserted application_id
            sql = 'select max(id) from application;'
            sql_data = ''
            cursor.execute(sql)
            app_id = cursor.fetchone()[0]
            # Insert Application parameters
            if parameters != []:
                for param in parameters:
                    sql = (
                        'insert into application_parameter (app_id\n'
                        '                                  ,param_id\n'
                        '                                  ,pname\n'
                        '                                  ,pvalue)\n'
                        'select %s                                          \n'
                        '      ,if(max(param_id) is NULL,1,max(param_id)+1) \n'
                        '      ,%s                                          \n'
                        '      ,%s                                          \n'
                        'from application_parameter\n'
                        'where app_id=%s')
                    sql_data = (app_id, param['name'], param['value'], app_id)
                    cursor.execute(sql, sql_data)
            # Insert Application input_files
            for ifile in inp_files:
                sql = (
                    'insert into application_file (app_id\n'
                    '                            ,file_id\n'
                    '                            ,file\n'
                    '                            ,path\n'
                    '                            ,override)\n'
                    'select %s                                          \n'
                    '      ,if(max(file_id) is NULL,1,max(file_id)+1)   \n'
                    '      ,%s                                          \n'
                    '      ,%s                                          \n'
                    '      ,%s                                          \n'
                    'from application_file\n'
                    'where app_id=%s')
                sql_data = (app_id, ifile['name'], ifile[
                            'path'], ifile['override'], app_id)
                cursor.execute(sql, sql_data)
            # Insert Application infrastructures
            for infra in infrastructures:
                sql = ('insert into infrastructure (id\n'
                       '                           ,app_id\n'
                       '                           ,name\n'
                       '                           ,description\n'
                       '                           ,creation\n'
                       '                           ,enabled\n'
                       # '                           ,vinfra\n'
                       '                           )\n'
                       'select if(max(id) is NULL,1,max(id)+1) \n'
                       '      ,%s                              \n'
                       '      ,%s                              \n'
                       '      ,%s                              \n'
                       '      ,now()                           \n'
                       '      ,%s                              \n'
                       # '      ,%s                             \n'
                       'from infrastructure;'
                       )
                sql_data = (app_id, infra['name'],
                            infra['description'],
                            infra['enabled']
                            # ,infra['vinfra']
                            )
                cursor.execute(sql, sql_data)
                # Get inserted infrastructure_id
                sql = 'select max(id) from infrastructure;'
                sql_data = ''
                cursor.execute(sql)
                infra_id = cursor.fetchone()[0]
                # Insert Application infrastructure parameters
                for param in infra['parameters']:
                    sql = (
                        'insert into infrastructure_parameter (infra_id\n'
                        '                                     ,param_id\n'
                        '                                     ,pname\n'
                        '                                     ,pvalue)\n'
                        'select %s                                          \n'
                        '      ,if(max(param_id) is NULL,1,max(param_id)+1) \n'
                        '      ,%s                                          \n'
                        '      ,%s                                          \n'
                        'from infrastructure_parameter\n'
                        'where infra_id = %s;')
                    sql_data = (infra_id, param['name'], param[
                                'value'], infra_id)
                    cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
            app_id = 0
        finally:
            self.close_db(db, cursor, True)
        return app_id

    """
      app_delete - delete application with a given id
    """

    def app_delete(self, app_id):
        # Start deleting app
        db = None
        cursor = None
        try:
            # Delete given application records
            db = self.connect()
            cursor = db.cursor()
            #
            # (!) Pay attention infrastructures belonging to
            #     different applications may share the same
            #    id (infra_id in parameters); a check is
            #    necessary here ...
            #
            sql = (
                'delete from infrastructure_parameter\n'
                'where infra_id in (select id \n'
                '                   from infrastructure \n'
                '                   where app_id=%s);')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            sql = ('delete from infrastructure where app_id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            sql = ('delete from application_file where app_id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            sql = ('delete from application_parameter where app_id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
            sql = ('delete from application where id=%s;')
            sql_data = (app_id,)
            cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return app_id

    """
      enable_app_by_userid - enable all groups owned by the given userid to
                             execute the specified application id
    """

    def enable_app_by_userid(self, user_id, app_id):
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            # Task record
            sql = ("select group_id from fg_user_group where user_id = %s")
            sql_data = (user_id,)
            cursor.execute(sql, sql_data)
            for group_id in cursor:
                sql = ("insert into fg_group_apps (group_id,app_id, creation)"
                       " values (%s,%s,now())")
                sql_data = (group_id, app_id)
                cursor.execute(sql, sql_data)
        except MySQLdb.Error as e:
            self.catch_db_error(e, db, True)
        finally:
            self.close_db(db, cursor, True)
        return None
