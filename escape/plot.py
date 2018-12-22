#!/usr/bin/env python
#import sys; 
import sys, re, os
#sys.path.insert(1, '/home/jake/code/rl')
import matplotlib.pyplot as plt
from matplotlib.colors import ColorConverter
from matplotlib.lines import Line2D
import signal; signal.signal(signal.SIGINT, signal.SIG_DFL)
from pylab import *
from analysis.agent_data import load_data
from analysis.escape import MeanResult, Results
from matplotlib import rcParams
import cfgescape
from args import parse_args

rcParams.update({'figure.autolayout': True})

args = parse_args()
args.metric = args.metric or 'ereward_mean'

adatas = load_data(args.metric)
sizes = [5]
trials = [1]
directory = args.exp_directory or 'results'
complexity = 4
timesteps = args.exp_timesteps
ignored_agets = {}
xmax, ymax = 0, 0
xmin, ymin = 0, 0
fig = plt.figure()
ax = fig.add_subplot(111)
handles, labels = [], []
for adata in adatas:
  if args.agents is not None and adata.name not in args.agents: continue
  xs, ys, std_errors = [], [], []
  times = []
  result = []
  times = []
  result = MeanResult(directory=directory, agent=adata.name, timesteps=timesteps, recompute=args.recompute,
    handicap=args.domain_handicap,
    size=args.domain_size
  )
  if result.empty(): continue
  adata.result = result
  ys = getattr(result, args.metric)
  stddevs = getattr(result, args.metric + '_stddev')
  if args.pct_max:
    ys = [100 * (1000.0 + y)/args.pct_max for y in ys]
    stddevs = [100 * s/1090 for s in stddevs]
  first_index = args.first_series_index
  if timesteps is None: timesteps = len(ys)
  xs = range(first_index, timesteps-first_index)
  ys = ys[first_index:timesteps-first_index]
  std_errors = [s/math.sqrt(result.metadata['sample_size']) for s in stddevs]
  xmax = min(timesteps or max(xs), max(xs))
  ymax = args.ymax or max(ymax, max(ys))
  ymin = args.ymin or min(ymin, min(ys))
  p, = ax.plot(xs, ys, adata.color, marker=adata.marker, markevery=0.1, markersize=10, linestyle=adata.style)
  handles.append(p)
  labels.append(adata.display)
  
  if args.error_bar:
    error_xs = xs
    error_ys = ys
    yerr = std_errors
    
    errors_upper = [ys[i] + std_errors[i] for i in range(len(ys))]
    ymax = max(ymax, max(errors_upper))

    ax.errorbar(error_xs, error_ys, yerr=yerr,
      ecolor=adata.color, fmt="none", capthick=2,
    )

  if args.stddev:
    ys_lower = [y - s for y,s in zip(ys,std_errors)]
    ys_upper = [y + s for y,s in zip(ys,std_errors)]
    cc = ColorConverter()
    c = cc.to_rgba(adata.color, .15)
    ax.fill_between(xs, ys_lower, ys_upper, facecolor=c,linewidth=0)

ylabel = {
  'treward': 'Total Reward',
  'time': 'Total Processing Time (ms)',
  'ereward_mean': 'Cumulative Mean Reward',
  'treward_mean': 'Average Reward Per Timestep',
  'esteps_mean': 'Average Episode Length',
  'esteps': 'Episode Length',
}[args.metric]
ax.set_ylabel(ylabel)
ax.set_xlabel('Episode')
if args.domain_complexity is None:
  ax.set_title('%s per Episode' % ylabel)
else:
  ax.set_title('%s per Episode [Complexity %i]' % (ylabel,args.domain_complexity))
if len(handles) > 3 and args.legend_location is None:
  ncol=1
  locs = ['upper left', 'lower left']
  first_legend = ax.legend(handles[:3], labels[:3], loc=locs[0], ncol=ncol)
  plt.gca().add_artist(first_legend)
  ax.legend(handles[3:], labels[3:], loc=locs[1], ncol=ncol)
else:
  ncol=args.legend_ncol or 2
  ax.legend(handles, labels, loc=args.legend_location, ncol=ncol)
plt.axis((xs[0],xmax*1.05,ymin-(abs(ymin)*0.1),ymax*1.1))
ax.set_yscale('symlog' if args.yscale == "log" else args.yscale)
ax.set_xscale('symlog' if args.xscale == "log" else args.xscale)
if args.pct_max:
  vals = ax.get_yticks()
  ax.set_yticklabels(['{:2.0f}%'.format(x) for x in vals])

if args.save_path:
  fig_shape = tuple(float(v) for v in re.findall("[0-9\.]+", args.fig_shape))
  fig.set_size_inches(fig_shape[0], fig_shape[1])
  plt.savefig(args.save_path, dpi=args.dpi)
else:
  plt.show()
if args.ttest:
  for i in range(len(adatas)):
    for j in range(i+1,len(adatas)):
      print "%s vs %s" % (adatas[i].name,adatas[j].name)
      Results.ttest(adatas[i].result,adatas[j].result)
      print ""
