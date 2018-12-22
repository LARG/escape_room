#!/usr/bin/env python

import sys, os, locale, time
import numpy as np
import random
os.environ['GLOG_minloglevel'] ='2'
locale.setlocale(locale.LC_ALL, 'en_US.utf8')
import panda3d.core

from app import EscapeRoom
from world import World
import cfgescape as config
import thread
import agents
import importlib

from rl.callbacks import Callback
class ExperimentCallback(Callback):
  def __init__(self, *args, **kwargs):
    self.domain = kwargs.get('domain')
    del kwargs['domain']
    super(ExperimentCallback, self).__init__(*args, **kwargs)
    self.treward = 0
    self.ereward = 0
    self.esteps = 0
    self.tsteps = 0
    self.episode = 0
    self.last_reward = None
    self.last_action = None
    self.headers = ['tsteps', 'treward', 'esteps', 'ereward', 'episode']
    pieces = map(str, [self.tsteps, self.treward, self.esteps, self.ereward])
    if config.current.exp_mode == 'Data':
      with open(config.current.output_path, 'w') as f:
        f.write('"' + '","'.join(self.headers) + '"' + "\n")

  def on_episode_begin(self, episode, logs={}):
    pass

  def on_episode_end(self, episode, logs={}):
    if config.current.exp_mode == 'Debug' or config.current.exp_mode == 'Verbose':
      self.print_status()
    if config.current.exp_mode == 'Data':
      with open(config.current.output_path, 'a') as f:
        self.print_data(f)
    elif config.current.exp_mode == 'Verbose':
      self.print_data()
    self.ereward = 0
    self.esteps = 0
    self.episode += 1

  def on_step_end(self, step, logs={}):
    self.ereward += logs['reward']
    self.treward += logs['reward']
    self.esteps += 1
    self.tsteps += 1
    self.last_reward = logs['reward']
    self.last_action = self.domain.world.getActions()[logs['action']]
    if config.current.exp_mode == 'Verbose':
      print self.last_action
      self.print_data()

  def print_data(self, outfile=None):
    pieces = map(str, [getattr(self, h) for h in self.headers])
    s = '"%s"' % '","'.join(pieces) 
    if outfile:
      outfile.write(s + "\n")
    else:
      print s

  def print_status(self):
    def lpad(s,n):
      if len(s) < n:
        s = ' ' * (n - len(s)) + s
      return s
    def rpad(s,n):
      if len(s) < n:
        s = s + ' ' * (n - len(s))
      return s
    length = 15
    if self.last_reward is None:
      r_str = 'INIT'
    else:
      r_str = rpad(('SUCCESS: ' if self.last_reward > 0 else 'FAILURE: ') + '(%3.f)' % self.last_reward, 20)
    tstep_str = lpad('%06i' % self.tsteps, 8)
    treward_str = lpad('%06i' % self.treward, 8)
    estep_str = lpad(str(self.esteps), 5)
    ereward_str = lpad('%2.f' % self.ereward, 5)
    t_str = lpad('total: %s' % (tstep_str), length)
    e_str = rpad('episode: %s, %s' % (estep_str, ereward_str), length)
    a_str = rpad('action: %s' % self.last_action, length)
    print '%s %s     %s %s' % (r_str, t_str, e_str, a_str)

def run_agent(domain):
  t1 = time.time()
  callback = ExperimentCallback(domain=domain)
  interval = 100
  iterations = int(config.current.exp_timesteps / interval)
  if config.current.enable_meta_actions:
    random.seed()
    np.random.seed()
    domain.agent.fit(domain.world, nb_steps=config.current.exp_timesteps, callbacks=[callback], visualize=False, verbose=0)
    return
  for i in range(iterations):
    if config.current.exp_mode == 'Verbose':
      print 'Fitting'
    domain.agent.fit(domain.world, nb_steps=interval, visualize=False, verbose=0)
    if config.current.exp_mode == 'Verbose':
      print 'Testing'
    domain.agent.test(domain.world, nb_episodes=1, callbacks=[callback], verbose=0)
    if config.current.exp_mode == 'Verbose':
      print 'Iteration Complete'
  t2 = time.time()
  print '%2.2f seconds' % (t2 - t1)

global domain
domain = None

class Domain:
  def __init__(self, app):
    self.world = World(app.player)
    agent_type = importlib.import_module('agents.%s' % config.current.agent_type)
    self.agent = agent_type.create(self.world)
    self.app = app

def log(state, action, nstate, reward):
  def lpad(s,n):
    return ' ' * (n - len(str(s))) + str(s)
  posestr = ','.join(['%2.1f' % s for s in state[:3]])
  print 'took action: %s, got pose: %s, got reward: %s' % (lpad(action, 20), lpad(posestr, 20), lpad(reward, 10))

# TODO: This function doesn't work because the agent constructor doesn't fully initialize the agent.
def agent_processor(app):
  global domain
  if domain is None:
    domain = Domain(app)
  state = domain.world.getState()
  action = domain.agent.forward(state)
  nstate, reward = domain.world.takeAction(action)
  domain.agent.backward(reward, False)
  log(state, action, nstate, reward)

def agent_processor(app):
  domain = Domain(app)
  run_agent(domain)
  app.exit()

def manual_processor(app):
  domain = Domain(app)
  while True:
    time.sleep(0.1)
    if domain.world.atGoal():
      domain.world.reset()
      print 'Goal Reached!'

def handler(app):
  if config.current.exp_mode != 'Manual':
    thread.start_new_thread(agent_processor, (app,))
  else:
    thread.start_new_thread(manual_processor, (app,))
  return False

def main():
  app = EscapeRoom(callback=handler, seed=2)
  if config.current.exp_mode == 'Data':
    print 'Performing data experiment:',config.current.description
  app.run()

if __name__ == '__main__':
  main()
