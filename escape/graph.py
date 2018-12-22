
class Graph(object):
  def __init__(self):
    self.nodes = {}
    self.roots = []

  def build(self, parents):
    self.simple = True
    self.nodes = {}
    for n in parents:
      self.nodes[n] = GraphNode(n)
    for n in parents:
      cnode = self.nodes[n]
      for p in parents[n]:
        pnode = self.nodes[p]
        pnode.children[n] = cnode
        cnode.parents[p] = pnode
    for n in self.nodes.values():
      if n.getDepth() == 0:
        self.roots.append(n)

  def topologicalFactors(self):
    nodes = sorted(self.nodes.values(), key=lambda x: x.getDepth())
    return [n.factor for n in nodes]

  def getPlan(self, state, goal):
    plan = []
    checks = [goal]
    while len(checks) > 0:
      n = checks.pop(0)
      if state[n] is True: continue
      plan.insert(0, n)
      parents = self.nodes[n].parents
      checks += parents.keys()
    return plan

class GraphNode(object):
  def __init__(self, factor):
    super(GraphNode, self).__init__()
    self.factor = factor
    self.parents = {}
    self.children = {}
    self.depth = None

  def getDepth(self, seen=None):
    if self.depth != None: return self.depth
    if seen == None: seen = set()
    if self in seen:
      self.depth = -1
      return self.depth
    seen.add(self)
    if self.depth == None:
      if len(self.parents) == 0:
        self.depth = 0
      else:
        self.depth = max(p.getDepth(seen) for p in self.parents.values()) + 1
    return self.depth
