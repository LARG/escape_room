def parse_args():
  import argparse
  parser = argparse.ArgumentParser(description='Analyzer argument parser')
  # Room Configs


  # Experiment Configs
  parser.add_argument('--exp_directory', dest='exp_directory', action='store', type=str,
                     help='The directory in which to store results.', default='results')
  parser.add_argument('--domain_seed', dest='domain_seed', action='store', type=int, default=None,
                     help='The random domain_seed for the generated domain.')
  parser.add_argument('--domain_size', dest='domain_size', action='store', type=int, default=None,
                     help='The size of the generated domain.')
  parser.add_argument('--domain_complexity', dest='domain_complexity', action='store', type=int, default=None,
                     help='The complexity of the generated domain.')
  parser.add_argument('--domain_handicap', dest='domain_handicap', action='store', type=int, default=None,
                     help='The handicap of the generated domain.')
  parser.add_argument('--agent_type', dest='agent_type', action='store', type=str, default=None,
                     help='The agent_type configuration to use.')
  parser.add_argument('--replay', dest='replay', action='store_true', default=False,
                     help='Replay actions from the last run.')
  parser.add_argument('--verbose', dest='verbose', action='store_true', default=False,
                     help='Print verbose state and action data.')
  parser.add_argument('--exp_trial', dest='exp_trial', action='store', type=int, default=None,
                     help='The current exp_trial number.')
  parser.add_argument('--exp_trials', dest='exp_trials', action='store', type=int, default=20,
                     help='The total number of exp_trials to run.')
  parser.add_argument('--exp_timesteps', dest='exp_timesteps', action='store', type=int, default=None,
                     help='The total number of exp_timesteps to run per trial.')
  parser.add_argument('--nogui', dest='nogui', action='store_true', default=False,
                     help='Disable the gui.')
  parser.add_argument('--exp_mode', dest='exp_mode', type=str, default='Debug',
                     help='Set the experiment mode (Debug, Data, Manual).')
  parser.add_argument('--overwrite', dest='overwrite', action='store_true', default=False,
                     help='Overwrite data from the last experiment.')

  # Plot Configs
  parser.add_argument('--metric', dest='metric', action='store', type=str,
                     help='The metric being plotted.', default='ereward')
  parser.add_argument('--stddev', dest='stddev', action='store_true',
                     help='Enable fill standard deviation.', default=False)
  parser.add_argument('--error-bar', dest='error_bar', action='store_true',
                     help='Enable error bars.', default=False)
  parser.add_argument('--interval', dest='interval', action='store', type=int,
                     help='Episode interval for rewards.', default=None)
  parser.add_argument('--legend', dest='legend_location', action='store', type=str,
                     help='The location of the legend in the generated plot.', default=None)
  parser.add_argument('--legend-ncol', dest='legend_ncol', action='store', type=int,
                     help='The number of columns to use for the legend.', default=None)
  parser.add_argument('--ymax', dest='ymax', action='store', type=int,
                     help='Set the max of the y-axis.', default=None)
  parser.add_argument('--ymin', dest='ymin', action='store', type=int,
                     help='Set the min of the y-axis.', default=None)
  parser.add_argument('--yscale', dest='yscale', action='store', type=str,
                     help='Set the scale of the y-axis.', default='linear')
  parser.add_argument('--xscale', dest='xscale', action='store', type=str,
                     help='Set the scale of the x-axis.', default='linear')
  parser.add_argument('--first_series_index', dest='first_series_index', action='store', type=int,
                     help='Set the first index to be used in the data series.', default=0)
  parser.add_argument('--save', dest='save_path', action='store', type=str,
                     help='An optional save path for the generated plot.', default=None)
  parser.add_argument('--dpi', dest='dpi', action='store', type=int,
                     help='DPI for the generated plot.', default=250)
  parser.add_argument('--fig_shape', dest='fig_shape', action='store', type=str,
                     help='The size of the generated figure as a tuple of inches.', default='(10,10)')
  parser.add_argument('--title', dest='title', action='store', type=str,
                     help='The title prefix for the plot.', default=None)
  parser.add_argument('--include-agent', action='append', dest='agents', type=str,
                     help='An agent to include in the generated plot. All agents will be ' + 
                     'included if none are specified.', default=None)
  parser.add_argument('--pct-max', dest='pct_max', action='store', type=float, default=None,
                      help='The maximum measured value to use for plotting percentages.')
  parser.add_argument('--ttest', dest='ttest', action='store_true', default=False,
                     help='Perform a t-test when computing result plots.')
  parser.add_argument('--recompute', dest='recompute', action='store_true', default=False,
                     help='Recompute aggregate data rather than reading from cached files.')
  
  # Log Configs
  parser.add_argument('--max-log-depth', dest='max_log_depth', action='store', type=int, default=None,
                      help='The maximum depth allowed for printing out log data.')
  parser.add_argument('--max-log-level', dest='max_log_level', action='store', type=int, default=None,
                      help='The maximum level allowed for printing out log data.')

  args, unk = parser.parse_known_args()
  return args

