from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import ROOT
import glob
import os
import argparse
import shutil
import json
import re

def process_dir(dir_,proc_name="HLTX"):
    files = glob.glob(os.path.join(dir_,"*.root"))
    good_files = []
    bad_files = []
    nr_tot = 0.
    nr_pass = 0.
    for file_ in files:
        root_file = ROOT.TFile.Open(file_,"READ")
        if not root_file or root_file.IsZombie() or root_file.TestBit(ROOT.TFile.kRecovered):
            bad_files.append(str(file_))
        else:
            good_files.append(str(file_))
            nr_pass += root_file.Events.GetEntries()
            root_file.Runs.GetEntry(0)
            nr_tot += getattr(root_file.Runs,"edmMergeableCounter_hltNrInputEvents_nrEventsRun_{proc_name}".format(proc_name=proc_name)).value
        
    return {"nr_pass" : nr_pass,"nr_tot" : nr_tot,
            "good_files" : good_files,"bad_files" : bad_files}
    
def get_xsec(job_name):
    """
    The defination of fragile, keyed to my scripts naming convension which is datasetname__conditions__tag
    """
    xsecs = {
        'QCD_Pt-15to20_EMEnriched_TuneCP5_14TeV_pythia8' : 1448000.0,
        'QCD_Pt-20to30_EMEnriched_TuneCP5_14TeV_pythia8' : 5370000.0,
        'QCD_Pt-30to50_EMEnriched_TuneCP5_14TeV_pythia8' : 7022000.0,
        'QCD_Pt-50to80_EMEnriched_TuneCP5_14TeV_pythia8' : 2211000.0,
        'QCD_Pt-80to120_EMEnriched_TuneCP5_14TeV_pythia8' : 413300.0,
        'QCD_Pt-120to170_EMEnriched_TuneCP5_14TeV_pythia8' : 76740.0,
        'QCD_Pt-170to300_EMEnriched_TuneCP5_14TeV_pythia8' : 19380.0,
        'QCD_Pt-300toInf_EMEnriched_TuneCP5_14TeV_pythia8' : 1337.0,   
        "QCD_Pt_15to20_TuneCP5_14TeV_pythia8" : 923300000.0,
        "QCD_Pt_20to30_TuneCP5_14TeV_pythia8" : 436000000.0,
        "QCD_Pt_30to50_TuneCP5_14TeV_pythia8" : 118400000.0,
        "QCD_Pt_50to80_TuneCP5_14TeV_pythia8" : 17650000.0,
        "QCD_Pt_80to120_TuneCP5_14TeV_pythia8" : 2671000.0,
        "QCD_Pt_120to170_TuneCP5_14TeV_pythia8" : 469700.0,
        "QCD_Pt_170to300_TuneCP5_14TeV_pythia8" : 121700.0,
        "QCD_Pt_300to470_TuneCP5_14TeV_pythia8" : 8251.0,
        "QCD_Pt_470to600_TuneCP5_14TeV_pythia8" : 686.4,
        "QCD_Pt_600oInf_TuneCP5_14TeV_pythia8" : 244.8,
        "WJetsToLNu_TuneCP5_14TeV-amcatnloFXFX-pythia8" : 56990.0,
        "DYJetsToLL_M-10to50_TuneCP5_14TeV-madgraphMLM-pythia8" : 16880.0,
        "DYToLL_M-50_TuneCP5_14TeV-pythia8" : 5795.0,
        'DoubleElectron_FlatPt-1To100' : 1.
    }
    dataset_name = job_name.split("__")[0]
    try:
        return xsecs[dataset_name]
    except KeyError:
        print("{} not found".format(dataset_name))
        return 0.

def get_qcd_em_filt_eff(min_pt,max_pt):
    filt_effs = {
        "0to9999" : 1.0,
        "15to20" : 1.0,
        "20to30" : 1.0,
        "30to50" : 1.0,
        "50to80" : 1.0,
        "80to120" : 1.0,
        "120to170" : 1.0,
        "170to300" : 1.0,
        "300to470" : 1.0,
        "470to600" : 1.0,
        "600to9999" : 1.0,
        "300to9999" : 1.0
    }
    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return filt_effs[key]
    except KeyError:
        print("{} not found".format(key))
        return 0.

def get_qcd_xsec(min_pt,max_pt):
    xsecs = {
        "0to9999" : 400000000.0,
        "15to20" : 923300000.0,
        "20to30" : 436000000.0,
        "30to50" : 118400000.0,
        "50to80" : 17650000.0,
        "80to120" : 2671000.0,
        "120to170" : 469700.0,
        "170to300" : 121700.0,
        "300to470" : 8251.0,
        "470to600" : 686.4,
        "600to9999" : 244.8,
        "300to9999" : 8251.0 + 686.4 + 244.8
    }
    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return xsecs[key]
    except KeyError:
        print("{} not found".format(key))
        return 0.
    


def clean_failed_jobs(files_failed):
    """
    function moves failed jobs in a failed subdir folder
    it deduces if the base_out_dir has a the batch job sub folder or is it
    and then makes a directory failed where it moves all the files

    this assumes all the jobs passed here life in the same directory, ie are 
    from the same batch job
    """

    jobs_failed = []
    failed_jobnrs = [int(re.search('(_)([0-9]+)_EDM.root',x).group(2)) for x in files_failed]
  

    if files_failed:

        src_dir,file_tail = os.path.split(files_failed[0])
        
        if not all(os.path.split(x)[0]==src_dir for x in files_failed):
            print("not all failed files are in the same sub dir {} skipping cleaning files".format(src_dir))
            return

        dest_dir = os.path.join(src_dir,"failed")
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        if not os.path.isdir(src_dir):
            print("src dir {} does not exist or is not a directory, skipping cleaning files".format(src_dir))
            return
            
        if not os.path.isdir(dest_dir):
            print("dest dir {} does not exist or is not a directory, skipping cleaning files".format(dest_dir))
            return
        
        print("\n\ngoing to copy from {} to {}".format(src_dir,dest_dir))
        print("jobs ",failed_jobnrs)

        prompt = ""
        while prompt!="y" and prompt!="n":
            print("enter y to continue, n to skip")
            prompt = raw_input().lower()
        if prompt=="n":
            print("not cleaning files")
        else:
            print("cleaning files")
            for filename in files_failed:                
                shutil.move(filename,dest_dir)

def gen_weight_file_v1(job_data):
    weights_dict = {}
    for name,data in job_data.iteritems():
        weights_dict[name] =  {"nrtot": data['job_stats']['nr_tot'], "xsec": data['xsec'], "nrpass": data['job_stats']['nr_pass']}
    return weights_dict

def get_pthat_range(name):
    if name.startswith("QCD_"):
        match = re.search(r'Pt[_-]([0-9]+)[to]+([a-zA-Z0-9]+)',name)
        sample_min_pt_hat = float(match.group(1) )
        sample_max_pt_hat = 9999. if match.group(2)=="Inf" else float(match.group(2))
    else:
        #min bias
        sample_min_pt_hat = 0.
        sample_min_pt_hat = 9999.
    return sample_min_pt_hat,sample_max_pt_hat

def qcd_weights_v2(sample_name,sample_data,output_data):
    min_pt,max_pt = get_pthat_range(sample_name)
    output_entry = None
    for entry in output_data:
        if min_pt == entry['min_pt']:
            output_entry  = entry
            break
    if not output_entry:
        output_entry = {
            'min_pt' : min_pt,'max_pt' : max_pt, 'xsec' : get_qcd_xsec(min_pt,max_pt),
            'nr_inclusive' : 0, 'nr_em' : 0, 'em_filt_eff' : get_qcd_em_filt_eff(min_pt,max_pt),
        }
        output_data.append(output_entry)
    
    if sample_name.find("EMEnriched")!=-1:
        output_entry['nr_em'] = sample_data['job_stats']['nr_tot']
    else:
        output_entry['nr_inclusive'] = sample_data['job_stats']['nr_tot']
    
def gen_weight_file_v2(job_data):
    weights_dict = {"qcd" : []}
    for name,data in job_data.iteritems():
        if name.startswith("QCD_") or name.startswith("MinimumBias"):
            qcd_weights_v2(name,data,weights_dict['qcd'])
        else:
            weights_dict[name] =  {"nrtot": data['job_stats']['nr_tot'], "xsec": data['xsec'], "nrpass": data['job_stats']['nr_pass']}
    weights_dict['qcd'].sort(key=lambda x : x['min_pt'])
    return weights_dict
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tries to open every root file in sub dir')
    parser.add_argument('dirs',nargs="+",help='dirs to look for root files')
    parser.add_argument('--clean',action='store_true',help='clean bad files')
    parser.add_argument('--out','-o',default='weights.json',help='output weights json')
    args = parser.parse_args()
    
    job_data = {}

    for dir_ in args.dirs:
        job_name = dir_.rstrip("/").split("/")[-1]
        job_data[job_name] = {}
        print("processing {}".format(dir_))
        job_data[job_name]['job_stats'] = process_dir(dir_,"HLTX")
        job_data[job_name]['xsec'] = get_xsec(job_name)
        
        
    weights_dict = {}
    weights_dict['v1'] = gen_weight_file_v1(job_data)
    weights_dict['v2'] = gen_weight_file_v2(job_data)

    with open(args.out,'w') as f:
        json.dump(weights_dict,f)

    for name,data in job_data.iteritems():
        with open("{}.list","w") as f:
            for filename in data['job_stats']['good_files']:
                f.write(filename"+\n")
                

    if args.clean:
        for k,v in job_data.iteritems():
            clean_failed_jobs(v['job_stats']['bad_files'])
    
    
