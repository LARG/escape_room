#!/usr/bin/env python
import sys, os, re, csv
import redis, json
from experiments.handicaps import get_commands

def main():
  server = redis.Redis()
  if len(sys.argv) == 0:
    return
  server.delete('condor-local')
  for cmd in get_commands():
    server.rpush('condor-local', cmd)

if __name__ == '__main__':
  main()
