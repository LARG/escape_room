from fmdp import Action, Factor, FactorState, FactorWorld
from graph import Graph
import cfgescape as config
import random
import numpy as np

class LightGenerator(object):
  def __init__(self):
    self.complexity = 0

  def generate(self, size=None, complexity=None):
    lights = ['L%02i'%i for i in range(1,size+1)]
    unused = list(lights)
    parents = {}
    prev = set()
    while len(unused) > 0:
      k = random.randint(1,min(4,len(unused))/2+1)
      sample = unused[:k]
      unused = unused[k:]
      for s in sample:
        parents[s] = []
        if len(prev) == 0: continue
        k = random.randint(1,min(len(prev),complexity))
        sparents = random.sample(list(prev), k)
        for p in sparents:
          parents[s].append(p)
      prev = sample
    self.lights = lights
    self.parents = parents
    
    self.graph = Graph()
    self.graph.build(self.parents)
    self.complexity = max(len(p) for p in self.parents.values())
    self.complexity += 1 # add one to satisfy minimal requirements when c=1
    self.goal = self.lights[-1]

class LightState(FactorState):
  def __init__(self, values=None, generator=None):
    self.generator = generator
    self.setDependencies()
    default = {l:False for l in self.parents}
    if values:
      for k in default:
        if k not in values:
          values[k] = default[k]
    else:
      values = default
    super(LightState, self).__init__(values)

  def setDependencies(self):
    self.lights, self.parents = self.generator.lights, self.generator.parents
    self.children = {l:[] for l in self.parents}
    for c in self.parents:
      for p in self.parents[c]:
        self.children[p] += [c]
    self.descendants = {}
    def getDescendants(p):
      descendants = []
      for c in self.children[p]:
        descendants += [c]
        descendants += getDescendants(c)
      return descendants
    for light in self.parents:
      self.descendants[light] = getDescendants(light)

  def toggleLight(self, light):
    self.reset = False
    if light not in self.values: raise Exception("Invalid light: %s" % light)
    if config.current.stochastic and random.random() < .1: return
    if config.current.independent_light_off and self.values[light]:
      if not config.current.enable_off_toggling:
        return
      self.values[light] = False
      return
    for p in self.parents[light]:
      if not self.values[p]:
        if config.current.use_reset:
          self.values = {l:False for l in self.lights}
          if config.current.ignore_reset_refinements: self.reset = True
        return
    self.values[light] = not self.values[light]

  def completed(self):
    return self[self.generator.goal]

  def __repr__(self):
    output = "lights: " + ",".join([l for l in self.lights if l  in self.values and self.values[l]])
    return output

  def copy(self):
    cstate = LightState(self.values, self.generator)
    cstate.reset = self.reset
    return cstate

  def convert(self, values):
    return LightState(values, self.generator)

class LightWorld(FactorWorld):
  def __init__(self, **kwargs):
    size = kwargs.get('size', 1) or 1 # dont allow 0
    seed = kwargs.get('seed', 1)
    complexity = kwargs.get('complexity', 1)
    actions = []
    factors = []
    self.generator = LightGenerator()

    # Set the seed before generating in case we need to
    # regenerate to meet complexity requirements
    random.seed(seed)
    np.random.seed(seed)
    i = 0
    while self.generator.complexity < complexity:
      i += 1
      self.generator.generate(size,complexity)
      if i >= 100: raise Exception("Generator has run %i times, settings are likely invalid." % i)
    # Reset the seed afterwards so that we get genuinely
    # random state progressions afterward
    # random.seed() # no - 08/06/18
    for light in self.generator.lights:
      actions += [Action(name='T' + light, value=light)]
      factors += [Factor(name=light)]
    super(LightWorld, self).__init__(actions, factors)
    self.complexity = self.generator.complexity
    self.graph = self.generator.graph
    self.state = None

  def createState(self):
    self.state = LightState(generator=self.generator)
    return self.state

  def takeAction(self, state, action):
    pvalue = state[action.value]
    state.toggleLight(action.value)
    nvalue = state[action.value]
    reward = 0
    if nvalue and not pvalue:
      reward = action.idx ** 2
    if state.completed(): reward = 100
    return reward

  def getLegalActions(self, state):
    return self.actions

  def start(self, state): pass
  def finish(self, state): pass
