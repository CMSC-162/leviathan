import mmap
import re

def main(dump_file):
  fp = open(dump_file, 'r')
  buffer = mmap.mmap(fp, 0)
  
  pattern = r"""(<title>(.+?)</title>)|(<id>(.+?)</id>)|(<text>(.+?)</text>)"""
  
  for match in re.findall(buffer):
    print repr(match.groups())

if __name__ == '__main__':
  sys.exit(main(*sys.argv[1:]))