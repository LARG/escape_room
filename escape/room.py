#!/usr/bin/env python

import sys, os, re, random
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
import numpy as np
from colors import *
from masks import *
import colliders
import geometry
import world_objects
from world_objects import WorldObject, OrqData, CompositeWO
from direct.gui.OnscreenText import OnscreenText
from puzzles.buttons import LightWorld as Puzzle, LightState as PuzzleState
import functools
import cfgescape as config

class Room(CompositeWO):
  def __init__(self, **kwargs):
    super(Room, self).__init__(**kwargs)
    self.seed = kwargs.get('seed', 1)
    self.walls = []
    self.cube = None
    self.panel = None
    self.doorway = None
    self.bounds = [Vec3(-10,-10,-10),Vec3(10,10,10)]
    
    wo_front = Wall(
      name='front',
      req=OrqData(
        scale=20,
        color=WALL_COLOR
      ),
      anchor=world_objects.Anchors.CENTER
    )
    self.walls.append(wo_front)
    wo_front.setPos(10,0,5)

    wo_left = Wall(
      name='left',
      req=OrqData(
        scale=20,
        color=WALL_COLOR
      ),
      anchor=world_objects.Anchors.CENTER
    )
    self.walls.append(wo_left)
    wo_left.setPos(0,10,5)
    wo_left.setH(-90)

    wo_right = Wall(
      name='right',
      req=OrqData(
        scale=20,
        color=WALL_COLOR
      ),
      anchor=world_objects.Anchors.CENTER
    )
    wo_right.setPos(0,-10,5)
    wo_right.setH(90)
    self.walls.append(wo_right)
    
    wo_back = Wall(
      name='back',
      req=OrqData(
        scale=20,
        color=WALL_COLOR
      ),
      anchor=world_objects.Anchors.CENTER
    )
    wo_back.setPos(-10,0,5)
    wo_back.setH(180)
    self.walls.append(wo_back)

    self.puzzle = Puzzle(
      seed=config.current.domain_seed,
      size=config.current.domain_size
    )
    self.cpanel = ControlPanel(parent=self, puzzle=self.puzzle)
    self.buttons = self.cpanel.buttons
    self.doorway = Doorway(parent=self)
    self.reset()

  def getState(self):
    return self.state

  def isComplete(self):
    if config is None: return # Fix random crashes on exit
    if config.current.enforce_puzzle:
      return self.doorway.exit.isPressed and self.state.completed()
    return self.doorway.exit.isPressed

  def inBounds(self, p):
    if p.x < self.bounds[0].x or p.x > self.bounds[1].x:
      return False
    if p.y < self.bounds[0].y or p.y > self.bounds[1].y:
      return False
    if p.z < self.bounds[0].z or p.z > self.bounds[1].z:
      return False
    return True

  def reset(self):
    self.state = self.puzzle.createState()
    self.cpanel.refresh()

class Wall(WorldObject):
  def __init__(self, **kwargs):
    super(Wall, self).__init__(
      gCreator=geometry.createSquare,
      cCreator=colliders.createBoxCollider,
      **kwargs
    )
    self.cPath.node().setCollideMask(BitMask32.allOff())
    self.cPath.node().setIntoCollideMask(WALL_MASK)
    self.gPath.setTwoSided(True)

class Doorway(CompositeWO):
  def __init__(self, **kwargs):
    self.door = None
    self.knob = None
    self.exit = None
    super(Doorway, self).__init__(
      name='doorway',
      **kwargs
    )

    self.model.setPos(9.5,9,-4)

    self.hinge = WorldObject(
      name='hinge',
      req=OrqData(
        color=DOOR_KNOB_COLOR,
        dx=0.1,
        dy=0.1
      ),
      gCreator=geometry.createCube
    )
    self.hinge.reparentTo(self)
    self.hinge.setPos(0,0,3)
    
    req_door = OrqData(
      color=DOOR_WOOD_COLOR,
      dz=10,
      dy=5,
      dx=0.2
    )
    wo_door = WorldObject(
      name='door',
      req=req_door,
      gCreator=geometry.createCube
    )
    wo_door.reparentTo(self.hinge)
    wo_door.setPos(0,-5,-5)
    #wo_door.setHpr(self.hinge, -45, 0, 0)
    self.door = wo_door

    req_knob = OrqData(
      color=DOOR_KNOB_COLOR,
      scale=0.3
    )
    wo_knob = Button(
      name='knob',
      req=req_knob
    )
    wo_knob.reparentTo(self.door)
    wo_knob.setPos(-0.2,0,5) #   9.5, -5, 0)
    self.knob = wo_knob

    req_exit = OrqData(
      color=(0,0.2,0.8,0),
      dx=config.current.exit_size,
      dy=config.current.exit_size,
      dz=0.1
    )
    wo_exit = Region(
      name='exit_region',
      req=req_exit
    )
    wo_exit.reparentTo(self)
    wo_exit.setH(180)
    wo_exit.setPos(0,0,-1)
    self.exit = wo_exit

  def taskOpen(self):
    def handler(task):
      h = self.door.model.getH()
      self.door.model.setH(h - 2)
      if h <= 90:
        return task.done
      return task.again
    t = taskMgr.doMethodLater(
      0.01,
      handler, 
      'doorway-open-action'
    )
    return t
  
  def taskClose(self):
    def handler(task):
      h = self.door.model.getH()
      self.door.model.setH(h + 2)
      if h >= 180:
        return task.done
      return task.again
    t = taskMgr.doMethodLater(
      0.01,
      handler, 
      'doorway-open-action'
    )
    return t


''' A standard Toggle button. '''
class Button(WorldObject):
  def __init__(self, **kwargs):
    kwargs['gCreator'] = kwargs.get('gCreator', geometry.createCube)
    kwargs['cCreator'] = kwargs.get('cCreator', colliders.createBoxCollider)
    super(Button, self).__init__(**kwargs)

    self.mask = kwargs.get('mask', BUTTON_MASK)
    self.onPressed = kwargs.get('onPressed')
    self.onReleased = kwargs.get('onReleased')
    self.onPressing = kwargs.get('onPressing')
    self.onReleasing = kwargs.get('onReleasing')
    self.factor = kwargs.get('factor')
    self.isPressed = False
    self.cPath.node().setCollideMask(BitMask32.allOff())
    self.cPath.node().setIntoCollideMask(self.mask)
    self.color = Vec4(self.req.color) * 0.6
    self.highlight = Vec4(self.req.color) * 2.0
    base.register(self)
    self.resetColor()

  #def setPos(self, *args):
    #p = np.array(args)
    #c = self.getCentroid()
    #pc = p - c
    #print p, c, pc
    #super(Button, self).setPos(*pc)

  def resetColor(self):
    self.model.setColor(*self.color)

  def setHighlight(self):
    self.model.setColor(*self.highlight)

  def setPressed(self):
    if self.onPressed:
      self.onPressed()
    self.setHighlight()
    self.isPressed = True

  def setReleased(self):
    if self.onReleased:
      self.onReleased()
    self.resetColor()
    self.isPressed = False

  def beginIntoInteraction(self):
    if self.isPressed:
      if self.onReleasing:
        self.onReleasing()
      else:
        self.setReleased()
    else:
      if self.onPressing:
        self.onPressing()
      else:
        self.setPressed()

  def endIntoInteraction(self): pass

class ControlPanel(CompositeWO):
  def __init__(self, **kwargs):
    self.puzzle = kwargs.get('puzzle')
    self.buttons = []
    self.plate = None
    super(ControlPanel, self).__init__(
      name='control-panel',
      **kwargs
    )

    buttons = self.buttons
    x, y, z = 9, 9, 0
    positions = [
      [0, y, z, -90], #Left
      [-x, 0, z, 180], # Rear
      [x, -5, z, 0], # Front
      [0, -y, z, 90], # Right
    ]
    #random.shuffle(positions)
    for f in self.puzzle.factors:
      button = Button(
        name='Button_' + f.id,
        factor=f,
        req = OrqData(
          color=COLOR_SEQUENCE[f.idx],
          scale=config.current.button_size,
          dx=0.1
        ),
        onPressing=functools.partial(self.executeToggle, f),
        onReleasing=functools.partial(self.executeToggle, f),
        anchor=world_objects.Anchors.CENTER
      )
      z += config.current.button_size / 4
      assert len(positions) > f.idx
      position = positions[f.idx]
      buttons.append(button)
      button.reparentTo(self)
      button.setPos(*position[:3])
      button.setH(position[3])
      self.updating = False
    
    self.setPos(self, 0, 0, -1)

  def refresh(self):
    state = self.parent.state
    for button in self.buttons:
      f = button.factor
      if state[f.id]:
        button.setPressed()
      else:
        button.setReleased()

  def executeToggle(self, f):
    if self.updating: return
    self.updating = True
    puzzle = self.parent.puzzle
    state = self.parent.state
    action = puzzle.actions[f.idx]
    puzzle.takeAction(state, action)
    self.refresh()
    self.updating = False

class Plane(WorldObject):
  def __init__(self, **kwargs):
    super(Plane, self).__init__(
      gCreator=geometry.createSquare,
      cCreator=colliders.createBoxCollider,
      **kwargs
    )
    self.cPath.node().setCollideMask(BitMask32.allOff())

class Region(Button):
  def __init__(self, **kwargs):
    super(Region, self).__init__(mask=REGION_MASK, **kwargs)
  
  def beginIntoInteraction(self):
    if self.onPressing:
      self.onPressing()
    else:
      self.setPressed()

  def endIntoInteraction(self):
    if self.onReleasing:
      self.onReleasing()
    else:
      self.setReleased()
