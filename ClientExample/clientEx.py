#!/usr/bin/env python

import sys
sys.path.append('../gen-py')

from Orders import OrderManager
from Orders.ttypes import *
from Orders.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol


try:
  # Make socket
  transport = TSSLSocket.TSSLSocket('dev.metidaprint.com', 30301, True, 'cacert.pem')

  transport = TSocket.TSocket('localhost', 30303)

  # Buffering is critical. Raw sockets are very slow
  transport = TTransport.TBufferedTransport(transport)

  # Wrap in a protocol
  protocol = TBinaryProtocol.TBinaryProtocol(transport)

  # Create a client to use the protocol encoder
  client = OrderManager.Client(protocol)

  # Connect!
  transport.open()

  # Ping
  client.ping()
  print "ping()"

  # Get auth token
  authToken = client.getAuthToken("cert-orders@example.com", "qwerty")
  print 'authToken = ' + authToken

  # Testing error case: no such user
  try:
    authToken = client.getAuthToken("NoUser", "")
    print 'authToken = ' + authToken
  except AccessDenied as err:
    print 'Error: ' + err._message

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
    print 'Error: ' + err._message

  # Testing error case: Not supported delivery address
  try:
    ordId = client.newOrder('wrongAddress', shipment, [product], misc)
  except OrderError as err:
    print 'Error: ' + str(err.code) + ' ' + err._message

  # Testing error case: General error
  try:
    ordId = client.newOrder('wrongSomething', shipment, [product], misc)
  except GeneralError as err:
    print 'Error: ' + str(err.orderId) + ' ' + err._message

  # Get order statuses
  orderStatuses = client.getOrderDetails(authToken, ordId)
  print orderStatuses

  # Testing error case: Access denied
  try:
    ordId = client.getOrderDetails("wrongAuthToken", ordId)
  except AccessDenied as err:
    print 'Error: ' + err._message

  # Testing error case: Invalid order id (misformatted)
  try:
    ordId = client.getOrderDetails(authToken, "1234567")
  except OrderError as err:
    print 'Error: ' + str(err.code) + ' ' + err._message

 # Testing error case: Invalid order id (non-existing)
  try:
    ordId = client.getOrderDetails(authToken, "54ce99c6f2ecd5121182d597")
  except OrderError as err:
    print 'Error: ' + str(err.code) + ' ' + err._message


  # Testing error case: General error
  try:
    ordId = client.getOrderDetails("wrongSomething", ordId)
  except GeneralError as err:
    print 'Error: ' + str(err.orderId) + ' ' + err._message


  # Testing error case: Invalid URL (real)
  try:
    product = ProductData('SHAMROCK-VITT-100', 1, 'http://vrepin.org/studies/no-such-url.pdf')
    ordId = client.newOrder(authToken, shipment, [product], misc)
  except OrderError as err:
    print 'Error: ' + str(err.code) + ' ' + err._message
  

  transport.close()

except Thrift.TException, tx:
  print "%s" % (tx.message)
