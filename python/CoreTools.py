from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import sys
import re
from enum import Enum
import functools

def load_fwlitelibs():
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
    if func_str.replace("_","").isalnum(): #basically allows "_" but not other non alphanumerica charactor
        return getattr(obj,func_str)

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
    """
    allows us to call a function/method via a string as you would type it in python
    It can also chain functions or simply return member variables
    examples:
       var("hltEgammaClusterShapeUnseeded_sigmaIEtaIEta5x5",0)
       eventAuxiliary().run()
       
    """
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


def get_filenames_vec(input_filenames,prefix=""):
    output_filenames = ROOT.std.vector("std::string")()
    for filename in input_filenames:
        if not filename.endswith(".root"):
            with open(filename) as f:
                for line in f:
                    output_filenames.push_back('{}{}'.format(prefix,line.rstrip()))
        else:
            output_filenames.push_back('{}{}'.format(prefix,filename))
    return output_filenames


class UnaryFunc:
    """
    this is a simple class which allows us to define a unary function 
    this can be a method of function or a normal one
    can be specified using parital wrapping around the function or a string
    which allows us to convert functions to unary functions vi
    """
    class FuncType(Enum):
        default = 0
        str_ = 1 
        partial_ = 2
        

    def __init__(self,func):
        self.func = func        

        func_type = type(func)
        if func_type==str:
            self.func_type = UnaryFunc.FuncType.str_
        elif func_type==functools.partial:
            self.func_type = UnaryFunc.FuncType.partial_
        else:
            self.func_type = UnaryFunc.FuncType.default


    def __call__(self,obj):
        if self.func_type==UnaryFunc.FuncType.str_:
            return call_func(obj,self.func)
        #here we work around the fact we need to put the object as the first
        #argument to the function when using partial
        elif self.func_type==UnaryFunc.FuncType.partial_: 
            return self.func.func(obj,*self.func.args,**self.func.keywords)
        elif self.func_type==UnaryFunc.FuncType.default:
            return self.func(obj)
        else:
            raise ValueError("error, func_type {} not known".func_type)


def get_best_dr_match(obj_to_match,coll,max_dr):
    best_dr2 = max_dr*max_dr
    matched_obj = None
    eta = obj_to_match.eta()
    phi = obj_to_match.phi()
    for obj in coll:
        dr2 = ROOT.reco.deltaR2(eta,phi,obj.eta(),obj.phi())
        if dr2 < best_dr2:
            best_dr2 = dr2
            matched_obj = obj
    return matched_obj
        
            
