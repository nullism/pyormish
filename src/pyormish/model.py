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

    def _create(self):
        pass

    def _delete(self):
        pass

    def _commit(self):
        pass

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


    def create(self, **kwargs):
        """Create a new object in the database, and return that object"""

        c_fs = []; v_fs = []
        for k in kwargs.keys():
            c_fs.append('`%s`'%(k))
            v_fs.append('%%(%s)s'%(k))
            if getattr(self, '_set_%s'%(k), None):
                getattr(self, '_set_%s'%(k), None)(kwargs[k])
                kwargs[k] = getattr(self, '_get_%s'%(k))()
        sql = 'INSERT INTO `%s` (%s) VALUES (%s)'%(
            self._TABLE_NAME, ','.join(c_fs), ','.join(v_fs))            

        if not self.db.execute(sql, kwargs):
            return None
        _id = self.db._cursor.lastrowid
        obj = self.get_many([_id])[0]
        obj._create()
        return obj

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
        self._commit()
        return True

    def delete(self):
        if not self._DELETE_SQL:
            raise StandardError("_DELETE_SQL is not defined")
        for sql in self._DELETE_SQL:
            self.db.execute(sql, self.__dict__)
        self._delete()
        del(self)
            
    def make(self):
        return None

    def get_by_fields(self, **kwargs):
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

    def get_many(self, ids, order_fields=None):
        if not self._GET_MANY_SQL:
            raise StandardError("_GET_MANY_SQL is not defined")
        ids = [str(int(i)) for i in ids]
        sql = self._GET_MANY_SQL % ','.join(ids)
          
        olist = []
        dl = self.db.select(sql)
        if not dl:
            return []
        return self._build_objects(dl)
            
    def get_many_by_query(self, sql, **kwargs):
        """ Like get_many, but allows a generic query """
        dl = self.db.select(sql, kwargs)
        return self._build_objects(dl)

    def get_many_by_fields(self, **kwargs):
        wheres = []
        for k in kwargs.keys():
            wheres.append('`%s`.`%s`=%%(%s)s'%(self._TABLE_NAME, k, k))
        return self.get_many_by_where(' AND '.join(wheres), **kwargs)
 
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
            return []
        return self.get_many(ids, kwargs.get('order_fields',None))


