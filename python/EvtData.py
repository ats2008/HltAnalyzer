from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from DataFormats.FWLite import Events, Handle

import json
import re
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import numpy
from enum import Enum

class HandleData(Handle):
    def __init__(self,product,label):
        Handle.__init__(self,product)
        self.label = str(label)
    def get(self,event):
        event.getByLabel(self.label,self)
        
class EvtHandles:
    def __init__(self,products=[],verbose=False):
        for product in products:
            if verbose:
                print("adding handle {name}, {type}, {tag}".format(**product))
            setattr(self,product['name'],HandleData(product['type'],product['tag']))
    
class EvtData:
    def __init__(self,products=[],verbose=False):
        self.handles = EvtHandles(products,verbose)
        self.event = None
        self.got_handles = []

    def get_handles(self,event,on_demand=True):
        """ 
        gets the handles for the event
        if on_demand=True it doesnt actually get the handles and instead
        waits for something to request the handle
        """ 
        self.got_handles = []
        self.event = event
        if not on_demand:
            for name,handle in vars(self.handles).iteritems():            
                handle.get(event)
                self.got_handles.append(name)
 
    def get_handle(self,name):
        """ 
        gets the product handle with name "name"
        now checks to ensure the handles are got first and not gets them
        """ 
        
        handle = getattr(self.handles,name)
        if not name in self.got_handles:
            handle.get(self.event)
            self.got_handles.append(name)

        return handle

    def get(self,name):
        """ 
        gets the product with name "name"
        now checks to ensure the handles are got first and not gets them
        """ 
        handle = self.get_handle(name)
        
        try:
            return handle.product()       
        except RuntimeError:
            return None
           
class EvtWeights:
    def __init__(self,input_filename=None,input_dict=None,corr_for_pu=False,lumi=0.075):
        if input_filename: 
            with open(input_filename,'r') as f:
                self.data = json.load(f)['v1']
        elif input_dict:
            self.data = dict(input_dict)
        else:
            self.data = {}
        self.warned = []
        self.corr_for_pu = corr_for_pu
        self.lumi = lumi #luminosity to weight to in pb

    def weight_from_name(self,dataset_name,evtdata=None):
        if dataset_name in self.data:
            val = self.data[dataset_name]
            weight = val['xsec']/val['nrtot']*self.lumi
            if not self.corr_for_pu:
                return weight
            else:
                return weight*self.pu_doublecount_weight(evtdata,dataset_name)

        else:
            if dataset_name not in self.warned:
                self.warned.append(dataset_name) 
                print("{} not in weights file, returning weight 1".format(dataset_name))
            return 1.

    def weight_from_evt(self,event,evtdata=None):
        filename = event.getTFile().GetName().split("/")[-1]
        dataset_name = re.search(r'(.+)(_\d+_EDM.root)',filename).groups()[0]
        return self.weight_from_name(dataset_name,evtdata)

    def pu_doublecount_weight(self,evtdata,dataset_name):
        frac_pu_with_lt_pthat = {160.0: 0.9996301858036174, 130.0: 0.9990026223188471, 100.0: 0.9966604657417576, 70.0: 0.9855212138870834, 40.0: 0.8834749086671, 10.0: 2.2412981598942108e-05, 140.0: 0.9992603716072349, 110.0: 0.9978259407849026, 80.0: 0.9915166864648004, 200.0: 0.9998767286012058, 50.0: 0.9488871954636126, 20.0: 0.23302776968420108, 190.0: 0.9998431091288074, 150.0: 0.9994957079140238, 120.0: 0.9985319497052693, 180.0: 0.9997758701840105, 90.0: 0.9948113947598449, 60.0: 0.9740569737992245, 170.0: 0.9997310442208126, 30.0: 0.7006746307461281}


        if not dataset_name.startswith("QCD"):
            return 1.
        else:
            match = re.search(r'Pt[_-]([0-9]+)[to]+([a-zA-Z0-9]+)',dataset_name)
            sample_min_pt_hat = float(match.group(1) )
            #sample_max_pt_hat = 9999. if match.group(2)=="Inf" else float(match.group(2))
            pu_sum  = evtdata.get("pu_sum")
            pu_max_pt_hat = max([x for x in pu_sum[3].getPU_pT_hats()])
            if pu_max_pt_hat>sample_min_pt_hat:
                return 0.
            else:       
                return 1./frac_pu_with_lt_pthat[sample_min_pt_hat]

class PtBinnedSample:

    def __init__(self,min_pt,max_pt,xsec,nr_inclusive,nr_em,em_filt_eff):
        self.min_pt = min_pt
        self.max_pt = max_pt
        self.xsec = xsec
        self.nr_inclusive = nr_inclusive
        self.nr_em = nr_em
        self.nr_em_expect = 0
        self.nr_em_actual = 0
        self.em_filt_eff = em_filt_eff
        self.nr_mu = 0.
        self.mu_filt_eff = 0.
        print("{}-{} {} {}".format(min_pt,max_pt,xsec,nr_inclusive)) 


class QCDWeightCalc:
    """ 
    translation of Christian Veelken's mcStiching
    https://github.com/veelken/mcStitching
    """
    def __init__(self,ptbinned_samples,bx_freq=30000000.0,nr_expt_pu=200):
        self.bx_freq = bx_freq
        #self.nr_expt_pu = nr_expt_pu
        self.bins = [PtBinnedSample(**x) for x in ptbinned_samples]
        self.bins.sort(key=lambda x: x.min_pt)
        self.bin_lowedges = [x.min_pt for x in self.bins]
        self.bin_lowedges.append(self.bins[-1].max_pt)
        self.gen_filters = TrigTools.TrigResults(["Gen_QCDMuGenFilter",
                                                  "Gen_QCDBCToEFilter",
                                                  "Gen_QCDEmEnrichingFilter",
                                                  "Gen_QCDEmEnrichingNoBCToEFilter"])
        #now we get the number of EM events (skip bin 0 which is  minbias)
        min_bias = self.bins[0]
        for bin_ in self.bins[1:]:
            nr_em_mb = min_bias.nr_inclusive*bin_.xsec/min_bias.xsec * bin_.em_filt_eff
            nr_em_qcd_inc  = bin_.nr_inclusive*bin_.em_filt_eff
            bin_.nr_em_expect = nr_em_mb + nr_em_qcd_inc
            bin_.nr_em_actual = nr_em_mb + nr_em_qcd_inc + bin_.nr_em

    def weight(self,evtdata,use_em_filt=True):
        pusum_intime = [x for x in evtdata.get("pu_sum") if x.getBunchCrossing()==0]
        bin_counts = [0]*(len(self.bins)+1)
        tot_count= pusum_intime[0].getPU_pT_hats().size()
        for pu_pt_hat in pusum_intime[0].getPU_pT_hats():
            bin_nr = numpy.digitize(pu_pt_hat,self.bin_lowedges)
            #overflow means we fill bin 1 which is the inclusive min bias bin
            try:
                bin_counts[bin_nr]+=1
            except IndexError:
                bin_counts[1]+=1
       
        geninfo = evtdata.get("geninfo")
        tot_count +=1
        #again like for PU, overflow means we fill bin 1 which is the inclusive min bias bin
        try:
            bin_counts[numpy.digitize(geninfo.qScale(),self.bin_lowedges)]+=1
        except IndexError:
            bin_counts[1]+=1
        
        min_bias_xsec = self.bins[0].xsec

        expect_events_mc = 0
        for bin_nr,sample_bin in enumerate(self.bins):
            bin_frac = float(bin_counts[bin_nr+1])/float(tot_count)
            theory_frac =  float(sample_bin.xsec) / float(min_bias_xsec)
            #dont correct inclusively generated sample
            prob_corr = bin_frac / theory_frac if bin_nr!=0 else 1.
            expect_events_mc += sample_bin.nr_inclusive * prob_corr
            
        weight = float(self.bx_freq) / float(expect_events_mc)
        if use_em_filt:
            weight *= self.em_weight(evtdata)
        return weight

    def em_weight(self,evtdata):
        geninfo = evtdata.get("geninfo")
        self.gen_filters.fill(evtdata)
        is_em = self.gen_filters.result("Gen_QCDEmEnrichingFilter") and not self.gen_filters.result("Gen_QCDBCToEFilter")
        weight = 1.
        if is_em:
            #should never be -1 as we should never hit the underflow and if 
            #so there is a problem
            sample_nr = numpy.digitize(geninfo.qScale(),self.bin_lowedges)-1
            sample_nr = sample_nr if sample_nr < len(self.bins) else 0
            bin_ = self.bins[sample_nr] 
            if bin_.nr_em_actual!=0:
                weight = float(bin_.nr_em_expect)/float(bin_.nr_em_actual)
        return weight


class EvtWeightsV2:
    
    class WeightType(Enum):
        V1 = 1
        V2 = 2
        V2NoEM = 3

    def __init__(self,input_filename=None,input_dict=None,bx_freq=30.0E6,nr_expt_pu=200,mb_xsec = 80.0E9):
        if input_filename: 
            with open(input_filename,'r') as f:
                self.data = json.load(f)
        elif input_dict:
            self.data = dict(input_dict)
        else:
            self.data = {}
            
        self.warned = []
        self.lumi = bx_freq * nr_expt_pu / mb_xsec
        if self.data:
            self.qcd_weights = QCDWeightCalc(self.data['v2']['qcd'],bx_freq,nr_expt_pu)
            self.weights_v1 = EvtWeights(input_dict=self.data['v1'])
    
    def weight_from_name(self,dataset_name,evtdata,weight_type=WeightType.V2):        
        if not weight_type==EvtWeightsV2.WeightType.V1 and (dataset_name.startswith("QCD") or dataset_name.startswith("MinBias")!=-1):
            use_em_filt = weight_type==EvtWeightsV2.WeightType.V2
            return self.qcd_weights.weight(evtdata,use_em_filt=use_em_filt)
        else:          
            return self.weights_v1.weight_from_name(dataset_name,evtdata)

    def weight_from_evt(self,evtdata,weight_type=WeightType.V2):
        filename = evtdata.event.object().getTFile().GetName().split("/")[-1]
        dataset_name = re.search(r'(.+)(_\d+_EDM.root)',filename).groups()[0]
        return self.weight_from_name(dataset_name,evtdata,weight_type)

def get_objs(evtdata,events,objname,indx):
    """
    A small helper function to save typing out this commands each time
    """
    events.to(indx)
    evtdata.get_handles(events)
    objs = evtdata.get(objname)
    print("event: {} {} {}".format(events.eventAuxiliary().run(),events.eventAuxiliary().luminosityBlock(),events.eventAuxiliary().event()))
    print("# {} = {}".format(objname,objs.size()))
    return objs

def add_product(prods,name,type_,tag):
    prods.append({'name' : name, 'type' : type_, 'tag' : tag})

std_products=[]
add_product(std_products,"egtrigobjs","std::vector<reco::EgTrigSumObj>","hltEgammaHLTExtraL1Seeded")
add_product(std_products,"genparts","std::vector<reco::GenParticle>","genParticles")

phaseII_products = []
add_product(phaseII_products,"egtrigobjs","std::vector<reco::EgTrigSumObj>","hltEgammaHLTExtra")
add_product(phaseII_products,"genparts","std::vector<reco::GenParticle>","genParticles")
add_product(phaseII_products,"l1trks","std::vector<TTTrackExtra<edm::Ref<edm::DetSetVector<Phase2TrackerDigi>,Phase2TrackerDigi,edm::refhelper::FindForDetSetVector<Phase2TrackerDigi> > > >","hltEgammaHLTPhase2Extra")
add_product(phaseII_products,"trkpart","std::vector<TrackingParticle>","hltEgammaHLTPhase2Extra")
add_product(phaseII_products,"hcalhits","edm::SortedCollection<HBHERecHit,edm::StrictWeakOrdering<HBHERecHit> >","hltEgammaHLTExtra")
add_product(phaseII_products,"trksv0","std::vector<reco::Track>","hltEgammaHLTExtra:generalTracksV0")
add_product(phaseII_products,"trksv2","std::vector<reco::Track>","hltEgammaHLTExtra:generalTracksV2")
add_product(phaseII_products,"trksv6","std::vector<reco::Track>","hltEgammaHLTExtra:generalTracksV6")
add_product(phaseII_products,"trksv72","std::vector<reco::Track>","hltEgammaHLTExtra:generalTracksV72")
add_product(phaseII_products,"hglayerclus","std::vector<reco::CaloCluster>","hltEgammaHLTPhase2Extra:hgcalLayerClusters")
add_product(phaseII_products,"hgpfclus","std::vector<reco::PFCluster>","hltEgammaHLTExtra:Hgcal")
add_product(phaseII_products,"ecalpfclus","std::vector<reco::PFCluster>","hltEgammaHLTExtra:Ecal")
add_product(phaseII_products,"hcalpfclus","std::vector<reco::PFCluster>","hltEgammaHLTExtra:Hcal")
add_product(phaseII_products,"trig_res","edm::TriggerResults","TriggerResults::HLTX")
add_product(phaseII_products,"l1tkeles_eb","std::vector<l1t::TkElectron>","L1TkElectronsEllipticMatchCrystal:EG")
add_product(phaseII_products,"l1tkeles_hgcal","std::vector<l1t::TkElectron>","L1TkElectronsEllipticMatchHGC:EG")
add_product(phaseII_products,"l1tkphos_eb","std::vector<l1t::TkEm>","L1TkPhotonsCrystal:EG")
add_product(phaseII_products,"l1tkphos_hgcal","std::vector<l1t::TkEm>","L1TkPhotonsHGC:EG")
add_product(phaseII_products,"l1egs_eb","BXVector<l1t::EGamma>","L1EGammaClusterEmuProducer")
add_product(phaseII_products,"l1egs_hgcal","BXVector<l1t::EGamma>","l1EGammaEEProducer:L1EGammaCollectionBXVWithCuts")
add_product(phaseII_products,"pu_sum","std::vector<PileupSummaryInfo>","addPileupInfo")
add_product(phaseII_products,"hghadpfclus","std::vector<reco::PFCluster>","hltEgammaHLTExtra:HgcalHAD")
add_product(phaseII_products,"geninfo","GenEventInfoProduct","generator")
