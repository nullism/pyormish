import logging

class Model(object):
    """ The generic model object for interacting with SQL databases """
    _GET_MANY_SQL = None
    _GET_ID_SQL = None
    _COMMIT_SQL = None
    _CREATE_SQL = None
    _DELETE_SQL = None
    _GET_LIMIT = 50
    _SELECT_FIELDS = []
    _COMMIT_FIELDS = []
    _TABLE_NAME = None
    _PRIMARY_FIELD = None
    _SELECT_GROUP = ''
    _JOINS = None
    _ORDER_FIELDS = None
      
    session = None
    db = None
    d = None

    def __init__(self, _id=None):
        if not self.session:
            raise StandardError("No database connection specified")
        self.db = self.session
        self.make_sql()
        if(_id):
            olist = self.get_many([_id])
            if not olist:
                return None     
            self.d = olist[0].d
            self.__dict__.update(olist[0].d)
            self.make()
    
    def _build_objects(self, dl):
        """Internal method for updating object properties"""
        olist = []
        for i in range(len(dl)):
            sobj = self.__class__()
            sobj.__class__ = self.__class__
            for k,v in dl[i].items():
                if getattr(sobj, '_get_%s'%(k), None):
                    setattr(sobj.__class__, k, 
                        property(getattr(sobj.__class__, '_get_%s'%(k)),
                            getattr(sobj.__class__, '_set_%s'%(k), None))
                    )
                    dl[i]['_'+k] = v
            
            sobj.d = dl[i]
            sobj.__dict__.update(dl[i])
            sobj.make_sql()
            sobj.make()         
            olist.append(sobj)
        return olist

    def make_sql(self):
        
        p_f_sql = '`%s`.`'%(self._TABLE_NAME)+self._PRIMARY_FIELD+'`'
        f_sql = ['`%s`.`'%(self._TABLE_NAME)+f+'`' for f in self._SELECT_FIELDS]
        wheres = 'WHERE `%s`.`%s` IN (%%s)'%(self._TABLE_NAME, self._PRIMARY_FIELD)
        joins = ''
        group_by = self._SELECT_GROUP
        order_by = ''

        if self._JOINS:
            for j in self._JOINS:
                if j.get('fields'):
                    f_sql += j['fields']
                if j.get('where'):
                    wheres += ' %s'%(j['where'])
                if j.get('group_by'):
                    group_by += ' %s'%(j['group_by'])
                joins += ' %s JOIN `%s` ON %s'%(j['type'],j['table'],j['on'])
    
        if group_by:
            group_by = 'GROUP BY %s'%(group_by)

        o_fs = []
        if self._ORDER_FIELDS:
            for o in self._ORDER_FIELDS:
                o_fs.append('`%s`.`%s` %s'%(self._TABLE_NAME, o[0], o[1]))
            order_by = 'ORDER BY %s'%(','.join(o_fs))
                
        self._GET_MANY_SQL = 'SELECT %s FROM `%s` %s %s %s %s'%(
            ','.join(f_sql), self._TABLE_NAME, joins, wheres, group_by, order_by)
        
        self._GET_ID_SQL = 'SELECT `%s`.`%s` FROM `%s` WHERE '%(
            self._TABLE_NAME, self._PRIMARY_FIELD, self._TABLE_NAME)

        u_fs = []
        for f in self._COMMIT_FIELDS:
            u_fs.append('`%s`=%%(%s)s'%(f,f))
        self._COMMIT_SQL = ['UPDATE `%s` SET %s WHERE `%s`=%%(%s)s'%(
            self._TABLE_NAME, ','.join(u_fs), 
            self._PRIMARY_FIELD, self._PRIMARY_FIELD)]

        self._DELETE_SQL = ['DELETE FROM `%s` WHERE `%s`=%%(%s)s'%(
            self._TABLE_NAME, self._PRIMARY_FIELD, self._PRIMARY_FIELD)]

        c_fs = []
        v_fs = []
        for f in self._COMMIT_FIELDS:
            c_fs.append('`%s`'%(f))
            v_fs.append('%%(%s)s'%(f))
        self._CREATE_SQL = ['INSERT INTO `%s` (%s) VALUES (%s)'%(
            self._TABLE_NAME, ','.join(c_fs), ','.join(v_fs))]

    def create(self, **kwargs):
        """Create a new object in the database, and return that object"""
        if not self._CREATE_SQL:
            msg = "_CREATE_SQL is not defined"
            logging.error(msg)
            raise StandardError(msg)
        for sql in self._CREATE_SQL:
            for k in kwargs.keys():
                if getattr(self, '_set_%s'%(k), None):
                    getattr(self, '_set_%s'%(k), None)(kwargs[k])
                    kwargs[k] = getattr(self, '_get_%s'%(k))()
            if not self.db.execute(sql, kwargs):
                return None
        _id = self.db._cursor.lastrowid
        return self.get_many([_id])[0]

    def commit(self):
        """Execute _COMMIT_SQL using self.* properties"""
        if not self._COMMIT_SQL:
            raise StandardError("_COMMIT_SQL is not defined")
        for sql in self._COMMIT_SQL:
            for k in self.__dict__.keys():
                if getattr(self, '_set_%s'%(k), None):
                    self.__dict__[k] = self.__dict__['_'+k]
            if not self.db.execute(sql, self.__dict__):
                sql = sql % self.__dict__
                raise StandardError("Unable to commit ```%s```"%(sql))
        return True

    def delete(self):
        if not self._DELETE_SQL:
            raise StandardError("_DELETE_SQL is not defined")
        for sql in self._DELETE_SQL:
            self.db.execute(sql, self.__dict__)
        del(self)
            
    def make(self):
        return None

    def get_by_field(self, **kwargs):
        if not self._GET_ID_SQL:
            raise StandardError("_GET_ID_SQL is not defined")
        if not kwargs:
            return None
        wheres = []
        for k,v in kwargs.items():
            wheres.append("`%s`=%%(%s)s"%(k, k))

        sql = self._GET_ID_SQL + " %s"%(" AND ".join(wheres))
        rows = self.db.select(sql, kwargs)
        if not rows:
            return None
        key, _id = rows[0].popitem()
        return self.get_many([_id])[0]

    def get_by_where(self, where, **kwargs):
        if not self._GET_ID_SQL:
            raise StandardError("_GET_ID_SQL is not defined")
        if "WHERE" not in self._GET_ID_SQL.upper()+where.upper():
            where = "WHERE " + where
        sql = self._GET_ID_SQL + " " + where
        rows = self.db.select(sql, kwargs)
        if not rows:
            return None
        key, _id = rows[0].popitem()
        return self.get_many([_id])[0]

    def get_many(self, ids, _start=0, _limit=_GET_LIMIT):
        if not self._GET_MANY_SQL:
            raise StandardError("_GET_MANY_SQL is not defined")
        ids = [str(int(i)) for i in ids]
        sql = self._GET_MANY_SQL % ','.join(ids) \
            + " LIMIT %s,%s"%(int(_start), int(_limit))
        olist = []
        dl = self.db.select(sql)
        if not dl:
            return None
        return self._build_objects(dl)
            
    def get_many_by_query(self, sql, **kwargs):
        """ Like get_many, but allows a generic query """
        dl = self.db.select(sql, kwargs)
        return self._build_objects(dl)
 
    def get_many_by_where(self, where, **kwargs):
        if not self._GET_ID_SQL:
            msg = "_GET_ID_SQL is not defined"
            logging.error(msg)
            raise StandardError(msg)
        if "WHERE" not in self._GET_ID_SQL.upper()+where.upper():
            where = "WHERE " + where
        sql = self._GET_ID_SQL + " " + where
        sql = sql + " LIMIT %s,%s"%(int(kwargs.get('_start',0)), 
            int(kwargs.get('_limit',self._GET_LIMIT)))
        rows = self.db.select(sql, kwargs)
        ids = [r.popitem()[1] for r in rows]
        if not ids:
            return None
        return self.get_many(ids)


# -----------------------------------------------------------------------------
# Database specific modules below
# -----------------------------------------------------------------------------

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

