from vcCommand import *
import re
import os.path
import vcMatrix

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

x = r'X' + colon + r'(?P<x>'+real+')' 
y = r'Y' + colon + r'(?P<y>'+real+')'
z = r'Z' + colon + r'(?P<z>'+real+')'
w = r'W' + colon + r'(?P<w>'+real+')'
p = r'P' + colon + r'(?P<p>'+real+')'
r = r'R' + colon + r'(?P<r>'+real+')'

xyzwpr = x + sp + y + sp + z + sp + w + sp + p + sp + r 

fut = r'(?P<fut>[FN]\s*[UD]*\s*[TB]*)'
t1 = r'(?P<t1>'+integer+')'
t2 = r'(?P<t2>'+integer+')'
t3 = r'(?P<t3>'+integer+')'
config = r'Config' + colon + fut + comma + t1 + comma + t2 + comma + t3 

frame = obracket + ginteger + comma + ginteger + cbracket + eq + 'Group' + colon + ginteger + sp + config + sp + xyzwpr
re_frame = re.compile( frame, re.M )

posregister = obracket + ginteger + comma + ginteger + cbracket + eq + r"\'(.*)\'"  + sp + 'Group' + colon + ginteger + sp + config + sp + xyzwpr
re_posreg = re.compile( posregister, re.M )

numregister = obracket + ginteger + cbracket + eq + greal + r"\s*\'(.*)\'" 
re_numreg = re.compile( numregister, re.M )

sysframe = r'\[\*SYSTEM\*\]' + r'(?P<FrameID>\$[a-zA-Z]+\w*)' + r'(.*)'
posreg = r'\[\*POSREG\*\]' + r'(?P<FrameID>\$[a-zA-Z]+\w*)' + r'(.*)'
numreg = r'\[\*NUMREG\*\]' + r'(?P<FrameID>\$[a-zA-Z]+\w*)' + r'(.*)'

app = getApplication()

def cleanUp():
  setNextState(None)

#-------------------------------------------------------------------------------
def OnAbort():
  cleanUp()

#-------------------------------------------------------------------------------
def OnStop():
  cleanUp()

#-------------------------------------------------------------------------------
def getActiveProgram():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

  return routine.Program

def OnStart():
  
  program = getActiveProgram()
  if not program:
    app.messageBox("No program selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return False
  #endif

  opencmd = app.findCommand("dialogOpen")
  uri = ""
  ok = True
  fileFilter = "FANUC Robot Program files (*.va)|*.va"
  opencmd.execute(uri,ok,fileFilter)
  if not opencmd.Param_2:
    print "No file selected for uploading, aborting command"
    return False
  #endif
  uri = opencmd.Param_1
  filename = uri[8:len(uri)]
  try:
    infile = open(filename,"r")
  except:
    print "Cannot open file \'%s\' for reading" % filename
    return
  #endtry

  filestring = infile.read()
  infile.close()

  executor = program.Executor
  comp = executor.Component
  robCnt = executor.Controller

  blocks = {}
  lineBuffer = ''
  currentSection = ''
  for line in filestring.split('\n'):

    SYSFRAME = re.match( sysframe + end, line)
    if SYSFRAME:
      if currentSection: blocks[currentSection] = lineBuffer
      lineBuffer = ''
      currentSection = SYSFRAME.group(1)
      continue
    #endif

    POSREG = re.match( posreg + end, line)
    if POSREG:
      if currentSection: blocks[currentSection] = lineBuffer
      lineBuffer = ''
      currentSection = POSREG.group(1)
      continue
    #endif

    NUMREG = re.match( numreg + end, line)
    if NUMREG:
      if currentSection: blocks[currentSection] = lineBuffer
      lineBuffer = ''
      currentSection = NUMREG.group(1)
      continue
    #endif

    lineBuffer += line + '\n'
  #endfor
  if currentSection: blocks[currentSection] = lineBuffer

  numregString = blocks.get('$NUMREG', '' )
  if numregString:
    numregs = re_numreg.finditer(numregString)
    for n in numregs:
      val = eval(n.group(2))
      comment = n.group(3)
      if val or comment:
        nindex = eval(n.group(1))
        prop = comp.createProperty( VC_REAL, 'Registers::R[%i]' % nindex )
        prop.Value = val
        prop.Group = nindex
      #endif
    #endfor
  #endif

  baseString = blocks.get('$MNUFRAME', '' )
  if baseString:
    bases = re_frame.finditer(baseString)
    for b in bases:
      bindex =eval(b.group(2))
      xx = eval(b.group('x'))
      yy = eval(b.group('y'))
      zz = eval(b.group('z'))
      ww = eval(b.group('w'))
      pp = eval(b.group('p'))
      rr = eval(b.group('r'))

      m = vcMatrix.new() 
      m.translateAbs( xx, yy, zz )
      m.setWPR( ww, pp, rr )

      if bindex > len(robCnt.Bases):
        base = robCnt.addBase()
        base.Name = 'Uframe%i' % bindex
      #endif

      robCnt.Bases[bindex-1].PositionMatrix = m
    #endfor
  #endif

  toolString = blocks.get('$MNUTOOL', '' )
  if toolString:
    tools = re_frame.finditer(toolString)
    for t in tools:
      tindex =eval(t.group(2))
      xx = eval(t.group('x'))
      yy = eval(t.group('y'))
      zz = eval(t.group('z'))
      ww = eval(t.group('w'))
      pp = eval(t.group('p'))
      rr = eval(t.group('r'))

      m = vcMatrix.new() 
      m.translateAbs( xx, yy, zz )
      m.setWPR( ww, pp, rr )

      if tindex > len(robCnt.Tools):
        tool = robCnt.addTool()
        tool.Name = 'Utool%i' % tindex
      #endif

      robCnt.Tools[tindex-1].PositionMatrix = m
    #endfor
  #endif
  
  posregString = blocks.get('$POSREG', '' )
  if posregString:
    routine = program.findRoutine( 'PositionRegister' )
    if routine:
      routine.clear()
    else:
      routine = program.addRoutine( 'PositionRegister' )
    
    posregs = re_posreg.finditer(posregString)
    for p in posregs:
      pindex = eval(p.group(2))
      comment = p.group(3)

      xx = eval(p.group('x'))
      yy = eval(p.group('y'))
      zz = eval(p.group('z'))
      ww = eval(p.group('w'))
      pp = eval(p.group('p'))
      rr = eval(p.group('r'))
      cfg = p.group('fut')
      if cfg == 'F': cfg = 'F U T'
      if cfg == 'N': cfg = 'N U T'
      t1 = eval(p.group('t1'))
      t2 = eval(p.group('t2'))
      t3 = eval(p.group('t3'))

      m = vcMatrix.new() 
      m.translateAbs( xx, yy, zz )
      m.setWPR( ww, pp, rr )

      stmt = routine.addStatement( VC_STATEMENT_PTPMOTION )
      posFrame = stmt.Positions[0]
      posFrame.PositionInReference = m
      posFrame.Configuration = cfg
      try:
        posFrame.JointTurns4 = t1
        posFrame.JointTurns5 = t2
        posFrame.JointTurns6 = t3
      except:
        pass
      if comment:
        posFrame.Name = comment
      else:
        posFrame.Name = routine.Name + '_%i' % pindex
      #endif
      stmt.createProperty(VC_INTEGER, 'INDEX' )
      stmt.INDEX = pindex
    #endfor
  #endif
  
  return True

#-------------------------------------------------------------------------------

addState(None)
