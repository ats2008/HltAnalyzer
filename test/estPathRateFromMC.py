import ROOT
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import argparse

def book_rate_hists(paths,df,basename="rate_{}"):
    hists = []
    for path in paths: 
        df = df.Define("{}_weight".format(path),"{}*weight".format(path))
        hists.append(df.Histo1D(ROOT.RDF.TH1DModel(basename.format(path),";# expt pu",nrpu_bins,pu_min,pu_max),"nrExptPU","{}_weight".format(path)))
    return hists

def finalise_hists(hists,pu_hist,out_file):
   for hist in hists:
       hist.Divide(pu_hist.GetValue())
       hist.SetDirectory(out_file)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='prints E/gamma pat::Electrons/Photons us')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--out_filename','-o',default="output.root",help='input filename')
    parser.add_argument('--report','-r',default=100000,type=int,help='input filename')
    args = parser.parse_args()

    nrpu_bins = 25
    pu_min = 10
    pu_max = 60

    paths_to_measure = ["HLT_Ele32_WPTight_Gsf_v"]

    ROOT.ROOT.EnableImplicitMT()

    filenames = CoreTools.get_filenames_vec(args.in_filenames)
    df = ROOT.RDataFrame("rateTree",filenames)
    nr_events = df.Count().GetValue()
    
   
    ROOT.gInterpreter.Declare("""
    ROOT::RDF::RResultPtr<ULong64_t> addProgressBar(ROOT::RDF::RNode df) {{
        auto c = df.Count();
        c.OnPartialResult({report}, [&df] (ULong64_t e) {{ std::cout << "processing entry " <<e << " / " << {nr_entries} <<std::endl; }});
        return c;
    }}
    """.format(report=args.report,nr_entries=nr_events))
   
 
    out_file = ROOT.TFile.Open(args.out_filename,"RECREATE")
    
    df = df.Define("leadingPtHat","ptHats[0]")

    count = ROOT.addProgressBar(ROOT.RDF.AsRNode(df))
    
    df_qcd = df.Filter("mcType<3")
    df_ewk = df.Filter("mcType>=3")
    
    

    pu_hist = df.Histo1D(ROOT.RDF.TH1DModel("pu_hist",";# expt pu",nrpu_bins,pu_min,pu_max),"nrExptPU")
    pu_hist_ewk = df_ewk.Histo1D(ROOT.RDF.TH1DModel("pu_hist_ewk",";# expt pu",nrpu_bins,pu_min,pu_max),"nrExptPU")
    pu_hist_qcd = df_qcd.Histo1D(ROOT.RDF.TH1DModel("pu_hist_qcd",";# expt pu",nrpu_bins,pu_min,pu_max),"nrExptPU")
    
    
    hlt_paths_ntup = [x for x in df.GetColumnNames()if x.startswith("HLT_") or x.startswith("L1_")]
    hlt_paths = []
    for path in paths_to_measure:
        if path in hlt_paths_ntup:
            hlt_paths.append(path)
        else:
            print("warning, requested path {} is not availible, skipping".format(path))

    hists = book_rate_hists(hlt_paths,df,"rate_{}")
    hists_qcd = book_rate_hists(hlt_paths,df_qcd,"rate_qcd_{}")
    hists_ewk = book_rate_hists(hlt_paths,df_ewk,"rate_ewk_{}")
    count.GetValue()
    pu_hist.Scale(1./pu_hist.GetEntries())
    pu_hist.SetDirectory(out_file)
    if pu_hist_ewk.GetEntries():
        pu_hist_ewk.Scale(1./pu_hist_ewk.GetEntries())
    pu_hist_ewk.SetDirectory(out_file)
    if pu_hist_qcd.GetEntries():
        pu_hist_qcd.Scale(1./pu_hist_qcd.GetEntries())

    pu_hist_qcd.SetDirectory(out_file)
    finalise_hists(hists,pu_hist,out_file)
    finalise_hists(hists_qcd,pu_hist_qcd,out_file)
    finalise_hists(hists_ewk,pu_hist_ewk,out_file)

    out_file.Write()


    
    
