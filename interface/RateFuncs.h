#ifndef Analysis_HLTAnalyserPy_RateFuncs_h
#define Analysis_HLTAnalyserPy_RateFuncs_h

#include <boost/algorithm/string/replace.hpp>

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RResultPtr.hxx"
#include "TH1D.h"
#include "TBits.h"

#include <iostream>
#include <numeric>

class RateFuncs {
public:
  
  static ROOT::RDF::RNode readTBits(ROOT::RDF::RNode df,std::string newName,std::string branchName) {
    auto vecTBits = [](const TBits& bits){
      ROOT::VecOps::RVec<bool> v(bits.GetNbits());
      for(unsigned int i=0;i<bits.GetNbits();i++){
	v.push_back(bits.TestBitNumber(i));
      }
      return v;
    };
    
    df = df.Define(newName,vecTBits,{branchName});
    return df;
  }
  
  class PassCounts : public TH1 {
  private:
    size_t trigBitNr_;
    std::vector<int> counts_;
  public:
    PassCounts(size_t bitNr,size_t nrBits):
      trigBitNr_(bitNr),counts_(nrBits,0){}

    PassCounts(const PassCounts& rhs):TH1(),counts_(rhs.counts_){}

    void Fill(const TBits& bits) {
      if(bits[trigBitNr_]) {
	std::cout <<" filling "<<trigBitNr_<<std::endl;
	for(size_t bitNr=0;bitNr<bits.GetNbits();bitNr++){
    	  counts_[bitNr] += bits.TestBitNumber(bitNr);
    	}	
      }
    }
    //template<typename T>
    Long64_t Merge(TCollection *coll) override {
      //TList list;
      //      list.AddAll(coll);
      TIter next(coll);
      PassCounts* rhs = nullptr;
      while ((rhs=static_cast<PassCounts*>(next()))){	
	for(size_t bitNr=0;bitNr<counts_.size();bitNr++){
	  counts_[bitNr]+=rhs->counts_[bitNr];
	}
      }
      return std::accumulate(counts_.begin(),counts_.end(),0);
    }
     // for(const auto& obj : merge){
    //	for(size_t bitNr=0;bitNr<counts_.size();bitNr++){
    ///	  counts_[bitNr]+=obj[bitNr];
    //	}
    //   }
    //  return std::accumulate(counts_.begin(),counts_.end(),0);
    // }

    const std::vector<int>& counts()const{return counts_;}
  };
  static ROOT::RDF::RResultPtr<std::decay_t<PassCounts> > test(ROOT::RDF::RNode df,size_t bitNr,size_t nrBits) {
    return df.Fill(PassCounts(bitNr,nrBits),{"hltRes"});

  }

  class L1SeedExpresConverter {
  private: 
    std::vector<std::vector<std::string> > l1Expres_;
    std::vector<std::vector<size_t> > l1Indices_;
    
  public:
    
    L1SeedExpresConverter(std::vector<std::vector<std::string> > l1Expres,
			  std::vector<std::vector<size_t> > l1Indices):
      l1Expres_(l1Expres),
      l1Indices_(l1Indices){}

    TBits operator()(const TBits& l1Bits){
      TBits expresBits;
      for(size_t expresNr=0;expresNr<l1Indices_.size();expresNr++){
	if(passAny(l1Indices_[expresNr],l1Bits)) expresBits.SetBitNumber(expresNr);
      }
      return expresBits;
    }

    static bool passAny(const std::vector<size_t>& indices,const TBits& l1Bits){
      for(auto indx : indices){
	if(l1Bits.TestBitNumber(indx)) return true;
      }
      if(!indices.empty()) return false;
      else return true; //no indicies means no seed so always true
    }
      
  };
  enum class TrigType {
    HLT,ALCA,DST,MC,UNKNOWN
      };
      
  static TrigType getTrigType(const std::string& name){
      if(name.find("HLT_")==0) return TrigType::HLT;
      if(name.find("AlCa_")==0) return TrigType::ALCA;
      if(name.find("DST_")==0) return TrigType::DST;
      if(name.find("MC_")==0) return TrigType::MC;
      return TrigType::UNKNOWN;	   
  } 

  class TrigPath {
  private:

    std::string name_;
    size_t hltIndex_;
    size_t l1SeedIndex_;
    TrigType type_;
    std::vector<int> prescales_;
    std::vector<std::string> l1Seeds_;
    bool physics_;

    int psCount_;
    std::vector<int> nrPassed_;
    std::vector<int> result_;
    bool anyPSColPass_;

  public:
    TrigPath():hltIndex_(0),l1SeedIndex_(0),
	       type_(RateFuncs::TrigType::UNKNOWN),
	       physics_(false),
	       psCount_(0),
	       anyPSColPass_(false){}
    TrigPath(std::string name,size_t hltIndex,size_t l1SeedIndex, std::vector<int> prescales, std::vector<std::string> l1Seeds, bool physics=true):
      name_(name),hltIndex_(hltIndex),l1SeedIndex_(l1SeedIndex),
      type_(getTrigType(name_)),
      prescales_(prescales),l1Seeds_(l1Seeds),physics_(physics),
      psCount_(341),
      nrPassed_(prescales_.size(),0),
      result_(prescales_.size(),0),
      anyPSColPass_(false)
    {

    }
   
    

    void fillResults(const TBits& l1Bits,const TBits& hltBits){
    
      if(l1Bits.TestBitNumber(l1SeedIndex_)){
	
	psCount_++;
	bool res = hltBits.TestBitNumber(hltIndex_);
	std::transform(prescales_.begin(),prescales_.end(),result_.begin(),
		       [res,this](int ps){return res && ps!=0 && this->psCount_%ps==0;});
	std::transform(nrPassed_.begin(),nrPassed_.end(),result_.begin(),nrPassed_.begin(),std::plus<int>());
	anyPSColPass_ = res && std::any_of(result_.begin(),result_.end(),[](int i){return i!=0;});
	  

      }else{
	//previously it passed and we have to reset it
	if(anyPSColPass_){
	  for(auto& res: result_){
	    res = 0;
	  }
	  anyPSColPass_ = false;
	}
	if( hltBits.TestBitNumber(hltIndex_)){
	  std::cout <<"warning "<<name()<<" passes but fails L1 seeds, this is not possible without an error "<<l1SeedIndex_<<std::endl;
	}
      }
    }

    const std::vector<int>& nrPassed()const{return nrPassed_;}
    const std::vector<int>& result()const{return result_;}
    const std::string& name()const{return name_;}
    size_t hltIndex()const{return hltIndex_;}
    size_t l1SeedIndx()const{return l1SeedIndex_;}
    TrigType trigType()const{return type_;}
    bool physics()const{return physics_;}
    const std::vector<std::string>& l1Seeds()const{return l1Seeds_;}
    const std::vector<int>& prescales()const{return prescales_;}
    
  };
  


  class TrigGroup {
  private:
    std::string name_;
    std::vector<std::string> pathNames_;
    std::vector<size_t> pathIndices_;
    std::vector<int> nrPassed_;

  public:
    TrigGroup(){}
    TrigGroup(std::string name,
	      std::vector<std::string> pathNames,
	      std::vector<size_t> pathIndices,int nrCols):
      name_(name),
      pathNames_(pathNames),
      pathIndices_(pathIndices),
      nrPassed_(nrCols,0){}
      
	      
    const std::string& name()const{return name_;}
    const std::vector<std::string>& pathNames()const{return pathNames_;}
    const std::vector<size_t>& pathIndices()const{return pathIndices_;}
    const std::vector<int>& nrPassed()const{return nrPassed_;}
     
    //first index is path, second is column
    void fill(const std::vector<TrigPath> & pathResults){
      if(pathResults.empty()){
	return; 
      }
      if(pathResults[0].result().size()!=nrPassed_.size()){
	std::cout <<"ps col mismatch "<<pathResults[0].result().size()<<" vs "<<nrPassed_.size()<<std::endl;
      }
      for(size_t psColl = 0;psColl<nrPassed_.size();psColl++){
	for(auto pathIndx : pathIndices_){	  
	  if(pathResults[pathIndx].result()[psColl]){
	    nrPassed_[psColl]++;
	    break;
	  }
	}
      }
    }	
  };

  class TrigMenu {
  private: 
    std::vector<TrigPath> paths_;
    std::vector<TrigGroup> datasets_;
    
    std::vector<int> nrPassed_;
    int nrTot_;
    
  public:
    TrigMenu():nrTot_(0){}
    TrigMenu(std::vector<TrigPath> paths,std::vector<TrigGroup> datasets,int nrCol):
      paths_(paths),datasets_(datasets),
      nrPassed_(nrCol,0),
      nrTot_(0)
    {
    }

    void fill(TBits& l1Expres,TBits& hltMenu){
      //first we fill the results then use that to fill the datasets
      //and nrPassed
      for(size_t pathNr=0;pathNr<paths_.size();pathNr++){
	paths_[pathNr].fillResults(l1Expres,hltMenu);
      }
      for(auto& dataset : datasets_){
	dataset.fill(paths_);
	
      }
      //probably could make this a std::transform too
      for(size_t psCol = 0; psCol < nrPassed_.size();psCol++){
	bool pass = false;
	for(const auto& path : paths_){
	  if(path.physics() && path.result()[psCol]){
	    pass = true;
	    break;
	  }	  
	}
	if(pass) nrPassed_[psCol]++;
      }
      nrTot_++;
    }

    const std::vector<TrigPath>& paths()const{return paths_;}
    const std::vector<TrigGroup>& datasets()const{return datasets_;}
    const std::vector<int>& nrPassed()const{return nrPassed_;}
    int nrTot()const{return nrTot_;}

  };
      
      
      
  
   

};

#endif
