import ROOT
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
from Analysis.HLTAnalyserPy.CoreTools import UnaryFunc
from Analysis.HLTAnalyserPy.NtupTools import TreeVar

from functools import partial

class EgHLTTree:
    def __init__(self,tree_name,min_et=0.,weights=None):
        self.tree = ROOT.TTree(tree_name,'')
        self.min_et = min_et
        self.weights = None
        self.initialised = False
        self.eg_extra_vars = {}
        self.eg_update_funcs = []

    def add_eg_vars(self,vars_):
        self.eg_extra_vars.update(vars_)

    def add_eg_update_funcs(self,update_funcs):
        self.eg_update_funcs.extend(update_funcs)

    def _init_tree(self):
        self.evtvars = [
            TreeVar(self.tree,"runnr/i",UnaryFunc("eventAuxiliary().run()")),
            TreeVar(self.tree,"lumiSec/i",UnaryFunc("eventAuxiliary().luminosityBlock()")),
            TreeVar(self.tree,"eventnr/i",UnaryFunc("eventAuxiliary().event()")),
        
        ]
        if self.weights:
            self.evtvars.append(TreeVar(self.tree,"weight/F",UnaryFunc(partial(weights.weight_from_evt))))
            
        egobjnr_name = "nrEgObjs"
        max_egs = 100    
        self.egobj_nr = TreeVar(self.tree,egobjnr_name+"/i",UnaryFunc(partial(len)))
       
        vars_ = {
            'et/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.et)),
            'energy/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.energy)),
            'eta/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.eta)),
            'phi/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.phi)),
            'sigmaIEtaIEta/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaClusterShapeUnseeded_sigmaIEtaIEta5x5",0)),
            'ecalPFIsol/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEcalPFClusterIsoUnseeded",0)),
            'hcalPFIsol/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaHcalPFClusterIsoUnseeded",0)),
            'trkIsolV0/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEleGsfTrackIsoUnseeded",0)),
            'trkIsolV6/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEleGsfTrackIsoV6Unseeded",0)),
            'trkIsolV72/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaEleGsfTrackIsoV72Unseeded",0)),
            'trkChi2/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_Chi2",0)),
            'trkMissHits/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_MissingHits",0)),
            'trkValidHits/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_ValidHits",0)),
            'invESeedInvP/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_OneOESeedMinusOneOP",0)),
            'invEInvP/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_OneOESuperMinusOneOP",0)),
            'trkDEta/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_Deta",0)),
            'trkDEtaSeed/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_DetaSeed",0)),
            'trkDPhi/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,"hltEgammaGsfTrackVarsUnseeded_DetaSeed",0)),
            'rVar/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_rVar',0)),
            'sigma2uu/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2uu',0)),
            'sigma2vv/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2vv',0)),
            'sigma2ww/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2ww',0)),
            'sigma2xx/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2xx',0)),
            'sigma2xy/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2xy',0)),
            'sigma2yy/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2yy',0)),
            'sigma2yz/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2yz',0)),
            'sigma2zx/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2zx',0)),
            'sigma2zz/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_sigma2zz',0)),
            'hgcalHForHoverE/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHGCALIDVarsUnseeded_hForHOverE',0)),
            'hcalHForHoverE/F' : UnaryFunc(partial(ROOT.reco.EgTrigSumObj.var,'hltEgammaHoverEUnseeded',0)),
        }
        vars_.update(self.eg_extra_vars)

        self.egobj_vars = []        
        for name,func in vars_.iteritems():
            self.egobj_vars.append(TreeVar(self.tree,"eg_"+name,func,max_egs,egobjnr_name))
            
        gen_vars_names = {
            'pt/F' : UnaryFunc(partial(ROOT.reco.GenParticle.pt)),
            'et/F' : UnaryFunc(partial(ROOT.reco.GenParticle.et)),
            'eta/F' : UnaryFunc(partial(ROOT.reco.GenParticle.eta)),
            'phi/F' : UnaryFunc(partial(ROOT.reco.GenParticle.phi)),
            'vz/F' : UnaryFunc(partial(ROOT.reco.GenParticle.vz)),
        }
        self.gen_vars = []
        for name,func in gen_vars_names.iteritems():
            self.gen_vars.append(TreeVar(self.tree,"eg_gen_"+name,func,max_egs,egobjnr_name))
            
        trig_names = ["Gen_QCDMuGenFilter",
                      "Gen_QCDBCToEFilter",
                      "Gen_QCDEmEnrichingFilter",
                      "Gen_QCDEmEnrichingNoBCToEFilter"]
        self.trig_res = TrigTools.TrigResults(trig_names)
        self.trig_vars = []
        for name in trig_names:
            self.trig_vars.append(TreeVar(self.tree,"path_{}/i".format(name),
                                          UnaryFunc(partial(TrigTools.TrigResults.result,name))))

        self.initialised = True

    def fill(self,evtdata):
        if not self.initialised:
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(evtdata.event.object())
            
        egobjs_raw = evtdata.get("egtrigobjs")
        egobjs = [eg for eg in egobjs_raw if eg.et()>self.min_et]
        egobjs.sort(key=ROOT.reco.EgTrigSumObj.et,reverse=True)
        for obj in egobjs:
            for update_func in self.eg_update_funcs:
                update_func(obj)

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

        self.trig_res.fill(evtdata)
        for var_ in self.trig_vars:
            var_.fill(self.trig_res)

        self.tree.Fill()