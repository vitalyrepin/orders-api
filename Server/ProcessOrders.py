#!/usr/bin/env python

import sys
sys.path.append('../gen-py')

from orders import PrintAndDelivery
from orders.ttypes import *

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

def encodeOrderTimePair(obj):
   return {"_type": "OrderTimePair", "tm" : obj.tm, "status": obj.status}

def decodeOrderTimePair(doc):
   assert doc["_type"] == "OrderTimePair"
   return OrderTimePair(doc["tm"], doc["status"])

def encodeOrderMiscDetails(obj):
   return {"_type": "OrderMiscDetails", "doc_id" : obj.doc_id, "comment": obj.comment}

def decodeOrderMiscDetails(doc):
   assert doc["_type"] == "OrderMiscDetails"
   return OrderMiscDetails(doc["doc_id"], doc["comment"])

def encodeFetchedProductData(obj):
   prod = obj.get_product_data()
   return {"_type": "ProductDataF", "code" : prod.product_code, "qty": prod.qty, "url" : prod.url, "gridfid" : obj.gridfs_id}

def decodeFetchedProductData(doc):
   assert doc["_type"] == "ProductDataF"
   return ProductData(doc["code"], doc["qty"], doc["url"])

def encodePerson(obj):
   return  {"_type": "Person", "name" : obj.Name, "Surname": obj.Surname, "Middle" : obj.MiddleName, "Title" : obj.Title}

def encodeAddress(obj):
   return {"_type": "Address", "To" : encodePerson(obj.To), "City": obj.City, "State" : obj.State, "Line1": obj.AddressLine1, "Line2": obj.AddressLine2, "ZIP": obj.ZIP, "cc": obj.cc }

def encodeShipmentData(obj):
   return {"_type": "ShipmentData", "addr" : encodeAddress(obj.address), "mode": obj.delivery_mode, "pkg" : obj.packaging_mode}

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
    return self.users.find_one({}, {})['_id']

  def getAuthToken(self, username, pswd):
    print 'username: "' + username + '"'
    if (username == 'tstAuthError'):
        raise AccessDenied('Not valid user/password combination')

    return '1234'

  def getOrderDetails(self, authToken, orderId):
    print 'orderId: "' + orderId + '"'

    if(authToken == 'wrongAuthToken'):
        raise AccessDenied('Access denied or invalid auth token')
    if(authToken == 'wrongSomething'):
        raise GeneralError('-1', 'Something went wrong. Mongo is down? Try again later...')

    try:
      order = self.orders.find_one({ '_id': ObjectId(orderId), 'issuer': self.getUserId(authToken) }, { 'status' : 1, '_id' : 0 })
      if order is None:
        raise PrintOrderError(PrintOrderErrCode.INVALID_ID, 'No such order: ' + orderId)
    except bson.errors.InvalidId as err:
        raise PrintOrderError(PrintOrderErrCode.INVALID_ID, 'Invalid order id format: ' + orderId)
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
        raise PrintOrderError(PrintOrderErrCode.INVALID_ADDRESS, 'We do not deliver mail to Afganistan, sorry')
    if(authToken == 'wrongURL'):
        raise PrintOrderError(PrintOrderErrCode.INVALID_PRINT_URL, 'Can not download file from URL: ' + products[0].url)
    if(authToken == 'wrongSomething'):
        raise GeneralError('-1', 'Something went wrong. Mongo is down? Try again later...')

    # TBD: Checking address - can we deliver to it?

    # fetching URL
    fetched_products = []
    for product in products:
        if product.url:
            r = requests.get(product.url, stream=True)
            if(r.status_code != 200):
                raise PrintOrderError(PrintOrderErrCode.INVALID_PRINT_URL, 'HTTP status ' + str(r.status_code) + ': can not download file from URL: ' + products[0].url)
            mime_type = mimetypes.guess_type(product.url)[0]
            fname = urlparse(product.url).path
            try:
              fetched_products.append(FetchedProduct(product, self.grid_fs.put(r.raw, contentType=mime_type, filename=fname)))
            except PyMongoError as err:
              raise GeneralError('-1', 'Something wrong: ' + str(err))
        else:
            fetched_products.append(FetchedProduct(product, None))

    pr = OrderTimePair(int(time.time()), PrintOrderStatus.RECEIVED)

    order = { "shipment" : shipment,
              "products" : fetched_products,
              "misc"     : misc,
              "issuer"   :  self.getUserId(authToken),
              "status"   : [ pr ]
             }
    print order

    try:
      self.orders.insert(order)
    except PyMongoError as err:
      raise GeneralError('-1', 'Something wrong: ' + str(err))

    return str(order['_id'])


handler = PrintAndDeliveryHandler()
processor = PrintAndDelivery.Processor(handler)
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
