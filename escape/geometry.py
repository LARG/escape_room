from shapes.polyhedra import Cube, BoundedPlane
from panda3d.core import *

def createSquare(model, req):
  format = GeomVertexFormat.getV3n3c4()
  vertexData = GeomVertexData(req.name, format, Geom.UHStatic)
  vertexData.setNumRows(4)
    
  vwriter = GeomVertexWriter(vertexData, 'vertex')
  nwriter = GeomVertexWriter(vertexData, 'normal')
  cwriter = GeomVertexWriter(vertexData, 'color')

  vertices =  [Vec3(c) for c in BoundedPlane.corners]
  vertices = [v * req.scale for v in vertices]
  vertices = [v + req.offset for v in vertices]
  for v in vertices:
    vwriter.addData3f(*v)

  t = [v for v in vertices[:3]]
  d = (t[1] - t[0]).cross(t[2] - t[1])
  normal = d / d.length()
   
  for i in range(len(vertices)):
    nwriter.addData3f(*normal)
   
  for i in range(len(vertices)):
    cwriter.addData4f(*req.color)
    
  primitive = GeomTriangles(Geom.UHStatic)
  for t in BoundedPlane.triangles:
    primitive.addVertices(*t)

  geom = Geom(vertexData)
  geom.addPrimitive(primitive)

  node = GeomNode('wall gnode')
  node.addGeom(geom)
  return model.attachNewNode(node)
  
def createCube(model, req):
  format = GeomVertexFormat.getV3n3c4()
  vertexData = GeomVertexData(req.name, format, Geom.UHStatic)

  vertexData.setNumRows(24)

  vwriter = GeomVertexWriter(vertexData, 'vertex')
  nwriter = GeomVertexWriter(vertexData, 'normal')
  cwriter = GeomVertexWriter(vertexData, 'color')

  corners = [Vec3(*c) for c in Cube.corners]

  scale = req.scale if hasattr(req, 'scale') else 1.0
  translation = req.translation if hasattr(req, 'translation') else (0, 0, 0)

  if hasattr(req, 'corners'):
    assert len(req.corners) == len(corners)
    corners = req.corners[:]
  def dscale(attr, index):
    if hasattr(req, attr):
      for i in range(len(corners)):
        corners[i][index] *= getattr(req, attr)
  def translate(attr, index):
    if hasattr(req, attr):
      for i in range(len(corners)):
        corners[i][index] += getattr(req, offset)
  for attr in ['dx', 'width']:
    dscale(attr, 0)
  for attr in ['dy', 'length']:
    dscale(attr, 1)
  for attr in ['dz', 'height']:
    dscale(attr, 2)
  for i in range(len(corners)):
    corners[i] *= scale
  for i in range(len(corners)):
    corners[i] += Vec3(*translation)

  for c in corners:
    for i in range(3):
      vwriter.addData3f(*c)

  for n in Cube.normals: 
    nwriter.addData3f(*n)

  for i in range(24):
    cwriter.addData4f(*req.color)

  # Store the triangles, counter clockwise from front
  primitive = GeomTriangles(Geom.UHStatic)
  for t in Cube.triangles:
    primitive.addVertices(*t)

  geom = Geom(vertexData)
  geom.addPrimitive(primitive)

  node = GeomNode(req.name)
  node.addGeom(geom)
  return model.attachNewNode(node)

