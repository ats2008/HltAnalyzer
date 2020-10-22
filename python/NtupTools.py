from array import array

def treetype_to_arraytype(treetype):
    if treetype=='I': 
        return 'i'
    if treetype=='i': 
        return 'I'
    elif treetype=='F':
        return 'f'
    else:
        raise ValueError("undefined type code",treetype)

def make_leaf_name(name,type_,sizename=None):
    """converts a names to a leaf string for a branch
    goes to the format {name}/{type_} or the format {name}[sizename]/{type_}
    also changes '-' to '_'
    """
    array_str = "[{sizename}]".format(sizename=sizename) if sizename else ""    
    return '{}{}/{}'.format(name,array_str,type_).replace('-','_')


class TreeVar:
    def __init__(self,tree,varnametype,func,maxsize=1,sizevar=""):
        self.varname = varnametype.split("/")[0]
        self.vartype = varnametype.split("/")[1]
        self.func = func
        self.data = array(treetype_to_arraytype(self.vartype),[0]*maxsize)
        self.sizevar = sizevar
        self.create_branch(tree)

    def create_branch(self,tree):       
        tree.Branch(self.varname,self.data,make_leaf_name(self.varname,self.vartype,self.sizevar))
        
    def fill(self,obj,objnr=0):
        self.data[objnr] = self.func(obj)
        
    def clear(self):
        for n,x in enumerate(self.data):
            self.data[n] = 0


