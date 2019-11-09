# -*- coding: utf-8 -*-
from hashlib import md5


class Md5HashDistributeStrategy(object):

    @classmethod
    def split(self, (identifier, partName)):
        result = [identifier]
        if ':' in identifier:
            first, second = identifier.split(':', 1)
            md5string = md5(identifier).hexdigest()
            result = [first, md5string[0:2], md5string[2:4], second]
        if partName != None:
            return result +[partName]
        return result    
    
    @classmethod
    def join(self, parts):
        if parts and len(parts) == 5:
            return ('%s:%s' %(parts[0], parts[3]), parts[-1])
        raise MD5JoinError('md5Join Error. Need 5 parts' + str(parts))


def md5Split((identifier, partName)):
    result = [identifier]
    if ':' in identifier:
        first, second = identifier.split(':', 1)
        md5string = md5(identifier).hexdigest()
        result = [first, md5string[0:2], md5string[2:4], second]
    if partName != None:
        return result +[partName]
    return result

def md5Join(parts):
    if parts and len(parts) == 5:
        return ('%s:%s' %(parts[0], parts[3]), parts[-1])
    raise MD5JoinError('md5Join Error. Need 5 parts' + str(parts))

class MD5JoinError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)