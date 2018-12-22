#!/usr/bin/env python

import sys, random
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from player import Player
from room import Room
from masks import *
import cfgescape as config

class EscapeRoom(ShowBase):
  def __init__(self, **kwargs):
    if not config.current.enable_interface:
      loadPrcFileData('', 'window-type none')
    ShowBase.__init__(self)
   
    self.seed = kwargs.get('seed', 1)
    self.callback = kwargs.get('callback', None)

    self.objects = {}
    self.into_interacting = {}
    self.from_interacting = {}
  
    self.disableMouse()
    self.initCollision()
    self.initRoom()
    self.initLighting()
    self.initPlayer()

    # Handlers
    self.accept("escape", sys.exit)
    self.taskMgr.add(self.interactionUpdate, 'interaction-task')
    if self.callback:
      period = config.current.temporal_quantum / config.current.time_coefficient
      self.taskMgr.doMethodLater(0, self.executeCallback, 'callback-task')

  def initRoom(self):
    self.room = Room(name='main', seed=self.seed)
  
  def initPlayer(self):
    self.player = Player(self.room)

  def initLighting(self):
    # Add a simple point light
    plight = PointLight('plight')
    plight.setColor(VBase4(0.5, 0.5, 0.5, 0.7))
    plight.setAttenuation(Point3(0, 0, 0.5))
    plnp = self.render.attachNewNode(plight)
    plnp.setPos(5, 0, 1)
    self.render.setLight(plnp)
    # Add an ambient light
    alight = AmbientLight('alight')
    alight.setColor(VBase4(0.6, 0.6, 0.6, 0.5))
    alnp = self.render.attachNewNode(alight)
    self.render.setLight(alnp)
    
    # Now we create a directional light. Directional lights add shading from a
    # given angle. This is good for far away sources like the sun
    dlight = render.attachNewNode(
      DirectionalLight("directionalLight")
    )
    dlight.node().setColor((.35, .35, .35, 1))
    # The direction of a directional light is set as a 3D vector
    dlight.node().setDirection(LVector3(1,1,-1))
    # These settings are necessary for shadows to work correctly
    dlight.setPos(-10,-10,10)
    dlens = dlight.node().getLens()
    dlens.setFilmSize(41, 21)
    dlens.setNearFar(50, 75)
    dlight.node().showFrustum()
    render.setLight(dlight)

  def initCollision(self):
    """ create the collision system """
    self.cTrav = CollisionTraverser()
    self.pusher = CollisionHandlerPusher()
    self.cQueue = CollisionHandlerQueue()

  def executeCallback(self, task):
    result = self.callback(self)
    if result:
      return task.again
    return task.done

  def exit(self):
    def exitHandler(task):
      sys.exit()
      return task.done
    self.taskMgr.doMethodLater(0, exitHandler, 'exit-task')

  def interactionUpdate(self, task):
    self.cQueue.sortEntries()
    n = self.cQueue.getNumEntries()

    # Process INTO interactions
    into_interacting = {}
    for i in range(n):
      entry = self.cQueue.getEntry(i)
      npInto = entry.getIntoNodePath()
      woInto = self.objects.get(npInto, None)
      if woInto is not None and npInto not in into_interacting:
        if npInto not in self.into_interacting:
          woInto.beginIntoInteraction()
        into_interacting[npInto] = True
    for np in self.into_interacting:
      if np not in into_interacting:
        wo = self.objects[np]
        wo.endIntoInteraction()
    self.into_interacting = into_interacting
    
    # Process FROM interactions
    from_interacting = {}
    for i in range(n):
      entry = self.cQueue.getEntry(i)
      npFrom = entry.getFromNodePath()
      woFrom = self.objects.get(npFrom, None)
      if woFrom is not None and npFrom not in from_interacting:
        if npFrom not in self.from_interacting:
          woFrom.beginFromInteraction()
        from_interacting[npFrom] = True

    for np in self.from_interacting:
      if np not in from_interacting:
        wo = self.objects[np]
        wo.endFromInteraction()
    self.from_interacting = from_interacting

    return task.cont

  def register(self, worldObject):
    self.objects[worldObject.cPath] = worldObject
