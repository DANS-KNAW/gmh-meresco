# -*- coding: utf-8 -*-

import sys
import os
from storagesplit import md5Split

# usage example: python uid2path.py tue:oai:library.tue.nl:692605

def getPath(id):
    splitted = md5Split((id, 'metadata'))
    print ("Path:", os.path.join(*splitted)[:-9])

if __name__ == "__main__":
    id = str(sys.argv[1])
    getPath(id)
