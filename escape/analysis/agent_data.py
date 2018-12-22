#!/usr/bin/env python

import sys, os, re, math
import numpy as np

class AgentData(object):
  IntervalOffset = 0
  def __init__(self, name, display, color, style, marker, stat, stddev, **kwargs):
    self.name = name
    self.display = display
    self.color = color
    self.style = style
    self.marker = marker
    self.stat = stat
    self.stddev = stddev
    self.interval_offset = AgentData.IntervalOffset
    self.result = None
    self.max_complexity = kwargs.get('max_complexity')
    AgentData.IntervalOffset += 200

class Bounds(object):
  def __init__(self):
    self.xmin, self.xmax, self.ymin, self.ymax = None, None, None, None
    self.initialized = False

  def update(self, xs, ys):
    if not self.initialized:
      self.xmin, self.xmax = min(xs), max(xs)
      self.ymin, self.ymax = min(ys), max(ys)
      self.initialized = True
    else:
      self.xmin, self.xmax, = min(self.xmin, min(xs)), max(self.xmax, max(xs)) 
      self.ymin, self.ymax = min(self.ymin, min(ys)), max(self.ymax, max(ys))

  def adjusted(self,xmin=False,xmax=True,ymin=True,ymax=True):
    xrange, yrange = float(self.xmax - self.xmin), float(self.ymax - self.ymin)
    if xmin: self.xmin -= xrange/20
    if xmax: self.xmax += xrange/20
    if ymin: self.ymin -= yrange/20
    if ymax: self.ymax += yrange/20
    return (self.xmin, self.xmax, self.ymin, self.ymax)

  def __str__(self):
    return "X: [%s,%s], Y:[%s,%s]" % (self.xmin, self.xmax, self.ymin, self.ymax)

def load_data(metric, keep=None, skip=None):
  agents = [
    AgentData('dqn', 'DQN', 'red', '-', '*', lambda x: getattr(x, metric), lambda x: getattr(x, metric+'_stddev')),
    AgentData('ddpg', 'DDPG', 'blue', '-', r'$\bowtie$', lambda x: getattr(x, metric), lambda x: getattr(x, metric+'_stddev')),
    AgentData('sarsa', 'SARSA', 'green', ':', r'$\clubsuit$', lambda x: getattr(x, metric), lambda x: getattr(x, metric+'_stddev')),
    #AgentData('naf', 'NAF', 'orange', ':', r'$\clubsuit$', lambda x: getattr(x, metric), lambda x: getattr(x, metric+'_stddev')),
    #AgentData('cem', 'CEM', 'purple', ':', r'$\clubsuit$', lambda x: getattr(x, metric), lambda x: getattr(x, metric+'_stddev')),
  ]
  if skip is None: skip = []
  if keep is None: keep = { a.name for a in agents }
  agents = [ a for a in agents if a.name in keep and a.name not in skip ]
  return agents
