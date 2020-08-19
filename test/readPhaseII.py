from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import json
import re
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()

    evtdata = EvtData(phaseII_products,verbose=True)
    
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)
    
    print("number of events",events.size())
