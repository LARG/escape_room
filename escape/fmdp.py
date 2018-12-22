import re, itertools
import cfgescape as config
import random

class Factor(object):
  __idx = 0
  def __init__(self, name=None, abbv=None, label=None, values=None, id=None, tabular=True, bounds=None, visualize=True, default=0):
    if tabular:
      if values: 
        self.values = values
        self.binary = False
      else: 
        self.values = [False, True]
        self.binary = True
      self.dim = 1
    else:
      self.bounds = bounds
      self.binary = False
      if config.current.tabular_discretization_factor:
        self.values = range(self.bounds[0],int(self.bounds[1]/config.current.tabular_discretization_factor+1))
      self.dim = len(self.bounds) / 2
    self.tabular = tabular
    self.name = name
    self.id = self.abbv = abbv or name
    self.label = label or name
    if id is not None: self.id = id
    self.visualize = visualize
    self.default = default
    
    self.idx = Factor.__idx
    Factor.__idx += 1

  def random_value(self):
    if self.tabular:
      return random.choice(self.values)
    else:
      point = [random.randint(self.bounds[2*i],self.bounds[2*i+1]) for i in range(self.dim)]
      return point

  def __eq__(self, other):
    if other == None: return False
    if not isinstance(other, Factor): return False
    return self.id == other.id

  def __cmp__(self, other):
    if other == None: return 1
    return cmp(self.id, other.id)

  @staticmethod
  def map(factor):
    return (factor.name, factor.id)

  @staticmethod
  def fromName(name, factors):
    for f in factors:
      if f.name == name:
        return f

  def __repr__(self):
    return 'F:%s' % self.id

class Action(object):
  __idx = 1
  def __init__(self, name=None, abbv=None, id=None, value=None, scale=None, type=None):
    self.name = name
    self.id = self.abbv = abbv or name
    if id is not None: self.id = id
    self.value = value
    self.idx = Action.__idx
    self.scale = scale
    self.type = type
    Action.__idx += 1

  @staticmethod
  def map(action):
    return (action.name, action.id)

  @staticmethod
  def fromName(name, actions):
    for a in actions:
      if a.name == name:
        return a

  def __cmp__(self, other):
    if other == None: return 1
    return cmp(self.id, other.id)

  def __eq__(self, other):
    if other == None: return False
    if not isinstance(other, Action): return False
    return self.id == other.id

  def __repr__(self):
    if self.scale == 1:
      return self.id
    return '%s, scale:%s' % (self.id,self.scale)

  def copy(self):
    a = Action(name=self.name,abbv=self.abbv,id=self.id,value=self.value,scale=self.scale)
    a.idx = self.idx
    return a

class FactorState(object):
  def __init__(self, values):
    self.values = values
    self.keys = self.values.keys
    self.items = self.values.items
    self.reset = False

  def __setitem__(self, i, v):
    self.values[i] = v

  def __getitem__(self, i):
    return self.values[i]

  def __contains__(self, i):
    return i in self.values

  def __iter__(self):
    return iter(self.values)

  def next(self):
    return next(self.values)

  def __len__(self):
    return len(self.values)

  def copy(self):
    state = self.__class__(self.values.copy())
    state.reset = self.reset
    return state
  
  def convert(self, values):
    return self.__class__(values.copy())

  def discretize(self, factors):
    for f in factors:
      if not f.tabular and config.current.tabular_discretization_factor:
        self.values[f.id] = round(self.values[f.id] / config.current.tabular_discretization_factor)

class GeneratedFactorState(FactorState):
  def copy(self):
    state = self.__class__(self.values.copy(), self.generator)
    state.reset = self.reset
    return state

class FactorWorld(object):
  def __init__(self, actions, factors):
    class Action: pass
    for a in actions:
      setattr(Action, a.name, a.id)
    type(self).Action = Action
    class Factor: pass
    for f in factors:
      setattr(Factor, f.name, f.id)
    type(self).Factor = Factor
    self.name = self.__class__.__name__
    self.actions = actions
    self.factors = factors
    self.layout = None
    self.agents = []
    self.alookup = {a.id:a for a in actions}
    self.flookup = {f.id:f for f in factors}

  def takeAction(self, state, action): pass

  def likelyNextStates(self, state):
    for action in self.actions:
      s = state.copy()
      self.takeAction(s, action)
      yield s
  
  def allNextStates(self):
    values, ids = [], []
    for f in self.factors:
      values.append(f.values)
      ids.append(f.id)
    s = self.createState()
    for combination in itertools.product(*values):
      s.values = dict(zip(ids, combination))
      yield s

class ActionSequence(list):
  def __init__(self, actions, path):
    self.path = path
    self.actions = {a.id:a for a in actions}
    try:
      self.read()
      self.reverse()
    except: pass

  def read(self):
    with open(self.path, 'r') as fh:
      while True:
        line = fh.readline()
        if line == '': break
        m = re.match(r'(\w+):(\d+)', line)
        if m:
          aid = m.group(1)
          iters = int(m.group(2))
          for i in range(iters):
            self.append(self.actions[aid])
          continue
        m = re.match(r'(\w+)', line)
        if m:
          aid = m.group(1)
          self.append(self.actions[aid])
