#!/usr/bin/env python
import sys, os, re, csv
import redis, json
import cfgescape
from analysis import util

def get_commands():
  agents = ['dqn','ddpg','sarsa']
  sizes = [2]
  seeds = [14]
  complexities = [1]
  trials = range(1,10+1)
  timesteps = int(2e4)
  handicaps = [6]
  for trial in trials:
    for size in sizes:
      for seed in seeds:
        for complexity in complexities:
          for handicap in handicaps:
            for a in agents:
              args = {
                'evaluator': '/home/jake/code/research/panda/escape/main.py',
                'agent_type': a,
                'domain_size': size,
                'domain_seed': seed,
                'domain_handicap': handicap,
                'domain_complexity': complexity,
                'exp_trial': trial,
                'exp_timesteps': timesteps,
                'exp_directory': '/home/jake/code/research/panda/escape/results',
                'exp_mode': 'Data',
                
                'nogui': True
              }
              config = cfgescape.Config(**args)
              last_ts = util.get_file_lines(config.output_path)
              if last_ts is None or last_ts < timesteps/100:
                cmd = '{evaluator} --nogui --agent_type {agent_type} --domain_size {domain_size} --domain_seed {domain_seed} --domain_complexity {domain_complexity} --domain_handicap {domain_handicap} --exp_trial {exp_trial} --exp_timesteps {exp_timesteps} --exp_directory {exp_directory} --exp_mode {exp_mode}'
                cmd = cmd.format(**args)
                yield cmd
              else:
                print 'Skipping completed evaluation with %i timesteps recorded: %s' % (last_ts, config.output_path)
