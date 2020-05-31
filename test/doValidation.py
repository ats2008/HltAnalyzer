from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import json
import re
import os

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,std_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

def make_val_hists(in_filenames,out_name):
    evtdata = EvtData(std_products,verbose=True)

    events = Events(in_filenames)

    out_file = ROOT.TFile(out_name,"RECREATE")

    hists_eb_genmatch = HistTools.create_histcoll(is_barrel=True,tag="EBGenMatch")
    hists_ee_genmatch = HistTools.create_histcoll(is_barrel=False,tag="EEGenMatch")
    
    hists_eb_genmatch_seed = HistTools.create_histcoll(is_barrel=True,tag="EBGenMatchSeed")
    hists_ee_genmatch_seed = HistTools.create_histcoll(is_barrel=False,tag="EEGenMatchSeed")
    hists_eb_genmatch_trk = HistTools.create_histcoll(is_barrel=True,add_gsf=True,tag="EBGenMatchTrk")
    hists_ee_genmatch_trk = HistTools.create_histcoll(is_barrel=False,add_gsf=True,tag="EEGenMatchTrk")
    
    for event_nr,event in enumerate(events):
        evtdata.get_handles(event)
        for egobj in evtdata.get("egtrigobjs"):
            if egobj.gsfTracks().size()!=0:
                gen_match = GenTools.match_to_gen(egobj.eta(),egobj.phi(),evtdata.handles.genparts.product(),pid=11)[0]
                if gen_match:
                    gen_pt = gen_match.pt()
                    hists_eb_genmatch.fill(egobj)
                    hists_ee_genmatch.fill(egobj)
                    
                    if not egobj.seeds().empty():
                        hists_eb_genmatch_seed.fill(egobj)
                        hists_ee_genmatch_seed.fill(egobj)
                    else:
                        print("ele failed seed")
                    if not egobj.gsfTracks().empty():                    
                        hists_eb_genmatch_trk.fill(egobj)
                        hists_ee_genmatch_trk.fill(egobj)

                else:
                    gen_pt = -1

        gen_eles = GenTools.get_genparts(evtdata.get("genparts"))
        if len(gen_eles)!=2:
            print("event missing electrons",event_nr)
    
    out_file.cd()
    eff_hists = []
    HistTools.make_effhists_fromcoll(numer=hists_eb_genmatch_trk,denom=hists_eb_genmatch,tag="EBTrk",dir_=out_file,out_hists = eff_hists)
    HistTools.make_effhists_fromcoll(numer=hists_ee_genmatch_trk,denom=hists_ee_genmatch,tag="EETrk",dir_=out_file,out_hists = eff_hists)
    HistTools.make_effhists_fromcoll(numer=hists_eb_genmatch_seed,denom=hists_eb_genmatch,tag="EBSeed",dir_=out_file,out_hists = eff_hists)
    HistTools.make_effhists_fromcoll(numer=hists_ee_genmatch_seed,denom=hists_ee_genmatch,tag="EESeed",dir_=out_file,out_hists = eff_hists)
    out_file.Write()
            
         #   print(GenTools.genparts_to_str(evtdata.get("genparts"),-1))
            #for genpart in evtdata.get("genparts"):
                #for mo in range(0,genpart.numberOfMothers()):
                    #ref = genpart.motherRef(0)
                    #print("sucess {}".format(ref.pt()))
              #  print("{} {} {} {} {}".format(genpart.pdgId(),
                #print("{} {} {} {} {}".format(egobj.pt(),egobj.eta(),egobj.phi(),egobj.gsfTracks()[0].pt(),gen_pt))
        
def plot_with_ratio(numer,denom,div_opt=""):
    numer_label = "ref"
    denom_label = "tar"
    c1 = ROOT.TCanvas("c1","c1",900,750)
    c1.cd()
    spectrum_pad = ROOT.TPad("spectrumPad","newpad",0.01,0.30,0.99,0.99)
    spectrum_pad.Draw() 
    spectrum_pad.cd()
    xaxis_title = denom.GetXaxis().GetTitle()
    denom.GetXaxis().SetTitle()
    denom.Draw("EP")
    numer.Draw("EP SAME")
    leg = ROOT.TLegend(0.115,0.766,0.415,0.888)
    leg.AddEntry(numer,numer_label,"LP")
    leg.AddEntry(denom,denom_label,"LP")
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.Draw()
    
    c1.cd()
    ratio_pad = ROOT.TPad("ratioPad", "newpad",0.01,0.01,0.99,0.33)
    ratio_pad.Draw()
    ratio_pad.cd()
    ratio_pad.SetTopMargin(0.05)
    ratio_pad.SetBottomMargin(0.3)
    #    ratio_pad.SetRightMargin(0.1)
    ratio_pad.SetFillStyle(0)
    ratio_hist = numer.Clone("ratioHist")
    ratio_hist.Divide(numer,denom,1,1,div_opt)
#    ratio_hist = make_ratio_hist(numer.hist,denom.hist,div_opt)

#    AnaFuncs::setHistAttributes(ratio_hist,1,1,8,1)
    ratio_hist.SetTitle("")
    #  ratio_hist.GetXaxis().SetLabelSize(ratio_hist.GetXaxis().GetLabelSize()*(0.99-0.33)/0.33)
    ratio_hist.GetXaxis().SetLabelSize(0.1)
    ratio_hist.GetXaxis().SetTitleSize(0.1)
    ratio_hist.GetXaxis().SetTitle(xaxis_title)
    ratio_hist.GetYaxis().SetLabelSize(0.1)
    ratio_hist.GetYaxis().SetTitleSize(0.1)
    ratio_hist.GetYaxis().SetTitleOffset(0.65) 
    ratio_hist.GetYaxis().SetTitle("ratio")   
  
    ratio_hist.Draw()
    spectrum_pad.cd()
    return c1,spectrum_pad,ratio_pad,ratio_hist,leg


def compare_hists(ref_filename,tar_filename,tar_label="target",ref_label="reference",out_dir="./"):
    
    tar_file = ROOT.TFile.Open(tar_filename)
    ref_file = ROOT.TFile.Open(ref_filename)

    out_file = ROOT.TFile.Open(os.path.join(out_dir,"output.root"),"RECREATE")
    
    for key in tar_file.GetListOfKeys():
        tar_hist = tar_file.Get(key.GetName())
        ref_hist = ref_file.Get(key.GetName())
        if ref_hist:

    
            tar_hist.SetLineColor(2)
            tar_hist.SetMarkerStyle(4)
            tar_hist.SetMarkerColor(2)

            ref_hist.SetLineColor(4)
            ref_hist.SetMarkerStyle(8)
            ref_hist.SetMarkerColor(4)
            res = plot_with_ratio(tar_hist,ref_hist,"")
            res.Update()
            raw_input("press enter to continue")

            tar_hist.Draw("EP")
            ref_hist.Draw("SAME EP")
            ROOT.c1.Update()
            ROOT.c1.Write("{}Canvas".format(key.GetName()))
            for suffex in [".C",".png"]:
                ROOT.c1.Print(os.path.join(out_dir,"{}{}".format(key.GetName(),suffex)))

        else:
            print("ref hist",key.GetName(),"not found")
            
if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('--ref',nargs="+",help='input filename')
    parser.add_argument('--tar',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out_dir','-o',default="./",help='output dir')

    args = parser.parse_args()

    print(args.ref)
    print(args.tar)

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    ref_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.ref]
    tar_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.tar]

    out_ref = os.path.join(args.out_dir,"ref.root")
    out_tar = os.path.join(args.out_dir,"tar.root")

    #make_val_hists(ref_filenames_with_prefix,out_ref)
    #make_val_hists(tar_filenames_with_prefix,out_tar)

    compare_hists(tar_filename=out_tar,ref_filename=out_ref,out_dir=args.out_dir)
    
