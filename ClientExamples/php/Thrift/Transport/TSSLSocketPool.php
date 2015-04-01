<?php

/* Inherits from SocketPool */
include_once $GLOBALS['THRIFT_ROOT'].'/transport/TSocketPool.php';

class TSSLSocketPool extends TSocketPool implements TSocketIFace {
  public function __construct($hosts=array('localhost'),
                              $ports=array(9090),
                              $persist=false,
                              $debugHandler=null) {
    parent::__construct($hosts, $ports, $persist, $debugHandler, 'TSSLSocket');
  }

  public function setCertificateFile($certFile) {
    $this->socket_->setCertificateFile($certFile);
  }

  public function setPassphrase($passphrase) {
    $this->socket_->setPassphrase($passphrase);
  }

  public function setSelfSign($selfsign) {
    $this->socket_->setSelfSign($selfsign);
  }
}

