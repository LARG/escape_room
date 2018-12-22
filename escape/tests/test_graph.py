#!/usr/bin/env python
import unittest

import os
import sys
sys.path.append('..')
import puzzles.buttons as puzzle

class test_graph(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_graph_planner(self):
    s = 10
    self.puzzle = puzzle.LightWorld(size=s)
    graph = self.puzzle.generator.graph
    state = self.puzzle.createState()
    goal = 'L%i' % s
    plan = graph.getPlan(state, goal)
    self.assertEqual(plan[-1], goal)
    self.assertLessEqual(len(plan), s)
    self.assertEqual(plan[0], 'L01')

if __name__ == '__main__':
  unittest.main()
