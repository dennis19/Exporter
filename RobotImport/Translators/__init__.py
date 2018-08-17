from vcApplication import *

def OnStart():
  cmduri = getApplicationPath() + 'import_mod_to_rsl.py'
  cmd = loadCommand('import_mod_to_rsl',cmduri)
  addMenuItem('VcTabTeach/Import', "Import", -1, "import_mod_to_rsl")
