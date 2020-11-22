from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import random
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product,QCDWeightCalc

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

        
        

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,type=int,help='max events, <0 is no limit')
    parser.add_argument('--verbose','-v',action='store_true',help='verbose printouts')
    parser.add_argument('--out_file','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    
    products = []
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","addPileupInfo")
    evtdata = EvtData(products,verbose=args.verbose)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)
    events = Events(in_filenames)
    
    out_file = ROOT.TFile(args.out_file,"RECREATE")
    hists = []
    for histnr in range(0,100):
        hists.append(ROOT.TH1D("maxPtHat{}".format(histnr),"maxPtHat{}".format(histnr),200,0.,200.))

    hist_sample = ROOT.TH1D("randPtHat","randPtHat",200,0.,200)

    with open("weights_test_qcd.json") as f:
       import json
       weights = json.load(f)

    qcd_weight_calc = QCDWeightCalc(weights["v2"]["qcd"])

    for eventnr,event in enumerate(events):
        if eventnr%1000==0:
            print("{} / {}".format(eventnr,events.size()))

        if args.maxevents>0 and eventnr>args.maxevents:
            break

        evtdata.get_handles(event)
        pu_sum  = evtdata.get("pu_sum")
        geninfo = evtdata.get("geninfo")
        pt_hats = [x for x in pu_sum[3].getPU_pT_hats()]
        pt_hats.append(geninfo.qScale())
        pt_hats.sort(reverse=True)

        weight = qcd_weight_calc.weight(evtdata)

        for histnr,max_pt_hat in enumerate(pt_hats):
            if histnr<len(hists):
                hists[histnr].Fill(pt_hat,weight)
        hist_sample.Fill(random.choice(pt_hats),weight)

    out_file.Write()
