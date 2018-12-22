import functools, threading
import numpy as np
import cfgescape as config

class World(object):
  class Space(object): pass
  class Info(object):
    def items(self): return []

  def __init__(self, player):
    self.player = player

    self.action_space = self.Space()
    self.action_space.n = len(self.getActions())
    self.action_space.sample = self.sampleActionSpace
    self.action_space.shape = (self.action_space.n,)

    self.observation_space = self.Space()
    self.observation_space.shape = (len(self.getState()),)
    self.episode_steps = 0
    self.total_steps = 0
    self.deltas = []

  def movementStopped(self, delta):
    self.deltas.append(delta)
    if len(self.deltas) > 10:
      self.deltas.pop(0)
    if len(self.deltas) < 10:
      return False
    if sum(self.deltas) < 0.001:
      return True
    return False

  'Open AI Gym Environment Implementation'

  def step(self, action):
    import numpy as np
    state = self.getState()
    nstate, reward = self.takeAction(action)
    done = False
    info = {}
    self.episode_steps += 1
    self.total_steps += 1
    delta = np.linalg.norm(nstate - state)
    if self.atGoal():
      self.restart_episode()
      reward = 100
      done = True
    elif self.episode_steps > config.current.max_episode_steps:
      self.restart_episode()
      done = True
    #elif self.movementStopped(delta):
      #self.restart_episode()
      #reward = -100
      #done = True
    elif not self.isValid():
      self.player.center()
      #self.restart_episode()
      #done = True
      #reward = -100
    #if self.total_steps >= config.current.exp_timesteps:
      #done = True
    return nstate, reward, done, info

  def restart_episode(self):
    self.episode_steps = 0
    self.deltas = []
    
  def isValid(self):
    if not self.player.inRoom(): 
      return False
    return True

  def reset(self):
    self.player.reset()
    self.restart_episode()
    return np.array(self.getState())

  def render(self, *args, **kwargs): pass
  def close(self): pass
  def seed(self, s): pass

  def sampleActionSpace(self):
    return random.choice(self.getActions())

  'World Implementation'

  def getActions(self):
    return self.player.getActions()

  def getState(self):
    return np.array(self.player.getState())

  def atGoal(self):
    return self.player.atGoal()

  def takeAction(self, action):
    if type(action) is int or type(action) is np.int64:
      action = self.getActions()[action]
    event = threading.Event()
    def handler(): event.set()
    state = self.getState()
    self.player.takeAction(action, config.current.temporal_quantum, callback=handler)
    event.wait()
    nstate = self.getState()
    reward = -1
    if action.startswith('meta'):
      reward = -1 * self.player.meta_action_count
    elif self.player.isWaitAction(action):
      reward = 0
    if self.atGoal():
      if config.current.exp_mode == 'Verbose':
        print 'Goal Reached!'
      reward += 100
    return nstate, reward
