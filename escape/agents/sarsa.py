import gym
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam
from rl.agents import SARSAAgent
from rl.policy import BoltzmannQPolicy
import tensorflow as tf
import numpy as np
import cfgescape as config

def create(env):
  np.random.seed(config.current.domain_seed)
  env.seed(config.current.domain_seed)
  nb_actions = env.action_space.n

  # Next, we build a very simple model.
  model = Sequential()
  model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
  model.add(Dense(config.current.agent_vfn_complexity))
  model.add(Activation('relu'))
  model.add(Dense(config.current.agent_vfn_complexity))
  model.add(Activation('relu'))
  model.add(Dense(config.current.agent_vfn_complexity))
  model.add(Activation('relu'))
  model.add(Dense(nb_actions))
  model.add(Activation('linear'))
  global graph 
  graph = tf.get_default_graph()

  # SARSA does not require a memory.
  policy = BoltzmannQPolicy()
  sarsa = SARSAAgent(model=model, nb_actions=nb_actions, nb_steps_warmup=10, policy=policy)
  sarsa.compile(Adam(lr=1e-3), metrics=['mae'])
  return sarsa

