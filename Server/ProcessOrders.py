#!/usr/bin/env python

import sys
sys.path.append('../gen-py')

from orders import PrintAndDelivery
from orders.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TSSLSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.server import THttpServer

import time
import socket

class PrintAndDeliveryHandler:
  def __init__(self):
    self.log = {}

  def ping(self):
    print 'ping()'

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
    if(authToken == 'wrongOrderId'):
       raise PrintOrderError(PrintOrderErrCode.INVALID_ID, 'No such order: ' + orderId)

    pair = OrderTimePair()
    pair.tm = int(time.time())
    pair.status = PrintOrderStatus.PROCESSING 
    return [pair, pair]

  def newOrder(self, authToken, addr, url, comment):
    print 'newOrder: URL: "' + url + '"' + '; Comment: "' + comment + '"'
    print addr
    if(authToken == 'wrongAuthToken'):
        raise AccessDenied('Access denied or invalid auth token')
    if(authToken == 'wrongAddress'):
        raise PrintOrderError(PrintOrderErrCode.INVALID_ADDRESS, 'We do not deliver mail to Afganistan, sorry')
    if(authToken == 'wrongURL'):
        raise PrintOrderError(PrintOrderErrCode.INVALID_PRINT_URL, 'Can not download file from URL: ' + url)
    if(authToken == 'wrongSomething'):
        raise GeneralError('-1', 'Something went wrong. Mongo is down? Try again later...')

    return 'dsddskjdkjsdkjs'


handler = PrintAndDeliveryHandler()
processor = PrintAndDelivery.Processor(handler)
#transport = TSSLSocket.TSSLServerSocket('localhost', 30303)
transport = TSocket.TServerSocket('localhost', 30303)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
 
#httpServer = THttpServer.THttpServer(processor, ('localhost', 30303), tfactory, pfactory)

print "Starting python server..."
server.serve()
print "done!"
