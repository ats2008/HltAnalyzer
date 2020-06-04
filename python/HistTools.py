from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

class CutBin:
    def __init__(self,var_func,var_label,bins,do_abs=False):
        self.var_func = var_func
        self.var_label = var_label
        self.do_abs = do_abs
        self.bins = []

        for idx,bin_low in enumerate(bins[:-1]):
            bin_high = bins[idx+1]
            print(var_func,var_label,bin_low,bin_high)
            if bin_low!=None and bin_high!=None:
                self.bins.append([bin_low,bin_high])
       
    def get_binnr(self,obj):
        var = CoreTools.call_func(obj,self.var_func)
        if self.do_abs:
            var = abs(var)

        print(self.var_func,self.do_abs,var)
        for bin_nr,bin_range in enumerate(self.bins):
            print("bin nr",bin_nr,"range ",bin_range)
            if var>=bin_range[0] and var<bin_range[1]:
                print("reutring bin_nr")
                return bin_nr
        return None

    def get_bin_str(self,binnr):
        return "{}{}{}".format(self.bins[binnr][0],self.var_label,self.bins[binnr][1]).replace(".","p").replace("-","M")

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
    
    def fill(self,obj,weight=1.):
        self.hist.Fill(CoreTools.call_func(obj,self.var_func),weight)

class VarHistBinned:

    def init_hists(self,hists,cutbins,bin_suffix,*args,**kwargs):
        for bin_nr,bin_range in enumerate(cutbins[0].bins):
            hists.append([])
            newbin_suffix = "{}{}Bin{}".format(bin_suffix,cutbins[0].var_label,bin_nr)
            if cutbins[1:]:
                self.init_hists(hists[-1],cutbins[1:],newbin_suffix,*args,**kwargs)
            else:
                name = "{name}{suffix}".format(name=args[1],suffix=newbin_suffix)
                new_args = args[:1] + (name,) + args[2:]
                hists[-1] = VarHist(*new_args,**kwargs)
            

    def __init__(self,cutbins,*args,**kwargs):
        self.cutbins = cutbins
        self.hists = []
        self.init_hists(self.hists,self.cutbins,"",*args,**kwargs)
        
    def _fill(self,obj,hists,cutbins,weight=1.):
        bin_nr = cutbins[0].get_binnr(obj)
        if bin_nr!=None:
            if cutbins[1:]:
                self._fill(obj,hists[bin_nr],cutbins[1:],weight)
            else:
                hists[bin_nr].fill(obj,weight)
            
    def fill(self,obj,weight=1.):
        self._fill(obj,self.hists,self.cutbins,weight)



class HistCollData: 
    def setval(self,**kwargs):
        for key,value in kwargs.items():
            if hasattr(self,key):
                setattr(self,key,value)
            else:
                raise AttributeError("HistCollData has no attribute {}".format(key))

    def __init__(self,**kwargs):
        self.descript = ""
        self.norm_val = 0.
        self.label = ""
        self.is_normable = True
        self.is_effhist = False
        self.display = True
        self.hist_names = []
        self.setval(**kwargs)
    

class HistColl:
    def __init__(self,suffix,label="",descript="",cutbins=None):
        self.hists = []
        self.suffix = suffix
        self.metadata = HistCollData(label=label,descript=descript)
        self.cutbins = cutbins

    def strip_suffix(self,name):
        start = name.rfind(self.suffix)
        if start!=-1:
            return name[0:start]
        else:
            return str(name)

    def add_hist_old(self,var_func,name,title,nbins,var_min,var_max,cut_func=None):
        self.hists.append(VarHist(var_func,"{name}{suffix}".format(name=name,suffix=self.suffix),title,nbins,var_min,var_max,cut_func))

    def add_hist(self,*args,**kwargs):
        name = "{name}{suffix}".format(name=args[1],suffix=self.suffix)
        new_args = args[:1] + (name,) + args[2:]
        self.hists.append(VarHistBinned(self.cutbins,*new_args,**kwargs))

    
    def fill(self,obj,weight=1.):
        for histnr,hist in enumerate(self.hists):
            hist.fill(obj,weight)

    
def create_histcoll(add_gsf=False,tag="",label="",descript="",cutbins=None):
    hist_coll = HistColl("{tag}Hist".format(tag=tag),label=label,descript=descript,cutbins=cutbins)
    hist_coll.add_hist("et()","et",";E_{T} [GeV];entries",20,0,100)
    hist_coll.add_hist("eta()","eta",";#eta;entries",60,-3,3)
    hist_coll.add_hist("phi()","phi",";#phi [rad];entries",64,-3.2,3.2)

    if add_gsf:
        hist_coll.add_hist("gsfTracks().at(0).pt()","gsfTrkPt",";GsfTrk p_{T} [GeV];entries",20,0,100)
    
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
 
