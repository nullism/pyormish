#!/usr/bin/python
import sys
sys.path.insert(0, '../')
from pyormish import Model, session
import hashlib

class Message(Model):

    """
    Our `messages` table looks like this
    +--------------+-------------+------+-----+---------+----------------+
    | Field        | Type        | Null | Key | Default | Extra          |
    +--------------+-------------+------+-----+---------+----------------+
    | id           | int(11)     | NO   | PRI | NULL    | auto_increment |
    | to_user_id   | varchar(45) | YES  |     | NULL    |                |
    | from_user_id | varchar(45) | YES  |     | NULL    |                |
    | body         | text        | YES  |     | NULL    |                |
    | is_read      | tinyint(1)  | NO   |     | 0       |                |
    +--------------+-------------+------+-----+---------+----------------+
    """

    _TABLE_NAME = 'messages'
    _PRIMARY_FIELD = 'id'
    _SELECT_FIELDS = ['id','to_user_id','from_user_id','body','is_read']
    _COMMIT_FIELDS = ['is_read']

    def __repr__(self):
        return '<Message(%s)>'%(self.id)


class User(Model):
    """
    Our `users` table looks like this: 
    +----------+--------------+------+-----+---------+----------------+
    | Field    | Type         | Null | Key | Default | Extra          |
    +----------+--------------+------+-----+---------+----------------+
    | id       | int(11)      | NO   | PRI | NULL    | auto_increment |
    | username | varchar(125) | NO   | UNI | NULL    |                |
    | password | varchar(256) | NO   |     | NULL    |                |
    | fullname | varchar(255) | NO   |     | NULL    |                |
    +----------+--------------+------+-----+---------+----------------+
    """
    _TABLE_NAME = 'users' # The name of the table
    _PRIMARY_FIELD = 'id' # The primary id field, auto_incrmenting in our case
    _SELECT_FIELDS = ['id','username','fullname','password'] # Only select these fields
    _COMMIT_FIELDS = ['username','fullname','password'] # Only save these fields
    """ Join example allowing user.message_count in one query
    _JOINS = [
        { 'type':'LEFT', 'table':'messages', 'on':'messages.user_id=user.id',
          'fields':['COUNT(messages.id) as message_count'],
          'group_by':'GROUP BY user.id' }
    ]
    """

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
        return m

    def _delete(self):
        """ Automagically called when a .delete() is called """
        sql = "DELETE FROM messages WHERE to_user_id=%(uid)s OR from_user_id=%(uid)s"
        self.db.execute(sql, {'uid':self.id})
    

if __name__ == "__main__":   
    Model.session = session.MySQL('localhost','pyormish','uXHvNqv3WccM4S5E', 'pyormish')    

    # Let's create some users
    user_list = [
        {'username':'bill', 'fullname':'Billy Ray', 'password':'SoMuchFOO!'},
        {'username':'sally', 'fullname':'Sally Joe', 'password':'SoMuchFOO!'},
        {'username':'jethro', 'fullname':'Jethro Williams', 'password':'SoMuchFOO!'},
    ]
    for user_d in user_list:
        user = User().create(**user_d)
    
        print user.id, user.username, user.fullname
        user.send_message(1, "BOOOYAH!")
        user.delete()
        
