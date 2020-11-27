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
import Analysis.HLTAnalyserPy.GsfTools as GsfTools
import Analysis.HLTAnalyserPy.IsolTools as IsolTools
import Analysis.HLTAnalyserPy.PixelMatchTools as PixelMatchTools
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
    weights = EvtWeights(args.weights,corr_for_pu=True) if args.weights else None

    out_file = ROOT.TFile(args.out_filename,"RECREATE")

    eghlt_tree = EgHLTTree('egHLTTree',evtdata,args.min_et,weights)
    # for each redefined variable, also add _validation branch, 
    # as a sanity check that our functions can reproduce default variables
    eghlt_tree.add_eg_vars({
        'hForHoverE/F' : get_h_for_he,
        'hSumForHoverE/F' : get_hsum_for_he,
        'nLayerIT/I' : GsfTools.get_nlayerpix_gsf,
        'nLayerOT/I' : GsfTools.get_nlayerstrip_gsf,
        'normChi2/F' : GsfTools.get_normchi2_gsf,
        'nGsf/I' : GsfTools.get_ngsf,
        'hltisov6/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hlt_iso,evtdata,trkcoll="trksv6")),
        'hltisov6_validation/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hlt_iso,evtdata,trkcoll="trksv6",min_pt=1.0,max_dz=0.15,min_deta=0.01,max_dr2=0.2*0.2,min_dr2=0.03*0.03)),
        'hltisov72/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hlt_iso,evtdata,trkcoll="trksv72")),
        'hltisov72_validation/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hlt_iso,evtdata,trkcoll="trksv72",min_pt=1.0,max_dz=0.15,min_deta=0.01,max_dr2=0.2*0.2,min_dr2=0.03*0.03)),
        'l1iso/F' : CoreTools.UnaryFunc(partial(IsolTools.get_l1_iso,evtdata)),
        'hgcaliso/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hgcal_iso,evtdata)),
        'hgcaliso_validation/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hgcal_iso,evtdata,min_pt=0.0,min_deta=0.0,max_dr2=0.3*0.3,min_dr2=0.0*0.0)),
        'ecaliso/F' : CoreTools.UnaryFunc(partial(IsolTools.get_ecal_iso,evtdata)),
        'ecaliso_validation/F' : CoreTools.UnaryFunc(partial(IsolTools.get_ecal_iso,evtdata,min_pt=0.0,min_deta=0.0,max_dr2=0.3*0.3,min_dr2=0.0*0.0)),
        'hcaliso/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hcal_iso,evtdata)),
        'hcaliso_validation/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hcal_iso,evtdata,min_pt=0.0,min_deta=0.0,max_dr2=0.3*0.3,min_dr2=0.0*0.0)),
        'hcalH_dep1/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hcalen_depth,evtdata,depth=1)),
        'hcalH_dep2/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hcalen_depth,evtdata,depth=2)),
        'hcalH_dep3/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hcalen_depth,evtdata,depth=3)),
        'hcalH_dep4/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hcalen_depth,evtdata,depth=4)),
        'pms2/F' : PixelMatchTools.get_pms2_phase2,
        'hgcaliso_layerclus/F' : CoreTools.UnaryFunc(partial(IsolTools.get_hgcal_iso_layerclus,evtdata,min_dr_had=0.0,min_dr_em=0.02,max_dr=0.2,min_energy_had=0.07,min_energy_em=0.02)),

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
        eghlt_tree.fill()

    out_file.Write()

if __name__ == "__main__":
    main()
