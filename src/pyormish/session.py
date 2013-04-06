"""
Copyright 2012 Aaron Meier

Licensed under the Apache License, Version 2.0 (the "License"); 
you may not use this file except in compliance with the License. 
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, 
software distributed under the License is distributed on an "AS IS" BASIS, 
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
See the License for the specific language governing permissions and 
limitations under the License.
"""
import logging

class GenericSQL(object):

    def _row2dict(self,data):

        if data == None:
            return None
        desc = self._cursor.description
        row = {}
        for (name, value) in zip(desc, data):
            if isinstance(value, basestring):
                value = value.decode('utf-8')
            row[name[0]] = value
        return row

    def bind_fix(self, sql, binds):
        return sql

    def select(self, sql, binds=None):
        try:
            if binds:
                sql = self.bind_fix(sql, binds)
                self._cursor.execute(sql, binds)
            else:
                self._cursor.execute(sql)
            rows = self._cursor.fetchall()

        except(Exception),e:
            sql = sql + " : %s"%(binds) if binds else sql
            msg = "Unable to select ```%s```, error: %s"%(sql, e) 
            logging.error(msg)
            raise StandardError(msg)
        
        if not rows:
            return []

        logging.debug("SELECT: %s"%(sql))

        dl = []
        for row in rows:
            dl.append(self._row2dict(row))
        return dl

    def execute(self, sql, binds=None):
        try:
            if binds:
                sql = self.bind_fix(sql, binds)
                res = self._cursor.execute(sql,binds)
            else:
                res = self._cursor.execute(sql)
            self.conn.commit()
            logging.debug("EXECUTE: %s"%(sql))
            return True
        except(Exception),e: 
            sql = sql + " : %s"%(binds) if binds else sql
            msg = "Unable to execute ```%s```, error: %s"%(sql, e)
            logging.error(msg)
            raise StandardError(msg)


class MySQL(GenericSQL):

    def __init__(self, host, user, passwd, db):
        import MySQLdb
        self.conn = MySQLdb.connect(host, user, passwd, db)
        self._cursor = self.conn.cursor()

class Postgres(GenericSQL):
    
    def __init__(self, conn_string):
        import psycopg2
        self.conn = psycopg2.connect(conn_string)
        self._cursor = self.conn.cursor()     

class SQLite(GenericSQL):   

    def __init__(self, path):
        import sqlite3
        self.conn = sqlite3.connect(path)
        self._cursor = self.conn.cursor()
    
    def bind_fix(self, sql, binds):
        for k in binds.keys():
            if k not in sql:
                continue
            sql = sql.replace('%%(%s)s'%(k),':%s'%(k))
        return sql         

