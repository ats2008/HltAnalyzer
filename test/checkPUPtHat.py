from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import random
from array import array
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product,QCDWeightCalc,EvtWeights,EvtWeightsV2

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
        
        

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,type=int,help='max events, <0 is no limit')
    parser.add_argument('--verbose','-v',action='store_true',help='verbose printouts')
    parser.add_argument('--out_file','-o',default="output.root",help='output filename')
    parser.add_argument('--weights','-w',default=None,help='weights filename')
    args = parser.parse_args()
    
    products = []
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","addPileupInfo")
    add_product(products,"geninfo","GenEventInfoProduct","generator")
    add_product(products,"pu_weight","double","stitchingWeight")
    add_product(products,"trig_res","edm::TriggerResults","TriggerResults::PUSkim")

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
    tree_hard_pt_hat = array("f",[0])
    tree_weight_v1 = array("f",[0])
    tree_weight_v2 = array("f",[0])
    tree_emweight_v2 = array("f",[0])
    tree_pass_em = array("i",[0])
    tree_pass_mu = array("i",[0])
    tree_weight_v2_cpp = array("f",[0])
    tree_filtweight_v2_cpp = array("f",[0])
    putree.Branch("nrPtHats",tree_nr_pt_hats,"nrPtHats/I")
    putree.Branch("hardPtHat",tree_hard_pt_hat,"hardPtHat/F")
    putree.Branch("ptHats",tree_pt_hats)
    putree.Branch("weightV1",tree_weight_v1,"weightV1/F")
    putree.Branch("weightV2",tree_weight_v2,"weightV2/F")
    putree.Branch("emWeightV2",tree_emweight_v2,"emWeightV2/F")
    putree.Branch("passEM",tree_pass_em,"passEM/I")
    putree.Branch("passMU",tree_pass_mu,"passMU/I")
    putree.Branch("weightV2CPP",tree_weight_v2_cpp,"weightV2CPP/F")
    putree.Branch("filtWeightV2CPP",tree_filtweight_v2_cpp,"filtWeightV2CPP/F")

    with open(args.weights) as f:
       import json
       weights = json.load(f)

    qcd_weight_calc = EvtWeightsV2(input_dict=weights) 
    qcd_weight_calc_cpp = ROOT.QCDWeightCalc(args.weights)
  #  qcd_weight_calc = QCDWeightCalc(weights['v2']['qcd'],use_em_filt=args.em_filt)
    weight_calc = EvtWeights(input_dict=weights["v1"],corr_for_pu=True)
    gen_filters = TrigTools.TrigResults(["Gen_QCDMuGenFilter",
                                         "Gen_QCDBCToEFilter",
                                         "Gen_QCDEmEnrichingFilter",
                                         "Gen_QCDEmEnrichingNoBCToEFilter"])
    
    for eventnr,event in enumerate(events):
        if eventnr%1000==0:
            print("{} / {}".format(eventnr,events.size()))

        if args.maxevents>0 and eventnr>args.maxevents:
            break

        evtdata.get_handles(event)
        pu_sum  = evtdata.get("pu_sum")
        geninfo = evtdata.get("geninfo")
        gen_filters.fill(evtdata)
        pt_hats = [x for x in pu_sum[3].getPU_pT_hats()]
        pt_hats.append(geninfo.qScale())
        pt_hats.sort(reverse=True)
        
        pass_em = gen_filters.result("Gen_QCDEmEnrichingNoBCToEFilter")
        pass_mu = gen_filters.result("Gen_QCDMuGenFilter")
      
        pt_hats_vec = ROOT.std.vector("float")()
        for pt_hat in pu_sum[3].getPU_pT_hats():
            pt_hats_vec.push_back(pt_hat)
        

        #weight = qcd_weight_calc.weight(evtdata)
     #   weight = qcd_weight_calc.weight_from_evt(evtdata)
        weight = qcd_weight_calc.weight_from_name("QCD",evtdata)
        weight_cpp = qcd_weight_calc_cpp.weight(geninfo.qScale(),pt_hats_vec,pass_em,pass_mu)
        weight_cpp_filt = qcd_weight_calc_cpp.filtWeight(geninfo.qScale(),pass_em,pass_mu)
        

        for histnr,pt_hat in enumerate(pt_hats):
            if histnr<len(hists):
                hists[histnr].Fill(pt_hat,weight)
        hist_sample.Fill(random.choice(pt_hats),weight)

        tree_pt_hats.clear()
        for pt_hat in pt_hats:
            tree_pt_hats.push_back(pt_hat)
        tree_nr_pt_hats = tree_pt_hats.size()
       # tree_weight_v1[0] = weight_calc.weight_from_evt(event.object(),evtdata)
    #    tree_weight_v1[0] = evtdata.get("pu_weight")[0]
        tree_weight_v1[0] = qcd_weight_calc.weight_from_name("QCD",evtdata,EvtWeightsV2.WeightType.V1)
        tree_weight_v2[0] = weight 
        tree_hard_pt_hat[0] = geninfo.qScale()
        tree_emweight_v2[0] = qcd_weight_calc.weight_from_name("QCD",evtdata,EvtWeightsV2.WeightType.V1)
        tree_pass_em[0] = pass_em
        tree_pass_mu[0] = pass_mu
        tree_weight_v2_cpp[0] = weight_cpp
        tree_filtweight_v2_cpp[0] = weight_cpp_filt
        
      
        putree.Fill()
        
       
       


    out_file.Write()
