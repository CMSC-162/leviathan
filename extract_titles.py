import gc
import mmap
import re
import sys
import HTMLParser
import resource

class Stage(object):
  def process(self, buffer):
    pattern = r"""(<title>(.+?)</title>)|(<id>(.+?)</id>)|(<text.*?>(.+?)</text>)|(<redirect title="(.+?)" />)"""
    rxp = re.compile(pattern, re.DOTALL)
    offset = 0
    prev_offset = 0
    
    page_title = None
    page_id = None
    while True:
      match = rxp.search(buffer, offset)
      if match is None:
        break
      
      offset = match.end()
      if offset <= prev_offset:
        raise Exception("Going backwards in the string!")
      prev_offset = offset
      
      self.offset_in_string = 0
      self.length_of_string = len(buffer)
      
      if match.group(0).startswith('<title'):
        page_title = match.group(2).decode('utf-8')
      elif match.group(0).startswith('<id'):
        if page_id is None:
          page_id = int(match.group(4))
      elif match.group(0).startswith('<redirect'):
        self.extract_redirect(page_title, page_id, match.group(8).decode('utf-8'))
        page_title = None
        page_id = None
      elif match.group(0).startswith('<text'):
        if page_title is None or page_id is None:
          continue
        text = match.group(6).decode('utf-8')
        self.extract_page(page_title, page_id, match.group(6).decode('utf-8'))
        page_title = None
        page_id = None
  
  def extract_page(self, title, id, links):
    pass
  
  def extract_redirect(self, title, id, destination):
    pass

class CounterStage(Stage):
  def __init__(self):
    self.total_pages = 0
    self.total_redirects = 0
  
  def extract_page(self, title, id, description):
    self.total_pages += 1
    
    if self.total_pages % 1000 == 0:
      print "%-7s %-12s %-10s / %-10s (%0.1f%%)" % (self.total_pages, self.total_redirects + self.total_pages,
        self.offset_in_string, self.length_of_string, self.offset_in_string * 100.0 / self.length_of_string)
  
  def extract_redirect(self, title, id, destination):
    self.total_redirects += 1

class BinaryPackStage(Stage):
  def __init__(self, titles=None, result_file=None):
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
