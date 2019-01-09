from vcCommand import *
import re
import os.path
import vcMatrix
import vcVector


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

pnum = r'P'+obracket+'(?P<pnum>'+integer+')'+ '(?P<comment>(?:\s*:.*)?)' + cbracket
uf = r'UF'+colon+'(?P<uf>'+integer+')'
ut = r'UT'+colon+'(?P<ut>'+integer+')'

fut = r'(?P<fut>[FN]\s*[UD]*\s*[TB]*)'
t1 = r'(?P<t1>'+integer+')'
t2 = r'(?P<t2>'+integer+')'
t3 = r'(?P<t3>'+integer+')'
cfg = r'CONFIG' + colon + '\''+ fut + comma + t1 + comma + t2 + '(?:'+comma + t3 +')?\s*\''

x = r'X' + eq + r'(?P<x>'+real+')' + sp + 'mm'
y = r'Y' + eq + r'(?P<y>'+real+')' + sp + 'mm'
z = r'Z' + eq + r'(?P<z>'+real+')' + sp + 'mm'
w = r'W' + eq + r'(?P<w>'+real+')' + sp + 'deg'
p = r'P' + eq + r'(?P<p>'+real+')' + sp + 'deg'
r = r'R' + eq + r'(?P<r>'+real+')' + sp + 'deg'

j1 = r'J1' + eq + r'(?P<j1>'+real+')' + sp + 'deg'
j2 = r'J2' + eq + r'(?P<j2>'+real+')' + sp + 'deg'
j3 = r'J3' + eq + r'(?P<j3>'+real+')' + sp + 'deg'
j4 = r'J4' + eq + r'(?P<j4>'+real+')' + sp + 'deg'
j5 = r'J5' + eq + r'(?P<j5>'+real+')' + sp + 'deg'
j6 = r'J6' + eq + r'(?P<j6>'+real+')' + sp + 'deg'

coord = uf + comma + ut + comma + cfg + comma + x + comma + y + comma + z + comma + w + comma + p + comma + r 
pos = pnum + obrace + 'GP\d+' + colon + coord + r'(?P<groups>[^}]*)' + cbrace + semicolon
re_pos = re.compile( pos, re.M )

jcoords = uf + comma + ut + comma + j1 + comma + j2 + comma + j3 + comma + j4 + comma + j5 + comma + j6 
jpos = pnum + obrace + 'GP\d+' + colon + jcoords + r'(?P<groups>[^}]*)' + cbrace + semicolon
re_jpos = re.compile( jpos, re.M )

group = r'GP(?P<grnum>\d+)' + colon + uf + comma + ut + comma + '(?P<jcoords>.*)'
re_group = re.compile( group, re.M | re.DOTALL)

jcoord = r'J(?P<jnum>\d+)' + eq + r'(?P<jval>'+real+')' + sp + r'[deg|mm]'
re_jcoord = re.compile( jcoord, re.M )

ecoord = r'E(?P<jnum>\d+)' + eq + r'(?P<jval>'+real+')' + sp + r'[deg|mm]'
re_ecoord = re.compile( ecoord, re.M )

lnum = r'\s*(?P<lnum>'+integer+')' + colon 

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

def addScript(comp):
  script = comp.findBehaviour( 'LSExecutor' )
  if not script:
    script = comp.createBehaviour( VC_SCRIPT, 'LSExecutor' )
  if script.Script != lsScript():
    script.Script = lsScript()
  return

def OnStart():
  global targetmovenameregex,robtargetregex,floatregex,toolnameregex,wobjregex,speedregex,filestring,firstwarning,elseregex,ifcondregex,movejregex,moveLregex,ifregex,lineSkip,i,lineCount
  lineCount = [0,0,0,0,0,0,0,0]
  i=1
  program = getActiveProgram()
  if not program:
    app.messageBox("No program selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif
  
  executor = program.Executor
  comp = executor.Component

  modbutton = comp.getProperty( 'MOD PROGRAM' )
  if not modbutton:
    modbutton = comp.createProperty( VC_BUTTON, 'MOD PROGRAM' )
    modbutton.Group = 2

  mainRoutine = comp.getProperty( 'MainRoutine' )
  if not mainRoutine:
    mainRoutine = comp.createProperty( VC_STRING, 'MainRoutine', VC_PROPERTY_STEP )
    mainRoutine.Group = 5

  routines = mainRoutine.StepValues
  if 'PNS' not in routines:
    routines.insert(0, 'PNS')
    mainRoutine.StepValues = routines

  if 'RSL' not in routines:
    routines.insert(0, 'RSL')
    mainRoutine.StepValues = routines
  
  progList = comp.getProperty( 'ProgramList' )
  if not progList:
    progList = comp.createProperty( VC_STRING, 'ProgramList')
    progList.Group = 6

  pnsSignal = comp.findBehaviour('PNSsignal')
  if not pnsSignal:
    pnsSignal = comp.createBehaviour( VC_STRINGSIGNAL, 'PNSsignal' )

  completeSignal = comp.getProperty('CompleteSignal')
  if not completeSignal:
    completeSignal = comp.createProperty( VC_INTEGER, 'CompleteSignal' )
    completeSignal.Value = 211
    completeSignal.Group = 7

  if getCommand().Name == 'ABBUpdate':
    addScript( comp )
    return
  #endif

  opencmd = app.findCommand("dialogOpen")
  uri = ""
  ok = True
  fileFilter = "ABB Robot Program files (*.mod)|*.mod"
  opencmd.execute(uri,ok,fileFilter)
  if not opencmd.Param_2:
    print "No file selected for uploading, aborting command"
    return
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

  robCnt = executor.Controller
  trg = robCnt.createTarget()

  robAxes = 0
  baseAxes = 0
  posAxes = 0

  pnpbase = comp.getBehaviour("RobotPositioner")
  if pnpbase:
    baseCmp = pnpbase.ConnectedComponent
    if baseCmp:
      baseCnt = baseCmp.findBehavioursByType(VC_SERVOCONTROLLER )[0]
      if baseCnt:
        baseAxes = baseCnt.JointCount
      #endif
    #endif
  #endif

  pnppos = comp.getBehaviour("WorkpiecePositionersJoints")
  if pnppos:
    posCmp = pnppos.ConnectedComponent
    if posCmp:
      posCnt = posCmp.findBehavioursByType(VC_SERVOCONTROLLER )[0]
      if posCnt:
        posAxes = posCnt.JointCount
      #endif
    #endif
  #endif

  robAxes = robCnt.JointCount - baseAxes - posAxes
  
  #robtarget regular expression
  robtargetregex="\[ *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *\]"
  # floating point regular expression
  floatregex = "[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"
  # workobject regular expression
  wobjregex = r"\\WObj:=(?P<workobject>[a-zA-Z0-9]+)"
  # tool definition regular expression
  toolregex = r", *(?P<tooln>[a-zA-Z0-9_]+)"  
  # get name of point
  targetnameregex= r"(?P<name>[a-zA-Z0-9_]+):="#
  #name in move
  targetmovenameregex=r" (?P<point>[a-zA-Z0-9_]+),"#
  #toolname
  toolnameregex = r"(?P<toolnam>[a-zA-Z0-9_]+)\\WObj"  
  #get name of wobj
  movejregex = "MoveJ "
  moveLregex = "MoveL "
  speedregex = r",v(?P<speed>[a-zA-Z0-9_]+)," 
  ifregex = "IF "
  elseregex = "ELSE"

  
  instFlag = False
  instructions = ''
  #myline=infile.readline()
  firstwarning=True

  for line in filestring.split('\n'):
    # lineCount = [0,0,0,0,0,0,0,0]
    # i=0
  
    MODULE = re.match(r'MODULE' + sp + galphanum + '(?:\s+Macro)?'+end,line)
    if MODULE:
      progname = MODULE.group(1)
      program.deleteRoutine( progname )
      routine = program.findRoutine( progname )
      if not routine:
        routine = program.addRoutine( progname )
      else:
        routine.clear()
      ###continue
    #endif
    scope=None
    if lineCount[0]!=0:
	  lineCount[0]-=1
	  continue
    print "lineCount[0]: %s" % (lineCount[0])  
    # if lineCount[1]!=0:
      # lineCount[1]-=1
      # continue

    createStatement(routine,line,filestring,robCnt,scope,program)
  

  return True

#read in pos
def readPos(s,line,robCnt):  
	  # find name of position
  global targetmovenameregex
  posname = re.search(targetmovenameregex,line)
  targetname= posname.group('point')
  #print "name: %s" % targetname
  for lineRT in filestring.split('\n'):
    #find position	  
    rtmatch=re.findall(targetname+":="+robtargetregex, lineRT)
    #print "rtmatch: %s" % rtmatch
    if rtmatch:
      positionmatch=re.findall(robtargetregex, lineRT)
      #print "positionmatch: %s" % positionmatch
      for mymatch in positionmatch:    
        match=re.findall(floatregex, mymatch)
        #print "match: %s" % match
                #   robtarget has 17 floating point values
        if len(match)==17:
          m = vcMatrix.new()
			
          m.P = vcVector.new(float(match[0]),float(match[1]),float(match[2]))
          m.setQuaternion(float(match[4]),float(match[5]),float(match[6]),float(match[3]))
          t = robCnt.createTarget(m)
          if s.Type==VC_STATEMENT_PTPMOTION:
            #t.CartesianSpeed=readSpeed(line)
            s.JointSpeed=float(readSpeed(line))/6000.00
            help= float(readSpeed(line))/6000.00
            print "s.JointSpeed %f" %help
            #s.MaxSpeed=readSpeed(line)
          elif s.Type==VC_STATEMENT_LINMOTION:
		    s.MaxSpeed=readSpeed(line)
          print "t.CartesianSpeed=: %s" % t.CartesianSpeed
              #use correct position
          posFrame= s.Positions[0]
          posFrame.PositionInReference=m  


def defineTool(s,line,robCnt):
  global toolnameregex,firstwarning
  toolname= re.search(toolnameregex,line)
  rtoolname = toolname.group('toolnam')	  
  #print "toolname: %s" % rtoolname
  if rtoolname:
	# for lineRT in filestring.split('\n'):
	# rtmatch=re.findall(rtoolname+":=", lineRT)
    #set base for statement only if the base is found from controller
    for b in robCnt.Tools:
      if b.Name == rtoolname:
        s.Tool=rtoolname
      if s.Tool!=rtoolname and firstwarning:
        firstwarning=False
        app.messageBox("Undefined tool \'%s\' in robot program" % rtoolname,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)		

def defineWObj(s,line,robCnt):
  global wobjregex,firstwarning
  wobjdef = re.search(wobjregex,line)
  #print "line: %s" % line
  #print "wobjdef: %s" % wobjdef
  if wobjdef:
    wobjname = wobjdef.group('workobject')

    if wobjname:
        #set base for statement only if the base is found from controller
      for b in robCnt.Bases:
        if b.Name == wobjname:
          s.Base=wobjname
        if s.Base!=wobjname and firstwarning:
          firstwarning=False
          app.messageBox("Undefined workobject \'%s\' in robot program" % wobjname,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)

def readSpeed(line):
  global speedregex	
  speeddef= re.search(speedregex,line)
  speed = speeddef.group('speed')
  print "speed: %s" % speed
  if speed == 'max':     return 6000
  elif speed == "4000":  return 4000
  elif speed == "3000":  return 3000
  elif speed == "2500":  return 2500
  elif speed == "2000":  return 2000
  elif speed == "1500":  return 1500
  elif speed == "1000":  return 1000
  elif speed == "800":    return 800
  elif speed == "600":    return 600
  elif speed == "500":    return 500
  elif speed == "400":    return 400
  elif speed == "300":    return 300
  elif speed == "200":    return 200
  elif speed == "150":    return 150
  elif speed == "100":    return 100
  elif speed == "80":     return 80
  elif speed == "60":     return 60
  elif speed == "50":     return 50
  elif speed == "40":     return 40
  elif speed == "30":     return 30
  elif speed == "20":     return 20
  elif speed == "10":     return 10
  else:                  return 5 

  
def createPTP(line,robCnt,routine,scope):
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_PTPMOTION)
  else:
    s = routine.addStatement(VC_STATEMENT_PTPMOTION)
  readPos(s,line,robCnt)
  defineTool(s,line,robCnt)  
  defineWObj(s,line,robCnt)
  #get accuracy
  return s
def createLin(line,robCnt,routine,scope):
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_LINMOTION)
  else:
    s = routine.addStatement(VC_STATEMENT_LINMOTION)
  #s = routine.addStatement(VC_STATEMENT_LINMOTION)
  readPos(s,line,robCnt)
  defineTool(s,line,robCnt)  
  defineWObj(s,line,robCnt)
  return s

		
		# #get accuracy
def createIF(routine,line,filestring,robCnt,scope,program):
  ifcondregex ="IF (?P<cond>[a-zA-Z0-9_]+)(?P<equal>[^a-zA-Z0-9_]+)(?P<value>[a-zA-Z0-9_]+) THEN"
  inif=0
  inelse=0
  conddef=re.search(ifcondregex,line)
  equal=conddef.group('equal')
  #notdef=conddef.group('not')
  print "equal: %s" % equal
  if conddef.group('equal')== "=":
    equal = "=="
  # elif notdef:
    # equal = "!="
  global lineCount,lineSkip,i
  endifregex="ENDIF"
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_IF)
  else:
    s = routine.addStatement(VC_STATEMENT_IF)
  conddef=re.search(ifcondregex,line)
  cond=conddef.group('cond')+equal+conddef.group('value')
  print "cond: %s" % cond  
  s.Condition=cond
  for lineRT in filestring.split('\n'):
    print "i: %s" % (i) 
    #lineCount+=1
    #print "lineRT: %s" % lineRT
    if lineCount[i]!=0:
      lineCount[i]-=1
      print "lineCount[i]: %s" % (lineCount[i])
      continue	  
    if re.findall("ENDIF",lineRT):
	  print "ENDIF"
	  inif=0
	  inelse=0
	  #lineCount[i-1]+=1
	  print "lineCount[i-1]: %s" % (lineCount[i-1])
	  break

    if re.findall("ELSE",lineRT):
      print "elsescope"
      inif=0
      inelse=1
      lineCount[i-1]+=1
      print "lineCount[i-1]: %s" % (lineCount[i-1])
      continue	  
    
    if inelse==1:
      selse=createStatement(routine,lineRT,filestring,robCnt,s.ElseScope,program)
      print "selse: %s" % (selse)
      s.ElseScope.Statements.append(selse)
      print "lineCount[i-1]: %s" % (lineCount[i-1]) 
      lineCount[i-1]+=1

    if inif==1:
      print "createStatement"
      print "lineRT+1: %s" % (lineRT)
      sthen=createStatement(routine,lineRT,filestring,robCnt,s.ThenScope,program)
      print "sthen+1: %s" % (sthen)
      s.ThenScope.Statements.append(sthen)
      lineCount[i-1]+=1
      print "lineCount[i-1]: %s" % (lineCount[i-1])     	  
	  
    if re.findall(line,lineRT):
      inif=1
      print "next is thenscope "
      print "lineCount[i-1]: %s" % (lineCount[i-1])
      continue
  lineCount[i]=lineCount[i-1]
  lineCount[0]+=lineCount[i-1]
  print "lineCount[i-1]: %s" % (lineCount[i-1])
  print "lineCount[i]: %s" % (lineCount[i])#   
    #else:
	  #print "move"
  return s

def createWhile(routine,line,filestring,robCnt,scope,program):
  whileregex= r"WHILE (?P<cond>[a-zA-Z0-9_]+)="
  conddef= re.search(whileregex,line)
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_WHILE)
  else:
    s = routine.addStatement(VC_STATEMENT_WHILE)
  cond=conddef.group('cond')
  inWhile=0
  print "cond %s" %cond
  s.Condition=cond
  for lineRT in filestring.split('\n'):
    print "i: %s" % (i) 
    #lineCount+=1
    #print "lineRT: %s" % lineRT
    if lineCount[i]!=0:
      lineCount[i]-=1
      print "lineCount[i]: %s" % (lineCount[i])
      continue	  
    if re.findall("ENDWHILE",lineRT):
	  print "ENDWHILE"
	  inWhile=0
	  #lineCount[i-1]+=1
	  print "lineCount[i-1]: %s" % (lineCount[i-1])
	  break

    if inWhile==1:
      print "createStatement"
      print "lineRT+1: %s" % (lineRT)
      sthen=createStatement(routine,lineRT,filestring,robCnt,s.Scope,program)
      print "sthen+1: %s" % (sthen)
      s.Scope.Statements.append(sthen)
      lineCount[i-1]+=1
      print "lineCount[i-1]: %s" % (lineCount[i-1])     	  
	  
    if re.findall(line,lineRT):
      inWhile=1
      print "next is whilescope "
      print "lineCount[i-1]: %s" % (lineCount[i-1])
      continue
  lineCount[i]=lineCount[i-1]
  lineCount[0]+=lineCount[i-1]
  

  
def createComment(routine,line,filestring,robCnt,scope):
  commentregex=r"!(?P<comment>[a-zA-Z0-9_]+)"
  commentString=re.search(commentregex,line)
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_COMMENT)
  else:
    s = routine.addStatement(VC_STATEMENT_COMMENT)
  s.Comment=commentString.group('comment')
  return s
  
def createBreak(scope):

  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_BREAK)
  else:
    s = routine.addStatement(VC_STATEMENT_BREAK)
  return s	

def createReturn(scope):

  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_RETURN)
  else:
    s = routine.addStatement(VC_STATEMENT_RETURN)
  return s	  
  
def createCall(routine,line,filestring,robCnt,scope,callDef,program):  

  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_CALL)
  else:
    s = routine.addStatement(VC_STATEMENT_CALL)
  
  print "s: %s" %s
  
  callRoutine = program.findRoutine( callDef.group('routine') )
  if not callRoutine:
    callRoutine = program.addRoutine( callDef.group('routine') )  
  #callRoutine.Name=callDef.group('routine')
  print "callRoutine: %s" %callRoutine
  s.Routine=callRoutine
  return s
  
def createSetBin(routine,line,filestring,robCnt,scope,program):
  SetBinregex = "SetDO do(?P<port>[a-zA-Z0-9]+),(?P<value>[a-zA-Z0-9]+);"
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_SETBIN)
  else:
    s = routine.addStatement(VC_STATEMENT_SETBIN)
  PortValue=re.search(SetBinregex,line)
  
  port=PortValue.group('port')
  value=PortValue.group('value')
  
  print "value: %s" %value
  print "port: %s" %port
  
  s.OutputPort=int(port)
  s.OutputValue=int(value)
  return s	
  
def createWaitBin(routine,line,filestring,robCnt,scope,program):
  WaitBinregex = "WaitDI di(?P<port>[a-zA-Z0-9_]+),(?P<value>[a-zA-Z0-9]+);"
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_WAITBIN)
  else:
    s = routine.addStatement(VC_STATEMENT_WAITBIN)
  PortValue=re.search(WaitBinregex,line)
  
  port=PortValue.group('port')
  value=PortValue.group('value')
  
  print "value: %s" %value
  print "port: %s" %port
  
  s.InputPort=int(port)
  s.InputValue=int(value)
  return s	  
 
def createSetProperty(routine,line,filestring,robCnt,scope,program):
  SetPropregex = "(?P<TargetProperty>[a-zA-Z0-9_]+) := (?P<value>[a-zA-Z0-9]+);"
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_SETPROPERTY)
  else:
    s = routine.addStatement(VC_STATEMENT_SETPROPERTY)
 
  PropertyValue=re.search(SetPropregex,line)
  if not PropertyValue:
    SetPropregex = "(?P<TargetProperty>[a-zA-Z0-9_]+):=(?P<value>[a-zA-Z0-9]+);"
    PropertyValue=re.search(SetPropregex,line)
  s.TargetProperty=PropertyValue.group('TargetProperty')
  s.ValueExpression=PropertyValue.group('value')
  
  
def createDelay(routine,line,filestring,robCnt,scope,program):
  Delayregex="WaitTime (?P<time>[a-zA-Z0-9]+);"
  if scope:
    if(scope.ParentStatement.Type==VC_STATEMENT_IF or scope.ParentStatement.Type==VC_STATEMENT_WHILE):
      s= scope.addStatement(VC_STATEMENT_DELAY)
  else:
    s = routine.addStatement(VC_STATEMENT_DELAY)
  TimeValue=re.search(Delayregex,line)
  s.Delay=int(TimeValue.group('time'))
 
def createStatement(routine,line,filestring,robCnt,scope,program):
  global movejregex,moveLregex,ifregex,i
  i+=1
  whileloopregex = " WHILE "
  callregex="(?P<routine>[a-zA-Z0-9_]+);"
  variableregex="(?P<a>[a-zA-Z0-9_]+):=(?P<b>[a-zA-Z0-9]+);"
  moveJdef=re.findall(movejregex,line)	
  print "line: %s" % line
  if moveJdef:
    s=createPTP(line,robCnt,routine,scope)
    i-=1
    return s	
  moveLdef=re.findall(moveLregex,line)
  if moveLdef:
    s=createLin(line,robCnt,routine,scope)
    i-=1
    return s	
  #ifdef= re.findall(ifregex,line)
  if re.findall(" IF",line):
    s=createIF(routine,line,filestring,robCnt,scope,program)
    i-=1	
    return s
  if re.findall("!",line):
    s=createComment(routine,line,filestring,robCnt,scope)
    i-=1
    return s
  if re.findall("BREAK;",line):
    s=createBreak(scope)
    i-=1
    return s
  if re.findall("RETURN;",line):
    s=createReturn(scope)
    i-=1
    return s	
  if re.findall(" WHILE ",line):
    s=createWhile(routine,line,filestring,robCnt,scope,program)
    i-=1
    return s
  if re.findall("SetDO ",line):
    s=createSetBin(routine,line,filestring,robCnt,scope,program)
    i-=1
    return s
  if re.findall("WaitDI ",line):
    s=createWaitBin(routine,line,filestring,robCnt,scope,program)
    i-=1
    return s
  if re.findall("WaitTime",line):
    s=createDelay(routine,line,filestring,robCnt,scope,program)
    i-=1
    return s
  variableDef=	re.search(callregex,line)
  if variableDef:
    s=createSetProperty(routine,line,filestring,robCnt,scope,program)
    i-=1
    return s
  callDef=	re.search(callregex,line)
  if callDef:
    s=createCall(routine,line,filestring,robCnt,scope,callDef,program)
    i-=1
    return s
	
  i-=1
    
  
  		
#-------------------------------------------------------------------------------

def lsScript():
  return r"""### VERSION 4.0
from vcScript import *
from math import *
import vcMatrix
import re

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
galphanum = r'(?P<name>'+alphanum+')'
compare = r'\s*(=|<>|>|<|<==|>==)\s*'
nl = r' *\r?[\n\0]'
sl = r'\A|\n'
end = r'\s*$'
cnt = '(\s+(?P<cnt>'+alphanum+'))?'
process = '(\s*:\s*(?P<process>.*))?'
units = '(?P<units>(mm/sec|inch/min))'
unitconv = {'mm/sec':1.0,'inch/min':(25.4/60)}
junits = '(?P<units>(%|msec))'

comment = '(?:\s*:.*)?'
fnum = r'F'+obracket+'(?P<fnum>'+integer+')'+ comment + cbracket
dnum = r'D'+obracket+'(?P<dnum>'+integer+')'+ comment + cbracket
rnum = r'R'+obracket+'(?P<rnum>'+integer+')'+ comment + cbracket
pnum = r'P'+obracket+'(?P<pnum>'+integer+')'+ comment + cbracket
pnum2 = r'P'+obracket+'(?P<pnum2>'+integer+')'+ comment + cbracket
prnum = r'PR'+obracket+'(?P<prnum>'+integer+')'+ '(?:\s*:[ \w\"]*)?' + cbracket
label = r'LBL'+obracket+'(?P<label>'+integer+')'+ '(?:\s*:[ \w\"]*)?' +cbracket
lnum = r'\s*(?P<lnum>'+integer+')' + colon

app = getApplication()
comp = getComponent()
executor = comp.findBehaviour('Executor')
pnsSignal = comp.findBehaviour('PNSsignal')

def signalPNS( port, value ):
  pns = app.findComponent( 'PNS' )
  if pns:
    pnsInSignal = pns.findBehaviour('InSignal')
    pnsInSignal.signal('%s,%d,%d' %(comp.Name,port,value) )

def displayIO( io, port, value ):
  digitalIO = 'DigitalIO::%s[%s]' % (io,port)
  prop = comp.getProperty(digitalIO)
  if not prop:
    prop = comp.createProperty(VC_BOOLEAN, digitalIO)
    prop.Group = port
  #endif
  prop.Value = value

def setIO( prop ):
  if comp.IO == 'DI':
    DI[comp.Port] = comp.Value
  elif comp.IO == 'DO':
    DO[comp.Port] = comp.Value
  elif comp.IO == 'RI':
    RI[comp.Port] = comp.Value
  elif comp.IO == 'RO':
    RO[comp.Port] = comp.Value

  displayIO( comp.IO, comp.Port, comp.Value )

def onSignalTrigger(sigMap, port, value):
  if sigMap == executor.DigitalInputSignals:
    if port < 11:
      RI[port] = bool(value)
      displayIO( 'RI', port, value )
    else:
      DI[port] = bool(value)
      displayIO( 'DI', port, value )
    #endif
  else:
    if port < 11:
      RO[port] = bool(value)
      displayIO( 'RO', port, value )
    else:
      DO[port] = bool(value)
      displayIO( 'DO', port, value )
    #endif
  #endif

mainRoutine = comp.getProperty('MainRoutine')
def onMainRoutine( prop ):
  if mainRoutine.Value == 'RSL':
    executor.IsEnabled = True
  else:
    executor.IsEnabled = False
  #endif
mainRoutine.OnChanged = onMainRoutine

def OnReset():
  pass
  
def OnSignal( signal ):
  global pnsRoutine

  if signal == pnsSignal and pnsSignal.Value:
    pnsRoutine = pnsSignal.Value

def OnRun():
  global robotNote
  global pnsRoutine
  global utool_num, uframe_num
  global positions, R, DI, DO, RI, RO, F, D, UserMessages
  global controller, trg
  global ON, OFF, LPOS

  if comp.MainRoutine == 'RSL':
    executor.IsEnabled = True
    return
  #endif

  executor.IsEnabled = False
  executor.DigitalInputSignals.OnSignalTrigger = onSignalTrigger
  executor.DigitalOutputSignals.OnSignalTrigger = onSignalTrigger

  controller = executor.Controller
  controller.clearTargets()

  if not comp.getProperty( 'MaxJointSpeeds' ):
    prop = comp.createProperty( VC_STRING, 'MaxJointSpeeds' )
    prop.IsVisible = False
    prop.Value = '450,380,520,550,545,1000,4000,720'
  #endif

  try:
    jspeeds = comp.MaxJointSpeeds.split(',')
    if jspeeds:
      for i,j in enumerate(controller.Joints):
        j.MaxSpeed = float(jspeeds[i])
        j.MaxAcceleration = j.MaxDeceleration = 4*j.MaxSpeed
      #endfor
      controller.MaxCartesianSpeed = float(jspeeds[6])
      controller.MaxCartesianAccel = 4*controller.MaxCartesianSpeed 
      controller.MaxAngularSpeed = float(jspeeds[7])
      controller.MaxAngularAccel = 4*controller.MaxAngularSpeed 
    #endif
  except:
    pass

  trg = controller.createTarget()
  ''' 
  for routineName in comp.getProperty( 'MainRoutine' ).StepValues:
    note = comp.findBehaviour(routineName)
    if not note: continue
    text = ''
    lineNumber = 0
    header = True
    for line in note.Note.split('\n'):
      if header:
        text += line + '\n'
        if re.match(r'/MN' + end, line): header = False
        continue
      #endif
      if len(line)<2: continue
      lineNumber += 1
      LNUM = re.match(lnum + '(.*)' + semicolon + end, line)
      if LNUM:
        line = '%4i%s\n' % (lineNumber, line[line.index(':'):])
      else:
        line = '%4i:  %s\n' % (lineNumber,line)
      #endif
      text += line
    #endfor
    note.Note = text
  #endfor
  ''' 
  if not comp.getProperty( 'SkipWaits' ):
    prop = comp.createProperty( VC_BOOLEAN, 'SkipWaits' )
    prop.Group = 10
  #endif
  
  if not comp.getProperty( 'OverrideSpeed' ):
    prop = comp.createProperty( VC_REAL, 'OverrideSpeed', VC_PROPERTY_LIMIT )
    prop.Group = 11
    prop.Quantity = 'Percentage'
    prop.MinValue = .01
    prop.MaxValue = 1.0
    prop.Value = 1.0
  #endif
  
  if not comp.getProperty( 'CurrentRoutine' ):
    prop = comp.createProperty( VC_STRING, 'CurrentRoutine' )
    prop.Group = 99
  #endif
  if not comp.getProperty( 'PrevLine2' ):
    prop = comp.createProperty( VC_STRING, 'PrevLine2' )
    prop.Group = 100
  #endif
  if not comp.getProperty( 'PrevLine1' ):
    prop = comp.createProperty( VC_STRING, 'PrevLine1' )
    prop.Group = 101
  #endif
  if not comp.getProperty( 'CurrentLine' ):
    prop = comp.createProperty( VC_STRING, 'CurrentLine' )
    prop.Group = 102
  #endif
  if not comp.getProperty( 'Step' ):
    prop = comp.createProperty( VC_BOOLEAN, 'Step' )
    prop.Group = 103
  #endif
  if not comp.getProperty( 'BreakAtLine' ):
    prop = comp.createProperty( VC_INTEGER, 'BreakAtLine' )
    prop.Group = 104
  #endif
  if not comp.getProperty( 'StartLine' ):
    prop = comp.createProperty( VC_INTEGER, 'StartLine' )
    prop.Group = 105
  #endif
  if not comp.getProperty( 'SelectedLine' ):
    prop = comp.createProperty( VC_INTEGER, 'SelectedLine' )
    prop.IsVisible = False
    prop.Group = 106
  #endif
  
  iobutton = comp.getProperty( 'SET IO' )
  if not iobutton:
    iobutton = comp.createProperty( VC_BUTTON, 'SET IO' )
    iobutton.Group = 200
  #endif
  iobutton.OnChanged = setIO

  if not comp.getProperty( 'IO' ):
    prop = comp.createProperty( VC_STRING, 'IO', VC_PROPERTY_STEP )
    prop.Group = 201
    prop.StepValues = ['DI','DO','RI','RO']
    prop.Value = 'DI'
  #endif
  
  prop = comp.getProperty( 'Port' )
  if not prop:
    prop = comp.createProperty( VC_INTEGER, 'Port', VC_PROPERTY_LIMIT )
    prop.Group = 202
    prop.MinValue = 0
  #endif
  prop.MaxValue = executor.DigitalInputSignals.PortCount - 1

  if not comp.getProperty( 'Value' ):
    prop = comp.createProperty( VC_BOOLEAN, 'Value' )
    prop.Group = 203
  #endif
  
  if not comp.getProperty( 'StatementExecutionDelay' ):
    prop = comp.createProperty( VC_REAL, 'StatementExecutionDelay', VC_PROPERTY_LIMIT )
    prop.Group = 300
    prop.IsVisible = False
    prop.Quantity = 'Time'
    prop.Magnitude = 0.001
    prop.MinValue = 0.0
    prop.MaxValue = 1.0
    prop.Value = 0.001 
  #endif
  
  robotNote = comp.findBehaviour( 'RobotProgram' )
  if not robotNote:
    robotNote = comp.createBehaviour( VC_NOTE, 'RobotProgram' )
  #endif

  comp.CurrentRoutine = ''
  comp.PrevLine2 = ''
  comp.PrevLine1 = ''
  comp.CurrentLine = ''
    
  DI = {}
  DO = {}
  RI = {}
  RO = {}

  for port in range(executor.DigitalInputSignals.PortCount):
    DI[port] = False
    DO[port] = False
    RI[port] = False
    RO[port] = False
  #endfor

  F = {}
  D = {}
  R = {}
  for reg in range( 256 ):
    F[reg] = False
    D[reg] = False
    R[reg] = 0.0
  #endfor
  
  UserMessages = {} 
  for prop in comp.Properties:
    if 'Registers::R' in prop.Name:
      R[int(prop.Name[13:-1])] = prop.Value
    if 'UserMessages::Message' in prop.Name:
      UserMessages[int(prop.Name[22:])] = prop.Value

  positions = {}
  for r in executor.Program.Routines:
    for s in r.Statements:
      if s.Type in [VC_STATEMENT_PTPMOTION, VC_STATEMENT_LINMOTION]:
        if s.getProperty('INDEX'):
          positions[r.Name+'_%i'%s.INDEX] = s
        else:
          positions[s.Name] = s
 
  LPOS = vcMatrix.new()
  
  ON = True
  OFF = False
  utool_num = 0
  uframe_num = 0
  pnsRoutine = None
  while True:
    if comp.MainRoutine == 'PNS':
      condition( lambda: pnsRoutine )
      routineName = pnsRoutine
      pnsRoutine = None
      if not comp.findBehaviour(routineName):
        msg = '%s: PNS Error -- no such routine <%s>:' % (comp.Name, routineName)
        app.messageBox(msg,"Error",VC_MESSAGE_TYPE_ERROR,VC_MESSAGE_BUTTONS_OK)
        continue
      executeRoutine( routineName )
    else:
      executeRoutine( comp.MainRoutine )
    if not executor.IsLooping: break

def setToolBase():
  global utool_num, uframe_num

  if not trg.ToolName and utool_num:
    trg.ToolName = controller.Tools[utool_num-1].Name

  if not trg.BaseName and uframe_num:
    trg.BaseName = controller.Bases[uframe_num-1].Name

  for tnum, tname in enumerate(controller.Tools):
    if tname == trg.ToolName:
      utool_num = tnum + 1
      break

  for bnum, bname in enumerate(controller.Bases):
    if bname == trg.BaseName:
      uframe_num = bnum + 1
      break

def doMove( cnt, motionTime = 0.0 ):
  global flyby
  setToolBase()
  trg.AccuracyMethod = VC_MOTIONTARGET_AM_VELOCITY
  if 'FINE' in cnt:
    trg.AccuracyValue = 0.0
    controller.addTarget(trg)
    if motionTime > 0.0: controller.setMotionTime( motionTime )
    controller.move()
    controller.clearTargets()
    flyby = False
  elif 'CNT' in cnt:
    if trg.MotionType == VC_MOTIONTARGET_MT_JOINT:
      trg.AccuracyValue = eval(re.sub( r'CNT', '', cnt ))/100.*trg.JointSpeedFactor*1000
    else:
      trg.AccuracyValue = eval(re.sub( r'CNT', '', cnt ))/100.*trg.CartesianSpeed
    controller.addTarget(trg)
    flyby = True
  #endif

def executeRoutine( routineName, args = None ):
  global utool_num, uframe_num, flyby, ls
  
  ls = comp.findBehaviour(routineName)
  if not ls: 
    routine = executor.Program.findRoutine(routineName)
    if routine: 
      executor.callRoutine( routine )
    else:
      print 'Subprogram <%s> is not defined, skipping execution' % routineName
    return

  skipPropName = "%s::SkipExecution"%routineName
  skipProp = comp.getProperty( skipPropName )
  if not skipProp:
    skipProp = comp.createProperty(VC_BOOLEAN, skipPropName )
  if skipProp.Value: return

  comp.CurrentRoutine = routineName
  robotNote.Note = ls.Note

  print 'Executing <%s>' % routineName
  
  flyby = False
  labels = {}
  elses = {}
  endifs = {}
  lines = []
  header = True
  fullLine = ''
  headerOffset = 0
  for line in ls.Note.split('\n'):
    if header:
      headerOffset += 1
      if re.match(r'/MN' + end, line): header = False
      continue
    #endif
    if len(line)<2: continue

    fullLine += line
    if ';' not in line: continue
    lines.append(fullLine)
    fullLine = ''
    
    LBL = re.match(lnum + label + semicolon + end, line)
    if LBL:
      labels[LBL.group('label')] = len(lines)-1
      continue
    #endif
    
    ELSE = re.match(lnum + 'ELSE' + semicolon + end, line)
    if ELSE:
      elses[len(lines)-1] = True
      continue
    #endif
    
    ENDIF = re.match(lnum + 'ENDIF' + semicolon + end, line)
    if ENDIF:
      endifs[len(lines)-1] = True
      continue
    #endif
  #endfor

  pc = max(0,comp.StartLine-1)
  numLines = len(lines)
  while -1 < pc < numLines:
    
    line = lines[pc]
    comp.PrevLine2 = comp.PrevLine1
    comp.PrevLine1 = comp.CurrentLine
    comp.CurrentLine = line
    comp.SelectedLine = pc + headerOffset + 1

    if comp.BreakAtLine == pc+1:
      if app.messageBox("Program Break at Line %d. Step Program?" % (pc+1),"Program Break",VC_MESSAGE_TYPE_QUESTION,VC_MESSAGE_BUTTONS_YESNO) == VC_MESSAGE_RESULT_NO:
        comp.Step = False
      else:
        comp.Step = True
      #endif
    elif comp.Step:
      if app.messageBox("Stepped to line %d. Step One Line?" % (pc+1),"Program Step",VC_MESSAGE_TYPE_QUESTION,VC_MESSAGE_BUTTONS_YESNO) == VC_MESSAGE_RESULT_NO:
        comp.Step = False
      #endif
    #endif
    
    STMT = re.match(lnum + r'(.*)' + semicolon + end, line)
    if STMT:
      pc = executeStatement( pc, STMT.group(2), line, routineName, labels, elses, endifs, numLines )
    else:
      pc += 1
    #endif
    
  #endwhile

def doCircularMove( P1, P2, P3, speed, cnt ):
  global flyby
  setToolBase()

  V1 = P1.P - P2.P
  V2 = P2.P - P3.P
  V3 = P3.P - P1.P
  if fabs((V1*V2)/(sqrt(V1*V1*V2*V2))) > 0.9999995:
    print "ERROR: CircularMove: Points are colinear"
    getSimulation().halt()
    return
  #endif

  N = V1 ^ V2
  circleRadius = V1.length()*V2.length()*V3.length()/(2.0*N.length())
  
  alpha = -1.0*(V2*V2)*(V1*V3)
  beta = -1.0*(V3*V3)*(V2*V1)
  gamma = -1.0*(V1*V1)*(V3*V2)

  cP = (alpha*P1.P + beta*P2.P + gamma*P3.P)*(1.0/(2.0*N*N))

  R = P1.P - cP

  xx = P1.P - cP
  xx.normalize()
  N.normalize()

  yy = N ^ xx
  yy.normalize()

  V = P3.P - cP
  V.normalize()
  circleAngle = degrees(atan2( V*yy, V*xx ))
  if circleAngle < 0.0 :
    circleAngle += 360.0
  #endif

  acc = controller.MaxCartesianAccel

  arg = speed*speed/(4.*circleRadius*acc)
  if arg > 1.0:
    arg = 1.0
  #endif

  dAngle = degrees(2.0*asin( arg ))

  i = (int) (circleAngle/dAngle)
  if i < 2:
    i = 2
  #endif

  dAngle = circleAngle/i
  if dAngle < 5.0:
    dAngle = 5.0
  #endif

  trg.MotionType = VC_MOTIONTARGET_MT_LINEAR
  trg.CartesianSpeed = speed
  trg.AccuracyMethod = VC_MOTIONTARGET_AM_VELOCITY
  trg.AccuracyValue = speed

  dC = vcMatrix.new()
  dC.setAxisAngle( N.X, N.Y, N.Z, circleAngle )
  dC.translateAbs( cP.X, cP.Y, cP.Z )

  invP1 = dC*P1
  invP1.invert()
  P12 = invP1*P3

  k12 = P12.getAxisAngle()
  if circleAngle > 180.0 and abs(k12.W) > 0.1:
    k12.W = -(360.0 - k12.W)
  #endif
  if k12.Z < -0.1:
    k12.W *= -1.0
  #endif

  dTheta = k12.W/circleAngle*dAngle
  dP12 = vcMatrix.new()

  C0 = vcMatrix.new(P1)
  C0.translateAbs( -cP.X, -cP.Y, -cP.Z )

  theta = 0.0
  angle = 0.0
  while angle < circleAngle: 
    dC.setAxisAngle( N.X, N.Y, N.Z, angle )
    dP12.setAxisAngle( k12.X, k12.Y, k12.Z, -angle )
    
    C = dC*C0*dP12
 
    trg.Target = C
    controller.addTarget(trg)
    angle += dAngle
    theta += dTheta
  #endwhile
  trg.AccuracyValue = 0.0
  trg.Target = P3
  controller.addTarget(trg)
  if 'FINE' in cnt:
    controller.move()
    controller.clearTargets()
    flyby = False
  else:
    flyby = True

def processStatement( line ):
  
  if not line: return
  
  ARCSTART = re.match('Arc' + sp + 'Start' + sp + '(.*)', line)
  if ARCSTART:
    arc = ARCSTART.group(1)
    executor.DigitalOutputSignals.output( 17, True )
    return True
  #endif
  
  ARCEND = re.match('Arc' + sp + 'End' + sp + '(.*)', line)
  if ARCEND:
    arc = ARCEND.group(1)
    executor.DigitalOutputSignals.output( 17, False )
    return True
  #endif
  
  SEARCHSTART = re.match('Search' + sp + 'Start' + sp + '(.*)', line)
  if SEARCHSTART:
    search = SEARCHSTART.group(1)
    return True
  #endif
  
  SEARCHEND = re.match('Search' + sp + 'End' + sp + '(.*)', line)
  if SEARCHEND:
    search = SEARCHEND.group(1)
    return True
  #endif
  
  return False
  
def executeStatement( pc, line, fullline, routineName, labels, elses, endifs, numLines ):
  global lhs, flyby, stmt, utool_num
  
  pc += 1
  delay( comp.StatementExecutionDelay )

  ENDIF = re.match(r'ENDIF', line)
  if ENDIF:
    return pc
  #endif

  ELSE = re.match(r'ELSE', line)
  if ELSE:
    return pc
  #endif
 
  J = re.match(r'J' + sp + pnum + sp + '(' + rnum + '|' + greal + ')' + junits + cnt + process, line)
  if J:
    stmt = positions[routineName+'_'+J.group('pnum')]
    stmt.writeToTarget( trg )
    trg.MotionType = VC_MOTIONTARGET_MT_JOINT
    if J.group('units') == '%':
      trg.JointSpeedFactor = eval(re.sub( r':.*?\]', ']', J.group(2) ))/100.*comp.OverrideSpeed
      motionTime = 0.0
    else:
      trg.JointSpeedFactor = 1.0
      motionTime = trg.JointSpeedFactor = eval(re.sub( r':.*?\]', ']', J.group(2) ))/1000./comp.OverrideSpeed
    #endif
    doMove( J.group('cnt'), motionTime )
    processStatement( J.group('process') )
    return pc
  #endif

  L = re.match(r'L' + sp + pnum + sp + '('+galphanum+'|((?P<value>(' + rnum + '|' + greal + '))' + units + '))' + cnt + process, line)
  if L:
    stmt = positions[routineName+'_'+L.group('pnum')]
    stmt.writeToTarget( trg )
    trg.MotionType = VC_MOTIONTARGET_MT_LINEAR
    varname = L.group('name')
    if varname:
      varprop = comp.getProperty( 'Variables::%s'%varname )
      if not varprop:
        msg = '%s:%s: Error at line %s: Undefined Speed variable <%s> in move. Creating property on Variables:: tab. Setting speed to 100mm/sec' % (comp.Name, routineName, pc, varname)
        app.messageBox(msg,"Error",VC_MESSAGE_TYPE_ERROR,VC_MESSAGE_BUTTONS_OK)
        varprop = comp.createProperty(VC_REAL, 'Variables::%s'%varname)
        varprop.Quantity = 'Speed'
        varprop.Value = 100.0
      #endif
      trg.CartesianSpeed = varprop.Value*comp.OverrideSpeed
    else:
      trg.CartesianSpeed = eval(re.sub( r':.*?\]', ']', L.group('value') ))*comp.OverrideSpeed*unitconv[L.group('units')]
    doMove( L.group('cnt') )
    processStatement( L.group('process') )
    return pc
  #endif

  C = re.match(r'C' + sp + pnum + colon + pnum2 + sp + '('+galphanum+'|((?P<value>(' + rnum + '|' + greal + '))' + units + '))' + cnt + process, line)
  if C:
    varname = C.group('name')
    if varname:
      varprop = comp.getProperty( 'Variables::%s'%varname )
      if not varprop:
        msg = '%s:%s: Error at line %s: Undefined Speed variable <%s> in move. Creating property on Variables:: tab. Setting speed to 100mm/sec' % (comp.Name, routineName, pc, varname)
        app.messageBox(msg,"Error",VC_MESSAGE_TYPE_ERROR,VC_MESSAGE_BUTTONS_OK)
        varprop = comp.createProperty(VC_REAL, 'Variables::%s'%varname)
        varprop.Quantity = 'Speed'
        varprop.Value = 100.0
      #endif
      speed = varprop.Value*comp.OverrideSpeed
    else:
      speed = eval(re.sub( r':.*?\]', ']', C.group('value') ))*comp.OverrideSpeed*unitconv[C.group('units')]

    stmt1 = positions[routineName+'_'+C.group('pnum')]
    stmt2 = positions[routineName+'_'+C.group('pnum2')]
    doCircularMove( stmt.Positions[0].PositionInReference, stmt1.Positions[0].PositionInReference, stmt2.Positions[0].PositionInReference, speed, C.group('cnt') )
    processStatement( C.group('process') )
    stmt = stmt2
    return pc
  #endif
    
  J = re.match(r'J' + sp + prnum + sp + '(' + rnum + '|' + greal + ')' + junits + cnt + process, line)
  if J:
    stmt = positions['PositionRegister_'+J.group('prnum')]
    stmt.writeToTarget( trg )
    trg.MotionType = VC_MOTIONTARGET_MT_JOINT
    if J.group('units') == '%':
      trg.JointSpeedFactor = eval(re.sub( r':.*?\]', ']', J.group(2) ))/100.*comp.OverrideSpeed
      motionTime = 0.0
    else:
      trg.JointSpeedFactor = 1.0
      motionTime = trg.JointSpeedFactor = eval(re.sub( r':.*?\]', ']', J.group(2) ))/1000./comp.OverrideSpeed
    #endif
    doMove( J.group('cnt'), motionTime )
    processStatement( J.group('process') )
    return pc
  #endif
 
  L = re.match(r'L' + sp + prnum + sp + '('+galphanum+'|((?P<value>(' + rnum + '|' + greal + '))' + units + '))' + cnt + process, line)
  if L:
    stmt = positions['PositionRegister_'+L.group('prnum')]
    stmt.writeToTarget( trg )
    trg.MotionType = VC_MOTIONTARGET_MT_LINEAR
    varname = L.group('name')
    if varname:
      varprop = comp.getProperty( 'Variables::%s'%varname )
      if not varprop:
        msg = '%s:%s: Error at line %s: Undefined Speed variable <%s> in move. Creating property on Variables:: tab. Setting speed to 100mm/sec' % (comp.Name, routineName, pc, varname)
        app.messageBox(msg,"Error",VC_MESSAGE_TYPE_ERROR,VC_MESSAGE_BUTTONS_OK)
        varprop = comp.createProperty(VC_REAL, 'Variables::%s'%varname)
        varprop.Quantity = 'Speed'
        varprop.Value = 100.0
      #endif
      trg.CartesianSpeed = varprop.Value*comp.OverrideSpeed
    else:
      trg.CartesianSpeed = eval(re.sub( r':.*?\]', ']', L.group('value') ))*comp.OverrideSpeed*unitconv[L.group('units')]
    doMove( L.group('cnt') )
    processStatement( L.group('process') )
    return pc
  #endif
    
  if flyby:
    controller.move()
    controller.clearTargets()
  flyby = False

  CALL = re.match(r'CALL' + sp + galphanum + '(\s*\((.*)\)\s*)?', line)
  if CALL:
    try:
      args = [eval(arg) for arg in CALL.group(3).split(',')]
    except:
      args = None
    #endtry
    executeRoutine( CALL.group('name').strip(), args )
    comp.CurrentRoutine = routineName
    if ls: robotNote.Note = ls.Note
    return pc
  #endif
    
  JMP = re.match(r'JMP' + sp + label, line)
  if JMP:
    jumpto = JMP.group('label')
    try:
      pc = labels[jumpto]
    except:
      msg = '%s:%s: Error at line %s: No such label <%s> for JMP' % (comp.Name, routineName, pc,jumpto)
      app.messageBox(msg,"Error",VC_MESSAGE_TYPE_ERROR,VC_MESSAGE_BUTTONS_OK)
      return -1
    #endtry
    return pc
  #endif
    
  IF = re.match(r'IF' + sp +'(.*)' + sp + 'THEN', line)
  if IF:
    expression = IF.group(1)
    expression = re.sub( r':.*?\]', ']', expression )
    expression = re.sub( '=', '==', expression )
    expression = re.sub( '<==', '<=', expression )
    expression = re.sub( '>==', '>=', expression )
    expression = re.sub( sp+'AND'+sp, ' and ', expression )
    expression = re.sub( sp+'OR'+sp, ' or ', expression )
    if eval(expression):
      pass
    else:
      for pc in range(pc, numLines):
        if elses.get(pc,0) or endifs.get(pc,0):
          return pc
    #endif
    return pc
  #endif
    
  IF = re.match(r'IF' + sp +'(.*)' + comma + '(.*)', line)
  if IF:
    expression = IF.group(1)
    expression = re.sub( r':.*?\]', ']', expression )
    expression = re.sub( '=', '==', expression )
    expression = re.sub( '<==', '<=', expression )
    expression = re.sub( '>==', '>=', expression )
    expression = re.sub( sp+'AND'+sp, ' and ', expression )
    expression = re.sub( sp+'OR'+sp, ' or ', expression )
    if eval(expression):
      pc = executeStatement( pc-1, IF.group(2), line, routineName, labels, elses, endifs, numLines )
    #endif
    return pc
  #endif
  
  SELECT = re.match(r'SELECT' + sp + '(.*)' + compare + '(.*)' + comma + '(.*)', line)
  if SELECT:
    lhs = SELECT.group(1)
    lhs = re.sub( r':.*?\]', ']', lhs )
    comparison = SELECT.group(2)
    comparison = re.sub( '=', '==', comparison )
    comparison = re.sub( '<==', '<=', comparison )
    comparison = re.sub( '>==', '>=', comparison )
    comparison = re.sub( sp+'AND'+sp, ' and ', comparison )
    comparison = re.sub( sp+'OR'+sp, ' or ', comparison )
    rhs = SELECT.group(3)
    rhs = re.sub( r':.*?\]', ']', rhs )
    expression = lhs + comparison + rhs
    if eval(expression):
      pc = executeStatement( pc-1, SELECT.group(4), line, routineName, labels, elses, endifs, numLines )
    #endif
    return pc
  #endif
  
  SELECT = re.match(compare + '(.*)' + comma + '(.*)', line)
  if SELECT:
    comparison = SELECT.group(1)
    comparison = re.sub( '=', '==', comparison )
    comparison = re.sub( '<==', '<=', comparison )
    comparison = re.sub( '>==', '>=', comparison )
    comparison = re.sub( sp+'AND'+sp, ' and ', comparison )
    comparison = re.sub( sp+'OR'+sp, ' or ', comparison )
    rhs = SELECT.group(2)
    rhs = re.sub( r':.*?\]', ']', rhs )
    expression = lhs + comparison + rhs
    if eval(expression):
      pc = executeStatement( pc-1, SELECT.group(3), line, routineName, labels, elses, endifs, numLines )
    #endif
    return pc
  #endif  
      
  RR = re.match( rnum + eq + '(.*)', line)
  if RR:
    ridx = int(RR.group('rnum'))
    R[ridx] = eval(re.sub( r':.*?\]', ']', RR.group(2) ))
    register = 'Registers::R[%s]' % ridx
    rprop = comp.getProperty(register)
    if not rprop:
      rprop = comp.createProperty(VC_REAL, register)
      rprop.Group = ridx
    #endif
    rprop.Value = R[ridx]
    return pc
  #endif
  
  DR = re.match(dnum + eq + '(.*)', line)
  if DR:
    didx = int(DR.group('dnum'))
    D[didx] = eval(re.sub( r':.*?\]', ']', DR.group(2) ))
    return pc
  #endif
  
  FR = re.match(dnum + eq + '(.*)', line)
  if FR:
    fidx = int(FR.group('fnum'))
    F[fidx] = eval(re.sub( r':.*?\]', ']', FR.group(2) ))
    return pc
  #endif
  
  PR = re.match(prnum + eq + '(.*)', line)
  if PR:
    pridx = int(PR.group('prnum'))
    prname = 'PositionRegister_'+PR.group('prnum')
    stmt = positions.get(prname, None)
    if not stmt:
      prroutine = executor.Program.findRoutine('PositionRegister')
      if not prroutine:
        prroutine = executor.Program.addRoutine('PositionRegister')
      #endif
      stmt = prroutine.addStatement( VC_STATEMENT_PTPMOTION )
      stmt.Name = prname
    #endif
    stmt.Target = eval(re.sub( r':.*?\]', ']', PR.group(2) ))
    return pc
  #endif
    
  RODO = re.match(r'(RO|DO)' + obracket + '(?P<port>(' + rnum + '|' + ginteger + '))' + comment + cbracket + eq + r'(?P<value>ON|OFF)', line)
  if RODO:
    port = int(eval(re.sub( r':.*?\]', ']', RODO.group('port') )))
    if RODO.group('value') == 'ON':
      value = True
    else:
      value = False
    #endif
    executor.DigitalOutputSignals.output( port, value )
    io = RODO.group(1)
    if io == 'RO':
      RO[port] = value
    else:
      DO[port] = value
      signalPNS( port, value )
    #endif
    displayIO( io, port, value )
    return pc
  #endif
    
  PULSE = re.match(r'(RO|DO)' + obracket + '(?P<port>(' + rnum + '|' + ginteger + '))' + comment + cbracket + eq + 'PULSE' + comma + greal + 'sec', line)
  if PULSE:
    io = PULSE.group(1)
    port = int(eval(re.sub( r':.*?\]', ']', PULSE.group('port') )))
    executor.DigitalOutputSignals.output( port, True )
    signalPNS( port, True )
    displayIO( io, port, True )
    delay( eval(PULSE.group(3)) )
    executor.DigitalOutputSignals.output( port, False )
    signalPNS( port, False )
    if io == 'RO':
      RO[port] = False
    else:
      DO[port] = False
    #endif
    displayIO( io, port, False )
    return pc
  #endif

  WAIT = re.match(r'WAIT' + sp + r'(RI|DI)' + obracket + ginteger + comment + cbracket + eq + r'(?P<value>ON|OFF)', line)
  if WAIT:
    io = WAIT.group(1)
    port = eval(WAIT.group(2))
    if WAIT.group('value') == 'ON':
      value = True
    else:
      value = False
    #endif
    if comp.SkipWaits:
      if io == 'RI':
        displayIO( 'RI', port, RI[port] )
      else:
        displayIO( 'DI', port, DI[port] )
      #endif
      delay( 1.0 )
    else:
      if io == 'RI':
        displayIO( 'RI', port, RI[port] )
        while not comp.SkipWaits and (executor.DigitalInputSignals.input( port ) != value and RI[port] != value): delay(0.02)
        RI[port] = value
        displayIO( 'RI', port, value )
      else:
        displayIO( 'DI', port, DI[port] )
        while not comp.SkipWaits and (executor.DigitalInputSignals.input( port ) != value and DI[port] != value): delay(0.02)
        DI[port] = value
        displayIO( 'DI', port, value )
      #endif
    #endif
    return pc
  #endif

  WAIT = re.match(r'WAIT' + sp + greal + r'\s*\(sec\)', line)
  if WAIT:
    delay( eval(WAIT.group(1)) )
    return pc
  #endif
    
  UALM = re.match(r'UALM' + obracket + ginteger + comment + cbracket, line)
  if UALM:
    app.render()
    delay(0.5)
    msgID = UALM.group(1)
    msg = '%s:%s:%s:\n%s' % (comp.Name, routineName, pc, UserMessages.get(int(msgID), msgID))
    app.messageBox(msg,"User Alarm",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return pc
  #endif
    
  COMMENT = re.match(r'!' + '(.*)', line)
  if COMMENT:
    print COMMENT.group(1)
    return pc
  #endif
    
  SEMICOLON = re.match(semicolon, line)
  if SEMICOLON:
    return pc
  #endif
    
  COMMENT = re.match(r'//' + '(.*)', line)
  if COMMENT:
    return pc
  #endif
    
  LBL = re.match(label, line)
  if LBL:
    return pc
  #endif
    
  UTOOL = re.match('UTOOL_NUM' + eq + ginteger, line)
  if UTOOL:
    utool_num = eval(UTOOL.group(1))
    return pc
  #endif
  
  UFRAME = re.match('UFRAME_NUM' + eq + ginteger, line)
  if UFRAME:
    uframe_num = eval(UFRAME.group(1))
    return pc
  #endif
  
  ASSIGNMENT = re.match('(.*)' + eq + '(.*)', line)
  if ASSIGNMENT:
    lhs = re.sub( r':.*?\]', ']', ASSIGNMENT.group(1).strip() )
    rhs = re.sub( r':.*?\]', ']', ASSIGNMENT.group(2).strip() )
    expression = lhs + ' = ' + rhs
    exec(expression)
    varname = 'Variables::' + lhs
    prop = comp.getProperty( varname )
    if not prop:
      prop = comp.createProperty(VC_REAL, varname )
    prop.Value = eval(lhs)
    return pc
  #endif
  
  if processStatement( line ):
    return pc
  #endif
  
  WEAVE = re.match('Weave' + sp + '(.*)', line)
  if WEAVE:
    weave = WEAVE.group(1)
    return pc
  #endif
  
  TRACK = re.match('Track' + sp + '(.*)', line)
  if TRACK:
    track = TRACK.group(1)
    return pc
  #endif
  
  TOUCH = re.match('Touch Offset' + sp + '(.*)', line)
  if TOUCH:
    touch = TOUCH.group(1)
    return pc
  #endif
  
  if not line:
    return pc
  #endif
  
  print 'IGNORING line: %s' % fullline
  
  return pc
"""

addState(None)
