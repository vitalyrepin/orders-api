<?php

namespace Thrift\Transport;

use Thrift\Transport\TTransport;
use Thrift\Transport\TSocket;
use Thrift\Exception\TException;
use Thrift\Exception\TTransportException;
use Thrift\Factory\TStringFuncFactory;


class TSSLSocket extends TSocket {
  
  private $certFile_ = null;

  private $canSelfSign_ = true;

  private $passphrase_ = null;

  public function __construct($ip, $port, $persist, $debughandler,
                              $options=array()) {
    parent::__construct($this->getSSLHost($ip), $port,
                        $persist, $debughandler, $options);
    if (isset($options['certfile'])) {
      $this->setCertificateFile($options['certfile']);
    }
    if (isset($options['selfsign'])) {
      $this->setSelfSign($options['selfsign']);
    }
    if (isset($options['passphrase'])) {
      $this->setPassphrase($options['passphrase']);
    }
  }

  public function setHost($host) {
    $this->host_ = $this->getSSLHost($host);
  }

  public function setCertificateFile($file) {
    $this->certFile_ = $file;
  }

  public function setSelfSign($selfsign) {
    $this->canSelfSign_ = $selfsign;
  }

  public function setPassphrase($passphrase) {
    $this->passphrase_ = $passphrase;
  }

  private function getSSLHost($host) {
    $protocol_loc = strpos($host, '://');
    if ($protocol_loc === false) {
      $host = 'ssl://'.$host;
    } else {
      $protocol = strtolower(substr($host, 0, $protocol_loc));
      $host = substr($host, $protocol_loc);
      switch ($protocol) {
        case 'http':
          $host = 'https'.$host;
          break;
        case 'ftp':
          $host = 'ftps'.$host;
          break;
      }
    }
    return $host;
  }

  public function open() {
     $context = stream_context_create();

    //$this->certFile_ = '/home/joel/fbcode_local/phpKeystore.pem.crt';
    //$this->passphrase_ = 'abc123';

    // set the certificates file
    if ($this->certFile_) {
      $cafile_res = stream_context_set_option($context, 'ssl', 'cafile',
                                              $this->certFile_);
      if (!$cafile_res) {
        $error = 'TSSLSocket: Could not set ca file: '.$this->certFile_;
        if ($this->debug_) {
          call_user_func($this->debugHandler_, $error);
        }
        throw new TException($error);
      }
    }

    // allow the cert to be self signed
    if ($this->canSelfSign_) {
      $selfsign_res = stream_context_set_option($context, 'ssl',
                                                'allow_self_signed', true);
      if (!$selfsign_res) {
        $error = 'TSSLSocket: Could not set self-signed.';
        if ($this->debug_) {
          call_user_func($this->debugHandler_, $error);
        }
        throw new TException($error);
      }
    }

    // password?
    if ($this->passphrase_) {
      $passphrase_res = stream_context_set_option($context, 'ssl', 'passphrase',
                                                  $this->passphrase_);
      if (!$passphrase_res) {
        $error = 'TSSLSocket: Could not set passphrase.';
        if ($this->debug_) {
          call_user_func($this->debugHandler_, $error);
        }
        throw new TException($error);
      }
    }
   
    // The default list of ciphers supplied by the openssl extension contain a number of unsafe ciphers which should be disabled unless absolutely necessary.
    // The below cipher list, in a syntax accepted by openssl, was implemented by cURL during January 2014.
    $ciphers_res = stream_context_set_option($context, 'ssl', 'ciphers','ALL!EXPORT!EXPORT40!EXPORT56!aNULL!LOW!RC4');
    if (!$ciphers_res) {
      $error = 'TSSLSocket: Could not set ciphers.';
      if ($this->debug_) {
        call_user_func($this->debugHandler_, $error);
      }
      throw new TException($error);
    }

    $this->sendTimeoutSec_ = 10;

    $this->handle_ = stream_socket_client(
        $this->host_.':'.$this->port_,
        $errno,
        $errstr,
        $this->sendTimeoutSec_,
        STREAM_CLIENT_CONNECT,
        $context); 

//    $this->handle_ = stream_socket_client("tcp://109.74.13.17:443", $errno, $errstr, 30);
    // Connect failed ?
    if ($this->handle_ === false) {
      $error = 'TSSLSocket: Could not connect to '
             . $this->host_.':'.$this->port_
             . ' ('.$errstr.' ['.$errno.'])';
      if ($this->debug_) {
        call_user_func($this->debugHandler_, $error);
      }
      throw new TException($error);
    }
 
    stream_set_timeout($this->handle_, $this->sendTimeoutSec_, $this->sendTimeoutUsec_);
//    $this->sendTimeoutSet_ = true;
  }
}

