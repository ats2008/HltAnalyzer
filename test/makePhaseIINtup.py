from array import array
import argparse
import sys
from DataFormats.FWLite import Events, Handle
import ROOT
from functools import partial

from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, EvtWeights, phaseII_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

def fix_hgcal_hforhe(obj,evtdata):
    layerclus = evtdata.get("hglayerclus")
    hforhe = ROOT.HGCalClusterTools.hadEnergyInCone(obj.eta(),obj.phi(),layerclus,0,0.15,0.,0.)
    obj.setVar("hltEgammaHGCALIDVarsUnseeded_hForHOverE",hforhe,True)
    

def get_h_for_he(obj):
    if(abs(obj.eta())<1.4442):
        return obj.var("hltEgammaHoverEUnseeded",0)
    else:
        return obj.var("hltEgammaHGCALIDVarsUnseeded_hForHOverE",0)

def get_hsum_for_he(obj):
    return obj.var("hltEgammaHoverEUnseeded",0) + obj.var("hltEgammaHGCALIDVarsUnseeded_hForHOverE",0)
        
def treetype_to_arraytype(treetype):
    if treetype=='I': 
        return 'i'
    if treetype=='i': 
        return 'I'
    elif treetype=='F':
        return 'f'
    else:
        raise ValueError("undefined type code",treetype)

def make_leaf_name(name,type_,sizename=None):
    """converts a names to a leaf string for a branch
    goes to the format {name}/{type_} or the format {name}[sizename]/{type_}
    also changes '-' to '_'
    """
    array_str = "[{sizename}]".format(sizename=sizename) if sizename else ""    
    return '{}{}/{}'.format(name,array_str,type_).replace('-','_')
     
class Func:
    def __init__(self,func):
        self.func_str = None
        self.func_obj = None
        
        if type(func)==str:
            self.func_str = func
        else:
            self.func_obj = func

    def val(self,obj):
        if self.func_str:
            return CoreTools.call_func(obj,self.func_str)
        elif self.func_obj:       
            return self.func_obj.func(obj,*self.func_obj.args,**self.func_obj.keywords)
        else:
            return None

class TreeVar:
    def __init__(self,tree,varnametype,func,maxsize=1,sizevar=""):
        self.varname = varnametype.split("/")[0]
        self.vartype = varnametype.split("/")[1]
        self.func = func
        self.data = array(treetype_to_arraytype(self.vartype),[0]*maxsize)
        self.sizevar = sizevar
        self.create_branch(tree)

    def create_branch(self,tree):       
        tree.Branch(self.varname,self.data,make_leaf_name(self.varname,self.vartype,self.sizevar))
        
    def fill(self,obj,objnr=0):
        self.data[objnr] = self.func.val(obj)
        
    def clear(self):
        for n,x in enumerate(self.data):
            self.data[n] = 0

class EgHLTTreeData:
    def __init__(self,tree_name,min_et=0.):
        self.tree = ROOT.TTree(tree_name,'')
        self.min_et = min_et
        self.initialised = False

    def _init_tree(self,weights):
        self.evtvars = [
            TreeVar(self.tree,"runnr/i",Func("eventAuxiliary().run()")),
            TreeVar(self.tree,"lumiSec/i",Func("eventAuxiliary().luminosityBlock()")),
            TreeVar(self.tree,"eventnr/i",Func("eventAuxiliary().event()")),
        
        ]
        if weights:
            self.evtvars.append(TreeVar(self.tree,"weight/F",Func(partial(weights.weight_from_evt))))
            
        egobjnr_name = "nrEgObjs"
        max_egs = 100
     #   self.egobj_nr = TreeVar(self.tree,egobjnr_name+"/i",Func(partial(ROOT.vector(ROOT.reco.EgTrigSumObj).size)))
        self.egobj_nr = TreeVar(self.tree,egobjnr_name+"/i",Func(partial(len)))
       
        vars_ = {
            'et/F' : Func(partial(ROOT.reco.EgTrigSumObj.et)),
            'energy/F' : Func(partial(ROOT.reco.EgTrigSumObj.energy)),
            'eta/F' : Func(partial(ROOT.reco.EgTrigSumObj.eta)),
            'phi/F' : Func(partial(ROOT.reco.EgTrigSumObj.phi)),
            'sigmaIEtaIEta/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaClusterShapeUnseeded_sigmaIEtaIEta5x5",0)),
            'ecalPFIsol/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEcalPFClusterIsoUnseeded",0)),
            'hcalPFIsol/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaHcalPFClusterIsoUnseeded",0)),
            'trkIsolV0/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEleGsfTrackIsoUnseeded",0)),
            'trkIsolV6/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEleGsfTrackIsoV72UnseededV6",0)),
            'trkIsolV72/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEleGsfTrackIsoV72Unseeded",0)),
            'trkChi2/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_Chi2",0)),
            'trkMissHits/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_MissingHits",0)),
            'trkValidHits/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_ValidHits",0)),
            'invESeedInvP/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_OneOESeedMinusOneOP",0)),
            'invEInvP/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_OneOESuperMinusOneOP",0)),
            'trkDEta/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_Deta",0)),
            'trkDEtaSeed/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_DetaSeed",0)),
            'trkDPhi/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_DetaSeed",0)),
            'rVar/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_rVar',0)),
            'sigma2uu/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2uu',0)),
            'sigma2vv/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2vv',0)),
            'sigma2ww/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2ww',0)),
            'sigma2xx/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2xx',0)),
            'sigma2xy/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2xy',0)),
            'sigma2yy/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2yy',0)),
            'sigma2yz/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2yz',0)),
            'sigma2zx/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2zx',0)),
            'sigma2zz/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2zz',0)),
            'hForHoverE/F' : Func(partial(get_h_for_he)),
            'hSumForHoverE/F' : Func(partial(get_hsum_for_he)),
            'hgcalHForHoverE/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_hForHOverE',0)),
            'hcalHForHoverE/F' : Func(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHoverEUnseeded',0)),
        }

        self.egobj_vars = []        
        for name,func in vars_.iteritems():
            self.egobj_vars.append(TreeVar(self.tree,"eg_"+name,func,max_egs,egobjnr_name))
            
        gen_vars_names = {
            'pt/F' : Func(partial(ROOT.reco.GenParticle.pt)),
            'et/F' : Func(partial(ROOT.reco.GenParticle.et)),
            'eta/F' : Func(partial(ROOT.reco.GenParticle.eta)),
            'phi/F' : Func(partial(ROOT.reco.GenParticle.phi)),
            'vz/F' : Func(partial(ROOT.reco.GenParticle.vz)),
        }
        self.gen_vars = []
        for name,func in gen_vars_names.iteritems():
            self.gen_vars.append(TreeVar(self.tree,"eg_gen_"+name,func,max_egs,egobjnr_name))
            

        self.initialised = True

    def fill(self,evtdata,weights):
        if not self.initialised:
            self._init_tree(weights)

        for var_ in self.evtvars:
            var_.fill(evtdata.event.object())
            
        egobjs_raw = evtdata.get("egtrigobjs")
        egobjs = [eg for eg in egobjs_raw if eg.et()>self.min_et]
        egobjs.sort(key=ROOT.reco.EgTrigSumObj.et,reverse=True)
        for obj in egobjs:
            fix_hgcal_hforhe(obj,evtdata)

        genparts = evtdata.get("genparts")
        self.egobj_nr.fill(egobjs)
        for var_ in self.gen_vars:
            var_.clear()
        for objnr,obj in enumerate(egobjs):
            for var_ in self.egobj_vars:                
                var_.fill(obj,objnr)
            gen_obj = GenTools.match_to_gen(obj.eta(),obj.phi(),genparts)[0]
            if gen_obj:
                for var_ in self.gen_vars:
                    var_.fill(gen_obj,objnr)

        self.tree.Fill()


def main():
    
    CoreTools.load_fwlitelibs();

    parser = argparse.ArgumentParser(description='prints E/gamma pat::Electrons/Photons us')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--out_filename','-o',default="output.root",help='output filename')
    parser.add_argument('--min_et','-m',default=20.,type=float,help='minimum eg et') 
    parser.add_argument('--weights','-w',default=None,help="weights filename")
    parser.add_argument('--report','-r',default=10,type=int,help="report every N events")
    args = parser.parse_args()
    
    evtdata = EvtData(phaseII_products,verbose=True)
    weights = EvtWeights(args.weights) if args.weights else None

    out_file = ROOT.TFile(args.out_filename,"RECREATE")
    eghlt_tree = EgHLTTreeData('egHLTTree',args.min_et)

    events = Events(args.in_filenames)
    nr_events = events.size()
    for event_nr,event in enumerate(events):
        if event_nr%args.report==0:
            print("processing event {} / {}".format(event_nr,nr_events))
        evtdata.get_handles(event)
        eghlt_tree.fill(evtdata,weights)

    out_file.Write()

if __name__ == "__main__":
    main()
