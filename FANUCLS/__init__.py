from vcApplication import *

def OnStart():
  localize = findCommand('netCommand') 

  cmduri = getApplicationPath() + 'uploadBackup.py'
  cmd = loadCommand('FanucUploadBackup', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Upload FANUC Backup', -1, cmd.Name, 'Uploads FANUC Backup into simulation environment', 'rgImportGeneral' )


  cmduri = getApplicationPath() + 'convert.py'
  cmd = loadCommand('FanucConvert', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Convert RSL program to FANUC LS', -1, cmd.Name, 'Converts the currently selected RSL subprogram into a FANUC LS program', 'rsMetadataShow' )

  cmduri = getApplicationPath() + 'convertva.py'
  cmd = loadCommand('FanucConvertVa', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Convert RSL program to FANUC VA', -1, cmd.Name, 'Converts the currently selected RSL subprogram into a FANUC VA program', 'rsMetadataShow' )

  cmduri = getApplicationPath() + 'deleteroutine.py'
  cmd = loadCommand('FanucDeleteRoutine', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Delete FANUC LS Subprogram', -1, cmd.Name, 'Removes selected Subprogram including any LS references', 'rTrashcan' )

  cmduri = getApplicationPath() + 'addroutine.py'
  cmd = loadCommand('FanucAddRoutine', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Add LS Subprogram', -1, cmd.Name, 'Adds FANUC LS Subprogram to Program page including any dependancies', 'rAdd' )

  cmduri = getApplicationPath() + 'upload.py'
  cmd = loadCommand('FanucUploadLS', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Upload FANUC LS Program', -1, cmd.Name, 'Uploads FANUC LS program file into simulation environment', 'rgImportGeneral' )

  cmduri = getApplicationPath() + 'upload.py'
  cmd = loadCommand('FanucUploadLSA', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Upload ABB MOD Program', -1, cmd.Name, 'Uploads ABB MOD program file into simulation environment', 'rgImportGeneral' )


  cmduri = getApplicationPath() + 'uploadva.py'
  cmd = loadCommand('FanucUploadVA', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Upload FANUC LS VA data file', -1, cmd.Name, 'Uploads a FANUC LS VA System Data file', 'rRestoreLayout' )

  cmduri = getApplicationPath() + 'uploadsum.py'
  cmd = loadCommand('FanucUploadSum', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Upload FANUC LS summary data file', -1, cmd.Name, 'Uploads a FANUC LS Summary System Data file', 'rRestoreLayout' )


  cmduri = getApplicationPath() + 'download.py'
  cmd = loadCommand('FanucDownloadLS', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Download FANUC LS file', -1, cmd.Name, 'Saves FANUC LS file to filesystem for export to controller', 'rgExportGeneral' )

  cmduri = getApplicationPath() + 'upload.py'
  cmd = loadCommand('FanucUpdate', cmduri)
  addMenuItem('VcProgramStatements/ProgramStatements/LS', 'Update FANUC LS Emulator', -1, cmd.Name, 'Update LS Emulator Python Script', 'rUpdate' )

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

