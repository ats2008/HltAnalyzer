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
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

def make_val_hists(in_filenames,out_name,norm_to=None):
    evtdata = EvtData(phaseII_products,verbose=True)

    events = Events(in_filenames)

    weight = 1.
    if norm_to:
        weight = norm_to/events.size()

    out_file = ROOT.TFile(out_name,"RECREATE")

    cutbins = [HistTools.CutBin("et()","Et",[20,50,100]),
               HistTools.CutBin("eta()","Eta",[0,1.4442,None,1.57,2.5,3.0],do_abs=True)]

    hist_meta_data = {}
    desc = "Gen Matched Electrons"
    hists_genmatch = HistTools.create_histcoll(tag="GenMatch",cutbins=cutbins,desc=desc,meta_data=hist_meta_data)
    desc = "Gen Matched Electrons with Pixel Match"
    hists_genmatch_seed = HistTools.create_histcoll(tag="GenMatchSeed",cutbins=cutbins,desc=desc,meta_data=hist_meta_data)
    desc = "Gen Matched Electrons with GsfTrack"
    hists_genmatch_trk = HistTools.create_histcoll(add_gsf=True,tag="GenMatchTrk",cutbins=cutbins,desc=desc,meta_data=hist_meta_data)
    
    for event_nr,event in enumerate(events):
        if event_nr%500==0:
            print("processing event {} / {}".format(event_nr,events.size()))
        evtdata.get_handles(event)
        for egobj in evtdata.get("egtrigobjs"):

            gen_match = GenTools.match_to_gen(egobj.eta(),egobj.phi(),evtdata.handles.genparts.product(),pid=11)[0]
            if gen_match:
                gen_pt = gen_match.pt()
                hists_genmatch.fill(egobj,weight)
                if not egobj.seeds().empty():
                    hists_genmatch_seed.fill(egobj,weight)
                if not egobj.gsfTracks().empty():                    
                    hists_genmatch_trk.fill(egobj,weight)
                else:
                    gen_pt = -1

        gen_eles = GenTools.get_genparts(evtdata.get("genparts"))
        if len(gen_eles)!=2:
            print("event missing electrons",event_nr)
    
    out_file.cd()
    eff_hists = []
#    HistTools.make_effhists_fromcoll(numer=hists_genmatch_trk,denom=hists_eb_genmatch,tag="Trk",dir_=out_file,out_hists = eff_hists)                
 #   HistTools.make_effhists_fromcoll(numer=hists_genmatch_seed,denom=hists_eb_genmatch,tag="Seed",dir_=out_file,out_hists = eff_hists)
    out_file.Write()
    with open(out_name.replace(".root",".json"),'w') as f:
        json.dump(hist_meta_data,f)
            
    return event.size()
         #   print(GenTools.genparts_to_str(evtdata.get("genparts"),-1))
            #for genpart in evtdata.get("genparts"):
                #for mo in range(0,genpart.numberOfMothers()):
                    #ref = genpart.motherRef(0)
                    #print("sucess {}".format(ref.pt()))
              #  print("{} {} {} {} {}".format(genpart.pdgId(),
                #print("{} {} {} {} {}".format(egobj.pt(),egobj.eta(),egobj.phi(),egobj.gsfTracks()[0].pt(),gen_pt))

def set_style_att(hist,color=None,line_width=None,marker_style=None,line_style=None,marker_size=None):
    if color!=None:
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
    if line_width!=None:
        hist.SetLineWidth(line_width)
    if line_style!=None:
        hist.SetLineWidth(line_style)
    if marker_style!=None:
        hist.SetMarkerStyle(marker_style)
    if marker_size!=None:
        hist.SetMarkerSize(marker_size)
            
        
def plot_with_ratio(numer,denom,div_opt=""):
    numer_label = "tar"
    denom_label = "ref"

    set_style_att(numer,color=2,marker_style=4)
    set_style_att(denom,color=4,marker_style=8)

    ROOT.gStyle.SetOptStat(0)
    c1 = ROOT.TCanvas("c1","c1",900,750)
    c1.cd()
    spectrum_pad = ROOT.TPad("spectrumPad","newpad",0.01,0.30,0.99,0.99)
    spectrum_pad.Draw() 
    spectrum_pad.cd()
    spectrum_pad.SetGridx()
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
    ratio_pad.SetFillStyle(0)
    ratio_hist = numer.Clone("ratioHist")
    ratio_hist.SetDirectory(0)
    ratio_hist.Sumw2()
    ratio_hist.Divide(numer,denom,1,1,div_opt)

    set_style_att(ratio_hist,color=1,marker_style=8)
#    AnaFuncs::setHistAttributes(ratio_hist,1,1,8,1)
    ratio_hist.SetTitle("")
    #  ratio_hist.GetXaxis().SetLabelSize(ratio_hist.GetXaxis().GetLabelSize()*(0.99-0.33)/0.33)
    ratio_hist.GetXaxis().SetLabelSize(0.1)
    ratio_hist.GetXaxis().SetTitleSize(0.1)
    ratio_hist.GetXaxis().SetTitle(xaxis_title)
    ratio_hist.GetYaxis().SetLabelSize(0.1)
    ratio_hist.GetYaxis().SetTitleSize(0.1)
    ratio_hist.GetYaxis().SetTitleOffset(0.3) 
    ratio_hist.GetYaxis().SetTitle("ratio")   
    ratio_hist.GetYaxis().SetRangeUser(0.5,1.5)
    ratio_hist.GetYaxis().SetNdivisions(505)
    
    
    ratio_hist.Draw("EP")
    spectrum_pad.cd()
    return c1,spectrum_pad,ratio_pad,ratio_hist,leg

def gen_html(canvases_to_draw,html_body=None):
    
    html_str="""
<!DOCTYPE html>
<html lang="en">
<head>
    
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
 
<title>E/gamma Validation</title>
 
<script src="scripts/JSRootCore.js" type="text/javascript"></script>
 
<script type='text/javascript'> 
  var filename = "output.root";
  JSROOT.gStyle.fOptStat = 0
  JSROOT.OpenFile(filename, function(file) {{
    {canvas_draw_js}
  }});
  </script>
</head>
 
<body>
  {canvas_pads}
  
</body>
 
</html>
    """

    canvas_pad_str_base = '<div id="{name}" style="width:800px; height:600px"></div>'
    canvas_draw_str_base = """  
    file.ReadObject("{name}", function(obj) {{
       JSROOT.draw("{name}", obj, "");
    }});"""
    
    canvas_draw_str = "".join([canvas_draw_str_base.format(name=c) for c in canvases_to_draw])
    if html_body==None:
        canvas_pad_str = "".join([canvas_pad_str_base.format(name=c) for c in canvases_to_draw])
    else:
        canvas_pad_str = "\n".join(html_body)
    
    
    return html_str.format(canvas_draw_js=canvas_draw_str,canvas_pads=canvas_pad_str)


def compare_hists(ref_filename,tar_filename,tar_label="target",ref_label="reference",out_dir="./"):
    
    tar_file = ROOT.TFile.Open(tar_filename)
    ref_file = ROOT.TFile.Open(ref_filename)

    out_file = ROOT.TFile.Open(os.path.join(out_dir,"output.root"),"RECREATE")
    canvases_to_draw=[]

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
            c1 = res[0]
            c1.Update()
            canvas_name = "{}Canvas".format(key.GetName())
            c1.Write(canvas_name)
            canvases_to_draw.append(canvas_name)
            
            for suffex in [".C",".png"]:
                c1.Print(os.path.join(out_dir,"{}{}".format(key.GetName(),suffex)))
             
        else:
            print("ref hist",key.GetName(),"not found")

    html_str = gen_html(canvases_to_draw)
    with open(os.path.join(out_dir,"index.html"),'w') as f:
        f.write(html_str)

def compare_hists_indx(ref_filename,tar_filename,tar_label="target",ref_label="reference",out_dir="./"):
    
    tar_file = ROOT.TFile.Open(tar_filename)
    ref_file = ROOT.TFile.Open(ref_filename)

    with open(tar_filename.replace(".root",".json")) as f:
        index = json.load(f)
    
    out_file = ROOT.TFile.Open(os.path.join(out_dir,"output.root"),"RECREATE")
    canvases_to_draw=[]

    html_body = []
    for collname,coll in index.iteritems():
        html_body.append(coll['desc'])
        hists_sorted = sorted(coll['hists'],key=lambda k: k['name'])
        for hist_data in hists_sorted:
            #unicode strings fun...hence the str()
            hist_name = str(hist_data['name'])

            tar_hist = tar_file.Get(hist_name)
            ref_hist = ref_file.Get(hist_name)
            if ref_hist:
            
                res = plot_with_ratio(tar_hist,ref_hist,"")
                c1 = res[0]
                c1.Update()
                canvas_name = "{}Canvas".format(hist_name)
                c1.Write(canvas_name)
                canvases_to_draw.append(canvas_name)
                html_body.append('<div id="{name}" style="width:800px; height:600px"></div>'.format(name=canvas_name))
                for suffex in [".C",".png"]:
                    c1.Print(os.path.join(out_dir,"{}{}".format(hist_name,suffex)))
             
            else:
                print("ref hist",hist_name,"not found")

    html_str = gen_html(canvases_to_draw,html_body)
    with open(os.path.join(out_dir,"index.html"),'w') as f:
        f.write(html_str)

            
def get_filenames(input_filenames,prefix=""):
    output_filenames = []
    for filename in input_filenames:
        if not filename.endswith(".root"):
            with open(filename) as f:
                output_filenames.extend(['{}{}'.format(prefix,l.rstrip()) for l in f])
        else:
            output_filenames.append('{}{}'.format(prefix,filename))
    return output_filenames

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('--ref',nargs="+",help='input filename')
    parser.add_argument('--tar',nargs="+",help='input filename')
    parser.add_argument('--tar_prefix',default='file:',help='file prefix')
    parser.add_argument('--ref_prefix',default='file:',help='file prefix')
    parser.add_argument('--out_dir','-o',default="./",help='output dir')

    args = parser.parse_args()

 
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

#    ref_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.ref]
#    tar_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.tar]

    ref_filenames = get_filenames(args.ref,args.ref_prefix)
    tar_filenames = get_filenames(args.tar,args.tar_prefix)

  

    out_ref = os.path.join(args.out_dir,"ref.root")
    out_tar = os.path.join(args.out_dir,"tar.root")

    make_val_hists(ref_filenames,out_ref)
    make_val_hists(tar_filenames,out_tar)

#    compare_hists(tar_filename=out_tar,ref_filename=out_ref,out_dir=args.out_dir)

    compare_hists_indx(tar_filename=out_tar,ref_filename=out_ref,out_dir=args.out_dir)
