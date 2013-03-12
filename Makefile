DOWNLOAD_URL = http://download.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
WIKIPEDIA_BZ2_SOURCE = enwiki-latest-pages-articles.xml.bz2
WIKIPEDIA_LARGE_FILE = enwiki-latest-pages-articles.xml

DEVELOPER_EMAIL_ADDRESS = open-source@fatlotus.com

help:
	@echo \#
	@echo \# To build this project, run \"make build\" on a suitably large machine.
	@echo \#

build:
	rm -rf data_file index_file
	./processor init titles.txt
	./processor link in incoming.txt
	./processor link out outgoing.txt

processor: processor.c
	cc -g processor.c -o processor

$(WIKIPEDIA_BZ2_SOURCE):
	wget http://download.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2

$(WIKIPEDIA_LARGE_FILE): $(WIKIPEDIA_BZ2_SOURCE)
	bunzip2 $(WIKIPEDIA_BZ2_SOURCE)
