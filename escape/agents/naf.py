import gym
from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Flatten, Input, Concatenate
from keras.optimizers import Adam
from rl.agents import NAFAgent
from rl.policy import BoltzmannQPolicy
from rl.callbacks import Callback
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess
from rl.core import Processor
import tensorflow as tf
import numpy as np
import random
import cfgescape as config

class PendulumProcessor(Processor):
  def process_action(self, action):
    action = np.clip(action, -1., 1.)
    indexes = range(len(action))
    random.shuffle(indexes)
    choice = None
    for i in indexes:
      if choice is None or action[choice] < action[i]:
        choice = i
    return choice


def create(env):
  np.random.seed(config.current.domain_seed)
  env.seed(config.current.domain_seed)
  nb_actions = env.action_space.n

  # Build all necessary models: V, mu, and L networks.
  V_model = Sequential()
  V_model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
  V_model.add(Dense(16))
  V_model.add(Activation('relu'))
  V_model.add(Dense(16))
  V_model.add(Activation('relu'))
  V_model.add(Dense(16))
  V_model.add(Activation('relu'))
  V_model.add(Dense(1))
  V_model.add(Activation('linear'))

  mu_model = Sequential()
  mu_model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
  mu_model.add(Dense(16))
  mu_model.add(Activation('relu'))
  mu_model.add(Dense(16))
  mu_model.add(Activation('relu'))
  mu_model.add(Dense(16))
  mu_model.add(Activation('relu'))
  mu_model.add(Dense(nb_actions))
  mu_model.add(Activation('linear'))

  action_input = Input(shape=(nb_actions,), name='action_input')
  observation_input = Input(shape=(1,) + env.observation_space.shape, name='observation_input')
  x = Concatenate()([action_input, Flatten()(observation_input)])
  x = Dense(32)(x)
  x = Activation('relu')(x)
  x = Dense(32)(x)
  x = Activation('relu')(x)
  x = Dense(32)(x)
  x = Activation('relu')(x)
  x = Dense(((nb_actions * nb_actions + nb_actions) // 2))(x)
  x = Activation('linear')(x)
  L_model = Model(inputs=[action_input, observation_input], outputs=x)

  # Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
  # even the metrics!
  processor = PendulumProcessor()
  memory = SequentialMemory(limit=100000, window_length=1)
  random_process = OrnsteinUhlenbeckProcess(theta=.15, mu=0., sigma=.3, size=nb_actions)
  agent = NAFAgent(nb_actions=nb_actions, V_model=V_model, L_model=L_model, mu_model=mu_model,
                   memory=memory, nb_steps_warmup=100, random_process=random_process,
                   gamma=.99, target_model_update=1e-3, processor=processor)
  agent.compile(Adam(lr=.001, clipnorm=1.), metrics=['mae'])
  return agent
