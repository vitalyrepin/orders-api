#!/usr/bin/env python

import sys, getopt
sys.path.append('../gen-py/')

import time
import json
import bcrypt
import platform
import string
import hashlib, time, base64

from Metida import OrderManager
from Metida.ttypes import *

import gridfs
import bson

from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.son_manipulator import SONManipulator

import time
import requests
import mimetypes
import socket

import logging
import logging.handlers

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
   return {"_type": "ProductDataF", "code" : prod.productCode, "qty": prod.qty, "url" : prod.url, "md5" : prod.md5, "gridfid" : obj.gridfs_id}

def decodeFetchedProductData(doc):
   assert doc["_type"] == "ProductDataF"
   return ProductData(doc["code"], doc["qty"], doc["url"], doc["md5"])

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


# Main
# Default values for database name and listening port number
dbname = 'DevOrders'

# Parsing cmdline
try:
    opts, args = getopt.getopt(sys.argv[1:],"hd:p:",["dbname="])
except getopt.GetoptError:
      print sys.argv[0] + ' -d <dbname>'
      sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print sys.argv[0] + ' -d <dbname>'
        sys.exit()
    elif opt in ("-d", "--dbname"):
        dbname = arg

logging.basicConfig(format='%(asctime)s %(message)s', filename='cbk-test-' + dbname +'.log', level=logging.DEBUG)

log = {}
mongo_conn = MongoClient('localhost', 27017)
db = mongo_conn[dbname]
db.add_son_manipulator(Transform())
users = db.users
orders = db.orders

logging.info("Starting cbk_test with database '%s'", dbname)

def call_cbks():
    # Check the users with callback_url field
    cursor = db.users.find({'callback_url' : {'$exists': 1}}, {'_id' : 1, 'callback_url' : 1})
    for u in cursor:
        order = orders.find_one({'issuer' : u['_id']}, {'_id' : 1})
        if '_id' in order:
            cbk = u['callback_url']
            order_id = order['_id']
            logging.info("Calling POST '%s?id=%s,%s,%s'", cbk, order_id, order_id, order_id)
            payload = {'ORDER': [str(order_id), str(order_id), str(order_id)]}
            logging.info("Calling POST '%s?id=%s'", cbk, order_id)
            r = requests.post(cbk, data = json.dumps(payload))
            logging.info("Result: %s", r.text)

            payload = {'ORDER': [str(order_id)]}
            r = requests.post(cbk, data = json.dumps(payload))
            logging.info("Result: %s", r.text)

while True:
    call_cbks()
    time.sleep(30)
