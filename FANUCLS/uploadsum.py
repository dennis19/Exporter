from vcCommand import *
import re
import os.path
import vcMatrix
import uploadva
import uploadBackup
sp = r'\s+'
eq = r'\s*=\s*'
comma = r'\s*,\s*'
colon = r'\s*:\s*'
semicolon = r'\s*;\s*'
obracket = r'\s*\[\s*'
cbracket = r'\s*\]\s*'
obrace = r'\s*\{\s*'
cbrace = r'\s*\}\s*'
integer = r'-?\d+'
ginteger = r'('+integer+')'
real = r'-?\d*\.?\d+(?:[eE][-+]?\d+)?'
greal = r'('+real+')'
alphanum = r'[a-zA-Z]+\w*'
galphanum = r'('+alphanum+')'

nl = r' *\r?[\n\0]'
sl = r'\A|\n'
end = r'\s*$'

roregister = "RO"+obracket+ginteger+cbracket+" "+"(?P<value>[a-zA-Z]+)"+"  "+"(?P<comment>[a-zA-Z0-9_\-\s\:\.]+)"
riregister = "RI"+obracket+ginteger+cbracket+" "+"(?P<value>[a-zA-Z]+)"+"  "+"(?P<comment>[a-zA-Z0-9_\-\s\:\.]+)"
flgregister = "FLG"+obracket+ginteger+cbracket+" "+"(?P<value>[a-zA-Z]+)"+"  "+"(?P<comment>[a-zA-Z0-9_\-\s\:\.]+)"
uoregister = "UO"+obracket+ginteger+cbracket+" "+"(?P<value>[a-zA-Z]+)"+"  "+"(?P<comment>[a-zA-Z0-9_\-\s\:\.\*]+)"
uiregister = "UI"+obracket+ginteger+cbracket+" "+"(?P<value>[a-zA-Z]+)"+"  "+"(?P<comment>[a-zA-Z0-9_\-\s\:\.\*]+)"

ro_="RO"+obracket
ri_="RI"+obracket
flg_="FLG"+obracket

app = getApplication()

def cleanUp():
  setNextState(None)

#-------------------------------------------------------------------------------
def OnAbort():
  cleanUp()

#-------------------------------------------------------------------------------
def OnStop():
  cleanUp()


def OnStart():
  program = uploadBackup.getActiveProgram()
  if not program:
    app.messageBox("No program selected, aborting.", "Warning", VC_MESSAGE_TYPE_WARNING, VC_MESSAGE_BUTTONS_OK)
    return False
  # endif

  opencmd = app.findCommand("dialogOpen")
  uri = ""
  ok = True
  fileFilter = "FANUC Robot Program files (*.dg)|*.dg"
  opencmd.execute(uri, ok, fileFilter)
  if not opencmd.Param_2:
    print "No file selected for uploading, aborting command"
    return False
  # endif
  uri = opencmd.Param_1
  filename = uri[8:len(uri)]
  try:
    infile = open(filename, "r")
  except:
    print "Cannot open file \'%s\' for reading" % filename
    return
  # endtry

  uploadsum_(program, infile)

  return True


def uploadsum_(program,infile):
  filestring = infile.read()
  infile.close()

  executor = program.Executor
  comp = executor.Component

  for line in filestring.split('\n'):

    ROREG_ = re.search(roregister, line)
    if ROREG_:
      val = ROREG_.group('value')
      if val == 'ON':
        val = 1
      elif val == 'OFF':
        val = 0
      comment=uploadva.delChars(ROREG_.group('comment'))
      if val or comment:
        nindex = eval(ROREG_.group(1))
        prop = comp.createProperty(VC_REAL, 'RobotOutput::RO%i' % nindex + '%s' % comment)
        prop.Value = val
        prop.Group = nindex
      continue

    RIREG_ = re.search(riregister, line)
    if RIREG_:
      val = RIREG_.group('value')
      if val == 'ON':
        val = 1
      elif val == 'OFF':
        val = 0
      comment=uploadva.delChars(RIREG_.group('comment'))
      if val or comment:
        nindex = eval(RIREG_.group(1))
        prop = comp.createProperty(VC_REAL, 'RobotInput::RI%i' % nindex + '%s' % comment)
        prop.Value = val
        prop.Group = nindex
      continue

    UOREG_ = re.search(uoregister, line)
    if UOREG_:
      val = UOREG_.group('value')
      if val == 'ON':
        val = 1
      elif val == 'OFF':
        val = 0
      comment=uploadva.delChars(UOREG_.group('comment'))
      if val or comment:
        nindex = eval(UOREG_.group(1))
        prop = comp.createProperty(VC_REAL, 'UserOutput::UO%i' % nindex + '%s' % comment)
        prop.Value = val
        prop.Group = nindex
      continue

    UIREG_ = re.search(uiregister, line)
    if UIREG_:
      val = UIREG_.group('value')
      if val == 'ON':
        val = 1
      elif val == 'OFF':
        val = 0
      comment=uploadva.delChars(UIREG_.group('comment'))
      if val or comment:
        nindex = eval(UIREG_.group(1))
        prop = comp.createProperty(VC_REAL, 'UserInput::UI%i' % nindex + '%s' % comment)
        prop.Value = val
        prop.Group = nindex
      continue


    FLGREG_ = re.search(flgregister, line)
    if FLGREG_:
      val = FLGREG_.group('value')
      if val == 'ON':
        val = 1
      elif val == 'OFF':
        val = 0
      comment = uploadva.delChars(FLGREG_.group('comment'))
      if val or comment:
        nindex = eval(FLGREG_.group(1))
        prop = comp.createProperty(VC_REAL, 'Flags::F%i' % nindex + '%s' % comment)
        prop.Value = val
        prop.Group = nindex
      continue

  return True



#-------------------------------------------------------------------------------

addState(None)
