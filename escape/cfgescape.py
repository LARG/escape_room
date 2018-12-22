import sys, os, re, math
from args import parse_args
from analysis import results

class Config(object):
  def __init__(self, **kwargs):
    self.nogui = False
    self.temporal_quantum = 0.1

    self.tabular_discretization_factor = None
    self.stochastic = False
    self.independent_light_off = True
    self.use_reset = True
    self.ignore_reset_refinements = True
    self.enforce_puzzle = True
    self.enable_off_toggling = False
    self.exp_mode = 'Data' #'Debug' #'Data' # 'Debug', 'Manual', etc
    self.max_episode_steps = 1000
    self.simple_button_collisions = True
    self.enable_meta_actions = True

    self.agent_type = 'dqn'
    self.exp_trial = 1
    self.exp_trials = 100
    self.exp_timesteps = 1e6
    self.exp_directory = 'results'
    self.domain_size = 1
    self.domain_seed = 1
    self.domain_complexity = 1
    self.domain_handicap = 10

    self.process_args(**kwargs)
    self.agent_vfn_complexity = 16
    if self.enable_meta_actions:
      if self.agent_type == 'ddpg':
        self.agent_vfn_complexity = 4
      elif self.agent_type == 'sarsa':
        self.agent_vfn_complexity = 32
      elif self.agent_type == 'dqn':
        self.agent_vfn_complexity = 3

    if self.domain_size == 0:
      self.enforce_puzzle = False

  def _convert_handicap(self):
    self.exit_size = self.domain_handicap
    self.button_size = self.domain_handicap

  def _process_gui_setting(self):
    if self.nogui:
      if self.agent_type == 'ddpg':
        self.time_coefficient = 1.0
      else:
        self.time_coefficient = 10.0
      self.enable_interface = False
    else:
      self.time_coefficient = 1.0
      self.enable_interface = True

  def process_args(self, **args):
    if len(args) == 0:
      args = vars(parse_args())
    for key, val in args.iteritems():
      if val is None and hasattr(self, key): continue
      setattr(self, key, val)

                  # Use +1 here just so we have some cushion
    trial_zeros = str(1 + int(math.ceil(math.log(self.exp_trials)/math.log(10))))
    trial_fmt = '%0' + trial_zeros  + 'i'
    trial_str = trial_fmt % self.exp_trial
    self.output_file = results.ResultFile.filename_from_keys(
      agent=self.agent_type,
      size=self.domain_size,
      seed=self.domain_seed,
      complexity=self.domain_complexity,
      handicap=self.domain_handicap,
      trial=self.exp_trial
    )
    self.description = '{agent_type} agent, seed {seed}, handicap {handicap}, trial {trial}'.format(
      agent_type = self.agent_type,
      seed = '%02i' % self.domain_seed,
      handicap = '%02i' % self.domain_handicap,
      trial = trial_str
    )
    self.output_path = os.path.join(self.exp_directory, self.output_file)
    self._convert_handicap()
    self._process_gui_setting()

current = Config()
