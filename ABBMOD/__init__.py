from vcApplication import *

def OnStart():
  localize = findCommand('netCommand') 

  cmduri = getApplicationPath() + 'convert.py'
  cmd = loadCommand('ABBConvert', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Convert RSL program to ABB MOD', -1, cmd.Name, 'Converts the currently selected RSL subprogram into a ABB MOD program', 'rsMetadataShow' )

  cmduri = getApplicationPath() + 'deleteroutine.py'
  cmd = loadCommand('ABBDeleteRoutine', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Delete ABB MOD Subprogram', -1, cmd.Name, 'Removes selected Subprogram including any ABB MOD references', 'rTrashcan' )

  cmduri = getApplicationPath() + 'addroutine.py'
  cmd = loadCommand('ABBAddRoutine', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Add ABB MOD Subprogram', -1, cmd.Name, 'Adds ABB MOD Subprogram to Program page including any dependancies', 'rAdd' )

  cmduri = getApplicationPath() + 'upload.py'
  cmd = loadCommand('ABBUploadMod', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Upload ABB MOD Program', -1, cmd.Name, 'Uploads ABB MOD program file into simulation environment', 'rgImportGeneral' )

  cmduri = getApplicationPath() + 'uploadva.py'
  cmd = loadCommand('ABBUploadVA', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Upload ABB MOD VA data file', -1, cmd.Name, 'Uploads a ABB MOD VA System Data file', 'rRestoreLayout' )

  cmduri = getApplicationPath() + 'download.py'
  cmd = loadCommand('ABBDownloadMod', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Download ABB MOD file', -1, cmd.Name, 'Saves ABB MOD file to filesystem for export to controller', 'rgExportGeneral' )

  cmduri = getApplicationPath() + 'upload.py'
  cmd = loadCommand('ABBUpdate', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/Mod', 'Update ABB MOD Emulator', -1, cmd.Name, 'Update ABB MOD Emulator Python Script', 'rUpdate' )

  """
  cmduri = getApplicationPath() + 'addstatement.py'
  cmd = loadCommand("FanucLSEditor",cmduri)
  iconuri = getApplicationPath() + 'editor.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC EDITOR", cmd )

  cmduri = getApplicationPath() + 'addstatement.py'
  cmd = loadCommand("FanucAddStatement",cmduri)
  iconuri = getApplicationPath() + 'addstatement.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC ADD STATEMENT", cmd )

  cmduri = getApplicationPath() + 'addroutine.py'
  cmd = loadCommand("FanucAddRoutine",cmduri)
  iconuri = getApplicationPath() + 'addroutine.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC ADD ROUTINE", cmd )

  cmduri = getApplicationPath() + 'deleteroutine.py'
  cmd = loadCommand("FanucDeleteRoutine",cmduri)
  iconuri = getApplicationPath() + 'deleteroutine.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC DELETE ROUTINE", cmd )

  cmduri = getApplicationPath() + 'download.py'
  cmd = loadCommand("FanucDownload",cmduri)
  iconuri = getApplicationPath() + 'download.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC DOWNLOAD", cmd )

  cmduri = getApplicationPath() + 'upload.py'
  cmd = loadCommand("FanucUpload",cmduri)
  iconuri = getApplicationPath() + 'upload.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC UPLOAD", cmd )

  cmduri = getApplicationPath() + 'uploadva.py'
  cmd = loadCommand("FanucUploadVA",cmduri)
  iconuri = getApplicationPath() + 'uploadva.bmp'
  icon = loadBitmap(iconuri)
  cmd.Icon = icon

  addMenuItem(VC_MENU_RSLPROCESS, "FANUC LS.FANUC UPLOAD SYS VARS", cmd )
  """

