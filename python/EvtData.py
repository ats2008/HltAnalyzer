from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from DataFormats.FWLite import Events, Handle

import json
import re

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
    def __init__(self,input_filename,lumi=0.075):
        if input_filename: 
            with open(input_filename,'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}            
        self.warned = []
        self.lumi = lumi #luminosity to weight to in pb

    def weight_from_name(self,dataset_name):
        if dataset_name in self.data:
            val = self.data[dataset_name]
            return val['xsec']/val['nrtot']*self.lumi
        else:
            if dataset_name not in self.warned:
                self.warned.append(dataset_name) 
                print("{} not in weights file, returning weight 1".format(dataset_name))
            return 1.

    def weight_from_evt(self,event):
        filename = event.getTFile().GetName().split("/")[-1]
        dataset_name = re.search(r'(.+)(_\d+_EDM.root)',filename).groups()[0]
        return self.weight_from_name(dataset_name)

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
