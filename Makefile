# Path to the thrift compiler
THRIFT = thrift
# rm command
RM = rm -rf
# Tar command
TGZ=tar -pczf

# Thrift file (IDL)
ORD = Orders.thrift

# Thrift common cmdline
THRIFTCMD=-out OrderManager $(ORD)

# File with CAs. Needed for verification of server certificate by the client. Downloaded from http://curl.haxx.se/ca/cacert.pem
CAPEM=ClientExample/cacert.pem

.PHONY: clean

all: $(CAPEM) html py php js ruby perl csharp cocoa android java

$(CAPEM):
	cd ClientExample ; wget http://curl.haxx.se/ca/cacert.pem

html:	$(ORD)
	$(THRIFT) --gen html $(ORD)

py:	$(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen py:new_style,utf8strings $(THRIFTCMD)
	$(THRIFT) --gen py:new_style,utf8strings $(ORD)
	$(TGZ) python-sdk.tar.gz OrderManager

php:  	$(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen php $(THRIFTCMD)
	$(TGZ) php-sdk.tar.gz OrderManager

js:	$(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen js:jquery $(THRIFTCMD)
	$(TGZ) js-sdk.tar.gz OrderManager

ruby: 	$(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen rb $(THRIFTCMD)
	$(TGZ) ruby-sdk.tar.gz OrderManager

perl: 	$(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen perl  $(THRIFTCMD)
	$(TGZ) perl-sdk.tar.gz OrderManager

csharp: $(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen csharp:wcf,serial  $(THRIFTCMD)
	$(TGZ) csharp-sdk.tar.gz OrderManager

cocoa: $(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen cocoa  $(THRIFTCMD)
	$(TGZ) cocoa-sdk.tar.gz OrderManager

android: $(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen java:java5 $(THRIFTCMD)
	$(TGZ) android-sdk.tar.gz OrderManager

java: $(ORD)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen java $(THRIFTCMD)
	$(TGZ) java-sdk.tar.gz OrderManager

clean:
	$(RM) gen-html gen-js gen-py gen-php $(CAPEM) *.tar.gz
