import argparse
import sys
from DataFormats.FWLite import Events, Handle
import ROOT
from functools import partial
import math

from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, phaseII_products
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.GsfTools as GsfTools
import Analysis.HLTAnalyserPy.IsolTools as IsolTools
import Analysis.HLTAnalyserPy.PixelMatchTools as PixelMatchTools
from Analysis.HLTAnalyserPy.Trees import EgHLTTree

def cal_cluster_maxdr(obj):
    max_dr2 = 0.
    sc = obj.superCluster()
    seed_eta = sc.seed().eta()
    seed_phi = sc.seed().phi()
    for clus in sc.clusters():
        if clus == sc.seed():
            continue
        dr2 = ROOT.reco.deltaR2(clus.eta(),clus.phi(),seed_eta,seed_phi)
        max_dr2 = max(max_dr2,dr2)
        
    #ECAL takes 999. if not other cluster for maxDR2
    if max_dr2==0. and sc.seed().seed().det()==ROOT.DetId.Ecal:
        return 999.
    else:
        return math.sqrt(max_dr2)

def get_hit_frac(detid,hits_and_fracs):
    for hit_and_frac  in hits_and_fracs:
        if hit_and_frac.first==detid:
            return hit_and_frac.second
    return 0.

def cal_r9(obj,evtdata,frac=True):
    sc = obj.superCluster()
    seed_id = sc.seed().seed()
    if seed_id.det()!=ROOT.DetId.Ecal or sc.rawEnergy()==0:
        return 0

    seed_id = ROOT.EBDetId(seed_id)
    e3x3 = 0.
    hits = evtdata.get("ebhits")
    for local_ieta in [-1,0,1]:
        for local_iphi in [-1,0,1]:
            hit_id = seed_id.offsetBy(local_ieta,local_iphi)
            if hit_id.rawId()!=0:
                hit = hits.find(hit_id)
                if hit!=hits.end():
                    hit_energy = hit.energy()
                    if frac:
                        hit_energy *=get_hit_frac(hit_id,sc.seed().hitsAndFractions())
                    e3x3+=hit_energy
    return e3x3/sc.rawEnergy()

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
    weights = EvtWeights(args.weights) if args.weights else None

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
        'r9Full/F' : CoreTools.UnaryFunc(partial(cal_r9,evtdata,frac=False)),
        'r9Frac/F' : CoreTools.UnaryFunc(partial(cal_r9,evtdata,frac=True)),
        'clusterMaxDR/F' : cal_cluster_maxdr
    })
    eghlt_tree.add_eg_update_funcs([
      #  CoreTools.UnaryFunc(partial(fix_hgcal_hforhe,evtdata))
    ])

    events = Events(CoreTools.get_filenames(args.in_filenames))
    nr_events = events.size()
    for event_nr,event in enumerate(events):
        if event_nr%args.report==0:
            print("processing event {} / {}".format(event_nr,nr_events))
        evtdata.get_handles(event)
        eghlt_tree.fill()

    out_file.Write()

if __name__ == "__main__":
    main()
