# -*- coding: utf-8 -*-
from meresco.core import Observable
from lxml.etree import parse, _ElementTree, tostring
from lxml import etree
import gc

class DNADebug(Observable):

    def __init__(self, enabled=True, prefix='DEBUG', gc=False):
        Observable.__init__(self)
        #assert len(allowed) == 0 or len(disallowed) == 0, 'Use disallowed or allowed'        
        self._enabled = enabled
        self._add_prefix = '[%s]'%(prefix)
        self._gc = gc
        #gc.enable()
        #gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
        #gc.DEBUG_LEAK - DEBUG_COLLECTABLE
        
    def unknown(self, method, *args, **kwargs):
        
        if self._enabled:
            
            print self._add_prefix, 'Method:', method
            for value in args:
                print self._add_prefix, 'Value:', value
            for key in kwargs:
                kwargkey = kwargs[key]
                if type(kwargs[key]) == _ElementTree:                    
                    kwargkey = etree.tostring(kwargs[key], encoding='UTF-8')                    
                print self._add_prefix, "Key: %s,  Value: %s" % (key, kwargkey)
        
        if self._gc:
            #gc.enable()
            gc.set_debug(gc.DEBUG_LEAK)
            # force collection            
            gc.collect()
            #print self._add_prefix, "GARBAGE collected...:"

            #print self._add_prefix, "Uncollected Objects!:",
            for x in gc.garbage:
                s = str(x)
                if len(s) > 80: s = s[:80]
                print "Uncollected Object!:", type(x),"->", s            

        yield self.all.unknown(method, *args, **kwargs)
        
        #      
#        class Transparent(Observable):
#223	    def all_unknown(self, message, *args, **kwargs):
#224	        yield self.all.unknown(message, *args, **kwargs)
#225	    def any_unknown(self, message, *args, **kwargs):
#226	        try:
#227	            response = yield self.any.unknown(message, *args, **kwargs)
#228	        except NoneOfTheObserversRespond:
#229	            raise DeclineMessage
#230	        raise StopIteration(response)
#231	    def do_unknown(self, message, *args, **kwargs):
#232	        self.do.unknown(message, *args, **kwargs)
#233	    def call_unknown(self, message, *args, **kwargs):
#234	        try:
#235	            return self.call.unknown(message, *args, **kwargs)
#236	        except NoneOfTheObserversRespond:
#237	            raise DeclineMessage