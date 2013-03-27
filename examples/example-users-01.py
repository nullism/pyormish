#!/usr/bin/python
import sys
sys.path.insert(0, '../')
from pyormish import Model, session

class User(Model):
    """
    Our `users` table looks like this: 
    +----------+--------------+------+-----+---------+----------------+
    | Field    | Type         | Null | Key | Default | Extra          |
    +----------+--------------+------+-----+---------+----------------+
    | id       | int(11)      | NO   | PRI | NULL    | auto_increment |
    | username | varchar(125) | NO   | UNI | NULL    |                |
    | password | varchar(255) | NO   |     | NULL    |                |
    | fullname | varchar(255) | NO   |     | NULL    |                |
    +----------+--------------+------+-----+---------+----------------+
    """
    _TABLE_NAME = 'users' # The name of the table
    _PRIMARY_FIELD = 'id' # The primary id field, auto_incrmenting in our case
    _SELECT_FIELDS = ['id','username','fullname','password'] # Only select these fields
    _COMMIT_FIELDS = ['username','fullname','password'] # Only save these fields
    

if __name__ == "__main__":   
    Model.session = session.MySQL('localhost','pyormish','uXHvNqv3WccM4S5E', 'pyormish')    

    try:
        # Create a new user
        user = User().create(username='FNG', fullname='The new guy', password='foofoo')
    except:
        # Load the user
        user = User().get_by_field(username='FNG')

    # Easily access properties
    print user.id, user.username, user.fullname

    # Reassign properties
    user.username = 'Foo'
    user.fullname = 'Fooanne Bar' 
    user.commit() # Saves the user object
    # UPDATE users SET username='Foo', fullname='Fooanne Bar' WHERE id=1

    print user.id, user.username, user.fullname # Prints `1, Foo, Fooanne Bar`

    # Delete rows
    user.delete() 
    # DELETE FROM users WHERE id=1

    # Get all remaining users
    all_users = User().get_many_by_where('1')
    # SELECT id, username, fullname, password FROM users WHERE 1

    for user in all_users:
        print user.id, user.username, user.fullname

