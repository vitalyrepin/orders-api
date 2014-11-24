#!/usr/bin/env python

import sys
sys.path.append('../gen-py')

from orders import PrintAndDelivery
from orders.ttypes import *
from orders.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol


try:
  # Make socket
  transport = TSSLSocket.TSSLSocket('localhost', 30301, True, 'client.crt')

  # Buffering is critical. Raw sockets are very slow
  transport = TTransport.TBufferedTransport(transport)

  # Wrap in a protocol
  protocol = TBinaryProtocol.TBinaryProtocol(transport)

  # Create a client to use the protocol encoder
  client = PrintAndDelivery.Client(protocol)

  # Connect!
  transport.open()

  # Ping
  client.ping()
  print "ping()"

  # Get auth token
  authToken = client.getAuthToken("John@john.de", "superlosenord")
  print 'authToken = ' + authToken

  # Testing error case: no such user
  try: 
    authToken = client.getAuthToken("tstAuthError", "superlosenord")
    print 'authToken = ' + authToken
  except AccessDenied as err:
    print 'Error: ' + err._message

  # Create new order
  person = Person('John', 'Smith', 'W.', 'Dr.')
  addr = Address(person, 'Boston', 'Massachusetts', 'StreetName 15', 'Apt. 25', 12567898, 'US')
  ordId = client.newOrder(authToken, addr, 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf', 'Test')
  print 'ordId = "' + ordId + '"'

  # Testing error case: Access denied
  try:
    ordId = client.newOrder('wrongAuthToken', addr, 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf', 'Test')
  except AccessDenied as err:
    print 'Error: ' + err._message

  # Testing error case: Not supported delivery address
  try:
    ordId = client.newOrder('wrongAddress', addr, 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf', 'Test')
  except PrintOrderError as err:
    print 'Error: ' + str(err.Code) + ' ' + err._message

  # Testing error case: Invalid URL
  try:
    ordId = client.newOrder('wrongURL', addr, 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf', 'Test')
  except PrintOrderError as err:
    print 'Error: ' + str(err.Code) + ' ' + err._message

  # Testing error case: General error
  try:
    ordId = client.newOrder('wrongSomething', addr, 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf', 'Test')
  except GeneralError as err:
    print 'Error: ' + str(err.OrderId) + ' ' + err._message


  # Get order statuses
  orderStatuses = client.getOrderDetails(authToken, ordId)
  print orderStatuses

  # Testing error case: Access denied
  try:
    ordId = client.getOrderDetails("wrongAuthToken", ordId)
  except AccessDenied as err:
    print 'Error: ' + err._message

  # Testing error case: Invalid order id
  try:
    ordId = client.getOrderDetails("wrongOrderId", ordId)
  except PrintOrderError as err:
    print 'Error: ' + str(err.Code) + ' ' + err._message


  # Testing error case: General error
  try:
    ordId = client.getOrderDetails("wrongSomething", ordId)
  except GeneralError as err:
    print 'Error: ' + str(err.OrderId) + ' ' + err._message

  transport.close()

except Thrift.TException, tx:
  print "%s" % (tx.message)
