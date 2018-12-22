from panda3d.core import *
import geometry
import colliders

""" Object Request Data """

class OrqData(object):
  def __init__(self, *args, **kwargs):
    self.scale = 1
    self.offset = (0,0,0)
    self.color = None
    for k in kwargs:
      setattr(self, k, kwargs[k])
    self.vertices = args
    if not hasattr(self, 'name'):
      self.name = ''


class Anchors:
  DEFAULT = 0
  CENTER = 1

class WorldObject(object):
  def __init__(self, **kwargs):
    self.cCreator = kwargs.get('cCreator')
    for k in kwargs:
      setattr(self, k, kwargs[k])
    if not hasattr(self, 'name'):
      raise Exception("Each world object must have a name.")
    if not hasattr(self, 'parent'):
      self.parent = base.render
    if not hasattr(self, 'anchor'):
      self.anchor = Anchors.DEFAULT
    if not self.isComposite() and not hasattr(self, 'req'):
      raise Exception("No object request specified for object %s" % self.name)
    
    self.model = NodePath(self.name)
    if isinstance(self.parent, WorldObject):
      self.model.reparentTo(self.parent.model)
    else:
      self.model.reparentTo(self.parent)
    if not self.isComposite():
      self.gPath = self.gCreator(self.model, self.req)
    if self.useCollisions() and self.cCreator is not None:
      self.cPath = self.cCreator(self.model, self.req)

  def isComposite(self): return False
  def useCollisions(self): 
    return not self.isComposite()

  # When an object F collides INTO another object I
  # When a collision FROM object F (INTO object I) occurs,
  # INTO and FROM interactions begin. The interactions end
  # when the collision ends.
  def beginIntoInteraction(self): pass
  def endIntoInteraction(self): pass
  def beginFromInteraction(self): pass
  def endFromInteraction(self): pass

  def reparentTo(self, wo):
    if hasattr(wo, 'model'):
      self.model.reparentTo(wo.model)
    else:
      self.model.reparentTo(wo)

  def getCentroid(self):
    upper, lower = self.model.getTightBounds(self.parent)
    center = lower + (upper - lower) / 2
    return center

  def getPos(self):
    if self.anchor == Anchors.CENTER:
      return self.getCentroid()
    return self.model.getPos()
  
  def getH(self):
    return self.model.getH()
  
  def getHpr(self):
    return self.model.getHpr()

  def setPos(self, *args):
    if len(args) > 0 and hasattr(args[0], 'model'):
      args = [args[0].model] + list(args[1:])
    self.model.setPos(*args)
    if self.anchor == Anchors.CENTER:
      c = self.getCentroid()
      orig = self.model.getPos()
      offset = c - self.model.getPos()
      self.model.setPos(self.model, -offset)

  def setH(self, *args):
    if len(args) > 0 and hasattr(args[0], 'model'):
      args = [args[0].model] + list(args[1:])
    start = self.getCentroid()
    if self.anchor == Anchors.CENTER:
      offset = self.getCentroid() - self.model.getPos()
      self.model.setPos(offset)
    self.model.setH(*args)
    if self.anchor == Anchors.CENTER:
      offset = start - self.getCentroid()
      newPosition = self.model.getPos() + offset
      self.model.setPos(newPosition)

  def setHpr(self, *args):
    if len(args) > 0 and hasattr(args[0], 'model'):
      args = [args[0].model] + list(args[1:])
    self.model.setHpr(*args)

  def setX(self, *args):
    self.model.setX(*args)
  def setY(self, *args):
    self.model.setY(*args)
  def setZ(self, *args):
    self.model.setZ(*args)

  def setColor(self, *colorArgs):
    self.model.setColor(*colorArgs)
  
  def setHighlight(self, *highlight):
    comb = (Vec4(*highlight) + Vec4(*self.req.color)) / 2
    for i in range(len(comb)):
      if comb[i] > 1:
        comb[i] = 1
    self.model.setColor(*comb)

  def resetColor(self):
    self.model.setColor(*self.req.color)

class CompositeWO(WorldObject):
  def isComposite(self): return True
