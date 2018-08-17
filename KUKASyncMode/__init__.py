from vcApplication import *

def OnStart():

  # krc versions
  cmduri = getApplicationPath() + 'import_kuka_machine_data_krc.py'
  cmd = loadCommand("ImportKUKAMachineData",cmduri)
  cmd.createProperty( VC_STRING, "ComponentName" )
  cmd.createProperty( VC_STRING, "FileName" )
  cmd.createProperty( VC_STRING, "ErrorString" )  
  
  cmduri = getApplicationPath() + 'export_kuka_machine_data_krc.py'
  cmd = loadCommand("ExportKUKAMachineData",cmduri)
  cmd.createProperty( VC_STRING, "ComponentName" )
  cmd.createProperty( VC_STRING, "FileName" )
  cmd.createProperty( VC_STRING, "BakFileName" )
  cmd.createProperty( VC_STRING, "ErrorString" )
  
  cmduri = getApplicationPath() + 'import_kuka_config_data_krc.py'
  cmd = loadCommand("ImportKUKAConfigData",cmduri)
  cmd.createProperty( VC_STRING, "ComponentName" )
  cmd.createProperty( VC_STRING, "FileName" )
  cmd.createProperty( VC_STRING, "ErrorString" )  
  
  cmduri = getApplicationPath() + 'export_kuka_config_data_krc.py'
  cmd = loadCommand("ExportKUKAConfigData",cmduri)
  cmd.createProperty( VC_STRING, "ComponentName" )
  cmd.createProperty( VC_STRING, "FileName" )
  cmd.createProperty( VC_STRING, "ErrorString" )
  
  addMenuItem('VcTabTeach/KUKAExport', "Pre Process", -1, "ExportKUKAMachineData")
    