from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from DataFormats.FWLite import Events, Handle

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
    def get_handles(self,event):
        for name,handle in vars(self.handles).iteritems():            
            handle.get(event)
    def get(self,name):
        try:
            return getattr(self.handles,name).product()
        except RuntimeError:
            return None
           

def add_product(prods,name,type_,tag):
    prods.append({'name' : name, 'type' : type_, 'tag' : tag})

std_products=[]
add_product(std_products,"egtrigobjs","std::vector<reco::EgTrigSumObj>","hltEgammaHLTExtraL1Seeded")
add_product(std_products,"genparts","std::vector<reco::GenParticle>","genParticles")
