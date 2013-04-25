#!/usr/bin/python
from pyormish import Model, session
import hashlib


class Message(Model):

    _TABLE_NAME = 'messages'
    _PRIMARY_FIELD = 'id'
    _SELECT_FIELDS = ['id','to_user_id','from_user_id','body','is_read']
    _COMMIT_FIELDS = ['is_read']

    def __repr__(self):
        return '<Message(%s)>'%(self.id)


class User(Model):

    _TABLE_NAME = 'users' # The name of the table
    _PRIMARY_FIELD = 'id' # The primary id field, auto_incrmenting in our case
    _SELECT_FIELDS = ['id','username','fullname','password'] # Only select these fields
    _COMMIT_FIELDS = ['username','fullname','password'] # Only save these fields
    _JOINS = [
        { 'type':'LEFT', 'table':'messages', 'on':'messages.from_user_id=users.id',
          'fields':['COUNT(messages.id) as sent_message_count'],
          'group_by':'users.id' }
    ]
    

    def __repr__(self):
        return '<User(%s) - %s>'%(self.id, self.username)

    def _get_password(self): 
        """ Automagically called when user.password is accessed """
        return self._password

    def _set_password(self, value):
        """ Automagically called when user.password is changed """
        self._password = hashlib.sha1(value).hexdigest()

    def send_message(self, to_uid, body):
        m = Message().create(from_user_id=self.id, to_user_id=to_uid, body=body)
        self.sent_message_count += 1
        return m

    def _delete(self):
        """ Automagically called when a .delete() is called """
        sql = "DELETE FROM messages WHERE to_user_id=%(uid)s OR from_user_id=%(uid)s"
        self.connection.execute(sql, {'uid':self.id})
    

if __name__ == "__main__":   

    Model.db_config = dict(DB_TYPE='sqlite', DB_PATH=':memory:')

    # Create the users table for this example
    Model().connection.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY ASC, 
            username VARCHAR(255), 
            fullname VARCHAR(255),
            password VARCHAR(256)
        )    
    ''')

    # Create the messages table for this example
    Model().connection.execute('''
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY ASC,
            to_user_id INTEGER,
            from_user_id INTEGER,
            body MEDIUMTEXT,
            is_read INTEGER DEFAULT 0
        )        
    ''')

    # Let's create some users 
    User().create(username='hpotter', fullname='Mr. Potter', password='V0ld3m0rtSuCk5')
    User().create(username='ronald', fullname='Weasle McGee', password='d3rp')
    User().create(username='hermy', fullname='Ms. Punctuality', password='Gr4ng3rD4ng3r')

    # Let's select those users with a where clause
    users = User().get_many_by_where('users.id > 0', order_fields=[['username','DESC']])
    for u in users:
        u.send_message(1, 'Hello from %s'%(u.fullname))
        print(u.id, u.username, u.fullname, u.sent_message_count)
        


