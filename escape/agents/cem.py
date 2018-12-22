import numpy as np
import gym

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import Adam

from rl.agents.cem import CEMAgent
from rl.memory import EpisodeParameterMemory
import cfgescape as config

# Get the environment and extract the number of actions.
def create(env):
  np.random.seed(config.current.domain_seed)
  env.seed(config.current.domain_seed)
  nb_actions = env.action_space.n

  obs_dim = env.observation_space.shape[0]

  # Option 1 : Simple model
  #model = Sequential()
  #model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
  #model.add(Dense(nb_actions))
  #model.add(Activation('softmax'))

  # Option 2: deep network
  model = Sequential()
  model.add(Flatten(input_shape=(1,) + env.observation_space.shape))
  model.add(Dense(16))
  model.add(Activation('relu'))
  model.add(Dense(16))
  model.add(Activation('relu'))
  model.add(Dense(16))
  model.add(Activation('relu'))
  model.add(Dense(nb_actions))
  model.add(Activation('softmax'))

  # Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
  # even the metrics!
  memory = EpisodeParameterMemory(limit=1000, window_length=1)

  cem = CEMAgent(model=model, nb_actions=nb_actions, memory=memory,
                 batch_size=50, nb_steps_warmup=2000, train_interval=50, elite_frac=0.05)
  cem.compile()
  return cem
