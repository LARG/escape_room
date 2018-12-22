import sys, os, re, csv

def get_file_lines(path):
  if not os.path.exists(path):
    return None
  with open(path, 'rb') as csvfile:
    reader = csv.reader(csvfile)
    headers = reader.next()
    return len([row for row in reader])

def get_last_timestep(path):
  if not os.path.exists(path):
    return None
  with open(path, 'rb') as csvfile:
    reader = csv.reader(csvfile)
    headers = reader.next()
    header_map = {v:i for i,v in enumerate(headers)}
    last = None
    for row in reader:
      last = row
  if last is None:
    return None
  if 'tsteps' in header_map:
    idx = header_map['tsteps']
    if len(last) > idx:
      ts = int(last[idx])
      return ts
  return None

