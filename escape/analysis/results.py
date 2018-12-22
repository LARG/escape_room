import sys, os, time, math, glob
import yaml
from parse import parse

FILTER_KEYS = ['agent', 'size', 'seed', 'complexity', 'handicap', 'trial']
DIGITS = {
  'size': 2,
  'seed': 2,
  'complexity': 2,
  'handicap': 2,
  'trial': 3
}

def now():
  millis = int(round(time.time() * 1000))
  return millis

class ResultFile(object):
  def __init__(self, path):
    self.path = path
    self.filename = os.path.basename(path)
    res = parse('escape_agent_{}_size_{:d}_seed_{:d}_complexity_{:d}_handicap_{:d}_trial_{:d}.csv', self.filename)
    self.success = res is not None
    self.filters = {}
    if self.success:
      self.agent, self.size, self.seed, self.complexity, self.handicap, self.trial = res
      for fk in FILTER_KEYS:
        self.filters[fk] = getattr(self, fk)
  
  @staticmethod
  def filter_from_keys(**kwargs):
    filter = 'escape_agent_' + kwargs['agent']
    for fk in FILTER_KEYS:
      if fk == 'agent': continue
      if fk not in kwargs or kwargs[fk] is None:
        filter += '_%s_*' % fk
        continue
      fmt = '_%s_%0' + str(DIGITS[fk]) + 'i'
      part = fmt % (fk, kwargs[fk])
      filter += part
    filter += '.csv'
    return filter

  @staticmethod
  def filename_from_keys(**kwargs):
    filename = 'escape_agent_' + kwargs['agent']
    for fk in FILTER_KEYS:
      if fk == 'agent': continue
      if fk not in kwargs or kwargs[fk] is None: continue
      fmt = '_%s_%0' + str(DIGITS[fk]) + 'i'
      part = fmt % (fk, kwargs[fk])
      filename += part
    filename += '.csv'
    return filename

  def matches(self, **kwargs):
    for fk in FILTER_KEYS:
      if fk not in kwargs: continue
      if kwargs[fk] is None: continue
      if fk not in self.filters: continue
      if self.filters[fk] is None: continue
      if self.filters[fk] != kwargs[fk]:
        return False
    return True

  @staticmethod
  def list_files(directory, filter=None, extension='.csv', kwargs=None):
    isfile = os.path.isfile
    join = os.path.join
    if kwargs:
      filter = ResultFile.filter_from_keys(**kwargs)
    if filter:
      fpath = join(directory,filter)
      for f in glob.iglob(fpath):
        yield os.path.basename(f)
      raise StopIteration()
    for f in os.listdir(directory):
      if isfile(join(directory,f)) and f.endswith(extension):
        yield f

  def __str__(self):
    s = "%s - Size: %s, Seed: %s, Complexity: %s, Handicap: %s, Trial: %s" % (
      self.agent, self.size, self.seed, self.complexity, self.handicap, self.trial
    )
    return s
