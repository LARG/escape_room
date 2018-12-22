import sys, os, re, time
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
from direct.gui.OnscreenText import OnscreenText
from masks import *
import geometry
import colliders
import world_objects
import cfgescape as config
from world_objects import WorldObject, OrqData
from colors import *
from meta_controller import PuzzleController
import threading
import random

class Player(object):
  """
      Player is the main actor in the fps game
  """
  EMPTY_VALUE = '<None>'
  speeds = {
    'move': 150,
    'strafe': 150,
    'look': 150,
    'actuate': 30
  }
  control_vectors = {
    'move': {
      'F': Vec3(1,0,0),
      'B': Vec3(-1,0,0),
      EMPTY_VALUE: Vec3(0)
    },
    'strafe': {
      'L': Vec3(0,1,0),
      'R': Vec3(0,-1,0),
      EMPTY_VALUE: Vec3(0)
    },
    'look': {
      'L': Vec3(1,0,0),
      'R': Vec3(-1,0,0),
      EMPTY_VALUE: Vec3(0)
    },
    'actuate': {
      'Inc': -1,
      'Dec': +1,
      EMPTY_VALUE: 0
    }
  }
  
  # The minimum number of seconds between updates.
  # ISSUE: If this value is too large it may be possible
  # for the agent to step through an entire wall within a
  # single timestep, effectively bypassing the wall's
  # collision physics. Ideally, the movement handler would
  # detect such an event and prevent it from occurring.
  minimum_update_delta = 0.01
  
  def __init__(self, room):
    """ inits the player """
    self.loadModel()
    self.setUpCamera()
    self.createCollisions()
    self.attachControls()
    # init mouse update task
    taskMgr.add(self.controlUpdate, 'control-task')
    taskMgr.add(self.debugUpdate, 'debug-task')
    if config.current.exp_mode == 'Manual':
      taskMgr.add(self.metaUpdate, 'meta-task')
    
    # This is the time delta since the last update. If
    # the delta is less than Player.minimum_update_delta
    # then the current update is skipped and the delta is
    # incremented by the most recent global time delta
    # (globalClock.getDt()).
    self.update_time_delta = 0.0 

    self.text = OnscreenText(text = 'HUD Text', pos = (-1.1, 0.9), scale = 0.07, align=TextNode.ALeft)
    self.controller = None
    self.room = room
    self.reset()

  def isWaitAction(self, action):
    return action == self.EMPTY_VALUE

  def atGoal(self):
    return self.room.isComplete()

  def inRoom(self):
    p = self.node.getPos()
    return self.room.inBounds(p)
    
  def loadModel(self):
    """ make the nodepath for player """
    self.node = NodePath('player')
    self.node.reparentTo(render)
    self.node.setScale(.05)
    self.arm = self.createArm()

  def center(self):
    self.node.setPos(0,0,0)
    self.node.setH(0)

  def reset(self):
    #x = random.random() * 18 - 9
    #y = random.random() * 18 - 9
    #h = random.random() * 360 - 180
    x, y, h = 0, 0, 0
    self.node.setPos(x, y, 0)
    self.node.setH(h)
    for joint in self.arm.joints.values():
      joint.reset()
    self.room.reset()
    self.resetControls()

  def resetControls(self):
    self.controller = None
    for cname in self.control_vectors:
      setattr(self, cname, self.EMPTY_VALUE)
    self.mod = 0

  def getDomain(self):
    return 'escape_room'

  def getPos(self):
    return self.node.getPos()

  def getH(self):
    return self.node.getH()

  def setPos(self, *args):
    self.node.setPos(*args)

  def setHpr(self, *args):
    self.node.setHpr(*args)

  def setH(self, *args):
    self.node.setH(*args)
  
  def getCentroid(self):
    return self.getPos()

  def getState(self):
    p,o = self.node.getPos(), self.node.getHpr()
    orientation = round(o.x / 10, 0) * 10
    pose_state = [p.x,p.y,orientation]
    joint_state = list(j.getState() for j in self.arm.joints.values())
    for i,v in enumerate(joint_state):
      joint_state[i] = round(v/10,0) * 10
    puzzle_state = list(self.room.getState().values.values())
    if config.current.enforce_puzzle:
      if config.current.enable_meta_actions:
        state = pose_state + puzzle_state
      else:
        state = pose_state + joint_state + puzzle_state
    else:
      state = pose_state + joint_state
    return state
    rounded_state = list(state)
    for i,v in enumerate(rounded_state):
      rounded_state[i] = round(v, 0)
    return rounded_state
  
  def getActions(self):
    actions = []
    for c in self.control_vectors:
      for v in self.control_vectors[c]:
        if v == self.EMPTY_VALUE:
          continue
        if c == 'actuate':
          actions.append('%s-%s-0'%(c,v))
        else:
          actions.append('%s-%s'%(c,v))
    if config.current.enable_meta_actions:
      for i in range(1, config.current.domain_size+1):
        actions.append('meta-%02i' % i)
      actions.append('meta-exit')
    return actions
  
  def setUpCamera(self):
    """ puts camera at the players node """
    if not base.camera:
      return
    pl =  base.cam.node().getLens()
    pl.setFov(90)
    base.camera.reparentTo(self.node)
    base.camera.setPos(-10, 0, 0)
    base.camera.setH(-90)
    base.camera.setP(0)
    
  def createCollisions(self):
    """ create a collision solid and ray for the player """
    cn = CollisionNode('player')
    cn.addSolid(CollisionSphere(0,0,0,15))
    solid = self.node.attachNewNode(cn)
    base.cTrav.addCollider(solid,base.pusher)
    base.pusher.addCollider(solid,self.node, base.drive.node())
    cn.setCollideMask(BitMask32.allOff())
    cn.setFromCollideMask(WALL_MASK)

    # init players floor collisions
    ray = CollisionRay()
    ray.setOrigin(0,0,-.2)
    ray.setDirection(0,0,-1)
    cn = CollisionNode('playerRay')
    cn.addSolid(ray)
    cn.setCollideMask(BitMask32.allOff())
    cn.setFromCollideMask(FLOOR_MASK | REGION_MASK)
    solid = self.node.attachNewNode(cn)
    self.nodeGroundHandler = CollisionHandlerQueue()
    base.cTrav.addCollider(solid, self.nodeGroundHandler)
    base.cTrav.addCollider(solid, base.cQueue)
    
    if config.current.simple_button_collisions:
      cn = CollisionNode('player-button')
      cn.addSolid(CollisionSphere(0,0,0,15))
      solid = self.node.attachNewNode(cn)
      cn.setCollideMask(BitMask32.allOff())
      cn.setFromCollideMask(BUTTON_MASK)
      base.cTrav.addCollider(solid, base.cQueue)

  def debugUpdate(self,task):
    # Player Pose
    p,o = self.node.getPos(), self.node.getHpr()
    pose_s = 'P = (%2.1f,%2.1f,%2.f) @ (%2.1f,%2.1f)' % (p.x,p.y,p.z,o.x,-o.z)

    # Arm Joints
    joints_s = '\n'.join(str(j) for j in self.arm.joints.values())

    # Action Controls
    cvals = []
    for cname in self.control_vectors:
      cval = getattr(self, cname)
      if cval != self.EMPTY_VALUE:
        cvals.append('%s: %s' % (cname,cval))
    cvals.append('mod:%s' % self.mod)
    cvals_s = ', '.join(cvals)

    state_s = 'Player State: <' + ','.join('%2.1f'%s for s in self.getState()) + '>'

    # Combine to Text
    text = '\n'.join([pose_s, joints_s, cvals_s, state_s])
    self.text.setText(text)
    return task.cont

  def attachControls(self):
    """ attach key events """
    def ak(key, id):
      base.accept(key, self.setControl, [id, True])
      base.accept('%s-up'%key, self.setControl, [id, False])
    ak('m', 'meta-02')
    ak('w', 'move-F')
    ak('s', 'move-B')
    ak('a', 'strafe-L')
    ak('d', 'strafe-R')
    ak('arrow_left',  'look-L')
    ak('arrow_right', 'look-R')
    ak('u', 'actuate-Inc')
    ak('j', 'actuate-Dec')
    for i in range(9+1):
      ak('%i'%i,'mod-%i'%i)
    ak('`','mod-0')

  def setControl(self, control, active=True):
    parts = control.split('-')
    if control.startswith('meta'):
      if active:
        self.controller = PuzzleController(player=self, button=parts[1])
      return
    if len(parts) != 2:
      raise Exception('Invalid control sent: %s' % (control))
    cname, cval = parts
    if active:
      setattr(self, cname, cval)
    elif cname != 'mod':
      setattr(self, cname, self.EMPTY_VALUE)

  def metaUpdate(self, task):
    a = self.processMetaController()
    if a is not None:
      self.setControl(a)
    return task.cont

  def processMetaController(self):
    if self.controller is not None:
      if self.controller.current_action is not None:
        self.setControl(self.controller.current_action, False)
      self.controller.processFrame()
      if self.controller.isComplete():
        if self.controller.current_action is not None:
          self.setControl(self.controller.current_action, False)
        self.resetControls()
      else:
        return self.controller.getAction()
    return None

  ''' this sucks, what's the point of minimum update delta?'''
  def controlUpdate(self, task):
    dt = globalClock.getDt()
    self.update_time_delta += dt
    if self.update_time_delta < Player.minimum_update_delta:
      return task.cont
    try:
      self._controlUpdate(self.update_time_delta)
    finally:
      self.update_time_delta = 0
    return task.cont

  def controlUpdate(self, task):
    self._controlUpdate(globalClock.getDt())
    return task.cont

  def _controlUpdate(self, dt):
    deltas = {}
    cv = self.control_vectors
    for c in cv:
      if c == self.EMPTY_VALUE: continue
      v = getattr(self, c)
      deltas[c] = self.getDelta(c, v, dt)
    for c in cv:
      if c == self.EMPTY_VALUE: continue
      self.perform(c, deltas[c], mod=self.mod)

  def perform(self, control, delta, mod=0):
    if control == 'look':
      self.node.setHpr(self.node, delta)
    elif control == 'move' or control == 'strafe':
      self.node.setPos(self.node, delta)
    elif control == 'actuate':
      joint = self.arm.joints[int(mod)]
      joint.setHpr(delta)

  def getDelta(self, control, value, dt):
    v = self.control_vectors[control][value]
    if control != 'actuate':
      v = Vec3(*v)
    return v * self.speeds[control] * dt * config.current.time_coefficient

  def takeAction(self, action, duration, callback=None):
    if action == self.EMPTY_VALUE:
      if callback: callback()
      return
    use_meta = False
    if action.startswith('meta'):
      parts = action.split('-')
      self.controller = PuzzleController(player=self, button=parts[1])
      use_meta = True
      self.meta_action_count = 0
    def handler(task):
      dt = globalClock.getDt()
      if use_meta:
        if task.time < duration / config.current.time_coefficient:
          return task.cont
        if self.controller is None:
          if callback: callback()
          interval = (duration / config.current.time_coefficient)
          self.meta_action_count = int(round(task.time / interval, 0))
          if self.meta_action_count == 0:
            self.meta_action_count = 1
          return task.done
      elif task.time >= duration / config.current.time_coefficient:
        if callback: callback()
        return task.done
      a = action
      if use_meta:
        a = self.processMetaController()
      if a is None:
        return task.cont
      parts = a.split('-')
      cname = parts[0]
      cval = parts[1]
      delta = self.getDelta(cname, cval, dt)
      cmod = None
      if cname == 'actuate':
        cmod = int(parts[2])
      self.perform(cname, delta, mod=cmod)
      return task.cont
    taskMgr.add(handler, 'take-action-handler')

  def createArm(self):
    arm = Arm()
    arm.model = NodePath('virtual arm')
    arm.model.reparentTo(self.node)
    
    intermediate = NodePath('arm rotator')
    intermediate.reparentTo(arm.model)
    
    req_fa = OrqData(
      color=ARM_SILVER_COLOR,
      dx = 6,
      scale = 3,
      link_index = 0,
      actuation_index = 2
    )
    wo_fa = Joint.create(
      name='forearm',
      req=req_fa
    )
    wo_fa.model.reparentTo(intermediate)
    arm.joints[wo_fa.link_index] = wo_fa

    req_hand = OrqData(
    )
    wo_hand = Hand.create(
      name='hand',
      req=OrqData(
        color=ARM_HAND_COLOR,
        scale=req_fa.scale,
        dx=4,
        dy=4,
        translation=(0,(-1.5*req_fa.scale),0)
      )
    )
    wo_hand.model.setPos(wo_hand.model, req_fa.scale * req_fa.dx, 0, 0)
    wo_hand.model.reparentTo(wo_fa.model)
    wo_hand.cPath.node().setCollideMask(BitMask32.allOff())
    wo_hand.cPath.node().setFromCollideMask(BUTTON_MASK)
    base.cTrav.addCollider(wo_hand.cPath, base.cQueue)

    arm.hand = wo_hand
    intermediate.setPos(4,-8,-8)
    return arm
 
class Hand(WorldObject):
  @staticmethod
  def create(**kwargs):
    hand = Hand(
      gCreator=geometry.createCube,
      cCreator=colliders.createBoxCollider,
      **kwargs
    )
    hand.cPath.show()
    return hand

class Joint(WorldObject):
  def __init__(self, *args, **kwargs):
    super(Joint, self).__init__(*args, **kwargs)
    self.link_index = self.req.link_index
    self.actuation_index = self.req.actuation_index
    self.max = 60
    self.min = -60
  
  def useCollisions(self): return False

  @staticmethod
  def create(**kwargs):
    joint = Joint(
      gCreator=geometry.createCube,
      cCreator=colliders.createBoxCollider,
      **kwargs
    )
    return joint

  def getState(self):
    jstate = self.model.getHpr()[self.actuation_index]
    return jstate

  def setHpr(self, delta):
    v = Vec3(0)
    current = self.model.getHpr()[self.actuation_index]
    if current + delta > self.max:
      return
    elif current + delta < self.min:
      return
    v[self.actuation_index] = delta
    self.model.setHpr(self.model, v)

  def reset(self):
    self.model.setHpr(Vec3(0))

  def __str__(self):
    jval = self.model.getHpr()[self.actuation_index]
    return "J%i: %2.1f" % (self.link_index,jval)

class Arm(WorldObject):
  def __init__(self):
    self.joints = {}
    self.hand = None

  def setHpr(self, *args, **kwargs):
    if len(args) > 0 and args[0] is self:
      self.model.setHpr(self.model, *args[1:], **kwargs)
    else:
      self.model.setHpr(*args, **kwargs)

  def setPos(self, *args, **kwargs):
    if len(args) > 0 and args[0] is self:
      self.model.setPos(self.model, *args[1:], **kwargs)
    else:
      self.model.setPos(*args, **kwargs)

  def getHpr(self):
    return self.model.getHpr()
  
  def getPos(self):
    return self.model.getPos()
