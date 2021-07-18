import FWCore.ParameterSet.Config as cms

process = cms.Process("WriteTest")
process.source = cms.Source( "EmptySource")
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(1))
 
process.writer = cms.EDAnalyzer("FWLiteESRecordWriterAnalyzer",
   fileName = cms.untracked.string("cond_test.root"),
   L1TUtmTriggerMenuRcd = cms.untracked.VPSet(
       cms.untracked.PSet(
           type=cms.untracked.string("L1TUtmTriggerMenu"),
           label=cms.untracked.string("")
           )
       )
   )
process.GlobalTag = cms.ESSource( "PoolDBESSource",
    globaltag = cms.string( "113X_dataRun3_HLT_v3" ),
    RefreshEachRun = cms.untracked.bool( False ),
    snapshotTime = cms.string( "" ),
    toGet = cms.VPSet( 
    ),
    pfnPostfix = cms.untracked.string( "None" ),
    DBParameters = cms.PSet( 
      connectionRetrialTimeOut = cms.untracked.int32( 60 ),
      idleConnectionCleanupPeriod = cms.untracked.int32( 10 ),
      enableReadOnlySessionOnUpdateConnection = cms.untracked.bool( False ),
      enablePoolAutomaticCleanUp = cms.untracked.bool( False ),
      messageLevel = cms.untracked.int32( 0 ),
      authenticationPath = cms.untracked.string( "." ),
      connectionRetrialPeriod = cms.untracked.int32( 10 ),
      connectionTimeOut = cms.untracked.int32( 0 ),
      enableConnectionSharing = cms.untracked.bool( True )
    ),
    RefreshAlways = cms.untracked.bool( False ),
    connect = cms.string( "frontier://FrontierProd/CMS_CONDITIONS" ),
    ReconnectEachRun = cms.untracked.bool( False ),
    RefreshOpenIOVs = cms.untracked.bool( False ),
    DumpStat = cms.untracked.bool( False )
)
process.source = cms.Source( "PoolSource",
    fileNames = cms.untracked.vstring(
        '/store/data/Run2018D/EphemeralHLTPhysics1/RAW/v1/000/323/775/00000/FE646EF8-1F20-C543-995D-3DBB282972BA.root',
    ),
    inputCommands = cms.untracked.vstring(
        'keep *'
    )
)
process.out = cms.EndPath(process.writer)
