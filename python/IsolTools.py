from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import sys
import re

import Analysis.HLTAnalyserPy.GsfTools as GsfTools

def get_HLT_iso(egobj,trks):

    if egobj.gsfTracks().empty():
        return 0

    indx_bestgsf = GsfTools.get_indx_best_gsf(egobj)

    eta = egobj.gsfTracks()[indx_bestgsf].eta()
    phi = egobj.gsfTracks()[indx_bestgsf].phi()
    vz = egobj.gsfTracks()[indx_bestgsf].vz() 

    min_pt = 1.
    max_dz = 0.15
    min_deta = 0.01
    max_dr2 = 0.3*0.3
    min_dr2 = 0.01*0.01

    isol = 0.

    for trk in trks:
        if trk.pt()<min_pt: continue
        dz = vz - trk.vz()
        if abs(dz)>max_dz: continue
        deta = eta - trk.eta()
        if abs(deta)<min_deta: continue #selecting a phi strip cutting on eta
        dr2 = ROOT.reco.deltaR2(eta,phi,trk.eta(),trk.phi())
        if dr2 > max_dr2 or dr2 < min_dr2: continue
        isol+=trk.pt()

    return isol

def get_L1_iso(egobj,l1trks):

    if egobj.gsfTracks().empty():
        return 0

    indx_bestgsf = GsfTools.get_indx_best_gsf(egobj)

    eta = egobj.gsfTracks()[indx_bestgsf].eta()
    phi = egobj.gsfTracks()[indx_bestgsf].phi()
    vz = egobj.gsfTracks()[indx_bestgsf].vz()
                      
    min_pt = 2.
    max_dz = 0.7
    min_deta = 0.003
    max_dr2 = 0.3*0.3
    min_dr2 = 0.01*0.01

    l1isol = 0.

    for l1trk_extra in l1trks:
        l1trk = l1trk_extra.ttTrk()
        pt = l1trk.momentum().perp()
        if pt <min_pt: continue
        dz = vz - l1trk.z0()
        if abs(dz)>max_dz: continue
        deta = eta - l1trk.eta() #selecting a phi strip cutting on eta
        if abs(deta)<min_deta: continue
        dr2 = ROOT.reco.deltaR2(eta,phi,l1trk.eta(),l1trk.phi())
        if dr2 > max_dr2 or dr2 < min_dr2: continue
        l1isol+=pt

    return l1isol
