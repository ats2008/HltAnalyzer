from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
from enum import Enum
import json
import re

class PartStatus(Enum):
    INITIAL = 1
    PREFSR = 2
    FINAL = 3 

def genpart_to_str(genpart,index=None):
    """converts a genparticle to a string, optionally taking an index to put in front"""
    mo1,mo2 = -1,-1
    nrMos = genpart.numberOfMothers()
    if nrMos >0:
        mo1 = genpart.motherRef(0).index()
        mo2 = genpart.motherRef(nrMos-1).index()
    da1,da2 = -1,-1
    nrDas = genpart.numberOfDaughters()
    if nrDas >0:
        da1 = genpart.daughterRef(0).index()
        da2 = genpart.daughterRef(nrDas-1).index()
    
    genpart_dict = {'mo1' : mo1 , 'mo2': mo2, 'da1' : da1 , 'da2' : da2}
    prefix=""
    if index!=None: prefix = "{:5d} ".format(index)

    for prop in ['pdgId','status','pt','eta','phi','mass','vx','vy','vz']:
        genpart_dict[prop] = getattr(genpart,prop)()
        
    return "{prefix}{pdgId:5d} {status:5d} {mo1:5d} {mo2:5d} {da1:5d} {da2:5d} {pt:7.2f} {eta: 8.1f} {phi: 4.2f} {mass: 7.1f} {vx: 3.2f} {vy: 3.2f} {vz: 4.2f}".format(prefix=prefix,**genpart_dict)

def genparts_to_str(genparts,max_to_print=20):
    index_max = min(genparts.size(),max_to_print)
    if max_to_print<0: index_max = genparts.size()
    ret_str = 'printing {} out of {} particles\n{{parts}}'.format(index_max,genparts.size())
    part_strs = ['index   pid  status  mo1  mo2   da1   da2      pt      eta   phi    mass    vx    vy    vz']

    for index in range(0,index_max):
        part_strs.append(genpart_to_str(genparts[index],index))
    return ret_str.format(parts='\n'.join(part_strs))
                  

def get_lastcopy_prefsr(part):
    daughters = part.daughterRefVector()
    if daughters.size()==1 and daughters[0].pdgId()==part.pdgId():
        return get_lastcopy_prefsr(daughters[0])
    else:
        return part
    
def get_lastcopy(part):
    for daughter in part.daughterRefVector():
        if daughter.pdgId() == part.pdgId():
            return get_lastcopy(daughter)
    return part

def get_genparts(genparts,pid=11,antipart=True,status=PartStatus.PREFSR):
    """
    returns a list of the gen particles matching the given criteria from hard process
    might not work for all generators as depends on isHardProcess()
    """

    selected = []

    for part in genparts:
        pdg_id = part.pdgId()
        if pdg_id == pid or (antipart and abs(pdg_id) == abs(pid)):
            if part.isHardProcess():
                if status == PartStatus.INITIAL:
                    selected.append(part)
                elif status == PartStatus.PREFSR:
                    selected.append(get_lastcopy_prefsr(part))
                elif status == PartStatus.FINAL:
                    selected.append(get_lastcopy(part))
                else:
                    raise RuntimeError("error status {} not implimented".format(status))
            else:
                #now we do the case where its particle gun and thus there is no hard process
                #however in this case it will have no mothers so we can detect it that way
                if part.numberOfMothers()==0:
                    selected.append(part)
    return selected

def match_to_gen(eta,phi,genparts,pid=11,antipart=True,max_dr=0.1,status=PartStatus.PREFSR):
    """
    Matches an eta,phi to gen level particle from the hard process
    might not work for all generaters as depends on isHardProcess()
    """

    best_match = None
    best_dr2 = max_dr*max_dr
    selected_parts = get_genparts(genparts,pid,antipart,status)
    for part in selected_parts:
        dr2 = ROOT.reco.deltaR2(eta,phi,part.eta(),part.phi())
        if dr2 < best_dr2:
            best_match = part
            best_dr2 = dr2
    return best_match,best_dr2

class EvtWeights:
    """ 
    class reads in a weights file and determines from the file the event is in
    what the weight should be 
    
    usage: 
    weights = EvtWeights("weights_file")
    weight = weights.weight_from_evt(event.object())
    """

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
