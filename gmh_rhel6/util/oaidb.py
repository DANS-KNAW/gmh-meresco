# -*- coding: utf-8 -*-

from sys import argv, path
from glob import glob
from os import remove
from os.path import join

#from meresco.components.facetindex.merescolucene import IndexWriter, merescoStandardAnalyzer
#from meresco.tools.lucenetools import unlock

#from meresco.components.integerlist import IntegerList
from meresco.components import PersistentSortedIntegerList


def readlist(args):

    path = '/data/meresco/oai/data/sets/publication.list'


    #raw_input("Press any key to continue (Ctrl-C to break) ")
    
    print 'Opening IntegerList', path
    publist = PersistentSortedIntegerList(path, use64bits=True)
    print 'AANTAL in publist:', len(publist)
    
    
    pad = '/data/meresco/oai/data/tombStones.list'
    tombstonelist = PersistentSortedIntegerList(pad, use64bits=True)
    
    cnt = 0
    for stamp in publist:
        if not stamp in tombstonelist: cnt = cnt + 1
        
    print cnt
    
    
    print 'in deleted:', len(tombstonelist)

    print 'Finished'


if __name__ == '__main__':
    readlist(argv)