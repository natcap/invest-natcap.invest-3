import unittest2 as unittest
import os, sys
cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + './')
sys.path.insert(0, cmd_folder + '/../')

this_dir = os.path.dirname(__file__)
unittest.defaultTestLoader.discover(start_dir=this_dir, pattern='*test.py')
