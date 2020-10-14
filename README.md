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


### runPhaseIINtup.py

This script reads in our HLT EDM format and converts it to a flat tree
