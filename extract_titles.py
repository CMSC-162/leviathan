import gc
import mmap
import re
import sys
import HTMLParser
import resource
from xml.sax import handler
from xml import sax

class Stage(handler.ContentHandler):
  def __init__(self):
    self.stack = [ ]
    self.capturing_input = False
    self.redirect = None
    self.title = None
    self.id = None
    self.content = [ ]
  
  def startElement(self, name, attrs):
    self.stack.append(name)
    self.content = None
    
    if (self.stack == ['mediawiki', 'page', 'title'] or
        self.stack == ['mediawiki', 'page', 'id']):
      self.content = [ ]
  
  def endElement(self, name):
    if self.stack == ['mediawiki', 'page', 'title']:
    
      self.title = ''.join(self.content)
    
    elif self.stack == ['mediawiki', 'page', 'id']:
    
      self.id = int(''.join(self.content))
    
    elif self.stack == ['mediawiki', 'page', 'redirect']:
    
      if self.id is not None and self.title is not None:
        self.extract_redirect(self.title, self.id, ''.join(self.content))
        self.id = self.title = None
      
    elif self.stack == ['mediawiki', 'page', 'text']:
      
      if self.id is not None and self.title is not None:
        links = [ ]
        
        for link in re.findall(r'\[\[.+?(|.+?)\]\]', ''.join(self.content)):
          links.append(link.group(0))
        
        self.extract_page(self.title, self.id, ''.join(self.content))
        self.id = self.title = None
    
    self.stack.pop()
  
  def characters(self, characters):
    if self.capturing_input:
      self.content.append(characters)
  
  def process(self, buffer):
    return sax.parseString(buffer, self)
  
  def extract_page(self, title, id, links):
    pass
  
  def extract_redirect(self, title, id, destination):
    pass

class CounterStage(Stage):
  def __init__(self):
    Stage.__init__.__call__(self)
    
    self.total_pages = 0
    self.total_redirects = 0
  
  def extract_page(self, title, id, links):
    self.total_pages += 1
    
    if self.total_pages % 1000 == 0:
      print "%-7s %-12s %-10s / %-10s (%0.1f%%)" % (self.total_pages, self.total_redirects + self.total_pages,
        self.offset_in_string, self.length_of_string, self.offset_in_string * 100.0 / self.length_of_string)
  
  def extract_redirect(self, title, id, destination):
    self.total_redirects += 1
    

class BinaryPackStage(Stage):
  def __init__(self, titles=None, result_file=None):
    Stage.__init__.__call__(self)
    
    self.offset = 0
    self.actually_pack = (titles is not None)
    self.titles = titles or [ ]
    self.result_file = result_file
  
  def pack_page(self, title, id, targets):
    links = struct.pack('I' * len(targets), *targets)
    return 'p%s%s%s' % (struct.pack('!IH', id, len(title)),
                       title, links)
  
  def pack_redirect(self, title, id, destination):
    links = struct.pack('I' * len(targets), *targets)
    return 'r%s%s%s' % (struct.pack('!IIH', id, destination, len(title)),
                       title)
  
  def lookup(self, title):
    index = bisect.bisect_right(self.titles, (link, 0))
    if index:
      offset = self.titles[index - 1][1]
    else:
      return None
  
  def extract_page(self, title, id, links):
    link_ids = [ ]
    
    if self.actually_pack:
      link_ids = [ 0 ] * len(links)
    else:
      link_ids = [ self.lookup(title) or 0 for title in links ]
    
    value = self.pack_page(title, id, link_ids)
    
    if self.actually_pack:
      self.result_file[self.offset:self.offset + len(value)] = value
    
    self.titles.append((title, self.offset))
    self.offset += len(value)
  
  def extract_redirect(self, title, id, destination):
    destination_id = self.lookup(destination) if self.actually_pack else 0
    
    value = self.pack_redirect(title, id, destination_id)
    
    if self.actually_pack:
      self.result_file[self.offset:self.offset + len(value)] = value
    
    self.titles.append((title, self.offset))
    self.offset += len(value)

def main(dump_file = None, result_file = None):
  if not dump_file or not result_file:
    print >>sys.stderr, "Usage: %s dump_file result_file" % sys.argv[0]
    return 1
  
  fp = open(dump_file, 'rb')
  buffer = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
  
  counter = CounterStage()
  counter.process(buffer)
  
  packer = BinaryPackStage()
  packer.process(buffer)
  
  titles = packer.titles
  titles.sort()
  
  out_fp = open(result_file, 'wb')
  out_buffer = mmap.mmap(out_fp.fileno(), 0, access.mmap.ACCESS_WRITE)
  
  packer2 = BinaryPackStage(titles, out_buffer)
  packer2.process(buffer)
  
  print "Subject: Progress Report"
  print
  print "Total pages: %i" % counter.total_pages
  print "Total redirects: %i" % counter.total_redirects
  return 0

if __name__ == '__main__':
  sys.exit(main(*sys.argv[1:]))
