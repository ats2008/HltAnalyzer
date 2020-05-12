from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import sys

def load_fwlitelibs():
    oldargv = sys.argv[:]
    sys.argv = [ '-b-' ]
    sys.argv = oldargv
    ROOT.gSystem.Load("libFWCoreFWLite.so");
    ROOT.gSystem.Load("libDataFormatsFWLite.so");
    ROOT.FWLiteEnabler.enable()
