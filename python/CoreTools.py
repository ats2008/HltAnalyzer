from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import sys
import re

def load_fwlitelibs():
    oldargv = sys.argv[:]
    sys.argv = [ '-b-' ]
    sys.argv = oldargv
    ROOT.gSystem.Load("libFWCoreFWLite.so");
    ROOT.gSystem.Load("libDataFormatsFWLite.so");
    ROOT.FWLiteEnabler.enable()


def convert_args(input_args):
    """supports ints, floats and strings and removes starting and ending quotes from strings"""
    
    output_args = []
    for arg in input_args:
        arg = arg.rstrip().lstrip()
        try:
            output_args.append(int(arg))
            break
        except ValueError:
            pass
        try: 
            output_args.append(float(arg))
        except ValueError:
            pass
        if arg.startswith('"') and arg.endswith('"'):
            output_args.append(arg[1:-1])
        else:
            output_args.append(arg)
    return output_args
        

def call_func_nochain(obj,func_str):
    #first check if it is just a property 
    if func_str.isalnum():
        return (obj,func_name)

    #okay is it a function
    re_res = re.search(r'([\w]+)(\(\)\Z)',func_str)
    if re_res:
        func_name = re_res.group(1)
        return getattr(obj,func_name)()

    #now check if its a function with arguments
    re_res = re.search(r'([\w]+)(\(([\w",. ]+)\))',func_str)
    if re_res:
        func_name = re_res.group(1)
        args = convert_args(re_res.group(3).split(","))
        try:
            return getattr(obj,func_name)(*args)
        except ValueError as err: 
            #much easier in python3, small hack here for 2.7
            err.message = "for function '{}' with args {}\n {}".format(func_name,str(args),err.message)
            err.args = (err.message,) + err.args[1:] 
            raise err

    raise RuntimeError("function string {} could not be resolved".format(func_str))

        
def call_func(obj,func_str):
    sub_funcs = func_str.split(".")
    res = obj
    for sub_func in sub_funcs:
        res = call_func_nochain(res,sub_func)
    return res

def get_filenames(input_filenames,prefix=""):
    output_filenames = []
    for filename in input_filenames:
        if not filename.endswith(".root"):
            with open(filename) as f:
                output_filenames.extend(['{}{}'.format(prefix,l.rstrip()) for l in f])
        else:
            output_filenames.append('{}{}'.format(prefix,filename))
    return output_filenames
