from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,help='max events, <0 is no limit')
    parser.add_argument
    args = parser.parse_args()

    products = []
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo","addPileupInfo")
    evtdata = EvtData(products,verbose=True)
    
    in_filenames = CoreTools.get_filenames(args.in_filename,args.prefix)
    events = Events(in_filenames)
    
    uniq_pu_evts = {}
    nr_dup_evts = 0
    nr_uniq_evts = 0
    expect_uniq_evts = 0
    for eventnr,event in enumerate(events):
        if eventnr%1000==0:
            expect_uniq_evts = eventnr*200*7
            print("number of events",eventnr,"number of unique PU events",nr_uniq_evts," expected unique events",expect_uniq_evts," number dups ",nr_dup_evts)

        if args.maxevents>0 and eventnr>args.maxevents:
            break


        evtdata.get_handles(event)
        pu_sum  = evtdata.get("pu_sum")
        for pu_bx in pu_sum:
            evt_ids = pu_bx.getPU_EventID()
            for evt_id in evt_ids:
                if evt_id.luminosityBlock() not in uniq_pu_evts:
                    uniq_pu_evts[evt_id.luminosityBlock()] = set()
                
                if evt_id.event() in uniq_pu_evts[evt_id.luminosityBlock()]:
                    nr_dup_evts += 1
                else:
                    nr_uniq_evts +=1
                    uniq_pu_evts[evt_id.luminosityBlock()].add(evt_id.event())



    print("number of events",events.size(),"number of unique PU events",nr_uniq_evts," expected unique events",expect_uniq_evts," number dups ",nr_dup_evts)
