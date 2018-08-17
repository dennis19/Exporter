from vcCommand import *
import vcMatrix
import time, os.path


defaults = {'Class':'', 
'JointMoveAtStart':True,
 'NegateSurfaceNormal': True,
 'UseFixedOrientations': True,
 'RollDelta': 0.0,
 'PitchDelta': 0.0,
 'YawDelta' : 0.0,
 'OffsetX' : 0.0,
 'OffsetY' : 0.0,
 'OffsetZ' : 0.0,
 'PosPath' : 'CNT0',
 'DefaultLINProcessSpeed' : 100.0,
 'DefaultLINRapidSpeed' : 500.0,
 'DefaultPTPProcessSpeed' : 10.0,
 'DefaultPTPRapidSpeed' : 50.0,
 'RobotGroup' : 1,
 'ExtAxisGroup1' : 1,
 'ExtAxisGroup2' : 1,
 'ExtAxisGroup3' : 1,
 'ExtAxisGroup4' : 1,
 'ExtAxisGroup5' : 1,
 'ExtAxisGroup6' : 1,
 'ExtAxisGroup7' : 1,
 'ExtAxisGroup8' : 1,
 'ExtAxisGroup9' : 1,
 'ExtAxisGroup10' : 1,
 'ExtAxisGroup11' : 1,
 'ExtAxisGroup12' : 1,
 'ExtAxisGroup13' : 1,
 'ExtAxisGroup14' : 1,
 'ExtAxisGroup15' : 1,
 'ExtAxisGroup16' : 1,
 'ExtAxisGroup17' : 1,
 'ExtAxisGroup18' : 1,
 'ExtAxisGroup19' : 1,
 'ExtAxisGroup20' : 1}


#-------------------------------------------------------------------------------
# This is to keep all numeric conversions consistent across platform locales.
import locale
locale.setlocale(locale.LC_NUMERIC,'C')

def GetToolIndex(controller,motiontarget):
  i = 0
  for t in controller.Tools:
    i += 1
    if t.Name == motiontarget.ToolName:
      return i
  return 0
#-------------------------------------------------------------------------------
def GetBaseIndex(controller,motiontarget):
  i = 0
  for b in controller.Bases:
    i += 1
    if b.Name == motiontarget.BaseName:
      return i
  return 0
#-------------------------------------------------------------------------------
def GetConfigs(motiontarget):
  rconf = motiontarget.RobotConfig
  if rconf == 0:
    c = "\'N U T"
  elif rconf == 1:
    c = "\'F U T"
  elif rconf == 2:
    c = "\'N D T"
  elif rconf == 3:
    c = "\'F D T"
  elif rconf == 4:
    c = "\'N U B"
  elif rconf == 5:
    c = "\'F U B"
  elif rconf == 6:
    c = "\'N D B"
  elif rconf == 7:
    c = "\'F D B"
  #if motiontarget.MotionType == VC_MOTIONTARGET_MT_JOINT:
  # check this out!
  j = motiontarget.JointValues
  t =""
  for jt in [j[3],j[4],j[5]]:
    if jt <-179.0:
      t+=", -1"
    elif jt > 179.0:
      t+=", 1"
    else:
      t+=", 0"
  t+="\',"   
    #t = ", %i, %i, %i" %(motiontarget.JointTurns4, 0, motiontarget.JointTurns6)
    #t = ", %i, %i, %i" %(motiontarget.JointTurns4, motiontarget.JointTurns5, motiontarget.JointTurns6)
    # t = ", 0, 0, 0\',"
  #else:
  #  t = ", 0, 0, 0\',"
  return c + t


def doWriteTargetDefinition(controller,mod,statement):
  global motiontarget, pointCount, num_of_groups, groupmask, extaxisunit
  pointCount += 1
  sn = statement.Name
  c = GetConfigs(motiontarget)
  uf = GetBaseIndex(controller,motiontarget)
  ut = GetToolIndex(controller,motiontarget)
  mod.write("P[%i]{ \n" % pointCount )
  mod.write("    GP1:\n" )
  mod.write("         UF : %i, UT : %i," % (uf, ut) )
  if motiontarget.MotionType == VC_MOTIONTARGET_MT_JOINT and uf == 0:
    mod.write("\n" )
    j = motiontarget.JointValues
    mod.write("         J1= %8.2f deg,     J2= %8.2f deg,     J3= %8.2f deg,\n" % (j[0],j[1],j[2]))
    mod.write("         J4= %8.2f deg,     J5= %8.2f deg,     J6= %8.2f deg" % (j[3],j[4],j[5]))
  else:
    p = motiontarget.Target.P
    a = motiontarget.Target.getWPR()
    mod.write("              CONFIG : %s\n" % c )
    mod.write("         X = %8.2f  mm,     Y = %8.2f  mm,     Z = %8.2f  mm,\n" % (p.X,p.Y,p.Z))
    mod.write("         W = %8.2f deg,     P = %8.2f deg,     R = %8.2f deg" % (a.X,a.Y,a.Z))
  externalAxes = len(motiontarget.JointValues)-6
  if externalAxes > 0 and num_of_groups>0:
    if num_of_groups==1:
      mod.write(",\n    ")
      for j in range(externalAxes):
        if j > 0:
          mod.write(",")
          if j%3 == 0:
            mod.write("\n      ")
        mod.write("     E%i = %8.2f %s" % (j+1,motiontarget.JointValues[6+j],extaxisunit[j]) )
    else:
      for groupnum in range(2,6):
        if groupmask[groupnum-1]=="1":
          mod.write("\n    GP%i:\n" % groupnum)
          mod.write("         UF : %i, UT : %i,\n" % (uf, ut) )
          
          jcount=0
          for j in range(externalAxes):
            if groupnum==defaults["ExtAxisGroup"+str(j+1)]:
              if jcount > 0:
                mod.write(",")
                if jcount%3 == 0:
                  mod.write("\n     ")
              mod.write("         J%i = %8.2f %s" % (jcount+1,motiontarget.JointValues[6+j],extaxisunit[j]) )
              jcount+=1
  mod.write("\n")
  mod.write("};\n" )


def WriteTargetDefinition(controller,mod,statement):
  global motiontarget
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    statement.writeToTarget(motiontarget)
    doWriteTargetDefinition(controller,mod,statement)


def GetStatementCount( routine ):
  sc = 0
  for statement in routine.Statements:
    sc += 1
  return sc


def WriteStatement(mod,statement):
  global motiontarget,statementCount,pointCount
  #Add missing property for positioning path
  #if (statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION) and statement.getProperty("PosPath")==None:
  #  addProperty(statement, VC_STRING, "PosPath",True,False,False,defaultparams.PosPath,None,"")
  statementCount += 1
  mod.write("%4i:" % statementCount)
  if statement.Type == VC_STATEMENT_CALL:
    mod.write("  CALL %s ;\n" % statement.getProperty("Routine").Value.Name )

  elif statement.Type == VC_STATEMENT_COMMENT:
    c = statement.Comment
    mod.write("  !%s;\n" % (c))
      
  elif statement.Type == VC_STATEMENT_DELAY:
    d = statement.Delay
    mod.write("  WAIT %6.2f(sec) ;\n" % (d))

  elif statement.Type == VC_STATEMENT_HALT:
    mod.write("  PAUSE ;\n")

  elif statement.Type == VC_STATEMENT_LINMOTION:
    statement.writeToTarget(motiontarget)
    pointCount += 1
    mod.write("L P[%i: %s]  %gmm/sec %s    ;\n" % (pointCount, statement.Positions[0].Name, statement.MaxSpeed, defaults['PosPath']))

  elif statement.Type == VC_STATEMENT_PTPMOTION:
    statement.writeToTarget(motiontarget)
    pointCount += 1
    mod.write("J P[%i: %s]  %g%% %s    ;\n" % (pointCount, statement.Positions[0].Name, statement.JointSpeed,defaults['PosPath']))

  elif statement.Type == VC_STATEMENT_SETBIN:
    mod.write("  DO[%i: %s]= " %(statement.OutputPort, statement.Name))
    if statement.OutputValue:
      mod.write("ON ;\n" )
    else:
      mod.write("OFF ;\n" )

  elif statement.Type == VC_STATEMENT_WAITBIN:
    mod.write("  WAIT DI[%i: %s]= " %(statement.InputPort, statement.Name))
    if statement.InputValue:
      mod.write("ON ;\n" )
    else:
      mod.write("OFF ;\n" )

  elif statement.Type == VC_STATEMENT_DEFINE_BASE:
    name = statement.Base.Name
    m = vcMatrix.new(statement.Position)
    motiontarget.BaseName = name
    if statement.IsRelative == 1:
      m = motiontarget.BaseMatrix * m
    p = m.P
    a = m.getWPR()
    mod.write("    !DEFINE BASE ;\n")

  elif statement.Type == VC_STATEMENT_DEFINE_TOOL:
    name = statement.Tool.Name
    m = vcMatrix.new(statement.Position)
    motiontarget.ToolName = name
    if statement.IsRelative == 1:
      m = motiontarget.ToolMatrix * m
    p = m.P
    a = m.getWPR()
    mod.write("    !DEFINE TOOL ;\n")

  elif statement.Type == VC_STATEMENT_PROG_SYNC:
    mod.write("    !PROGSYNC ;\n")
  else:
    mod.write("    ;\n")


def WriteProgramBody(controller, routine, name, filename ):
  global statementCount, pointCount, num_of_groups, groupmask

  try:
    mod = open(filename,"w")
  except:
    print "Cannot open file \'%s\' for writing" % filename
    return False
  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  mod.write("/PROG %s\n" % name )
  mod.write("/ATTR\n")
  mod.write("OWNER = MNEDITOR;\n")
  mod.write("COMMENT = \"RSL generated Program\";\n")
  mod.write("PROG_SIZE = 64000;\n")
  mod.write("CREATE = %s;\n" % td)
  mod.write("MODIFIED = %s;\n" % td)
  mod.write("FILE_NAME = %s;\n" % name )
  mod.write("VERSION = 0;\n")
  mod.write("LINE_COUNT = %i;\n" % GetStatementCount( routine ) )
  mod.write("MEMORY_SIZE = 64000;\n")
  mod.write("PROTECT = READ_WRITE;\n")
  mod.write("TCD: STACK_SIZE = 0,\n")
  mod.write("     TASK_PRIORITY = 50,\n")
  mod.write("     TIME_SLICE = 0,\n")
  mod.write("     BUSY_LAMP_OFF = 0,\n")
  mod.write("     ABORT_REQUEST = 0,\n")
  mod.write("     PAUSE_REQUEST = 0;\n")
  #group definitions
  #print first group (always 1)
  mod.write("DEFAULT_GROUP = 1")
  groupmask=["*","*","*","*","*"]
  #loop through all external axis group definitions and set the the group mask
  for axisindex in range(1,21):
    groupindex=defaults["ExtAxisGroup"+str(axisindex)]
    if groupindex>0:
      groupmask[groupindex-1]="1"
  #print group masks 2-4 
  for i in range(1,5):
    mod.write(","+groupmask[i])
  mod.write(";\n")
  num_of_groups=groupmask.count("1")
  mod.write("CONTROL_CODE = 00000000 00000000;\n")
  # main routine
  mod.write("/MN\n")
  pointCount = 0
  statementCount = 0
  for statement in routine.Statements:
    WriteStatement(mod,statement)
  # collect all position definitions
  mod.write("/POS\n")
  pointCount = 0
  for statement in routine.Statements:
    WriteTargetDefinition(controller,mod,statement)
  mod.write("/END\n")
  mod.close
  return True

#-------------------------------------------------------------------------------
def postProcess(app,program,uri):
  global motiontarget,defaultparams,extaxisunit
  controller = program.Executor.Controller
  motiontarget = controller.createTarget()
  head, tail = os.path.split(uri)
  mainName = tail[:len(tail)-3]
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
  motiontarget = controller.createTarget()
  filenamelist=[]
  # main routine
  filenamelist.append(uri)
  if not WriteProgramBody(controller, program.MainRoutine, mainName, uri  ):
    return False,filenamelist
  # subroutines
  for routine in program.Routines:
    filename = head + "\\" + routine.Name + ".ls"
    filenamelist.append(filename)
    if not WriteProgramBody(controller, routine, routine.Name,  filename ):
      return False,filenamelist
  return True,filenamelist

