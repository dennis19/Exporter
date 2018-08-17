#-------------------------------------------------------------------------------
# Copyright 2012-2013 Visual Components Ltd. All rights reserved.
#-------------------------------------------------------------------------------

from vcCommand import *
from vcHelpers.Application import *
from vcHelpers.Robot import *
import re
import os.path
import vcMatrix
import vcVector
from math import *
from olpdefaults import *


sp = r'\s+'
eq = r'\s*=\s*'
comma = r'\s*,\s*'
colon = r'\s*:\s*'
semicolon = r'\s*;\s*'
obracket = r'\s*\[\s*'
cbracket = r'\s*\]\s*'
obrace = r'\s*\{\s*'
cbrace = r'\s*\}\s*'
int = r'-?\d+'
gint = r'('+int+')'
num = r'-?\d*\.?\d+(?:[eE][-+]?\d+)?'
gnum = r'('+num+')'
alphanum = r'[a-zA-Z]+\w*'
galphanum = r'('+alphanum+')'

nl = r' *\r?[\n\0]'
sl = r'\A|\n'
end = r'\s*$'

pnum = r'P'+obracket+'(?P<pnum>'+int+')'+ '(?:\s*:[ \w\"]*)?' + cbracket
uf = r'UF'+colon+'(?P<uf>'+int+')'
ut = r'UT'+colon+'(?P<ut>'+int+')'

wr = r'(?P<wr>N|F)'
el = r'(?P<el>U|D)'
sh = r'(?P<sh>T|B)'
t1 = r'(?P<t1>'+int+')'
t2 = r'(?P<t2>'+int+')'
t3 = r'(?P<t3>'+int+')'
cfg = r'CONFIG' + colon + '\''+ wr + sp + el + sp + sh + comma + t1 + comma + t2 + comma + t3 +'\s*\''

x = r'X' + eq + r'(?P<x>'+num+')' + sp + 'mm'
y = r'Y' + eq + r'(?P<y>'+num+')' + sp + 'mm'
z = r'Z' + eq + r'(?P<z>'+num+')' + sp + 'mm'
w = r'W' + eq + r'(?P<w>'+num+')' + sp + 'deg'
p = r'P' + eq + r'(?P<p>'+num+')' + sp + 'deg'
r = r'R' + eq + r'(?P<r>'+num+')' + sp + 'deg'

coord = uf + comma + ut + comma + cfg + comma + x + comma + y + comma + z + comma + w + comma + p + comma + r 
pos = pnum + obrace + 'GP1' + colon + coord + r'(?P<groups>[^}]*)' + cbrace + semicolon
re_pos = re.compile( pos, re.M )

group = r'GP(?P<grnum>\d+)' + colon + uf + comma + ut + comma + '(?P<jcoords>.*)'
re_group = re.compile( group, re.M | re.DOTALL)

jcoord = r'J(?P<jnum>\d+)' + eq + r'(?P<jval>'+num+')' + sp + '(mm|deg)'
re_jcoord = re.compile( jcoord, re.M )

ecoord = r'E(?P<ejnum>\d+)' + eq + r'(?P<ejval>'+num+')' + sp + '(mm|deg)'
re_ecoord = re.compile( ecoord, re.M )

lnum = r'\s*(?P<lnum>'+int+')' + colon 

#-------------------------------------------------------------------------------
def assignTarget( stmt, snum ):
  global robCnt, pvals

  for p in pvals:
    (idx, xx, yy, zz, ww, pp, rr, uf, ut, cfg, t1, t2, t3, numEx, exJvals) = p 
    if idx == snum:
      m = vcMatrix.new() 
      m.translateAbs( xx, yy, zz )
      #print ww,pp,rr
      m.setWPR( ww, pp, rr )
      stmt.Target = m
      if stmt.Type == VC_STATEMENT_PTPMOTION:
        stmt.Configuration = cfg
        stmt.JointTurns1 = t1
        stmt.JointTurns4 = t2
        stmt.JointTurns6 = t3
      #endif
      #stmt.readFromTarget( trg )

      baseNum = uf
      if baseNum == 0:
        pass
        #stmt.Base = "*NULL*"
      else:
        stmt.Base = robCnt.Bases[baseNum-1].Name
      #endif

      toolNum = ut
      if toolNum == 0:
        stmt.Tool = "*NULL*"
      else:
        stmt.Tool = robCnt.Tools[toolNum-1].Name
      #endif
      stmt.Name = 'P%i' % idx

      for j in range(numEx):
        jname = "ExternalJoint%i" % (j+1)
        for prop in stmt.Properties:
	  if prop.Name == jname:
            prop.Value = exJvals[j]
	    break
          #endif
        #endfor
      #endfor
      return
    #endif
  #endfor

#-------------------------------------------------------------------------------

def importPath(app,filename,subroutine):
  global program, routine, controller, basename, toolname, basenames, toolnames, robotconfig, robotconfigs
  program, routine, controller, basename, toolname, basenames, toolnames, robotconfig, robotconfigs = getSelectedRobotsData()
  routine=subroutine
  
  try:
    infile = open(filename,"r")
  except:
    app.messageBox("Cannot open file \'%s\' for reading" % filename,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return False
    
  #global cmd
  global robCnt
  global pvals
  global robAxes, baseAxes, posAxes
  firstgroupcheck=True
  
  #Initialize default parameters
  initDefaultParams()
  defaultparams=app.findLayoutItem("DefaultParameters")  
  
  
  numOfExtendedAxis=0
  #collect units of external axis values based on external axis type
  extaxisunit = []
  extjc=0
  for j in controller.Joints:
    if j.ExternalController:
      if j.Type==VC_JOINT_TRANSLATIONAL:
        extaxisunit.append("mm")
      else:
        extaxisunit.append("deg")
      extjc+=1
      #calculate amount of extended axis defined in motion group definitions    
      if defaultparams.RobotGroup==defaultparams.getProperty("ExtAxisGroup"+str(extjc)).Value:
        numOfExtendedAxis+=1      
  
  if routine == None:
    routine = program.MainRoutine
  #endif

  filestring = infile.read()
  infile.close()

  comp = program.Component
  robCnt = program.Controller

  robAxes = 0
  baseAxes = 0
  posAxes = 0

  pnpbase = comp.getBehaviour("PnP Base")
  if pnpbase:
    baseCmp = pnpbase.ConnectedComponent
    if baseCmp:
      baseCnt = baseCmp.findBehavioursByType(VC_SERVOCONTROLLER )[0]
      if baseCnt:
        baseAxes = baseCnt.JointCount
      #endif
    #endif
  #endif

  pnppos = comp.getBehaviour("Joint_Base_R1")
  if pnppos == None:
    pnppos = comp.getBehaviour("Servo Axes")
  #endif
  if pnppos:
    posCmp = pnppos.ConnectedComponent
    if posCmp:
      posCnt = posCmp.findBehavioursByType(VC_SERVOCONTROLLER )[0]
      if posCnt:
        posAxes = posCnt.JointCount
      #endif
    #endif
  #endif

  robAxes = program.Controller.JointCount - baseAxes - posAxes

  pvals = []
  positions = re_pos.finditer(filestring)
  for p in positions:
    idx = eval(p.group('pnum'))
    xx = eval(p.group('x'))
    yy = eval(p.group('y'))
    zz = eval(p.group('z'))
    ww = eval(p.group('w'))
    pp = eval(p.group('p'))
    rr = eval(p.group('r'))
    uf = eval(p.group('uf'))
    ut = eval(p.group('ut'))
    cfg = p.group('wr') + ' ' + p.group('el') + ' ' + p.group('sh')
    t1 = eval(p.group('t1'))
    t2 = eval(p.group('t2'))
    t3 = eval(p.group('t3'))

    numEx = 0
    exJvals = []
    foundgroups = []

    #check if extended axis (E1=...) found
    ecoords = re_ecoord.finditer(p.group('groups'))
    for e in ecoords:
      exJvals.append(eval(e.group('ejval')))
      numEx += 1
    
    if firstgroupcheck and numEx>0:
      if numOfExtendedAxis!=numEx:
        app.messageBox("Number of defined \'%d\' extended axis  does not match number of found \'%d\' extended axis"%(numOfExtendedAxis,numEx),"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
      
    #check if external axis values have been defined for GP2 or later
    groups = re_group.finditer(p.group('groups'))
    for g in groups:
      if firstgroupcheck:  
        foundgroups.append(eval(g.group('grnum')))
      jcoords = re_jcoord.finditer(g.group('jcoords'))
      for j in jcoords:
        exJvals.append(eval(j.group('jval')))
        numEx += 1
      #endfor
    #endif
    pvals.append( ( idx, xx, yy, zz, ww, pp, rr, uf, ut, cfg, t1, t2, t3, numEx, exJvals ) )
    
    #check if found groups can be found from motion group definitions
    if firstgroupcheck:
      for fg in foundgroups:
        for axisindex in range(1,21):
          if fg==defaultparams.getProperty("ExtAxisGroup"+str(axisindex)).Value:
            break
          app.messageBox("Group \'%d\' not found in motion group definitions" % fg,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
          break
      firstgroupcheck=False
  #endfor

  try:
    infile = open(filename,"r")
  except:
    app.messageBox("[2] Cannot open file \'%s\' for reading" % filename,"Error",VC_MESSAGE_TYPE_ERROR,VC_MESSAGE_BUTTONS_OK)
    #cmd.Checked = False
    return False
  #endtry

  while True:
    try:
      line = infile.readline()
    except:
      break
    #endtry

    if line == None or line == '':
      break
    #endif
    
    J = re.match(lnum + r'J' + sp + pnum + sp + gnum +'%' + sp + galphanum + '(.*)' + semicolon + end, line)
    if J:
      stmt = routine.createStatement( VC_STATEMENT_PTPMOTION )
      stmt.JointSpeed = eval(J.group(3))
      addProperty(stmt, VC_STRING, "PosPath",True,False,False,J.group(4),None,"")

      assignTarget( stmt, eval(J.group('pnum')) )

      continue
    #endif

    L = re.match(lnum + r'L' + sp + pnum + sp + gnum +'mm/sec' + sp + galphanum +'(.*)' + semicolon + end, line)
    if L:
      stmt = routine.createStatement( VC_STATEMENT_LINMOTION )
      stmt.MaxSpeed = eval(L.group(3))
      addProperty(stmt, VC_STRING, "PosPath",True,False,False,L.group(4),None,"")

      assignTarget( stmt, eval(L.group('pnum')) )

      continue
    #endif

    PULSE = re.match(r'PULSE' + sp + r'OT#\((\d+)\)' + sp + r'T'+ eq + num + end, line)
    if PULSE:
      stmt = routine.createStatement( VC_STATEMENT_SETBIN )
      stmt.Output = eval(PULSE.group(1))
      stmt.Value = True
	
      stmt = routine.createStatement( VC_STATEMENT_DELAY )
      stmt.Delay = eval(PULSE.group(2))

      stmt = routine.createStatement( VC_STATEMENT_SETBIN )
      stmt.Output = eval(PULSE.group(1))
      stmt.Value = False
      continue
    #endif

    RO = re.match(lnum + r'RO' + obracket + gint +'(?:\s*:[ \w\"]*)?' + cbracket+eq+r'(ON|OFF)'+semicolon +  end, line)
    if RO:
      stmt = routine.createStatement( VC_STATEMENT_SETBIN )

      stmt.Output = eval(RO.group(2))

      if RO.group(3) == 'ON':
        stmt.Value = True
      else:
        stmt.Value = False
      #endif
      continue
    #endif

    DI = None
    if DI:
      stmt = routine.createStatement( VC_STATEMENT_WAITBIN )

      stmt.Input = eval(WAIT.group(1))

      if WAIT.group(2) == 'ON':
        stmt.Value = True
      else:
        stmt.Value = False
      #endif
      continue
    #endif

    WAIT = re.match(lnum + r'WAIT' + sp + gnum + r'\s*\(sec\)' + semicolon + end, line)
    if WAIT:
      stmt = routine.createStatement( VC_STATEMENT_DELAY )
      stmt.Delay = eval(WAIT.group(2))
      continue
    #endif

    NOP = re.match(r'NOP' + end,line)
    if NOP:
      continue
    #endif

    COMMENT = re.match(lnum + r'!' + '(.*)' + semicolon + end, line)
    if COMMENT:
      stmt = routine.createStatement( VC_STATEMENT_COMMENT )
      stmt.Name = "CMT1"
      stmt.Comment = COMMENT.group(2)
      continue
    #endif

    CALL = re.match(lnum + r'CALL' + sp + galphanum + semicolon + end, line)
    if CALL:
      routineName = CALL.group(2)
      #Creating of empty subroutines is currently removed, was there any reason to create these?
      # routineFound = False
      # for r in program.SubRoutines:
        # if r.Name == routineName:
          # routineFound = True
          # break
        # #endif
      # #endfor
      # if not routineFound:
        # program.createSubRoutine( routineName )
      # #endif
      stmt = routine.createStatement( VC_STATEMENT_CALL )
      stmt.RoutineName = routineName
      continue
    #endif

    END = re.match(r'/END' + end,line)
    if END:
      continue
    #endif

    POS = re.match(r'/POS' + end, line )
    if POS:
      continue
    #endif

    MN = re.match(r'/MN' + end, line )
    if MN:
      posFlag = False
      instFlag = True
      trg = robCnt.createTarget()
      trg.UseJoints = True
      trg.TargetMode = VC_MOTIONTARGET_TM_ROBOTROOT
      continue
    #endif

    # This renaming of routine by deleting it and recreating it won't work currently because
    # the routine is referenced in calling pathimport.py and the reference becomes invalid
    # We need probably R/W access to routine name to fix this issue
    # PROG = re.match(r'/PROG' + sp + galphanum + '(?:\s+Macro)?'+end,line)
    # if PROG:
      # program.deleteSubRoutine( PROG.group(1) )
      # routine = program.createSubRoutine( PROG.group(1) )
      # continue
    #endif

    ATTR = re.match(r'/ATTR' + end,line)
    if ATTR:
      continue
    #endif

    #print "Unrecognized Syntax:", line

  #endwhile

  infile.close()
  app.render()
  return True
#-------------------------------------------------------------------------------

#addState(firstState)

