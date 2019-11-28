## begin license ##
#
#
## end license ##

from meresco.components import Converter


class UiaConverter(Converter):
    """ "Upload Identifier Aware Converter" (UiaConverter) overrides meresco.components.Converter#_convertArgs().
    The uploadid (kwargs['identifier'] from the calling message should now be available in the #_convert() method as self._uploadid). """

    def __init__(self, fromKwarg, toKwarg=None, name=None):
        Converter.__init__(self, name=name, fromKwarg=fromKwarg, toKwarg=toKwarg)
        self._uploadid = None

    def _convertArgs(self, *args, **kwargs):
        """ Overrides meresco.components.Converter#_convertArgs() to be able to extract the meresco uploadid. """
        try:
            oldvalue = kwargs[self._fromKwarg]
            self._uploadid = kwargs['identifier']
        except KeyError:
            pass
        else:
            del kwargs[self._fromKwarg]
            kwargs[self._toKwarg] = self._convert(oldvalue)
        return args, kwargs