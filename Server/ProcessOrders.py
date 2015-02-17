#!/usr/bin/env python

import sys
sys.path.append('../gen-py')

import bcrypt
import platform
import string
import hashlib, time, base64

from Orders import OrderManager
from Orders.ttypes import *

import gridfs
import bson

from urlparse import urlparse

from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.son_manipulator import SONManipulator
from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.server import THttpServer

import time
import requests
import mimetypes
import socket

# Validity time of authentication token. In seconds
AUTH_TOK_VALIDITY_TIME = 30

def encodeOrderTimePair(obj):
   return {"_type": "OrderTimePair", "tm" : obj.tm, "status": obj.status}

def decodeOrderTimePair(doc):
   assert doc["_type"] == "OrderTimePair"
   return OrderTimePair(doc["tm"], doc["status"])

def encodeOrderMiscDetails(obj):
   return {"_type": "OrderMiscDetails", "docId" : obj.docId, "comment": obj.comment}

def decodeOrderMiscDetails(doc):
   assert doc["_type"] == "OrderMiscDetails"
   return OrderMiscDetails(doc["docId"], doc["comment"])

def encodeFetchedProductData(obj):
   prod = obj.get_product_data()
   return {"_type": "ProductDataF", "code" : prod.productCode, "qty": prod.qty, "url" : prod.url, "gridfid" : obj.gridfs_id}

def decodeFetchedProductData(doc):
   assert doc["_type"] == "ProductDataF"
   return ProductData(doc["code"], doc["qty"], doc["url"])

def encodePerson(obj):
   return  {"_type": "Person", "name" : obj.name, "Surname": obj.surname, "Middle" : obj.middleName, "Title" : obj.title}

def encodeAddress(obj):
   return {"_type": "Address", "To" : encodePerson(obj.to), "City": obj.city, "State" : obj.state, "Line1": obj.addressLine1, "Line2": obj.addressLine2, "ZIP": obj.zip, "cc": obj.cc }

def encodeShipmentData(obj):
   return {"_type": "ShipmentData", "addr" : encodeAddress(obj.address), "mode": obj.deliveryMode, "pkg" : obj.packagingMode}

# TBD!!!!
def decodeShipmentData(doc):
   assert doc["_type"] == "ShipmentData"
   return ProductData(doc["code"], doc["qty"], doc["url"])

class FetchedProduct:
    gridfs_id = None
    def __init__(self, product_data, gridfs_id):
      self.product_data = product_data
      self.gridfs_id = gridfs_id
    def get_product_data(self):
      return self.product_data
    def __repr__(self):
      return self.__str__()
    def __str__(self):
      return str(self.product_data) + ', gridfs_id: ' + str(self.gridfs_id)

class Transform(SONManipulator):
  def transform_value(self, v):
    if isinstance(v, OrderTimePair):
      v = encodeOrderTimePair(v)
    elif isinstance(v, OrderMiscDetails):
      v = encodeOrderMiscDetails(v)
    elif isinstance(v, FetchedProduct):
      v = encodeFetchedProductData(v)
    elif isinstance(v, ShipmentData):
      v = encodeShipmentData(v)
    return v

  def transform_incoming(self, son, collection):
    for (key, value) in son.items():
      if isinstance(value, dict): # Make sure we recurse into sub-docs
        son[key] = self.transform_incoming(value, collection)
      elif isinstance(value, list):
         r = []
         for item in value:
            r.append(self.transform_value(item))
            son[key] = r
      else:
        son[key] = self.transform_value(value)

    return son

  # TBD: lists of custom types will not work
  def transform_outgoing(self, son, collection):
    for (key, value) in son.items():
      if isinstance(value, dict):
        if "_type" in value and value["_type"] == "OrderTimePair":
          son[key] = decodeOrderTimePair(value)
        else: # Again, make sure to recurse into sub-docs
          son[key] = self.transform_outgoing(value, collection)
    return son

def makeSessionId(st):
    m = hashlib.md5()
    m.update(str(time.time()))
    m.update(str(st))
    return string.replace(base64.encodestring(m.digest())[:-3], '/', '$')

class PrintAndDeliveryHandler:
  def __init__(self):
    self.log = {}
    self.mongo_conn = MongoClient('localhost', 27017)
    self.db = self.mongo_conn.orders
    self.db.add_son_manipulator(Transform())
    self.users = self.db.users
    self.orders = self.db.orders
    self.grid_fs = gridfs.GridFS(self.db, 'printfiles')

  def ping(self):
    print 'ping()'

  def getUserId(self, authToken):
    # Searhing user id record by token
    # TBD: find_one: theoretically there can be more records because of the collisions with hash
    user = self.users.find_one({'token.tok' : authToken}, {'_id' : 1, 'token' : 1})
    if user is None:
      raise AccessDenied('Invalid authentication token')

    if not(self.checkIsAuthTokValid(user['token']['tm'])):
      print "Auth token is expired"
      raise AccessDenied('Authentication token is expired')

    return user['_id']

  def checkIsAuthTokValid(self, toktm):
     tm =time.time()
     return (tm - toktm < AUTH_TOK_VALIDITY_TIME)

  def mkNewAuthToken(self, userId):
    token = {}
    token['tok'] = makeSessionId(platform.node())
    token['tm'] = time.time()
    self.users.update({'_id' : userId}, { '$set' : {'token' : token} })
    return token['tok']

  def getAuthToken(self, username, pswd):
    print 'username: "' + username + '"'

    tokAuth = ''
    try:
      user = self.users.find_one({'name' : username})
      if user is None:
        raise AccessDenied('Invalid username or password')
      if bcrypt.hashpw(pswd.encode('utf-8'), user['pswd'].encode('utf-8')) != user['pswd'].encode('utf-8'):
        raise AccessDenied('Invalid username or password')
      else:
        # If token exists in the users collection, return it. Otherwise generate, write to the database and return
        if 'token' in user:
           tokAuth = user['token']['tok']
           tm = time.time()
           if(not(self.checkIsAuthTokValid(user['token']['tm']))):
             print "Regenerating Auth token for the user '" + username + "'"
             tokAuth = self.mkNewAuthToken(user['_id'])
        else:
           print "Generating new Auth token for the user '" + username + "'"
           tokAuth = self.mkNewAuthToken(user['_id'])
    except PyMongoError as err:
        raise GeneralError('-1', 'Something wrong: ' + str(err))

    return tokAuth

  def getOrderDetails(self, authToken, orderId):
    print 'orderId: "' + orderId + '"'

    if(authToken == 'wrongAuthToken'):
        raise AccessDenied('Access denied or invalid auth token')
    if(authToken == 'wrongSomething'):
        raise GeneralError('-1', 'Something went wrong. Mongo is down? Try again later...')

    try:
      order = self.orders.find_one({ '_id': ObjectId(orderId), 'issuer': self.getUserId(authToken) }, { 'status' : 1, '_id' : 0 })
      if order is None:
        raise OrderError(OrderErrCode.INVALID_ID, 'No such order: ' + orderId)
    except bson.errors.InvalidId as err:
        raise OrderError(OrderErrCode.INVALID_ID, 'Invalid order id format: ' + orderId)
    except PyMongoError as err:
        raise GeneralError('-1', 'Something wrong: ' + str(err))

    res = []
    for i in order['status']:
        res.append(OrderTimePair(int(i['tm']), i['status']))

    return res

  def newOrder(self, authToken, shipment, products, misc):
    if(authToken == 'wrongAuthToken'):
        raise AccessDenied('Access denied or invalid auth token')
    if(authToken == 'wrongAddress'):
        raise OrderError(OrderErrCode.INVALID_ADDRESS, 'We do not deliver mail to Afganistan, sorry')
    if(authToken == 'wrongSomething'):
        raise GeneralError('-1', 'Something went wrong. Mongo is down? Try again later...')

    issuer = self.getUserId(authToken)

    # TBD: Checking address - can we deliver to it?

    # fetching URL
    fetched_products = []
    for product in products:
        if product.url:
            r = requests.get(product.url, stream=True)
            if(r.status_code != 200):
                raise OrderError(OrderErrCode.INVALID_PRINT_URL, 'HTTP status ' + str(r.status_code) + ': can not download file from URL: ' + products[0].url)
            mime_type = mimetypes.guess_type(product.url)[0]
            fname = urlparse(product.url).path
            try:
              fetched_products.append(FetchedProduct(product, self.grid_fs.put(r.raw, contentType=mime_type, filename=fname)))
            except PyMongoError as err:
              raise GeneralError('-1', 'Something wrong: ' + str(err))
        else:
            fetched_products.append(FetchedProduct(product, None))

    pr = OrderTimePair(int(time.time()), OrderStatus.RECEIVED)

    order = { "shipment" : shipment,
              "products" : fetched_products,
              "misc"     : misc,
              "issuer"   : issuer,
              "status"   : [ pr ]
             }
    print order

    try:
      self.orders.insert(order)
    except PyMongoError as err:
      raise GeneralError('-1', 'Something wrong: ' + str(err))

    return str(order['_id'])


handler = PrintAndDeliveryHandler()
processor = OrderManager.Processor(handler)
#transport = TSSLSocket.TSSLServerSocket('localhost', 30303)
# We listen to localhost only!!! SSL service is a public one. Provided with the help of stunnel
transport = TSocket.TServerSocket('localhost', 30303)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
 
#httpServer = THttpServer.THttpServer(processor, ('localhost', 30303), tfactory, pfactory)

print "Starting python server..."
server.serve()
print "done!"
