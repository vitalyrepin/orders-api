<?php

 error_reporting(E_ALL);


 define('THRIFT_PATH', __DIR__);

 require_once THRIFT_PATH . '/Thrift/ClassLoader/ThriftClassLoader.php';

 $classLoader = new Thrift\ClassLoader\ThriftClassLoader();
 $classLoader->registerNamespace('Thrift', THRIFT_PATH);
 $classLoader->register();


 /*
 * Copyright 2015 Metida Print Ab Oy
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

 use Thrift\Protocol\TBinaryProtocol;
 use Thrift\Transport\TSocket;
 use Thrift\Transport\TSSLSocket;
 use Thrift\Transport\THttpClient;
 use Thrift\Transport\TBufferedTransport;
 use Thrift\Exception\TException;

 // (!) include after classLoader
 require_once '../../OrderManager/Metida/OrderManager.php';
 require_once '../../OrderManager/Metida/Types.php';

 use Metida\AccessDenied;
 use Metida\GeneralError;
 use Metida\OrderError;
 use Metida\AuthTokenExpired;
 use Metida\OrderManagerClient;
 use Metida\Person;
 use Metida\Address;
 use Metida\ProductData;
 use Metida\ShipmentData;
 use Metida\OrderMiscDetails;
 use Metida\DeliveryMode;
 use Metida\PackagingMode;
 use Metida\ProfileParam;

 try {
//  $socket = new TSSLSocket('dev.metidaprint.com', 443, FALSE, null, array('certfile' => 'cacert.pem'));

  $socket = new TSocket('localhost', 30303);
  $timeout = 10; // in seconds.
  $socket->setRecvTimeout($timeout*1000);
  $socket->setSendTimeout($timeout*1000);

  // Buffering is critical. Raw sockets are very slow
  $transport = new TBufferedTransport($socket, 1024, 1024);

  // Wrap in a protocol
  $protocol = new TBinaryProtocol($transport);

  //Create a client to use the protocol encoder
  $client = new OrderManagerClient($protocol);

  // Connect!
  $transport->open();


  // Get auth token
  $authToken = $client->getAuthToken('test@metidaprint.com', 'MetisZeus1450BC');
  printf("authToken = '%s'\n", $authToken);

  // Ping
  $client->ping($authToken);
  print "ping()\n";

  // Testing error case: no such user
  try {
    $authToken = $client->getAuthToken("NoUser", "");
    printf("authToken = '%s'\n", $authToken);
  } catch (AccessDenied $err) {
    printf("[OK] Error: %s\n", $err->_message);
  }

  # Create new order
  $person = new Person(array('name' => 'John',
  			     'surname' => 'Smith',
			     'middleName' => 'W.',
			     'title' => 'Dr.'));

  $addr = new Address(array('to' => $person,
  			    'city' => 'Boston',
			    'state' => 'Massachusetts',
			    'addressLine1' => 'StreetName 15',
			    'addressLine2' => 'Apt. 25',
			    'zip' => 1256789,
			    'cc' => 'US'));

  $shipment = new ShipmentData(array('address' => $addr,
  				     'deliveryMode' => DeliveryMode::ECONOMY,
				     'packagingMode' => PackagingMode::ENVELOPE));

  $product = new ProductData(array('productCode' => 'SHAMROCK-VITT-100',
  				   'qty' => 1,
				   'url' => 'http://vrepin.org/studies/Gamification2014/CourseraGamification2014.pdf',
				   'md5' => '593e00fe36e3f82a8c6859027673f671'));

  $misc = new OrderMiscDetails(array('docId' => 'DocIdTest',
  				     'comment' => 'Test comment'));

  /*********************************** get and set Profile Parameters ************************************/

  // Testing error case: Access denied
  try {
    $res = $client->getProfileParam('wrongAuthToken', ProfileParam::CBK_URL);
  } catch (AccessDenied $err) {
    printf("[OK] Error: %s\n", $err->_message);
  }

  try {
    $client->setProfileParam('wrongAuthToken', ProfileParam::CBK_URL, '');
  } catch (AccessDenied $err) {
    printf("[OK] Error: %s\n", $err->_message);
  }

  // Testing error case: General error
  try {
    $res = $client->getProfileParam('wrongSomething', ProfileParam::CBK_URL);
  } catch (GeneralError $err) {
    printf("[OK] Error: %s %s\n", $err->orderId, $err->_message);
  }

  try {
    $client->setProfileParam('wrongSomething', ProfileParam::CBK_URL, '');
  } catch (GeneralError $err) {
    printf("[OK] Error: %s %s\n", $err->orderId, $err->_message);
  }

  // Setting CBK_URL. You can monitor the calls to this callback URL via httpd logs
  $cbk_url = 'http://localhost/orderstatuschanged.php';
  $client->setProfileParam($authToken, ProfileParam::CBK_URL, $cbk_url);
  $res = $client->getProfileParam($authToken, ProfileParam::CBK_URL);

  if ($res == $cbk_url) {
    printf("[OK] Setting/getting callback url was successfull\n");
  } else {
    printf("[NOK] returned callback url: '%s'\n", res);
  }

  /*********************************** newOrder **********************************************************/

  $ordId = $client->newOrder($authToken, $shipment, array($product), $misc);
  print "ordId = '" . $ordId . "\n";

  // Testing error case: Access denied
  try {
    $ordId = $client->newOrder('wrongAuthToken', $shipment, array($product), $misc);
  } catch (AccessDenied $err) {
    printf("[OK] Error: %s\n", $err->_message);
  }

  // Testing error case: Not supported delivery address
  try {
    // Syria is not supported destination. We shall receive an exception
    $shipment->address->cc = "SY";
    $ordId = $client->newOrder($authToken, $shipment, array($product), $misc);
  } catch (OrderError $err) {
    printf("[OK] Error: %d %s \n", $err->code, $err->_message);
  }

  // Restoring destination country to the supported value
  $shipment->address->cc = "FI";

  // Testing error case: General error
  try {
    $ordId = $client->newOrder('wrongSomething', $shipment, array($product), $misc);
  } catch (GeneralError $err) {
    printf("[OK] Error: %s %s\n", $err->orderId, $err->_message);
  }

  /*********************************** getOrderDetails ***************************************************/

  // Get order statuses
  $orderStatuses = $client->getOrderDetails($authToken, $ordId);
  print_r($orderStatuses);

  // Testing error case: Access denied
  try {
    $ordId = $client->getOrderDetails("wrongAuthToken", $ordId);
  } catch (AccessDenied $err) {
    printf("[OK] Error: %s\n", $err->_message);
  }

  // Testing error case: Invalid order id (misformatted)
  try {
    $ordId = $client->getOrderDetails($authToken, "1234567");
  } catch (OrderError $err) {
    printf("[OK] Error: %d %s\n", $err->code, $err->_message);
  }

  // Testing error case: Invalid order id (non-existing)
  try {
    $ordId = $client->getOrderDetails($authToken, "54ce99c6f2ecd5121182d597");
  } catch (OrderError $err) {
    printf("[OK] Error: %d %s\n", $err->code, $err->_message);
  }

  // Testing error case: General error
  try {
    $ordId = $client->getOrderDetails("wrongSomething", $ordId);
  } catch(GeneralError $err) {
    printf("[OK] Error: %s %s\n", $err->orderId, $err->_message);
  }

  // Testing error case: Invalid URL (real)
  try {
    $product = new ProductData(array('productCode' => 'SHAMROCK-VITT-100',
    				     'qty' => 1,
				     'url' => 'http://vrepin.org/studies/no-such-url.pdf'));
    $ordId = $client->newOrder($authToken, $shipment, array($product), $misc);
  } catch(OrderError $err) {
    printf("[OK] Error: %d %s\n", $err->code, $err->_message);
  }

  // Testing exception: AuthTokenExpired
  print("Waiting 30 secs...\n");
  sleep(30);
  try {
   $client->ping($authToken);
  } catch(AuthTokenExpired $err) {
    printf("[OK] Error: %s\n", $err->_message);
  }

 }
 catch (Exception $e) {
   if ($e instanceof OrderError OR $e instanceof GeneralError or $e instanceof AccessDenied) {
     printf("OrderManager error: %s\n", $e->_message);
   } else {
     printf("TException: %s\n", $e->getMessage());
   }
 }
?>

