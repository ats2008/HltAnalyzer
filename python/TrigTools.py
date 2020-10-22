from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT

def get_trig_indx(selected_name,trig_names):
    """
    returns the index of the trigger (if it exists, otherwise returns the size of trig_names, yes this is a bit c++ like)
    the annoying thing here is we want to match all HLT_Blah_v*
    there are several ways to do it, the quickest is see which starts with HLT_Blah_v
    
    note one can be smarter and cache the result and update when trig_names.parameterSetID() changes 
    """
    for idx,name in enumerate(trig_names.triggerNames()):
        if name.startswith(selected_name):
            return idx
    return None

def match_trig_objs(eta,phi,trig_objs,max_dr=0.1):    
    max_dr2 = max_dr*max_dr
    matched_objs = [obj for obj in trig_objs if ROOT.reco.deltaR2(eta,phi,obj.eta(),obj.phi()) < max_dr2]
    return matched_objs

class TrigResults:
    def __init__(self,trigs):
        self.trig_psetid = None
        self.trig_indices = {x : None for x in trigs}
        self.trig_res = {x : 0 for x in trigs}
        
    def fill(self,evtdata):
        trig_res = evtdata.get("trig_res")
        trig_names = evtdata.event.object().triggerNames(trig_res)
        if self.trig_psetid != trig_names.parameterSetID():
            self.trig_psetid = trig_names.parameterSetID()
            for name in self.trig_indices:
                self.trig_indices[name] = get_trig_indx(name,trig_names)
        for trig in self.trig_res:
            trig_indx = self.trig_indices[trig]
            self.trig_res[trig] = trig_res[trig_indx].accept() if trig_indx is not None else False
            
    def result(self,trig):
        if trig in self.trig_res:
            return self.trig_res[trig]
        else:
            return False
