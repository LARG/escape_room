import gym
from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Flatten, Input, Concatenate
from keras.optimizers import Adam
from rl.agents import SARSAAgent, DDPGAgent, DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.callbacks import Callback
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess
from rl.core import Processor
import tensorflow as tf
import cfgescape as config


def create(env):
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
  #print(model.summary())

  # Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
  # even the metrics!
  memory = SequentialMemory(limit=50000, window_length=1)
  policy = BoltzmannQPolicy()
  dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=1000,
                 target_model_update=1e-2, policy=policy)
  dqn.compile(Adam(lr=1e-3), metrics=['mae'])
  return dqn


