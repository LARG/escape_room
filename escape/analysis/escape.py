import sys, os, math, re, csv
import glob, time, yaml
from parse import parse
try:
  import scipy.stats as spstats
except ImportError:
  spstats = None
from results import ResultFile, now, FILTER_KEYS
import cfgescape as config
import numpy as np

RESULT_KEYS = FILTER_KEYS + ['filename', 'directory']
VALID_METRICS = ['tsteps', 'treward', 'esteps', 'ereward', 'episode']
#ROLLING_METRICS = ['treward', 'ereward', 'esteps']
ROLLING_METRICS = ['esteps', 'ereward']
AGGREGATE_METRICS = VALID_METRICS + [m + '_mean' for m in ROLLING_METRICS]
TTEST_METRICS = ['treward', 'ereward']

class Analysis(object):
  def __init__(self):
    self.abstraction_error = 0
    self.reward = 0
    self.treward = 0
    self.time = 0

  def __str__(self):
    s = ""
    return s

class Analyzer(object):
  def __init__(self, world):
    self.world = world
    self.grid = world.flookup['Grid']
    self.action = world.alookup['Pickup']
    self.objective = world.flookup['P0']
    self.last_total_reward = 0

  def create_results(self, *args, **kwargs):
    return Results(*args, **kwargs)

  def analyze(self, agent, result=None):
    analysis = Analysis()
    if agent.model is None or agent.UseDiscretization:
      analysis.abstraction_error = 10000
      analysis.size = 0
    else:
      cpt = agent.model.cpts(self.objective.id,self.action.id)
      root = cpt.root()
      dataset = np.array(list(cpt.swig_predictions(self.grid.id)))
      augdim = self.grid.dim + self.objective.dim
      dataset = dataset.reshape(len(dataset)/augdim,augdim)
      for point in dataset:
        x, y, model = point
        gt = self.world.prediction([x,y], self.objective)
        analysis.abstraction_error += abs(model - gt)**2
      analysis.abstraction_error = math.sqrt(analysis.abstraction_error / len(dataset))
      analysis.size = len(dataset)
    analysis.reward = agent.totalReward - self.last_total_reward
    analysis.treward = agent.totalReward
    self.last_total_reward = analysis.treward
    if result:
      analysis.time = now() - result.start
    else: analysis.time = now()
    if result:
      for metric in VALID_METRICS:
        m = getattr(result, metric)
        v = getattr(analysis, metric)
        m.append(v)
      result.length += 1
      result.update()
    return analysis

class Result(object):
  def __init__(self, **kwargs):
    self.start = now()
    for fk in RESULT_KEYS:
      if fk in kwargs:
        setattr(self, fk, kwargs[fk])
      else:
        setattr(self, fk, None)
    self.length = 0
    
    for m in VALID_METRICS:
      setattr(self, m, [])
    self.metadata = {}
    for metric in TTEST_METRICS:
      self.metadata['final_' + metric] = []
    self.metadata['sample_size'] = 0
    self.filename = ResultFile.filename_from_keys(**kwargs)

  def save(self):
    path = os.path.join(self.directory, self.filename)
    print "saving to ",path
    if self.length == 0:
      print "Error saving to %s" % path
      print "Attempted saving an empty Result - did you actually get any results for this?"
      sys.exit()
    with open(path, 'w') as f:
      fmt = ','.join("%2.6f" for i in range(len(VALID_METRICS)))+ "\n"
      for i in range(self.length):
        values = []
        for idx, metric in enumerate(VALID_METRICS):
          m = getattr(self, metric)
          values.append(m[i])
        f.write(fmt % m)

  def update(self):
    path = os.path.join(self.directory, self.filename)
    with open(path, 'a') as f:
      i = self.length - 1
      fmt = ','.join("%2.6f" for i in range(len(VALID_METRICS))) + "\n"
      values = []
      for idx, metric in enumerate(VALID_METRICS):
        m = getattr(self, metric)
        values.append(m[i])
      f.write(fmt % tuple(values))

  @staticmethod
  def load(**kwargs):
    rfile = ResultFile(kwargs.get('filename'))
    result = Result(**kwargs)
    filename = kwargs['filename']
    timesteps = kwargs['timesteps']
    if not rfile.matches(**kwargs):
      return None
    path = os.path.join(result.directory, filename)
    with open(path, 'rb') as csvfile:
      reader = csv.reader(csvfile)
      i = 0
      header = reader.next()
      for row in reader:
        for idx, metric in enumerate(header):
          m = getattr(result, metric)
          m.append(float(row[idx]))
        i += 1
        if timesteps is not None and i >= timesteps: break
      result.length = i
    return result

  def touch(self, overwrite):
    path = os.path.join(self.directory, self.filename)
    if not overwrite:
      if os.path.isfile(path): return False
    with open(path, 'w'):
      os.utime(path, None)
    return True

  def exists(self):
    path = os.path.join(self.directory, self.filename)
    return os.path.isfile(path)

  def linecount(self):
    path = os.path.join(self.directory, self.filename)
    if not os.path.isfile(path): return 0
    i = 0
    with open(path,'r') as f:
      for i, l in enumerate(f): pass
    return i + 1

  def compute_rolling_means(self):
    metrics = ['ereward']
    maxlen = 5
    for metric in metrics:
      source = getattr(self, metric)
      target = []
      setattr(self, metric + '_mean', target)
      ep = 0
      completed = []
      for i, v in enumerate(source):
        nextep = int(self.episode[i])
        vprev = source[i - 1]
        if ep < nextep:
          completed.append(vprev)
        ep = nextep
        if len(completed) > maxlen:
          completed.pop(0)
        if len(completed) > 0:
          mean = float(sum(completed))/len(completed)
          target.append(mean)
        else:
          target.append(0)

  def compute_episode_lengths(self):
    epends, epstarts = [], []
    for i, v in enumerate(self.episode):
      if i > 0  and v != self.episode[i - 1]:
        epends.append(i-1)
        epstarts.append(i)
    metric = 'esteps_mean'
    source = getattr(self, 'esteps')
    target = []
    setattr(self, metric, target)
    recent, prior = [config.current.max_episode_steps], [config.current.max_episode_steps]
    maxlen = 100
    for i, v in enumerate(source):
      ep = int(self.episode[i])
      if ep > len(prior):
        success = self.treward[i-1] - self.treward[i - 2] > 1
        if success:
          prior[-1] = v
          recent[-1] = v
        prior.append(config.current.max_episode_steps)
        recent.append(config.current.max_episode_steps)
      if len(recent) > maxlen:
        recent.pop(0)
      window = recent
      mean = float(sum(window))/len(window)
      if ep == 0:
        target.append(0)
      else:
        target.append(mean)
    
class Results(list):
  def __init__(self, **kwargs):
    for key, value in kwargs.iteritems():
      setattr(self, key, value)
    self.kwargs = kwargs
    self.filters = {}
    for fk in FILTER_KEYS:
      if fk in kwargs:
        self.filters[fk] = kwargs[fk]
    super(Results, self).__init__()
  
  def get_trial(self):
    if self.trial is not None: return self.trial
    files = ResultFile.list_files(self.directory, kwargs=self.filters)
    trials = set()
    for f in files:
      res = parse('{}_size_{:d}_seed_{:d}_complexity_{:d}_trial_{:d}.csv', f)
      if not res: continue
      if res[0] == self.agent and res[1] == self.size and res[2] == self.seed and res[3] == self.complexity:
        trials.add(res[4])
    for i in range(self.trials):
      if i not in trials:
        return i

  def pad(self,l,size,value):
    l += [value] * (size - len(l))
    
  def combine(self, collection, metric, stat):
    collection = map(metric, collection)
    collection = [c[:] for c in collection]
    maxlen = max(len(ci) for ci in collection)
    if maxlen == 0: return []
    for c in collection:
      self.pad(c, maxlen, c[-1])
    z = map(stat, zip(*collection))
    return z

  @staticmethod
  def ttest(left, right):
    for m in TTEST_METRICS:
      ldata = left.metadata['final_' + m]
      rdata = right.metadata['final_' + m]
      if not ldata or not rdata: continue
      if ldata == rdata:
        print "  Skipping %s [datasets are equal]" % m
      else:
        t, pval = spstats.ttest_ind(ldata, rdata)
        print "  %s: %2.16f" % (m,pval)

  def save(self):
    if not self.directory: raise Exception("No path given for results file.")
    for result in self:
      if not result.exists():
        result.save()

  @staticmethod
  def load(directory=None, **kwargs):
    filter = ResultFile.filter_from_keys(**kwargs)
    print "Loading files with filter:",filter
    print "Args:",kwargs
    files = ResultFile.list_files(directory, kwargs=kwargs)
    results = Results(directory=directory)
    for filename in files:
      if filename.endswith("mean.csv"): continue
      result_kwargs = dict(kwargs)
      result_kwargs['filename'] = filename
      result = Result.load(directory=directory, **result_kwargs)
      if result == None: continue
      result.compute_episode_lengths()
      result.compute_rolling_means()
      results.append(result)
    return results

class MeanResult(Result):
  def __init__(self, **kwargs):
    if 'directory' not in kwargs: raise Exception("No directory provided to MeanResult")
    if 'agent' not in kwargs: raise Exception("No directory provided to MeanResult")
    super(MeanResult, self).__init__(**kwargs)
    self.directory = kwargs['directory']
    self.length = 0
    self.filename = re.sub(r'\.csv$', '_mean.csv', self.filename)
    self.metafile = re.sub(r'\.csv$', '.yaml', self.filename)
    resultpath = os.path.join(self.directory, self.filename)
    metapath = os.path.join(self.directory, self.metafile)
    if os.path.exists(resultpath) and os.path.exists(metapath) and not kwargs.get('recompute'):
      self.load()
      with open(metapath, 'r') as f:
        self.metadata = yaml.load(f)
    else:
      results = Results.load(filename=self.filename, **kwargs)
      if len(results) > 0:
        self.combine_results(results)
      self.save()
      with open(metapath, 'w') as f:
        f.write(yaml.dump(self.metadata))

  def combine_results(self, results):
    def lnmean(l):
      return float(sum(l))/len(l)
    
    def lnstddev(l):
      u = float(sum(l))/len(l)
      return math.sqrt(sum((x - u)**2 for x in l)/len(l))

    for metric in AGGREGATE_METRICS:
      setattr(self, metric, results.combine(results, lambda x: getattr(x, metric), lnmean))
      setattr(self, metric+'_stddev', results.combine(results, lambda x: getattr(x, metric), lnstddev))
      self.length = max(self.length, len(getattr(self, metric)))
    
    for result in results:
      for metric in TTEST_METRICS:
        final_list = self.metadata['final_' + metric]
        source_list = getattr(result, metric)
        final_list.append(source_list[-1])
    self.metadata['sample_size'] = len(results)
    return self

  def empty(self):
    return self.metadata['sample_size'] == 0

  def sample_size(self):
    return self.metadata['sample_size']

  def save(self):
    path = os.path.join(self.directory, self.filename)
    if self.length == 0:
      print "Error saving to %s" % path
      print "Attempted saving an empty MeanResult - did you actually get any results for this?"
      sys.exit()
    with open(path, 'w') as f:
      fmt = ','.join("%2.6f" for i in range(2 *len(AGGREGATE_METRICS))) + "\n"
      for i in range(self.length):
        values = []
        for idx, metric in enumerate(AGGREGATE_METRICS):
          m = getattr(self, metric)
          if len(m) == 0:
            values.append(0)
            values.append(0)
            continue
          m_stddev = getattr(self, metric + '_stddev')
          values.append(m[i])
          values.append(m_stddev[i])
        f.write(fmt % tuple(values))
  
  def load(self):
    for metric in AGGREGATE_METRICS:
      setattr(self, metric, [])
      setattr(self, metric + '_stddev', [])
    with open(os.path.join(self.directory, self.filename), 'r') as f:
      for i, line in enumerate(f):
        res = [float(s) for s in line.split(",")]
        for idx, metric in enumerate(AGGREGATE_METRICS):
          if 2*idx >= len(res): break
          metric_list = getattr(self, metric)
          metric_list.append(res[2*idx])
          metric_list = getattr(self, metric + '_stddev')
          metric_list.append(res[2*idx + 1])
    return self
