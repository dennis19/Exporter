#-------------------------------------------------------------------------------
from vcApplication import *
from vcCommand import *
import vcMatrix
from math import *
import re, time, os, os.path

#-------------------------------------------------------------------------------
# This is to keep all numeric conversions consistent across platform locales.
import locale
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

def GetBaseIndex( s ):
  for uf, b in enumerate(controller.Bases):
    if b == s.Base:
      return uf + 1
  return 0

def GetToolIndex( s ):
  for ut, t in enumerate(controller.Tools):
    if t == s.Tool:
      return ut + 1
  return 0

def doWriteTargetDefinition(ls,sn,statement):

  uf = GetBaseIndex( statement )
  ut = GetToolIndex( statement )

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
    ls.write('P[%i:%s]{ \n' % (sn,comment) )
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

def WriteProgramBody( routine, name, filename,program ):
  global statementCount, groups, line 
  if routine==program.MainRoutine:
    modnote = comp.findBehaviour(routine.Name)
  else:
    modnote = comp.findBehaviour(name)
  if not modnote:
    return False
  #endif

  try:
    mod = open(filename,"w")
  except:
    print "Cannot open file \'%s\' for writing" % filename
    return False
  #endtry
  if not re.findall("MODULE %s" % name,modnote.Note):
    mod.write( 'MODULE %s\n' % name)

  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  for line in modnote.Note.split('\n'):
    if line[:8] == 'MODIFIED':
      line = "MODIFIED \t= %s;" % td
    elif line[:10] == 'LINE_COUNT':
      line = "LINE_COUNT \t= %i;" % GetStatementCount( modnote )
    #endif
    mod.write( '%s\n' % line )

  #endfor
  
  #mod.write("/POS\n")
  positions = []
  i=0
  for s in routine.Statements:
    if s.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
      if s.getProperty('INDEX'):
        num = s.INDEX
      else:
        pName = s.Positions[0].Name
        #print "pName = %s" %pName
        #num = int(pName[pName.rindex('_')+1:])
      #endif
      positions.append((i, s))
      i+=1
    #endif
  #endif
  positions.sort()

  #for n,s in positions:
    #doWriteTargetDefinition(mod,n,s)
    
  mod.write("ENDMODULE\n")
  mod.close

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

  # Ask user to select file, where PE will be dumped
  save = app.findCommand("dialogSaveFile")
  uri = getValue( comp, "Filename", "", VC_URI, "Download" )
  ok = True
  Modfilter = "ABB Mod Robot Program file (*.mod)|*.mod"
  save.execute(uri,ok,Modfilter,'Choose File to save ABB Mod Robot Program file')
  if not save.Param_2:
    print "No file selected for saving, aborting command"
    return
  #endif

  uri = save.Param_1
  uri = uri[8:]

  head, tail = os.path.split(uri)
  mainName = tail[:len(tail)-4]

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
    if not WriteProgramBody( program.MainRoutine, mainName, uri,program  ):
      print "RSL to ABB FAILED at MAIN" 
      return
    #endif

    for routine in program.Routines:
      # print "routine.Name %s" % routine.Name
      for statement in routine.Statements:
        if statement.Type==VC_STATEMENT_COMMENT:
          # print "name should be %s" % statement.Comment
          name=statement.Comment
          break  
      #name = goodName( routine.Name )
      filename = head + "\\" + name + ".mod"
      if not WriteProgramBody( routine, name,  filename,program ):
        print "RSL to ABB FAILED at routine: %s" % name
        return
      #endif
    #endfor
    print "RSL to ABB Successfully Written to: ", uri 

    os.startfile(head)
  else:
    name = goodName( routine.Name )
    filename = head + "\\" + name + ".mod"
    if not WriteProgramBody( routine, name,  filename ):
      print "RSL to ABB FAILED at routine: %s" % name
      return
    #endif
    print "RSL to ABB Successfully Written to: ", filename 

    os.startfile(filename)
  #endif

  return
#-------------------------------------------------------------------------------

# Register states
addState( None )

