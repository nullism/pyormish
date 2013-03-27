#!/usr/bin/python
from pyormish import Model, session
import hashlib
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class User(Model):

    _PRIMARY_FIELD = 'id'
    _TABLE_NAME = 'users'
    _SELECT_FIELDS = ('id','username','fullname','password')
    _JOINS = [{'type':'LEFT', 'table':'messages', 
        'fields':['COUNT(messages.id) AS unread_message_count'],
        'on':'messages.to_user_id=users.id AND messages.is_read=0',
        'group_by':'`users`.`id`',
        'where':'AND `users`.`id`>0'}]
    _COMMIT_FIELDS = ('username','fullname','password')
    _ORDER_FIELDS = (('username','DESC'),)

    _emails = []
    _friends = []
    _unread_messages = []
    
    def __repr__(self):
        return "<User(%s) - %s>"%(self.id, self.username)

    def _get_password(self):
        return self._password

    def _set_password(self,value):
        self._password = self.hash_password(value)

    def _get_username(self):
        return self._username

    def _set_username(self, value):
        ucheck = User().get_by_field(username=value)
        if ucheck:
            raise Exception('Username already in use')
        self._username = value

    @property
    def unread_messages(self):
        if self._unread_messages:
            return self._unread_messages
        sql = """
            SELECT id FROM messages 
            WHERE to_user_id=%(uid)s
            AND is_read=0
        """
        rows = self.db.select(sql, {'uid':self.id})
        if not rows:
            return []
        ids = [r['id'] for r in rows]
        self._unread_messages = Message().get_many(ids)
        return self._unread_messages 

    @property
    def friends(self):
        if self._friends:
            return self._friends
        sql = """
            SELECT u.id  FROM users u
            JOIN friends f ON (f.to_user_id=u.id OR f.from_user_id=u.id)
            WHERE (f.from_user_id=%(uid)s OR f.to_user_id=%(uid)s)
            AND u.id <> %(uid)s
        """
        rows = self.db.select(sql, {'uid':self.id})
        if not rows:
            self._friends = []
            return []
        ids = [r['id'] for r in rows]
        self._friends = User().get_many(ids)
        return self._friends       

    @property
    def emails(self):
        if self._emails:
            return self._emails
        sql = """
            SELECT id FROM emails 
            WHERE user_id=%(uid)s 
            ORDER BY is_primary DESC
        """
        rows = self.db.select(sql, {'uid':self.id})
        if not rows:
            return []
        ids = [r['id'] for r in rows]
        self._emails = Email().get_many(ids)
        return self._emails       

    def hash_password(self, password):
        return hashlib.sha1(password).hexdigest() 
 
    def add_email(self, email, is_primary=False):
        self._emails.append(Email().create(
            email=email, user_id=self.id, is_primary=is_primary))

    def set_primary_email(self, email):
        sql = "UPDATE emails SET is_primary=0 WHERE user_id=%(uid)s"
        res = self.db.execute(sql, {'uid':self.id})
        for e in self.emails:
            if e.email == email:
                e.is_primary = True
                e.commit()
        self._emails = None  
                
    def delete_email(self, email):
        for e in self._emails:
            if e.email == email:
                e.delete()
                self._emails.remove(e)        


class Message(Model):
    
    _PRIMARY_FIELD = 'id'
    _TABLE_NAME = 'messages'
    _SELECT_FIELDS = ['id','to_user_id','from_user_id','text','date','is_read']
    _COMMIT_FIELDS = ['is_read']

    _to_user = None
    _from_user = None

    def __repr__(self):
        return '<Message(%s) - %s>'%(self.id, self.date)
    
    @property
    def to_user(self):
        if self._to_user:
            return self._to_user
        self._to_user = User(self.to_user_id)
        return self._to_user

    @property
    def from_user(self):
        if self._from_user:
            return self._from_user
        self._from_user = User(self.from_user_id)
        return self._from_user

                    
class Email(Model):

    _PRIMARY_FIELD = 'id'
    _TABLE_NAME = 'emails'
    _SELECT_FIELDS = ['id','email','user_id','is_primary']
    _COMMIT_FIELDS = ['email','is_primary']

    def __repr__(self):
        return '<Email(%s) - %s>'%(self.id, self.email)
        

def main():
  
    Model.session = session.MySQL('localhost','pyormish','uXHvNqv3WccM4S5E', 'pyormish')

    session_user = User(1)
    ulist = User().get_many_by_where('id > 0')

    for user in ulist:
        print("="*30+"[ %s ]"%(user.username)+"="*30)
        if str(session_user) in str(user.friends):
            print("%s is friends with %s"%(user.fullname, session_user.fullname))
        user.password = user.hash_password('foobittles')
        print("User ID:\t%s"%(user.id))
        print("Full Name:\t%s"%(user.fullname))
        print("Password Hash:\t%s"%(user.password))
        if user.unread_message_count > 0:
            print("\tUser has %s unread messages!"%(len(user.unread_messages)))
            for msg in user.unread_messages:
                print("\t"+"-"*30)
                print("\tID: %s"%(msg.id))
                print("\tFrom: %s"%(msg.from_user.username))
                print("\tText:")
                for line in msg.text.split('\n'):
                    print("\t%s"%(line))
        if user.emails:
            print("Emails:")
            for email in user.emails:
                #email.is_primary = True
                email.commit()
                print("\tEmail:\t%s [%s]"%(email.email, email.is_primary))
        if user.friends:
            print("Friends:")
            for friend in user.friends:
                print("\tFriend:\t%s (%s)"%(friend.fullname, friend.username))
            

    #u2 = User().get_by_where("username=%(username)s",username='administrator')
    u2 = User().get_by_field(username='administrator')
    print("u2.fullname = %s"%(u2.fullname))
    print u2.friends

    print("="*60)
    print("Creating a new user...")
    u3 = User().create(username="Markus", fullname="Sir Markus III", password=User().hash_password('monkeys'))
    print("id = %s"%(u3.id))
    print("username = %s"%(u3.username))
    print("Deleting that user...")
    u3.delete()

    

    #u2 = User().create(username="MissFooanne", fullname="Mrs. Fooanne Bar")     
    #print u2.username
    #print u2.fullname 

if __name__ == "__main__":
    main()
    
