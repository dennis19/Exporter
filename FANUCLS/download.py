#-------------------------------------------------------------------------------
from vcApplication import *
from vcCommand import *
import vcMatrix
from math import *
import re, time, os, os.path

#-------------------------------------------------------------------------------
# This is to keep all numeric conversions consistent across platform locales.
import locale
import convert
sp = r'\s+'
eq = r'\s*=\s*'
comma = r'\s*,\s*'
colon = r'\s*:\s*'
semicolon = r'\s*;\s*'
obracket = r'\s*\[\s*'
cbracket = r'\s*\]\s*'
orbracket = r'\s*\(\s*'
crbracket = r'\s*\)\s*'
obrace = r'\s*\{\s*'
cbrace = r'\s*\}\s*'
integer = r'-?\d+'
ginteger = r'('+integer+')'
real = r'-?\d*\.?\d+(?:[eE][-+]?\d+)?'
greal = r'('+real+')'
alphanum = r'[a-zA-Z]+\w*'
galphanum = r'('+alphanum+')'
locale.setlocale(locale.LC_NUMERIC,'C')
#-------------------------------------------------------------------------------
app = getApplication()

#-------------------------------------------------------------------------------

def goodName( name ):
  name = name.strip()
  if name[0:1].isdigit():
    name = '_'+name
  return name

def getProperty( op, name ):
  for prop in op.Properties:
    if prop.Name == name:
      return prop
    #endif
    idx = prop.Name.find( '::' ) 
    if idx > -1 and prop.Name[idx+2:] == name:
      return prop
    #endif
  #endfor
  return None

def getValue( op, name, default=0, type=None, tab="" ):

  prop = getProperty( op, name )
  if prop != None:
    return prop.Value
  #endif

  # if property does not exist, then create it for future use
  if type != None:
    if len(tab):
      tab+="::"
    #endif
    prop = op.createProperty( type, tab+name )
    prop.Value = default
  #endif

  return default

def GetBaseIndex( s,controller ):
  for uf, b in enumerate(controller.Bases):
    if b == s.Base:
      return uf + 1
  return 0

def GetToolIndex( s ,controller ):
  for ut, t in enumerate(controller.Tools):
    if t == s.Tool:
      return ut + 1
  return 0

def doWriteTargetDefinition(ls,sn,statement):

  uf = GetBaseIndex( statement,controller )
  ut = GetToolIndex( statement,controller )

  posFrame = statement.Positions[0]
  t4 = getValue( posFrame, 'JointTurns4', 0 )
  t5 = getValue( posFrame, 'JointTurns5', 0 )
  t6 = getValue( posFrame, 'JointTurns6', 0 )
  cf = getValue( posFrame, 'Configuration', 'F U T' )
  config = '%s, %i, %i, %i' % (cf, t4, t5, t6 )

  group = 1
  try:
    comment = posFrame.Name[posFrame.Name.rindex('_')+1:]
  except:
    comment = None
  if comment and comment != str(sn):
    ls.write('P[%i]{ \n' % (sn) )
  else:
    ls.write('P[%i]{ \n' % (sn) )
  #endif
  ls.write("    GP%i:\n" % group )
  ls.write("         UF : %i, UT : %i," % (uf, ut) )
  m = posFrame.PositionInReference
  p = m.P
  a = m.WPR
  ls.write("              CONFIG : '%s',\n" % config )
  ls.write("         X = %8.2f  mm,     Y = %8.2f  mm,     Z = %8.2f  mm,\n" % (p.X,p.Y,p.Z))
  ls.write("         W = %8.2f deg,     P = %8.2f deg,     R = %8.2f deg" % (a.X,a.Y,a.Z))
  internalAxes = len(posFrame.InternalJointValues)
  i = 0
  for j, joint in enumerate( posFrame.ExternalJointValues ):
    if groups[j+internalAxes] == group:
      if j == 0: ls.write(",\n    ")
      else: ls.write(",")
    else:
      i = 0
      ls.write("\n")
      group = groups[j+internalAxes]
      ls.write("    GP%i:\n" % group )
      ls.write("         UF : %i, UT : %i,\n    " % (uf, ut) )
    #endif
    if i > 0 and i%3 == 0:
      ls.write("\n    ")
    #endif
    if group == 1:
      ls.write("     E%i = %8.2f %s" % (j+1, joint.Value, jUnits[internalAxes+j]) )
    else:
      ls.write("     J%i = %8.2f %s" % (i+1, joint.Value, jUnits[internalAxes+j]) )
    #endif
    i += 1
  #endfor
  ls.write("\n")
  ls.write("};\n" )

#-------------------------------------------------------------------------------
def GetStatementCount( note ):

  if not note: return 0

  sc = 0
  header = True
  for line in note.Note.split('\n'):
    if header:
      if re.match(r'/MN\s*$', line): header = False
      continue
    #endif
    if len(line)<2: continue
    sc += 1
  #endfor

  return sc
#-------------------------------------------------------------------------------
def writePosReg(program,filename):
  i=1
  try:
    ls = open(filename,"w")
  except:
    print "Cannot open file \'%s\' for writing" % filename
    return False

  line="[*POSREG*]$POSREG  Storage: CMOS  Access: RW  : ARRAY[1,100] OF Position Reg\n"
  while i<=100:
    pos_reg_defined=0
    for routine in program.Routines:
      j="%s" %i
      if re.search("POSREG_PR"+obracket+j+'(?P<comment>(?:\s*:.*)?)'+cbracket,routine.Name):
        pos_reg_def=re.search("POSREG_PR"+obracket+j+'(?P<comment>(?:\s*:.*)?)'+cbracket,routine.Name)
        comment_=pos_reg_def.group("comment")[1:len(pos_reg_def.group("comment"))]
        pos_reg_defined=1
        pos_=routine.Statements[0].Positions[0]
        xx = pos_.PositionInReference.P.X
        yy = pos_.PositionInReference.P.Y
        zz = pos_.PositionInReference.P.Z
        ww = pos_.PositionInReference.WPR.X
        pp=pos_.PositionInReference.WPR.Y
        rr = pos_.PositionInReference.WPR.Z
        conf = convert.getConfig(routine.Statements[0])

        #print "name %s" % comment_


        line += "    [1,%s] = '%s'\n" \
                "  Group: 1 Config: %s\n" \
                "  X: %s  Y: %s  Z: %s\n" \
                "  W: %s  P: %s  R: %s\n" % (i,comment_,conf, xx, yy, zz, ww, pp, rr)

        #print "name %s" %routine.Name
        break
      #elif re.match

    if not pos_reg_defined==1:
      line +="    [1,%s] = '' Uninitialized\n" %i
    i=i+1


  ls.write('%s\n' %line)
  ls.close

def writeSysFrame(controller_,name,filename):
  #lsnote = comp.findBehaviour(name)
  # if not lsnote:
  #   return False
  #endif
  print "filename :%s" %filename
  try:
    ls = open(filename,"w")
  except:
    print "Cannot open file \'%s\' for writing" % filename
    return False

  line="[*SYSTEM*]$MNUFRAME  Storage: CMOS  Access: RW  : ARRAY[1,9] OF POSITION\n"
  bases=controller_.Bases
  i=0
  while i<=len(bases)-1:
    xx = bases[i].PositionMatrix.P.X
    yy = bases[i].PositionMatrix.P.Y
    zz = bases[i].PositionMatrix.P.Z
    ww = bases[i].PositionMatrix.WPR.X
    pp = bases[i].PositionMatrix.WPR.Y
    rr = bases[i].PositionMatrix.WPR.Z
    line += "    [1,%s] = \n" \
            "  Group: 1 Config: N D B, 0, 0, 0\n" \
            "  X: %s  Y: %s  Z: %s\n" \
            "  W: %s  P: %s  R: %s\n" % (i+1, xx, yy, zz, ww, pp, rr)

    #print "bases %s" %bases[i].Name
    #line+="  [1,%s] = \n" %i
    i+=1
  line+="[*SYSTEM*]$MNUFRAMENUM  Storage: CMOS  Access: RW  : ARRAY[1] OF BYTE\n" \
        "  [1] =%s\n"%i
  line+="[*SYSTEM*]$MNUTOOL  Storage: CMOS  Access: RW  : ARRAY[1,10] OF POSITION\n"
  tools=controller_.Tools
  i=0
  while i<=len(tools)-1:
    xx=tools[i].PositionMatrix.P.X
    yy=tools[i].PositionMatrix.P.Y
    zz=tools[i].PositionMatrix.P.Z
    ww=tools[i].PositionMatrix.WPR.X
    pp=tools[i].PositionMatrix.WPR.Y
    rr=tools[i].PositionMatrix.WPR.Z
    #print "tools %s" %tools[i].Name
    line += "    [1,%s] = \n" \
            "  Group: 1 Config: N D B, 0, 0, 0\n" \
            "  X: %s  Y: %s  Z: %s\n" \
            "  W: %s  P: %s  R: %s\n" % (i+1,xx,yy,zz,ww,pp,rr)
    i+=1
  line+="[*SYSTEM*]$MNUTOOLNUM  Storage: CMOS  Access: RW  : ARRAY[1] OF BYTE\n"\
  "[1] = %s\n"%i
  ls.write('%s\n' %line)
  ls.close

def WriteRegisterBody(routine,name,filename):
  lsnote = comp.findBehaviour(name)
  if not lsnote:
    return False
  #endif
  #print "filename :%s" %filename
  try:
    ls = open(filename,"w")
  except:
    print "Cannot open file \'%s\' for writing" % filename
    return False

  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  for line in lsnote.Note.split('\n'):
    #print "line %s" % line
    if line[:8] == 'MODIFIED':
      line = "MODIFIED \t= %s;" % td
    elif line[:10] == 'LINE_COUNT':
      line = "LINE_COUNT \t= %i;" % GetStatementCount( lsnote )
    #endif
    ls.write( '%s\n' % line )
  ls.close
  return True

def WriteProgramBody( routine, name, filename ):
  global statementCount, groups

  lsnote = comp.findBehaviour(routine.Name)
  if not lsnote:
    return False
  #endif

  try:
    ls = open(filename,"w")
  except:
    print "Cannot open file \'%s\' for writing" % filename
    return False
  #endtry

  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  for line in lsnote.Note.split('\n'):
    if line[:8] == 'MODIFIED':
      line = "MODIFIED \t= %s;" % td
    elif line[:10] == 'LINE_COUNT':
      line = "LINE_COUNT \t= %i;" % GetStatementCount( lsnote )
    #endif

    ls.write( '%s\n' % line )
  #endfor
  #
  # ls.write("/POS\n")
  # positions = []
  # for s in routine.Statements:
  #   if s.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
  #     if s.getProperty('INDEX'):
  #       num = s.INDEX
  #     else:
  #       pName = s.Positions[0].Name
  #       num = int(pName[pName.rindex('_')+1:])
  #     #endif
  #     positions.append((num, s))
  #   #endif
  # #endif
  # positions.sort()
  #
  # for n,s in positions:
  #   doWriteTargetDefinition(ls,n,s)
  #
  ls.write("/END\n")
  ls.close

  return True

def getActiveRoutine():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

  return routine

#-------------------------------------------------------------------------------
def OnStart():
  global comp, executor, controller, motiontarget, jUnits

  routine = getActiveRoutine()
  if not routine:
    app.messageBox("No routine selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif


  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller
  routine=program.MainRoutine
  VAfilter = "FANUC LS Robot Program file (*.va)|*.va"
  LSfilter = "FANUC LS Robot Program file (*.ls)|*.ls"
  ok = True

  #writePosReg(program)


  #save1 = app.findCommand("dialogSaveFile")
  save = app.findCommand("dialogSaveFile")
  uri = getValue( comp, "Filename", "", VC_URI, "Download" )
  save.execute(uri, ok, VAfilter, 'SYSFRAME')
  if not save.Param_2:
    print "No file selected for saving, aborting command"
    return
  #endif


  uri = save.Param_1
  uri = uri[8:]

  head, tail = os.path.split(uri)

  name='SYSFRAME'
  filename = head + "\\" + name + ".va"
  #print "filename %s" % filename

  #print "note %s" %comp.findBehavioursByType(VC_NOTE)[i].Name
  writeSysFrame(controller,name,filename)
  #os.startfile(filename)

  name='POSREG'
  filename = head + "\\" + name + ".va"
  print "filename %s" % filename
  #
  writePosReg(program,filename)
  #os.startfile(filename)
  #uri = getValue(comp, "Filename", "", VC_URI, "Download")

  # Ask user to select file, where PE will be dumped



  if comp. findBehavioursByType(VC_NOTE):
    i=0
    while i<=len(comp.findBehavioursByType(VC_NOTE))-1:
      if comp.findBehavioursByType(VC_NOTE)[i].Name=="NUMREG":
        name=comp.findBehavioursByType(VC_NOTE)[i].Name
        filename = head + "\\" + name + ".va"
        WriteRegisterBody(routine,comp.findBehavioursByType(VC_NOTE)[i].Name,filename)
        #os.startfile(filename)
      i+=1

  mainName = tail[:len(tail)-3]

  motiontarget = controller.createTarget()
  kinematics = controller.Kinematics
  Joints = controller.Joints
  jUnits = []
  for j in Joints:
    if j.Type == VC_JOINT_ROTATIONAL:
      jUnits.append("deg")
    else:
      jUnits.append("mm")
    #endif
  #endfor

  group = 1
  groups = []
  for joint in controller.Joints:
    if joint.Controller != controller and (comp not in joint.Controller.Component.ChildComponents): 
      group += 1
    #endif
    groups.append(group)
  #endif

  # main routine

  if routine == program.MainRoutine:
    filename=head + "\\" + routine.Name + ".ls"
    if not WriteProgramBody( program.MainRoutine, mainName, filename ):
      print "RSL to FANUC FAILED at MAIN" 
      return
    #endif

    for routine in program.Routines:
      name = goodName( routine.Name )
      name = routine.Name
      filename = head + "\\" + name + ".ls"
      if not WriteProgramBody( routine, name,  filename ):
        if re.findall("POSREG_PR",name):
          print "Position Register(%s) routines are not translated" %name
        else:
          print "RSL to FANUC FAILED at routine: %s" % name
        #return
      #endif
    #endfor
    print "RSL to FANUC Successfully Written to: ", uri 

    os.startfile(head)
  else:
    name = goodName( routine.Name )
    name = routine.Name
    filename = head + "\\" + name + ".ls"
    if not WriteProgramBody( routine, name,  filename ):
      print "RSL to FANUC FAILED at routine: %s" % name
      return
    #endif
    print "RSL to FANUC Successfully Written to: ", filename 

    #os.startfile(filename)
  #endif

  return
#-------------------------------------------------------------------------------

# Register states
addState( None )

