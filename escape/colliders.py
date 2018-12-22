from panda3d.core import *

def createSphereCollider(model, req):
  bounds = model.getBounds()
  solid = CollisionSphere(bounds.getCenter(), bounds.getRadius())
  cn = CollisionNode('solid')
  cn.addSolid(solid)
  collider = model.attachNewNode(cn)
  return collider

def createBoxCollider(model, req):
  bounds = model.getTightBounds()
  for i in range(3):
    if bounds[0][i] == bounds[1][i]:
      bounds[0][i] -= 1.0
      bounds[1][i] += 1.0
  solid = CollisionBox(*bounds)
  cn = CollisionNode('solid')
  cn.addSolid(solid)
  collider = model.attachNewNode(cn)
  return collider
