import math

EPSILON = 0.00001

def toRadians(deg):
  return deg / 180 * math.pi

def toDegrees(rad):
  return rad / math.pi * 180

def normalizeAngle(angle):
  n = angle % (math.pi * 2)
  if n > math.pi:
    n -= math.pi * 2
  if n < -math.pi:
    n += math.pi * 2
  return n

class Point2D(object):

  def __init__(self, x=None, y=None, r=None, angle=None, p=None):
    if x != None and y != None:
      pass 
    elif p:
      x,y = p.x,p.y
    elif angle is not None and r is not None:
      x = math.cos(angle) * r
      y = math.sin(angle) * r
    elif x is None and y is None:
      x = y = 0.0

    self.x = float(x)
    self.y = float(y)

  def getDistanceTo(self, p):
    """Returns the distance to Point2D p."""
    return (self - p).getMagnitude()

  def getBearingTo(self, p, o):
    """Returns the bearing (angle) to Point2D p, and subtracts offset o."""
    relPoint = Point2D(p.x - self.x, p.y - self.y)
    absDir = relPoint.getDirection()
    return normalizeAngle(absDir - o)

  def getDirection(self):
    return math.atan2(self.y, self.x)

  def getMagnitude(self):
    """Returns the magnitude of this vector (the normal)."""
    return math.sqrt(self.x * self.x + self.y * self.y)

  def globalToRelative(self, origin, ang):
    retVal = Point2D(self.x,self.y)
    retVal -= origin
    return retVal.rotate(-ang)

  def relativeToGlobal(self, origin, ang):
    retVal = Point2D(self.x, self.y)
    retVal = retVal.rotate(ang)
    retVal += origin
    return retVal

  def rotate(self, ang):
    mag = self.getMagnitude()
    newDir = self.getDirection() + ang
    self.x = mag * math.cos(newDir)
    self.y = mag * math.sin(newDir)
    return self

  # http://stackoverflow.com/questions/328107/how-can-you-determine-a-point-is-between-two-other-points-on-a-line-segment
  def isBetween(self, a, b):
    crossproduct = (self.y - a.y) * (b.x - a.x) - (self.x - a.x) * (b.y - a.y)
    if abs(crossproduct) > EPSILON: return False   # (or != 0 if using integers)

    dotproduct = (self.x - a.x) * (b.x - a.x) + (self.y - a.y)*(b.y - a.y)
    if dotproduct < 0 : return False

    squaredlengthba = (b.x - a.x)*(b.x - a.x) + (b.y - a.y)*(b.y - a.y)
    if dotproduct > squaredlengthba: return False

    return True

  def __add__(self, other):
    return Point2D(self.x + other.x, self.y + other.y)

  def __sub__(self, other):
    return Point2D(self.x - other.x, self.y - other.y)

  def __mul__(self, other):
    if type(other) == Point2D:
      return Point2D(self.x * other.x, self.y * other.y)
    return Point2D(self.x * other, self.y * other)

  def __div__(self, other):
    if not type(other) == float and not type(other) == int:
      raise Exception("Invalid point divisor:" + str(other))
    return Point2D(self.x / other, self.y / other)

  def __str__(self):
    return "%2.2f,%2.2f" % (self.x,self.y)


class Line2D(object):
  def __init__(self, loc=None, angle=None, loc1=None, loc2=None):
    if type(loc) not in (Point2D,type(None)):
      loc = Point2D(loc.x, loc.y)
    self.loc = loc
    self.angle = angle
    self.loc1 = loc1
    self.loc2 = loc2

    if self.loc is not None and self.angle is not None:
      self.loc1 = self.loc
      self.loc2 = self.loc1 + Point2D(r=100,angle=angle)

    if self.loc1 is not None and self.loc2 is not None:
      self.m_a = 1.0
      temp = self.loc2.x - self.loc1.x
      if abs(temp) < EPSILON:
        self.m_a = 0.0
        self.m_b = 1.0
      else:
        self.m_a = 1.0
        self.m_b = -(self.loc2.y - self.loc1.y) / temp
    self.m_c = -self.m_a * self.loc2.y - self.m_b * self.loc2.x
    self.center = (self.loc1 + self.loc2) / 2
    denom = math.sqrt(self.m_a**2 + self.m_b**2)
    self.m_a /= denom
    self.m_b /= denom
    self.m_c /= denom

  def getXGivenY(self, y):
    if self.m_b == 0: 
      return self.center.x / 2
    return -(self.m_a*y+self.m_c)/self.m_b

  def getYGivenX(self, x):
    if self.m_a == 0: return 0
    return -(self.m_b * x + self.m_c) / self.m_a

  def isParallelTo(self, line):
    if self.m_a == 0 or line.m_a == 0:
      return self.m_b == line.m_b
    return abs(self.m_b / self.m_a - line.m_b / line.m_a) <= EPSILON

  def getIntersection(self, line):
    if self.isParallelTo(line): return Point2D()
    if self.m_a == 0:
      x = -self.m_c/self.m_b
      return Point2D(x, line.getYGivenX(x))
    elif line.m_a == 0:
      x = -line.m_c/line.m_b
      return Point2D(x, self.getYGivenX(x))
    else:
      x = (self.m_a * line.m_c - line.m_a * self.m_c) / (line.m_a * self.m_b - self.m_a * line.m_b);
      return Point2D(x, self.getYGivenX(x))

  def __str__(self):
    return "a: %2.2f, b: %2.2f, c: %2.2f" % (self.m_a, self.m_b, self.m_c)

class LineSegment(Line2D):
  def __init__(self, x1, y1, x2, y2):
    super(LineSegment, self).__init__(loc1=Point2D(x1,y1), loc2=Point2D(x2,y2))
    self.start = self.loc1
    self.end = self.loc2

  def intersects(self, other):
    i = self.getIntersection(other)
    if i.isBetween(self.start,self.end) and i.isBetween(other.start,other.end):
      return True
    return False

  def length(self):
    return (self.end - self.start).getMagnitude()

  def getPointOnSegmentClosestTo(self, point):
    l2 = self.length()**2
    vec = (point - self.start) * (self.end - self.start)
    dp = vec.x + vec.y
    t = dp / l2
    if dp < 0: return self.start
    elif t > 1: return self.end
    proj = (self.end - self.start)
    proj.x *= t
    proj.y *= t
    proj = proj + self.start
    return proj

  def getDistanceTo(self, point):
    closest = self.getPointOnSegmentClosestTo(point)
    return (point - closest).getMagnitude()

  def __str__(self):
    return "%2.f,%2.f --> %2.f,%2.f" % (self.start.x, self.start.y, self.end.x, self.end.y)
