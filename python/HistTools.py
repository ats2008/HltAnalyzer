from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

class VarHist:
    def __init__(self,var_func,name,title,nbins,var_min,var_max,cut_func=None):
        self.var_func = var_func
        self.cut_func = cut_func
        self.hist = ROOT.TH1D(name,title,nbins,var_min,var_max)
        
    def passcut(self,obj):
        if self.cut_func:
            return self.cut_func(CoreTools.call_func(obj,self.var_func))
        else:
            return True
    
    def fill(self,obj):
        self.hist.Fill(CoreTools.call_func(obj,self.var_func))
    
class HistColl:
    def __init__(self,suffix):
        self.hists = []
        self.suffix = suffix

    def strip_suffix(self,name):
        start = name.rfind(self.suffix)
        if start!=-1:
            return name[0:start]
        else:
            return str(name)

    def add_hist(self,var_func,name,title,nbins,var_min,var_max,cut_func=None):
        self.hists.append(VarHist(var_func,"{name}{suffix}".format(name=name,suffix=self.suffix),title,nbins,var_min,var_max,cut_func))
    
    def fill(self,obj):
        cuts_failed = [i for i,v in enumerate(self.hists) if not v.passcut(obj)]
        
        for histnr,hist in enumerate(self.hists):
            if len(cuts_failed)==0 or len(cuts_failed)==1 and histnr in cuts_failed:
                hist.fill(obj)
    
    
def create_histcoll(is_barrel=True,add_gsf=False,tag=""):
    hist_coll = HistColl("{tag}Hist".format(tag=tag))
    hist_coll.add_hist("et()","et","Et Hist",20,0,100,lambda x: x>20)
    if is_barrel:
        hist_coll.add_hist("eta()","eta","Eta Hist",60,-3,3,lambda x: 0<abs(x)<1.4442)
    else:
        hist_coll.add_hist("eta()","eta","Eta Hist",60,-3,3,lambda x: 1.566<abs(x)<3.0)
    hist_coll.add_hist("phi()","phi","Phi Hist",64,-3.2,3.2)

    if add_gsf:
        hist_coll.add_hist("gsfTracks().at(0).pt()","gsfTrkPt","GsfTrk pt Hist",20,0,100)
    
    return hist_coll

def make_effhists_fromcoll(numer,denom,tag="",dir_=None,out_hists=[]):
    #building a map for numer hists
    numer_hist_map = {}
    for varhist in numer.hists:
        numer_hist_map[numer.strip_suffix(varhist.hist.GetName())] = varhist.hist
    
    for denom_varhist in denom.hists:
        hist_name = denom.strip_suffix(denom_varhist.hist.GetName())
        try:
            numer_hist = numer_hist_map[hist_name] 
            eff_hist = numer_hist.Clone("{name}{tag}EffHist".format(name=hist_name,tag=tag))
            eff_hist.Divide(numer_hist,denom_varhist.hist,1,1,"B")
            eff_hist.Draw()
            if dir_:
                eff_hist.SetDirectory(dir_)
            out_hists.append(eff_hist)
        except KeyError:
            print("hist {} not found".format(hist_name))
            print(numer_hist_map)
    return out_hists
 
