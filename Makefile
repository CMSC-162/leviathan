DOWNLOAD_URL = http://download.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
WIKIPEDIA_BZ2_SOURCE = enwiki-latest-pages-articles.xml.bz2
WIKIPEDIA_LARGE_FILE = enwiki-latest-pages-articles.xml

help:
	@echo \#
	@echo \# To build this project, run \"make build\" on a suitably large machine.
	@echo \#

build: $(WIKIPEDIA_LARGE_FILE)

$(WIKIPEDIA_BZ2_SOURCE):
	wget http://download.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2

$(WIKIPEDIA_LARGE_FILE): $(WIKIPEDIA_BZ2_SOURCE)
	bunzip2 $(WIKIPEDIA_BZ2_SOURCE)