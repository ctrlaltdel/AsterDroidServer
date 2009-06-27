#!/usr/bin/env python

import unittest

class Tests(unittest.TestCase):
  def test_dummy(self):
    print "tests"
    return True


  def test_fails(self):
    raise Exception("Blah")

if __name__ == '__main__':
  unittest.main()
