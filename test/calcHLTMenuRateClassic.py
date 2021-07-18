import ROOT
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import argparse
import json
import re
from collections import OrderedDict

#really needs to go into a package....
def strip_path_version(name):
    return re.sub(r'_v[0-9]+\Z',r'_v',name)

def convert_to_vec(input_list,vec_type):
    vec = ROOT.std.vector(vec_type)()
    if input_list:
        for entry in input_list:
            vec.push_back(entry)
    return vec
        

def make_path2indx(path_names_vec):
    path2indx  = {}
    for indx,name in enumerate(path_names_vec):
        path2indx[strip_path_version(str(name))] = indx
    return path2indx

def make_l1seed_str(l1_seeds):
    return ":".join(l1_seeds) if l1_seeds else "None"

def make_l1groups(cfg,l1menu):
    indx_count = 0
    l1groups = OrderedDict()

    l1name_to_indx = {x.second.getName() :x.second.getIndex() for x in l1menu.getAlgorithmMap()}

    for pathname,pathdata in cfg.items():        
        l1seeds = make_l1seed_str(pathdata['l1_seeds']) 
        if pathdata['l1_seeds']:
            l1seed_indices = [l1name_to_indx[x] for x in pathdata['l1_seeds']]
        else:
            l1seed_indices = []
        
        if l1seeds not in l1groups:
            l1groups[l1seeds] = {"seednames" : pathdata['l1_seeds'],
                                 "seedindices" : l1seed_indices,
                                 "indx" : indx_count}
            indx_count+=1
    return l1groups


def make_trigpaths(cfg,path2indx,l1group2indx):
    trigpaths = ROOT.std.vector("RateFuncs::TrigPath")()
    for pathname,pathdata in cfg.items():
        datasets = convert_to_vec(pathdata['datasets'],"std::string")
        prescales = convert_to_vec(pathdata['prescales'],"int")
        l1seeds = convert_to_vec(pathdata['l1_seeds'],"std::string")
        hlt_indx = path2indx[pathname]
        l1_indx = l1group2indx[make_l1seed_str(pathdata['l1_seeds'])]
        trigpaths.push_back(ROOT.RateFuncs.TrigPath(pathname,hlt_indx,l1_indx['indx'],prescales,l1seeds))        
    return trigpaths

def get_nr_pscols(cfg):
    for name,data in cfg.items():
        if data['prescales']:
            return len(data['prescales'])
    return 0
                               

def make_datasets(cfg,path2indx):
    datasets = {}
    for pathname,pathdata in cfg.items():   
        for dataset in pathdata['datasets']:
            if dataset not in datasets:
                datasets[dataset] = []
            datasets[dataset].append(pathname)

    datasets_vec = ROOT.std.vector("RateFuncs::TrigGroup")()
    for name,paths in datasets.items():

        path_names = convert_to_vec(paths,"std::string")
        path_indices = convert_to_vec([path2indx[p] for p in paths],"int")
        nr_coll = get_nr_pscols(cfg)
        datasets_vec.push_back(ROOT.RateFuncs.TrigGroup(
            name,path_names,path_indices,nr_coll
            )
        )
                        
    return datasets_vec


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='calculates HLT menu rate')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--cfg',help='menu config')
    parser.add_argument('--l1menufile',help='l1menu file')
    parser.add_argument('--out_filename','-o',default="output.root",help='input filename')
    parser.add_argument('--report','-r',default=100000,type=int,help='input filename')
    args = parser.parse_args()

    nrpu_bins = 25
    pu_min = 10
    pu_max = 60

    ROOT.ROOT.EnableImplicitMT()

    filenames = CoreTools.get_filenames(args.in_filenames)

    #for now just assume its all the same menu
    path_tree_file = ROOT.TFile.Open(filenames[0])
    path_tree = path_tree_file.hltPathNameTree
    path_tree.GetEntry(0)
    path2indx = make_path2indx(path_tree.pathNames)
    
    l1menu_tree_file = ROOT.TFile.Open(args.l1menufile)
    l1menu_tree = ROOT.L1TUtmTriggerMenuRcd
    l1menu_tree.GetEntry(0)
    l1menu = l1menu_tree.L1TUtmTriggerMenu__

    rateTree = ROOT.TChain("tsgRateTree","")
    for filename in filenames:
        rateTree.Add(filename)
    
    with open(args.cfg,'r') as f:
        cfg = json.load(f)
 
    
    l1_groups = make_l1groups(cfg,l1menu)
    trig_paths = make_trigpaths(cfg,path2indx,l1_groups)
    datasets = make_datasets(cfg,path2indx)
    nr_col = get_nr_pscols(cfg)

    l1_groups_names = [convert_to_vec(v['seednames'],"std::string") for k,v in l1_groups.items()]
    l1_groups_indices = [convert_to_vec(v['seedindices'],"size_t") for k,v in l1_groups.items()]

    l1ExpresConv = ROOT.RateFuncs.L1SeedExpresConverter(convert_to_vec(l1_groups_names,"std::vector<std::string>"),
                                                        convert_to_vec(l1_groups_indices,"std::vector<size_t>"))

    print("nr col ",nr_col)
    trigmenu = ROOT.RateFuncs.TrigMenu(
        trig_paths,datasets,nr_col
    )
    

    for entry in rateTree:
        l1ExpresBits = l1ExpresConv(entry.l1ResFinal)
        trigmenu.fill(l1ExpresBits,entry.hltRes)
        
    
    
