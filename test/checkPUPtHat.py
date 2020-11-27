from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import random
from array import array
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product,QCDWeightCalc,EvtWeights

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
    add_product(products,"geninfo","GenEventInfoProduct","generator")
    add_product(products,"pu_weight","double","stitchingWeight")

    evtdata = EvtData(products,verbose=args.verbose)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)
    events = Events(in_filenames)
    print("setup events")
    out_file = ROOT.TFile(args.out_file,"RECREATE")
    hists = []
    for histnr in range(0,100):
        hists.append(ROOT.TH1D("maxPtHat{}".format(histnr),"maxPtHat{}".format(histnr),200,0.,200.))

    hist_sample = ROOT.TH1D("randPtHat","randPtHat",200,0.,200)

    putree = ROOT.TTree("puTree","")
    tree_pt_hats = ROOT.std.vector("float")()
    tree_nr_pt_hats = array("i",[0])
    tree_weight_v1 = array("f",[0])
    tree_weight_v2 = array("f",[0])
    putree.Branch("nrPtHats",tree_nr_pt_hats,"nrPtHats/I")
    putree.Branch("ptHats",tree_pt_hats)
    putree.Branch("weightV1",tree_weight_v1,"weightV1/F")
    putree.Branch("weightV2",tree_weight_v2,"weightV2/F")
    
    with open("weights_test_qcdV4.json") as f:
       import json
       weights = json.load(f)

    qcd_weight_calc = QCDWeightCalc(weights["v2"]["qcd"])
    weight_calc = EvtWeights(input_dict=weights["v1"],corr_for_pu=True)
    
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

        for histnr,pt_hat in enumerate(pt_hats):
            if histnr<len(hists):
                hists[histnr].Fill(pt_hat,weight)
        hist_sample.Fill(random.choice(pt_hats),weight)

        tree_pt_hats.clear()
        for pt_hat in pt_hats:
            tree_pt_hats.push_back(pt_hat)
        tree_nr_pt_hats = tree_pt_hats.size()
#        tree_weight_v1[0] = weight_calc.weight_from_evt(event.object(),evtdata)
        tree_weight_v1[0] = evtdata.get("pu_weight")[0]
        tree_weight_v2[0] = weight

        putree.Fill()
        
       
       


    out_file.Write()
