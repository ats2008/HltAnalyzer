# HLTAnalyserPy

A set of tools to analyse the HLT EDM files in py fwlite

## EvtData module

A package which eases the use retrieval of objects from the event


### EvtData 

The main class EvtData is designed as a single access point for retreiving objects from the event, it is expected that all objects are retrieved through this object

   * EvtData(products=[],verbose=False)
      * takes a list of products to setup handles 
      * product format is a dict with fields name, type and tag
         * name = name to retrieve the object with
         * type = c++ type, eg "std::vector<reco::EgTrigSumObj>"
	 * tag = input tag corresponding the the product
      * EvtData can be set to "lazy" and so does not retrieve any declared product till it is required so is costs nothing to over declare the products here
    * get_handles(event,on_demand=True)
      * gets the handles for the event, if on_demand=True, it instead waits for something to request the handle
      * necessary to call on each new event before retreiving the products
      * a better name would be initalise_handles()
    * get_handle(name):
      * gets the handle corresponding to the product with nane name
    * get(name):
      * gets the product with name name, returns None if the handle is invalid
 
### EvtWeight

This takes in a json of all the MC weights and returns the correct one for a given event.   

   * EvtWeights(input_filename,lumi)
      * reads in the weights from input_filename for a luminosity of lumi (in pb)
   * weight_from_evt(event)
      * returns the weight appriopriate for the event
      * note: it does this based of the file the event is read from so requires the filename is encoded in a certain way
      * note you need to pass in a fwlite::ChainEvent not the FWLite.Events class, therefore you might need to do a events.object() if you are using the Events class directly
   * weight_from_name(dataset_name)
      * returns the weight for  a given dataset with the specified name

### Misc Funcs

   * add_product(prods,name,type_,tag)
      * helper func to make add a product dict with keys name,type and tag to a list of product dicts named prods
   * get_objs(evtdata,events,objname,indx)
      * used interactively, simplifes getting an object from the event, basically saves typing events.to(index), evtdata.gethandles(events), evtdata.get(objname)
      * should not be used interactively as its inefficient and may have side effects if its used for multiple collections


## GenTools

This package allows us to gen match objects

  * get_genparts(genparts,pid=11,antipart=True,status=PartStatus.PREFSR)
     * returns a list of all gen particles matching the given criteria from the the hard process
     * genparts = the GenParticle collection
     * pid = pid of the particle
     * antipart if true, also allows the antiparticle
     * status: whether it is prefsr (PREFSR), post fsr (POSTFSR) or final version of the object (FINAL)
 
  * match_to_gen(eta,phi,genparts,pid=11,antipart=True,max_dr=0.1,status=PartStatus.PREFSR)
     * returns (GenParticle,dr) of the best match to the eta,phi passed in. If no match is found GenParticle is None
     * eta/phi = eta/phi to do the dr with
     * max_dr = maximum allowed dr to consider a match
     * pid = pid of the particle
     * antipart if true, also allows the antiparticle
     * status: whether it is prefsr (PREFSR), post fsr (POSTFSR) or final version of the object (FINAL)
     

## Scripts

The following scripts exist in the test directory

### runMultiThreaded.py

A useful script to parallelise other scripts. Pythons multithreading is a bit awful, listwise with roots. The simpliest solution is just to run N seperate versions of a script, splitting the input files amoungst the N jobs and then concatenate the output. This script will automatically do this for you and then optionally hadd the output 

It assumes the script its parallelising takes a list of input files as the first argument and "-o" as the output filename. 

if you have a script 
```python Analysis/HLTAnalyserPy/test/makePhaseIINtup.py /eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/Upgrade/EGM_PhaseII/mc/11_1_3/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th_* -o doubleEleTest.root -w weights_Oct4th.json -r 5000```

to parallelise it you just need to do

```python Analysis/HLTAnalyserPy/test/runMultiThreaded.py -o doubleEleTest.root /eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/Upgrade/EGM_PhaseII/mc/11_1_3/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th_* --cmd "python Analysis/HLTAnalyserPy/test/makePhaseIINtup.py  -w weights_Oct4th.json -r 5000" --hadd```

where we have moved the input and output filenames to arguments of the runMultiThreaded script and then put the command to execute as --cmd "<  >". We have set it to automatically hadd the output, remove "--hadd" to stop this


### makePhaseIINtup.py

This script reads in our HLT EDM format and converts it to a flat tree. This as been designed to be easy to collaborate between ourselfs to add new variables

The tree is constructed by EgHLTTree in Trees. The EgHLTTree class defines a series of core branches and how to fill them from the EvtData object. 

To aid collaboration, two extra functions have been defined `add_eg_vars` and `add_eg_update_funcs`. These functions will add you to add variables for a e/g hlt objects to the tree and also specific functions which may be needed to update the e/g hlt objects before filling the tree

To add new variables, you will need to define a function to make it which takes an EgTrigSumObj as the first argument (or is a method of EgTrigSumObj, to python these are effectively the same thing). 

It would be best to create a new file in HLTAnalyserPy/python with the function or collection of functions and import that function into makePhaseIINtup.py

#### Adding a New EG Variable

To add a variable simply pass as dictionary with the keys being the name of the variable with the [root type](https://root.cern.ch/doc/master/classTTree.html#addcolumnoffundamentaltypes) appended (eg "et/F") and the values being a function or other callable object which takes an EgTrigSumObj as its sole arugment to EgHLTTree.add_eg_vars(). This function can be called multiple times and will just add the variables, overriding existing variables of the same name

If the function to produce the variable requires additional arguements beyond the egobj, you can use CoreTools.UnaryFunc. This you can pass in either a string as you would type in python, including nesting functions such as superCluster().energy(). In this case the string has to be a method of the object the unary func is called with. You can also pass in functools.partial object where you can specify the addtional arguements and these can be either member functions or non member functions or in deed any callable object.
   
You can see examples of this in the EgHLTTree class defination where it fills the default variables. Its important to remember here that member variables in python act like a function which takes the object as the first argument, a fact we exploit here. 

#### Updating the EG objects

It might be useful to update the e/gamma objects before filling. This might be adding new variables to them, fixing existing variables, etc. This can be done by passing a function which takes an EgTrigSumObj as its only argument. As before functions which require additional arguments can be added using UnaryFunc taking a functools.partial object






