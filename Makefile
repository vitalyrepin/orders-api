# Path to the thrift compiler
THRIFT = thrift
# rm command
RM = rm -rf

# Thrift file (IDL)
ORD = orders.thrift

# File with CAs. Needed for verification of server certificate by the client. Downloaded from http://curl.haxx.se/ca/cacert.pem
CAPEM=ClientExample/cacert.pem

.PHONY: clean

all: $(CAPEM) html py php js

$(CAPEM):
	cd ClientExample ; wget http://curl.haxx.se/ca/cacert.pem

html:	$(ORD)
	$(THRIFT) --gen html $(ORD)

py:	$(ORD)
	$(THRIFT) --gen py:new_style,utf8strings $(ORD)

php:  	$(ORD)
	$(THRIFT) --gen php $(ORD)

js:	$(ORD)
	$(THRIFT) --gen js:jquery $(ORD)

clean:
	$(RM) gen-html gen-js gen-py gen-php $(CAPEM)
