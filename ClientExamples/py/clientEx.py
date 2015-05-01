#!/usr/bin/env python

'''
  Copyright 2015 Metida Print Ab Oy
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing,
  software distributed under the License is distributed on an
  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
  KIND, either express or implied. See the License for the
  specific language governing permissions and limitations
  under the License.
'''

import sys
sys.path.append('../../gen-py')
import time

from Metida import OrderManager
from Metida.ttypes import *
from Metida.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol


try:
  # Make socket
#  transport = TSSLSocket.TSSLSocket('dev.metidaprint.com', 443, True, 'cacert.pem')

#  transport = TSSLSocket.TSSLSocket('orders.metidaprint.com', 443, True, 'cacert.pem')

  transport = TSocket.TSocket('localhost', 30303)

  # Buffering is critical. Raw sockets are very slow
  transport = TTransport.TBufferedTransport(transport)

  # Wrap in a protocol
  protocol = TBinaryProtocol.TBinaryProtocol(transport)

  # Create a client to use the protocol encoder
  client = OrderManager.Client(protocol)

  # Connect!
  transport.open()

   # Get auth token
  authToken = client.getAuthToken("test@metidaprint.com", "MetisZeus1450BC")
  print 'authToken = ' + authToken

  # Ping
  client.ping(authToken)
  print "ping()"

  # Testing error case: no such user
  try:
    authToken = client.getAuthToken("NoUser", "")
    print 'authToken = ' + authToken
  except AccessDenied as err:
    print '[OK] Error: ' + err._message

  '''
  *********************************** get and set Profile Parameters ***********************************
  '''

  # Testing error case: Access denied
  try:
    client.setProfileParam('wrongAuthToken', ProfileParam.CBK_URL, '')
  except AccessDenied as err:
    print '[OK] Error: ' + err._message

  try:
    r = client.getProfileParam('wrongAuthToken', ProfileParam.CBK_URL)
  except AccessDenied as err:
    print '[OK] Error: ' + err._message

  # Testing error case: General error
  try:
    client.setProfileParam('wrongSomething', ProfileParam.CBK_URL, '')
  except GeneralError as err:
    print '[OK] Error: ' + err._message

  try:
    r = client.getProfileParam('wrongSomething', ProfileParam.CBK_URL)
  except GeneralError as err:
    print '[OK] Error: ' + err._message

  # Setting CBK_URL. You can monitor the calls to this callback URL via httpd logs
  cbk_url = 'http://localhost/orderstatuschanged'
  client.setProfileParam(authToken, ProfileParam.CBK_URL, cbk_url)
  res = client.getProfileParam(authToken, ProfileParam.CBK_URL)

  if (res == cbk_url):
    print "[OK] Setting/getting callback url was successfull"
  else:
    print "[NOK] returned callback url: '" + res + "'"

  '''
  *********************************** newOrder **********************************************************
  '''

  # Create new order
  person = Person('John', 'Smith', 'W.', 'Dr.')
  addr = Address(person, 'Boston', 'Massachusetts', 'StreetName 15', 'Apt. 25', 12567898, 'US')
  shipment = ShipmentData(addr, DeliveryMode.ECONOMY, PackagingMode.ENVELOPE)
  product = ProductData('SHAMROCK-VITT-100', 1, 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf', '593e00fe36e3f82a8c6859027673f671')
  misc = OrderMiscDetails('DocIdTest', 'Test comment')

  ordId = client.newOrder(authToken, shipment, [product], misc)
  print 'ordId = "' + ordId + '"'

  # Testing error case: Access denied
  try:
    ordId = client.newOrder('wrongAuthToken', shipment, [product], misc)
  except AccessDenied as err:
    print '[OK] Error: ' + err._message

  # Testing error case: Not supported delivery address
  try:
    # Syria is not supported destination. We shall receive an exception
    shipment.address.cc = 'SY'
    ordId = client.newOrder(authToken, shipment, [product], misc)
  except OrderError as err:
    print '[OK] Error: ' + str(err.code) + ' ' + err._message

  # Restoring destination country to the supported value
  shipment.address.cc = 'FI'

  # Testing error case: General error
  try:
    ordId = client.newOrder('wrongSomething', shipment, [product], misc)
  except GeneralError as err:
    print '[OK] Error: ' + str(err.orderId) + ' ' + err._message

  '''
  *********************************** getOrderDetails *******************************************************
  '''

  # Get order statuses
  orderStatuses = client.getOrderDetails(authToken, ordId)
  print orderStatuses

  # Testing error case: Access denied
  try:
    ordId = client.getOrderDetails("wrongAuthToken", ordId)
  except AccessDenied as err:
    print '[OK] Error: ' + err._message

  # Testing error case: Invalid order id (misformatted)
  try:
    ordId = client.getOrderDetails(authToken, "1234567")
  except OrderError as err:
    print '[OK] Error: ' + str(err.code) + ' ' + err._message

  # Testing error case: Invalid order id (non-existing)
  try:
    ordId = client.getOrderDetails(authToken, "54ce99c6f2ecd5121182d597")
  except OrderError as err:
    print '[OK] Error: ' + str(err.code) + ' ' + err._message


  # Testing error case: General error
  try:
    ordId = client.getOrderDetails("wrongSomething", ordId)
  except GeneralError as err:
    print '[OK] Error: ' + str(err.orderId) + ' ' + err._message


  # Testing error case: Invalid URL (real)
  try:
    product = ProductData('SHAMROCK-VITT-100', 1, 'http://vrepin.org/studies/no-such-url.pdf')
    ordId = client.newOrder(authToken, shipment, [product], misc)
  except OrderError as err:
    print '[OK] Error: ' + str(err.code) + ' ' + err._message

  # Testing error case: AuthTokenExpired
  print 'Sleeping for 30 seconds...';
  time.sleep(30)
  try:
    client.ping(authToken)
  except AuthTokenExpired as err:
    print '[OK] Error: ' + err._message

  transport.close()

except Thrift.TException, tx:
  print "%s" % (tx.message)
