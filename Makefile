# Path to the thrift compiler
THRIFT = thrift
# rm command
RM = rm -rf
# cp command
CP = cp
# Tar command
TGZ=tar -pczf

# License for SDK - file name
LICENSESDK=SDK-LICENSE.TXT

# Thrift file (IDL)
ORD = Orders.thrift

# Thrift common cmdline
THRIFTCMD=-out OrderManager $(ORD)

# File with CAs. Needed for verification of server certificate by the client. Downloaded from http://curl.haxx.se/ca/cacert.pem
CAPEM=ClientExamples/cacert.pem

.PHONY: clean

all: $(CAPEM) html py php js ruby perl csharp cocoa android java

$(CAPEM):
	cd ClientExamples ; wget http://curl.haxx.se/ca/cacert.pem
	cd ClientExamples/py ; ln -s ../cacert.pem cacert.pem
	cd ClientExamples/php ; ln -s ../cacert.pem cacert.pem

$(LICENSESDK):
	@echo "Copyright 2015 Metida Print Ab Oy" > $(LICENSESDK)
	@echo "Licensed under the Apache License, Version 2.0 (the \"License\");" >> $(LICENSESDK)
	@echo "you may not use this file except in compliance with the License." >> $(LICENSESDK)
	@echo "You may obtain a copy of the License at" >> $(LICENSESDK)
	@echo "http://www.apache.org/licenses/LICENSE-2.0" >> $(LICENSESDK)
	@echo "Unless required by applicable law or agreed to in writing, software" >> $(LICENSESDK)
	@echo "distributed under the License is distributed on an "AS IS" BASIS," >> $(LICENSESDK)
	@echo "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied." >> $(LICENSESDK)
	@echo "See the License for the specific language governing permissions and" >> $(LICENSESDK)
	@echo "limitations under the License." >> $(LICENSESDK)

html:	$(ORD)
	$(THRIFT) --gen html $(ORD)

py:	$(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen py:new_style,utf8strings $(THRIFTCMD)
	$(THRIFT) --gen py:new_style,utf8strings $(ORD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) python-sdk.tar.gz OrderManager

php:  	$(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen php $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) php-sdk.tar.gz OrderManager

js:	$(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen js:jquery $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) js-sdk.tar.gz OrderManager

ruby: 	$(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen rb $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) ruby-sdk.tar.gz OrderManager

perl: 	$(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen perl  $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) perl-sdk.tar.gz OrderManager

csharp: $(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen csharp:wcf,serial  $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) csharp-sdk.tar.gz OrderManager

cocoa: $(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen cocoa  $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) cocoa-sdk.tar.gz OrderManager

android: $(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen java:java5 $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) android-sdk.tar.gz OrderManager

java: $(ORD) $(LICENSESDK)
	$(RM) OrderManager
	mkdir OrderManager
	$(THRIFT) --gen java $(THRIFTCMD)
	$(CP) $(LICENSESDK) OrderManager/
	$(TGZ) java-sdk.tar.gz OrderManager

clean:
	$(RM) gen-html gen-js gen-py gen-php $(CAPEM) *.tar.gz $(LICENSESDK)
