import sys, os, re, math
import point2d
from panda3d.core import Vec3
import numpy as np
from world_objects import WorldObject

class ActionController(object):
  def __init__(self, **kwargs):
    self.state = 0
    self.player = kwargs.get('player')
    self.subs = kwargs.get('subcontrollers', [])
    self.current_action = None
    self.previous_action = None

  def processFrame(self, **kwargs):
    for c in self.subs:
      c.processFrame(**kwargs)

  def getAction(self):
    for c in self.subs:
      if not c.isComplete():
        a = c.getAction()
        self.previous_action = self.current_action
        self.current_action = c.getAction()
        return self.current_action

  def isComplete(self):
    for c in self.subs:
      if not c.isComplete():
        return False
    return True

class PuzzleController(ActionController):
  def __init__(self, **kwargs):
    super(PuzzleController, self).__init__(**kwargs)
    self.puzzle = self.player.room.puzzle
    self.goal = 'L' + kwargs.get('button')
    self.graph = self.puzzle.generator.graph
    self.exit_controller = ButtonPressController(target=self.player.room.doorway.exit, **kwargs)
    for light in self.puzzle.generator.lights:
      factor = self.puzzle.flookup[light]
      button = self.player.room.buttons[factor.idx]
      self.subs.append(ButtonPressController(target=button, **kwargs))
  
  def processFrame(self, **kwargs):
    self.state = self.player.room.getState()
    if self.goal != 'Lexit':
      self.plan = self.graph.getPlan(self.state, self.goal)
      self.next_id = self.plan[0] if len(self.plan) > 0 else None
    for c in self.subs:
      c.processFrame(**kwargs)
    self.exit_controller.processFrame(**kwargs)

  def getAction(self):
    if self.goal == 'Lexit':
      controller = self.exit_controller
    else:
      factor = self.puzzle.flookup[self.next_id]
      controller = self.subs[factor.idx]
    return controller.getAction()

  def isComplete(self):
    if self.goal == 'Lexit':
      return self.exit_controller.isComplete()
    else:
      return self.next_id is None

class ButtonPressController(ActionController):
  def __init__(self, **kwargs):
    super(ButtonPressController, self).__init__(**kwargs)
    self.subs.append(ViewController(**kwargs))
    self.subs.append(ApproachController(**kwargs))

class InteractionController(ActionController):
  def __init__(self, **kwargs):
    super(InteractionController, self).__init__(**kwargs)
    self.target = kwargs.get('target')
    self.p_target = None
    self.p_player = None
    self.o_player = None
    self.previous_bearing = None
    self.current_bearing = None
    self.previous_distance = None
    self.current_distance = None

  def processFrame(self, **kwargs):
    self.p_target = point2d.Point2D(p=self.target.getCentroid())
    self.p_player = point2d.Point2D(p=self.player.getCentroid())
    self.o_player = self.player.getH()
    self.previous_bearing = self.current_bearing
    self.current_bearing = point2d.toDegrees(self.p_player.getBearingTo(self.p_target, point2d.toRadians(self.o_player)))
    self.previous_distance = self.current_distance
    self.current_distance = self.p_player.getDistanceTo(self.p_target)

class ViewController(InteractionController):
  def getAction(self):
    assert isinstance(self.target, WorldObject)
    if np.sign(self.current_bearing) > 0:
      return 'look-L'
    else:
      return 'look-R'
  
  def isComplete(self):
    # If we're close to the target bearing then stop
    if abs(self.current_bearing) < 5:
      return True
    # We'll be checking switches in bearing sign to 
    # see if we're close, but if we're facing backward 
    # then keep moving.
    if abs(self.current_bearing) > 90:
      return False
    if self.previous_bearing is None:
      return False
    # If movement changes directions then we're about 
    # as close as we can get
    if np.sign(self.previous_bearing) != np.sign(self.current_bearing):
      return True
    return False

class ApproachController(InteractionController):
  def getAction(self):
    return 'move-F'

  def isComplete(self):
    if self.current_distance is None:
      return False
    return self.current_distance < 1
