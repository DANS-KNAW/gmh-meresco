# -*- coding: utf-8 -*-

from unittest import TestCase
from md5 import md5

from meresco.components.storagecomponent import defaultSplit, defaultJoin

from meresco_server.storagesplit import md5Split, md5Join, MD5JoinError

class StorageSplitTest(TestCase):
    def testOriginal(self):
        identifier = ('meresco:record:id:1', 'partname')
        self.assertEquals(['meresco', 'record:id:1', 'partname'], defaultSplit(identifier))
        self.assertEquals(identifier, defaultJoin(['meresco', 'record:id:1', 'partname']))
        self.assertEquals(identifier, defaultJoin(defaultSplit(identifier)))
        
    def testSplitWithMd5(self):
        identifier = ('meresco:record:id:1', 'partname')
        self.assertEquals(['meresco', '37', '34', 'record:id:1', 'partname'], md5Split(identifier))
        identifier2 = ('meresco:record:id:2', 'partname')
        self.assertEquals(['meresco', 'ab', 'c8', 'record:id:2', 'partname'], md5Split(identifier2))
        self.assertEquals(identifier2, md5Join(md5Split(identifier2)))
        
    def testWithNoneAsPartname(self):
        identifier = ('meresco:record:id:1', None)        
        self.assertEquals(['meresco', '37', '34', 'record:id:1'], md5Split(identifier))        
        self.assertEquals(['meresco', 'record:id:1'], defaultSplit(identifier))
        self.assertRaises(MD5JoinError, md5Join, md5Split(identifier))
                    
    def testWithoutColon(self):
        identifier = ('without_colon', 'partname')
        self.assertEquals(['without_colon', 'partname'], defaultSplit(identifier))
        self.assertEquals(['without_colon', 'partname'], md5Split(identifier))
        self.assertRaises(MD5JoinError, md5Join, md5Split(identifier))
        #self.assertEquals(identifier, md5Join(md5Split(identifier)))
        
    def testWithoutColonNonePartName(self):
        identifier = ('without_colon', None)
        self.assertEquals(['without_colon'], defaultSplit(identifier))
        self.assertEquals(['without_colon'], md5Split(identifier))
        self.assertRaises(MD5JoinError, md5Join, md5Split(identifier))
        