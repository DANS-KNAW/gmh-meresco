#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
from os import system
from sys import path
system('find .. -name "*.pyc" | xargs rm -f')

from glob import glob
for p in glob('../deps.d/*'):
    path.insert(0, p)

path.insert(0, '..')

from unittest import main

from storagesplittest import StorageSplitTest
from norm_modstest import NormModsTest
from addharvestdatetest import AddHarvestdateTest
from norm_didltest import NormDIDLTest


if __name__ == '__main__':
    try:
        main()
    finally:
        system('find .. -name "*.pyc" | xargs rm -f')
