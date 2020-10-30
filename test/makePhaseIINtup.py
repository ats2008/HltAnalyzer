import argparse
import sys
from DataFormats.FWLite import Events, Handle
import ROOT
from functools import partial

from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, EvtWeights, phaseII_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
from Analysis.HLTAnalyserPy.Trees import EgHLTTree

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

def get_indx_best_gsf(obj):
    min_EoPm1=999.9
    min_mhit=999
    index_best_gsf=0
    index=0
    for gsf in obj.gsfTracks():
        this_mhit = gsf.hitPattern().numberOfLostHits(ROOT.reco.HitPattern.MISSING_INNER_HITS)
        this_EoPm1 = abs(( (obj.superCluster().energy()) /  (gsf.innerMomentum().R() ) ) - 1)
        if ( this_mhit < min_mhit ):
            min_mhit=this_mhit
            if (this_EoPm1 < min_EoPm1): min_EoPm1 = this_EoPm1
            index_best_gsf=index
        elif (this_mhit == min_mhit):
            if (this_EoPm1 < min_EoPm1):
                index_best_gsf=index
        index=index+1
    return index_best_gsf

def get_nlayerpix_gsf(obj):
    if obj.gsfTracks().empty():
        return 0
    else:
        indx_bestgsf=get_indx_best_gsf(obj)
        return obj.gsfTracks()[indx_bestgsf].hitPattern().pixelLayersWithMeasurement()

def get_nlayerstrip_gsf(obj):
    if obj.gsfTracks().empty():
        return 0
    else:
        indx_bestgsf=get_indx_best_gsf(obj)
        return obj.gsfTracks()[indx_bestgsf].hitPattern().stripLayersWithMeasurement()

def get_normchi2_gsf(obj):
    if obj.gsfTracks().empty():
        return 999
    else:
        indx_bestgsf=get_indx_best_gsf(obj)
        return obj.gsfTracks()[indx_bestgsf].normalizedChi2() 
     
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
    eghlt_tree = EgHLTTree('egHLTTree',args.min_et,weights)
    eghlt_tree.add_eg_vars({
        'hForHoverE/F' : get_h_for_he,
        'hSumForHoverE/F' : get_hsum_for_he,
        'nLayerIT_gsf/I' : get_nlayerpix_gsf,
        'nLayerOT_gsf/I' : get_nlayerstrip_gsf,
        'normalisedChi2_gsf/F' : get_normchi2_gsf
    })
    eghlt_tree.add_eg_update_funcs([
        CoreTools.UnaryFunc(partial(fix_hgcal_hforhe,evtdata))
    ])

    events = Events(args.in_filenames)
    nr_events = events.size()
    for event_nr,event in enumerate(events):
        if event_nr%args.report==0:
            print("processing event {} / {}".format(event_nr,nr_events))
        evtdata.get_handles(event)
        eghlt_tree.fill(evtdata)

    out_file.Write()

if __name__ == "__main__":
    main()
