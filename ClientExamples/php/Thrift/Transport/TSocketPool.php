<?php
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 *
 * @package thrift.transport
 */

namespace Thrift\Transport;

use Thrift\Transport\TSocket;
use Thrift\Exception\TException;

/**
 * This library makes use of APC cache to make hosts as down in a web
 * environment. If you are running from the CLI or on a system without APC
 * installed, then these null functions will step in and act like cache
 * misses.
 */
if (!function_exists('apc_fetch')) {
  function apc_fetch($key) { return FALSE; }
  function apc_store($key, $var, $ttl=0) { return FALSE; }
}

/**
 * Sockets implementation of the TTransport interface that allows connection
 * to a pool of servers.
 *
 * @package thrift.transport
 */
class TSocketPool extends TTransport implements TSocketIFace {

  /**
   * Remote servers. Array of associative arrays with 'host' and 'port' keys
   */
  private $servers_ = array();

  /**
   * How many times to retry each host in connect
   *
   * @var int
   */
  private $numRetries_ = 1;

  /**
   * Retry interval in seconds, how long to not try a host if it has been
   * marked as down.
   *
   * @var int
   */
  private $retryInterval_ = 60;

  /**
   * Max consecutive failures before marking a host down.
   *
   * @var int
   */
  private $maxConsecutiveFailures_ = 1;

  /**
   * Try hosts in order? or Randomized?
   *
   * @var bool
   */
  private $randomize_ = TRUE;

  /**
   * Always try last host, even if marked down?
   *
   * @var bool
   */
  private $alwaysTryLast_ = TRUE;
  
  /**
   * Internal representation of the socket
   * @var TSocket
   */
  protected $socket_ = null;

  /**
   * Socket pool constructor
   *
   * @param array  $hosts        List of remote hostnames
   * @param mixed  $ports        Array of remote ports, or a single common port
   * @param bool   $persist      Whether to use a persistent socket
   * @param mixed  $debugHandler Function for error logging
   * @param string $sockClass    Class name of class which extends TSocket
   */
  public function __construct($hosts=array('localhost'),
                              $ports=array(9090),
                              $persist=FALSE,
                              $debugHandler=null,
                              $sockClass='TSocket') {
    $this->socket_ = new $sockClass(null, 0, $persist, $debugHandler);
 
    parent::__construct(null, 0, $persist, $debugHandler);

    if (!is_array($ports)) {
      $port = $ports;
      $ports = array();
      foreach ($hosts as $key => $val) {
        $ports[$key] = $port;
      }
    }

    foreach ($hosts as $key => $host) {
      $this->servers_ []= array('host' => $host,
                                'port' => $ports[$key]);
    }
  }

  /**
   * Add a server to the pool
   *
   * This function does not prevent you from adding a duplicate server entry.
   *
   * @param string $host hostname or IP
   * @param int $port port
   */
  public function addServer($host, $port) {
    $this->servers_[] = array('host' => $host, 'port' => $port);
  }

  /**
   * Sets how many time to keep retrying a host in the connect function.
   *
   * @param int $numRetries
   */
  public function setNumRetries($numRetries) {
    $this->numRetries_ = $numRetries;
  }

  /**
   * Sets how long to wait until retrying a host if it was marked down
   *
   * @param int $numRetries
   */
  public function setRetryInterval($retryInterval) {
    $this->retryInterval_ = $retryInterval;
  }

  /**
   * Sets how many time to keep retrying a host before marking it as down.
   *
   * @param int $numRetries
   */
  public function setMaxConsecutiveFailures($maxConsecutiveFailures) {
    $this->maxConsecutiveFailures_ = $maxConsecutiveFailures;
  }

  /**
   * Turns randomization in connect order on or off.
   *
   * @param bool $randomize
   */
  public function setRandomize($randomize) {
    $this->randomize_ = $randomize;
  }

  /**
   * Whether to always try the last server.
   *
   * @param bool $alwaysTryLast
   */
  public function setAlwaysTryLast($alwaysTryLast) {
    $this->alwaysTryLast_ = $alwaysTryLast;
  }


  /**
   * Connects the socket by iterating through all the servers in the pool
   * and trying to find one that works.
   */
  public function open() {
    // Check if we want order randomization
    if ($this->randomize_) {
      shuffle($this->servers_);
    }

    // Count servers to identify the "last" one
    $numServers = count($this->servers_);

    for ($i = 0; $i < $numServers; ++$i) {

      // This extracts the $host and $port variables
      extract($this->servers_[$i]);

      // Check APC cache for a record of this server being down
      $failtimeKey = 'thrift_failtime:'.$host.':'.$port.'~';

      // Cache miss? Assume it's OK
      $lastFailtime = apc_fetch($failtimeKey);
      if ($lastFailtime === FALSE) {
        $lastFailtime = 0;
      }

      $retryIntervalPassed = FALSE;

      // Cache hit...make sure enough the retry interval has elapsed
      if ($lastFailtime > 0) {
        $elapsed = time() - $lastFailtime;
        if ($elapsed > $this->retryInterval_) {
          $retryIntervalPassed = TRUE;
          if ($this->socket_->getDebug()) {
            call_user_func($this->socket_->getDebugHandler(),
                           'TSocketPool: retryInterval '.
                           '('.$this->retryInterval_.') '.
                           'has passed for host '.$host.':'.$port);
          }
        }
      }

      // Only connect if not in the middle of a fail interval, OR if this
      // is the LAST server we are trying, just hammer away on it
      $isLastServer = FALSE;
      if ($this->alwaysTryLast_) {
        $isLastServer = ($i == ($numServers - 1));
      }

      if (($lastFailtime === 0) ||
          ($isLastServer) ||
          ($lastFailtime > 0 && $retryIntervalPassed)) {

        // Set underlying TSocket params to this one
	$this->socket_->setHost($host);
        $this->socket_->setPort($port);
 

        // Try up to numRetries_ connections per server
        for ($attempt = 0; $attempt < $this->numRetries_; $attempt++) {
          try {
            // Use the underlying TSocket open function
	    $this->socket_->open();

            // Only clear the failure counts if required to do so
            if ($lastFailtime > 0) {
              apc_store($failtimeKey, 0);
            }

            // Successful connection, return now
            return;

          } catch (TException $tx) {
            // Connection failed
	    debug_rlog0($tx->getMessage());
          }
        }

        // Mark failure of this host in the cache
        $consecfailsKey = 'thrift_consecfails:'.$host.':'.$port.'~';

        // Ignore cache misses
        $consecfails = apc_fetch($consecfailsKey);
        if ($consecfails === FALSE) {
          $consecfails = 0;
        }

        // Increment by one
        $consecfails++;

        // Log and cache this failure
        if ($consecfails >= $this->maxConsecutiveFailures_) {
          if ($this->socket_->getDebug()) {
            call_user_func($this->socket_->getDebugHandler(),
                           'TSocketPool: marking '.$host.':'.$port.
                           ' as down for '.$this->retryInterval_.' secs '.
                           'after '.$consecfails.' failed attempts.');
          }
          // Store the failure time
          apc_store($failtimeKey, time());

          // Clear the count of consecutive failures
          apc_store($consecfailsKey, 0);
        } else {
          apc_store($consecfailsKey, $consecfails);
        }
      }
    }

    // Oh no; we failed them all. The system is totally ill!
    $error = 'TSocketPool: All hosts in pool are down. ';
    $hosts = array();
    foreach ($this->servers_ as $server) {
      $hosts []= $server['host'].':'.$server['port'];
    }
    $hostlist = implode(',', $hosts);
    $error .= '('.$hostlist.')';
    if ($this->socket_->getDebug()) {
      call_user_func($this->socket_->getDebugHandler(), $error);
    }
    throw new TException($error);
  }

 /**
  * Delegate isOpen to internal socket
  */
 public function isOpen() {
   return $this->socket_->isOpen();
 }

 /**
  * Delegate close to internal socket
  */
 public function close() {
   return $this->socket_->close();
 }

 /**
  * Delegate read to internal socket
  */
 public function read($len) {
   return $this->socket_->read($len);
 }

 /**
  * Delegate read to internal socket
  */
 public function readAll($len) {
   return $this->socket_->readAll($len);
 }

 /**
  * Delegate write to internal socket
  */
 public function write($buf) {
   return $this->socket_->write($buf);
 }

 /**
  * Delegate flush to internal socket
  */
 public function flush() {
   return $this->socket_->flush();
 }

 /**
  * Delegate setSendTimeout to internal socket
  */
 public function setSendTimeout($timeout) {
   return $this->socket_->setSendTimeout($timeout);
 }

 /**
  * Delegate setRecvTimeout to internal socket
  */
 public function setRecvTimeout($timeout) {
   return $this->socket_->setRecvTimeout($timeout);
 }

 /**
  * Delegate setDebug to internal socket
  */
 public function setDebug($debug) {
   return $this->socket_->setDebug($debug);
 }

 /**
  * Delegate getHost to internal socket
  */
 public function getHost() {
   return $this->socket_->getHost();
 }

 /**
  * Delegate getPort to internal socket
  */
 public function getPort() {
   return $this->socket_->getPort();
 }
}
