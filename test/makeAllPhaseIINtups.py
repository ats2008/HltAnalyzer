from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import subprocess
import os
import sys
import glob

def main():
    """
    a simple script to quickly ntuplise a large set of samples from EDM
    you pass it the directories you want ntuplised and it does the rest
    """
    parser = argparse.ArgumentParser(description='prints E/gamma pat::Electrons/Photons us')
    parser.add_argument('input_dirs',nargs="+",help='input filename')
    parser.add_argument('--out_dir','-o',default="./",help='output direction') 
    parser.add_argument('--min_et','-m',default=20.,type=float,help='minimum eg et') 
    parser.add_argument('--weights','-w',default=None,help="weights filename")
    parser.add_argument('--report','-r',default=10,type=int,help="report every N events")
    parser.add_argument('--nr_threads','-t',default=8,type=int,help='number of threads')
    args = parser.parse_args()

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    elif not os.path.isdir(args.out_dir):
        print("error output dir {} exists and is not a dir, exiting".format(args.out_dir))
        sys.exit()

    dirs_to_run = []
    print("going to process the following dirs")    
    for dir_ in args.input_dirs:
        if os.path.isdir(dir_):
            dirs_to_run.append(dir_)
            print(dir_)
        else:
            print("ignoring {} as not directory".format(dir_))
                  
    script_dir = os.path.dirname(__file__)
    print(script_dir)
    ntup_script = os.path.join(script_dir,"makePhaseIINtup.py")
    run_script = os.path.join(script_dir,"runMultiThreaded.py")
    for dir_ in dirs_to_run:
                  
        head,tail = os.path.split(dir_.rstrip("/"))
        base_name = tail if tail else head
        out_file = os.path.join(args.out_dir,"{}.root".format(base_name))
        

        ntupcmd = "python {ntup_script} --min_et {a.min_et} -r 5000 -w {a.weights}".format(ntup_script=ntup_script,a=args)
        input_files = glob.glob(os.path.join(dir_,"*.root"))

        runcmd = ["python",run_script,"-o",out_file,"--cmd",ntupcmd,"--hadd","-t",str(args.nr_threads)]
        runcmd.extend(input_files)
        
        print("running {}".format(dir_))
        subprocess.Popen(runcmd).communicate()
    print("all done")
        
        
    
if __name__ == "__main__":
    main()
