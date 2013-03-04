import gc
import mmap
import re
import sys
import HTMLParser
import resource

total_pages = 0
total_redirects = 0

def emit_page(title, id, destination):
  global total_pages
  total_pages += 1
  if total_pages % 1000 == 0:
    print >>sys.stderr, "%s\r" % total_pages,

def emit_redirect(title, id, destination):
  global total_redirects
  total_redirects += 1

def main(dump_file = None):
  if not dump_file:
    print >>sys.stderr, "Usage: %s dump_file" % sys.argv[0]
    return 1
  
  fp = open(dump_file, 'rb')
  buffer = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
    
  pattern = r"""(<title>(.+?)</title>)|(<id>(.+?)</id>)|(<text.*?>(.+?)</text>)|(<redirect title="(.+?)" />)"""
  rxp = re.compile(pattern, re.DOTALL)
  offset = 0
    
  page_title = None
  page_id = None
  while True:
    match = rxp.search(buffer, offset)
    if match is None:
      break
    offset = match.end()
    if match.group(0).startswith('<title'):
      page_title = match.group(2).decode('utf-8')
    elif match.group(0).startswith('<id'):
      if page_id is None:
        page_id = int(match.group(4))
    elif match.group(0).startswith('<redirect'):
      emit_redirect(page_title, page_id, match.group(8).decode('utf-8'))
      page_title = None
      page_id = None
    elif match.group(0).startswith('<text'):
      if page_title is None or page_id is None:
        continue
      text = match.group(6).decode('utf-8')
      emit_page(page_title, page_id, match.group(6).decode('utf-8'))
      page_title = None
      page_id = None
  
  print "Subject: Progress Report"
  print
  print "Total pages: %i" % total_pages
  print "Total redirects: %i" % total_redirects
  return 0

if __name__ == '__main__':
  sys.exit(main(*sys.argv[1:]))
