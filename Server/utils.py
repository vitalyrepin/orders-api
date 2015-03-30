#!/usr/bin/env python


import sys
import bcrypt

from pymongo.errors import PyMongoError
from pymongo import MongoClient


mongo_conn = MongoClient('localhost', 27017)
db = mongo_conn.DevOrders
users = db.users

def create_user(name, pswd):
   print "Creating user: " + name
   if(check_user(name)):
	print "User '" + name + "' already exists in the database"
   else:

       user = { "name" : name,
                "pswd" : hash_pass(pswd),
                "subscriptions": []
              }
       users.insert(user)
       print "User '" + name + "' added to the database"

def check_user(name):
    user = users.find_one({'name' : name}, {})
    return (user != None)

def hash_pass(password):
    hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
    return hash_password

create_user('cert-orders@example.com', 'qwerty')

