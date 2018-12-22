import gym
from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Flatten, Input, Concatenate
from keras.optimizers import Adam
from rl.agents import SARSAAgent, DDPGAgent
from rl.policy import BoltzmannQPolicy
from rl.callbacks import Callback
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess
from rl.core import Processor
import tensorflow as tf
import numpy as np
import random
import cfgescape as config

class ArgmaxProcessor(Processor):
  def process_action(self, action):
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

  # Next, we build a very simple model.
  actor = Sequential()
  actor.add(Flatten(input_shape=(1,) + env.observation_space.shape))
  actor.add(Dense(config.current.agent_vfn_complexity))
  actor.add(Activation('relu'))
  actor.add(Dense(config.current.agent_vfn_complexity))
  actor.add(Activation('relu'))
  actor.add(Dense(config.current.agent_vfn_complexity))
  actor.add(Activation('relu'))
  actor.add(Dense(nb_actions))
  actor.add(Activation('linear'))
  #print(actor.summary())

  action_input = Input(shape=(nb_actions,), name='action_input')
  observation_input = Input(shape=(1,) + env.observation_space.shape, name='observation_input')
  flattened_observation = Flatten()(observation_input)
  x = Concatenate()([action_input, flattened_observation])
  x = Dense(config.current.agent_vfn_complexity)(x)
  x = Activation('relu')(x)
  x = Dense(config.current.agent_vfn_complexity)(x)
  x = Activation('relu')(x)
  x = Dense(config.current.agent_vfn_complexity)(x)
  x = Activation('relu')(x)
  x = Dense(1)(x)
  x = Activation('linear')(x)
  critic = Model(inputs=[action_input, observation_input], outputs=x)
  #print(critic.summary())

  # Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
  # even the metrics!
  memory = SequentialMemory(limit=100000, window_length=1)
  random_process = OrnsteinUhlenbeckProcess(size=nb_actions, theta=.15, mu=0., sigma=.3)
  agent = DDPGAgent(nb_actions=nb_actions, actor=actor, critic=critic, critic_action_input=action_input,
                    memory=memory, nb_steps_warmup_critic=1000, nb_steps_warmup_actor=100,
                    random_process=random_process, gamma=.99, target_model_update=1e-3,
                    processor=ArgmaxProcessor())
  agent.compile(Adam(lr=.001, clipnorm=1.), metrics=['mae'])
  return agent

