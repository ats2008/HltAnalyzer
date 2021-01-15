from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import ROOT
import glob
import os
import argparse
import shutil
import json
import re
from enum import IntEnum

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, add_product
import Analysis.HLTAnalyserPy.CoreTools as CoreTools

class MCSample:
    class ProcType(IntEnum):
        Unknown=0
        MB = 1
        QCD = 2
        DY = 3
        WJets = 4
    class FiltType(IntEnum):
        Incl=0
        Em = 1
        Mu = 2

    def __init__(self,mc_type=ProcType.Unknown,
                 filt_type=FiltType.Incl,
                 min_pthat=0,max_pthat=9999):
        self.mc_type = mc_type
        self.filt_type = filt_type
        self.min_pthat = min_pthat
        self.max_pthat = max_pthat
    
    def __str__(self):
        return "ProcType {s.mc_type} FiltType {s.filt_type}  min pthat {s.min_pthat} max pthat {s.max_pthat}".format(s=self)

        
class MCSampleGetter:
    def __init__(self):
        self.last_type = MCSample()
        self.last_file = None
        self.root_func_init = False
        self.getval_re = re.compile(r'[= ]([0-9.]+)')

    def get_type(self,evtdata):
        """
        this is keyed to the TSG samples which are all pythia except WJets
        it also assumes a given file will only contain a given process
        """

        if self.last_file==evtdata.event.object().getTFile().GetName():
            return last_type
        
        self.last_file==evtdata.event.object().getTFile().GetName()
        
        sig_id = evtdata.get("geninfo").signalProcessID()
        if sig_id >=101 and sig_id<=106:
            self.last_type = MCSample(MCSample.ProcType.MB)
        elif sig_id>=111 and sig_id<=124:
            if not self.root_func_init:
                ROOT.gInterpreter.Declare("""
#include "FWCore/ParameterSet/interface/ParameterSet.h"
int qcdMCFiltType(edm::ParameterSet& pset,const int inclCode,const int emCode,const int muCode){
   if(pset.exists("emenrichingfilter")) return emCode;
   else if(pset.exists("mugenfilter")) return muCode;
   else return inclCode;
}
                """)  
                ROOT.gInterpreter.Declare("""
#include "FWCore/ParameterSet/interface/ParameterSet.h"
std::vector<std::string> getGenProcParam(edm::ParameterSet& pset){
   const auto& genPSet = pset.getParameterSet("generator");
   const auto& pythPSet = genPSet.getParameterSet("PythiaParameters");
   return pythPSet.getParameter<std::vector<std::string> >("processParameters");
}
                """)
                self.root_func_init = True
            cfg = ROOT.edm.ProcessConfiguration()  
            proc_hist = events.object().processHistory() 
            proc_hist.getConfigurationForProcess("SIM",cfg) 
            cfg_pset = evtdata.event.object().parameterSet(cfg.parameterSetID())  
            filt_type = ROOT.qcdMCFiltType(cfg_pset,MCSample.FiltType.Incl,MCSample.FiltType.Em,
                                           MCSample.FiltType.Mu)
            proc_params = ROOT.getGenProcParam(cfg_pset)
            min_pthat = 0
            max_pthat = 9999
            for param in proc_params:
                if param.lstrip().startswith("PhaseSpace:pTHatMin"):
                    min_pthat = float(self.getval_re.search(param).group(1))
                if param.lstrip().startswith("PhaseSpace:pTHatMax"):
                    max_pthat = float(self.getval_re.search(param).group(1))

            self.last_type = MCSample(MCSample.ProcType.QCD,filt_type,min_pthat,max_pthat)

        elif sig_id==221:
            self.last_type = MCSample(MCSample.ProcType.DY)
        elif sig_id==9999:
            #not this just means its an external generator but our only one is WJets 
            self.last_type = MCSample(MCSample.ProcType.WJets)
        else:
            self.last_type = MCSample(MCSample.ProcType.Unknown)
        
        return self.last_type

def get_xsec(mcdata):
    if mcdata.mc_type == MCSample.ProcType.DY: return 5795.0
    if mcdata.mc_type == MCSample.ProcType.WJets: return 56990.0
    if mcdata.mc_type == MCSample.ProcType.MB: return 80.0E9
    if mcdata.mc_type == MCSample.ProcType.QCD: return get_qcd_xsec(mcdata.min_pthat,mcdata.max_pthat)
    return 1.

def get_qcd_em_filt_eff(min_pt,max_pt):
    filt_effs = {
        "0to9999" : 1.0,
        "15to20" : 0.001569,
        "20to30" : 0.01232,
        "30to50" : 0.05929,
        "50to80" : 0.1253,
        "80to120" : 0.1547,
        "120to170" : 0.1634,
        "170to300" : 0.1593,
        "300to470" : 1.0,
        "470to600" : 1.0,
        "600to9999" : 1.0,
        "300to9999" : 1.0
    }
    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return filt_effs[key]
    except KeyError:
        print("{} not found".format(key))
        return 0.

def get_qcd_filt_effs(min_pt,max_pt):
    
    filt_effs = {
        "80to120": {
            "mu_filt_eff": 0.0219,
            "mu_em_filt_eff": 0.1367,
            "em_filt_eff": 0.1563,
            "em_mu_filt_eff": 0.0177
        },
        "170to300": {
            "mu_filt_eff": 0.0358,
            "mu_em_filt_eff": 0.1426,
            "em_filt_eff": 0.1595,
            "em_mu_filt_eff": 0.0316
        },
        "50to80": {
            "mu_filt_eff": 0.0146,
            "mu_em_filt_eff": 0.1096,
            "em_filt_eff": 0.1259,
            "em_mu_filt_eff": 0.0108
        },
        "30to50": {
            "mu_filt_eff": 0.0082,
            "mu_em_filt_eff": 0.0491,
            "em_filt_eff": 0.0593,
            "em_mu_filt_eff": 0.0059
        },
        "15to20": {
            "mu_em_filt_eff": 0.0012,
            "em_mu_filt_eff": 0.0015,
            "em_filt_eff" : 0.001569,
            "mu_filt_eff" : 0.00328
        },
        "20to30": {
            "mu_filt_eff": 0.0043,
            "mu_em_filt_eff": 0.01,
            "em_filt_eff": 0.0122,
            "em_mu_filt_eff": 0.0031
        },
        "120to170": {
            "mu_filt_eff": 0.0292,
            "mu_em_filt_eff": 0.1417,
            "em_filt_eff": 0.1635,
            "em_mu_filt_eff": 0.0245
        },
        "300to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "0to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "300to470": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "470to600": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "600to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        }
    }
    
    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return filt_effs[key]
    except KeyError:
        print("{} not found".format(key))
        return {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        }   
        
        

def get_qcd_xsec(min_pt,max_pt):
    xsecs = {
        "0to9999" : 80.0E9,
        "15to20" : 923300000.0,
        "20to30" : 436000000.0,
        "30to50" : 118400000.0,
        "50to80" : 17650000.0,
        "80to120" : 2671000.0,
        "120to170" : 469700.0,
        "170to300" : 121700.0,
        "300to470" : 8251.0,
        "470to600" : 686.4,
        "600to9999" : 244.8,
        "300to9999" : 8251.0 + 686.4 + 244.8
    }
    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return xsecs[key]
    except KeyError:
        print("{} not found".format(key))
        return 0.
    

def qcd_weights_v2(output_data,nrevents,mcdata):
    output_entry = None
    min_pt,max_pt = mcdata.min_pthat,mcdata.max_pthat
    for entry in output_data:
        if min_pt == entry['min_pt']:
            output_entry  = entry
            break
    if not output_entry:
        output_entry = {
            'min_pt' : min_pt,'max_pt' : max_pt, 'xsec' : get_qcd_xsec(min_pt,max_pt),
            'nr_inclusive' : 0, 'nr_em' : 0, 'nr_mu' : 0
        }
        output_entry.update(get_qcd_filt_effs(min_pt,max_pt))
        
        output_data.append(output_entry)
    
    if mcdata.filt_type==MCSample.FiltType.Em:
        output_entry['nr_em'] += nrevents
    elif mcdata.filt_type==MCSample.FiltType.Mu:
        output_entry['nr_mu'] += nrevents
    else:
        output_entry['nr_inclusive'] = nrevents
    
def fill_weights_dict_v2(weights_dict,nrevents,mcdata):
    if mcdata.mc_type == MCSample.ProcType.QCD or mcdata.mc_type == MCSample.ProcType.MB:
        qcd_weights_v2(weights_dict['qcd'],nrevents,mcdata)
    else:
        key = ""
        if mcdata.mc_type == MCSample.ProcType.DY: key = "dy"
        if mcdata.mc_type == MCSample.ProcType.WJets: key = "wjets"
        
        if not weights_dict[key]:
            weights_dict[key].append({"nrtot": 0, "xsec": get_xsec(mcdata)})
        weights_dict[key]["nrtot"]+=nrevents

        
    return weights_dict
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tries to open every root file in sub dir')
    parser.add_argument('in_filenames',nargs="+",help='input files')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default='weights.json',help='output weights json')
    parser.add_argument('--direct','-d',action='store_true',help='read nrtot directly from tree entries')
                             
    args = parser.parse_args()
    
    products = []
    add_product(products,"geninfo","GenEventInfoProduct","generator")
    evtdata = EvtData(products)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)

    weights_dict = {"v2" : { "dy" : [], "qcd": [], "wjets" : [] } }
    #we always need a MB entry so force it to be created
    fill_weights_dict_v2(weights_dict['v2'],0.,MCSample(MCSample.ProcType.MB))

    mc_type_getter = MCSampleGetter()
    for in_filename in in_filenames:
        events = Events(in_filename)          
        if events.size()==0: 
            continue
        events.to(0)
        evtdata.get_handles(events)
        mcinfo = mc_type_getter.get_type(evtdata)
        fill_weights_dict_v2(weights_dict["v2"],events.size(),mcinfo)
        
    weights_dict['v2']['qcd'].sort(key=lambda x : x['min_pt'])
    with open(args.out,'w') as f:
        json.dump(weights_dict,f)
        
    
