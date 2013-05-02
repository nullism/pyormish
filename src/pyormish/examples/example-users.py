#!/usr/bin/python
from pyormish import Model
import hashlib


class User(Model):

    _TABLE_NAME = 'users' # The name of the table
    _PRIMARY_FIELD = 'id' # The primary id field, auto_incrmenting in our case
    _SELECT_FIELDS = ('id','username','fullname','password') # Only select these fields
    _COMMIT_FIELDS = ('username','fullname','password') # Only save these fields
    

    def __repr__(self):
        return '<User(%s) - %s>'%(self.id, self.username)

    def _get_password(self): 
        """ Automagically called when user.password is accessed """
        return self._password

    def _set_password(self, value):
        """ Automagically called when user.password is changed """
        self._password = hashlib.sha1(value).hexdigest()

if __name__ == "__main__":   

    Model.set_db_config(DB_PATH=':memory:',DB_TYPE='sqlite')

    # Create the users table for this example
    Model().connection.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY ASC, 
            username VARCHAR(255) UNIQUE, 
            fullname VARCHAR(255),
            password VARCHAR(256)
        )    
    ''')
   

    # Let's create some users 
    User().create(username='hpotter', fullname='Mr. Potter', password='V0ld3m0rtSuCk5')
    User().create(username='ronald', fullname='Weasle McGee', password='d3rp')
    User().create(username='hermy', fullname='Ms. Punctuality', password='Gr4ng3rD4ng3r')

    # Let's select those users with a where clause
    users = User().get_many_by_where('users.id > 0', order_fields=[['username','DESC']])
    for u in users:
        print(u.id, u.username, u.fullname, u.password)
        
