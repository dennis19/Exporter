#-------------------------------------------------------------------------------
# Copyright 2016 Visual Components Ltd. All rights reserved.
#-------------------------------------------------------------------------------
from vcCommand import *
import vcMatrix, os


def postProcess(app,program,uri):
  global bases, tools, loads, writeStatement, motiontarget
  motiontarget = program.Executor.Controller.createTarget()
  modulename = os.path.basename(uri)
  modulename = modulename[:len(modulename)-4]
  with open(uri,"wb") as output_file:
    # We should have properties for defining loads (needs standarisation)
    loads = getLoads(program)
    # Collect all statements from all scopes to one flat list to simplify collecting data
    allstatements = getAllStatements(program)
    # Function dictionary organized by statement type
    writeStatement = getAllStatementWriters()
    # Start writing
    indentation = 4
    # standard header for all RAPID modules
    output_file.write("%%%\n")
    output_file.write("VERSION: 1\n")
    output_file.write("LANGUAGE: ENGLISH\n")
    output_file.write("%%%\n\n")
    output_file.write("MODULE %s\n\n" % modulename)
    # Bases
    bases = []
    for statement in allstatements:
      writeBaseDefinition(output_file,statement,indentation)
    output_file.write("\n")
    # Tools
    tools = []
    for statement in allstatements:
      writeToolDefinition(output_file,statement,indentation)
    output_file.write("\n")
    # Targets
    for statement in allstatements:
      writeTargetDefinition(output_file,statement,indentation)
    output_file.write("\n")
    # Main
    output_file.write("  PROC main()\n")
    for statement in program.MainRoutine.Statements:
      writeStatement[statement.Type](output_file,statement,indentation)
    output_file.write("  ENDPROC\n\n")
    # Other routines    
    for routine in program.Routines:
      output_file.write("  PROC %s()\n" % routine.Name)
      for statement in routine.Statements:
        writeStatement[statement.Type](output_file,statement,indentation)
      output_file.write("  ENDPROC\n\n")
    output_file.write("ENDMODULE\n")
    output_file.close()
    return True, [uri]
  return False, [uri]


def getAllStatements(program):
  allstatements = []
  for s in program.MainRoutine.Statements:
    allstatements = extendStatements(s,allstatements)
  for routine in program.Routines:
    for s in routine.Statements:
      allstatements = extendStatements(s,allstatements)
  return allstatements


def extendStatements(statement,statements):
  statements.append(statement)
  if statement.Type == VC_STATEMENT_WHILE:
    for s in statement.Scope.Statements:
      statements = extendStatements(s,statements)
  elif statement.Type == VC_STATEMENT_IF:
    for s in statement.ThenScope.Statements:
      statements = extendStatements(s,statements)
    for s in statement.ElseScope.Statements:
      statements = extendStatements(s,statements)
  return statements


def getLoads(program):
  # this example reads a note containing information, but this should be changed
  loads = []
  loadnote = program.Executor.Component.findBehaviour("Loads")
  if loadnote != None:
    lines = loadnote.Note.split('\n',1000)
    #tool1;[1,[0,0,0.001],[1,0,0,0],0,0,0]
    #tool2;[2,[0,0,0.001],[1,0,0,0],0,0,0]
    if lines != None:
      for pline in lines:
        if len(pline) < 1:
          break
        line = string.strip(pline,"\n\r")
        columns = line.split(';',20)
        loads.append(columns)
  return loads


def getToolLoad(toolname):
  global loads
  i = 0
  for tn, load in loads:
    if toolname==tn:
      return load
    i = i + 1
  return "[5,[0,0,0.001],[1,0,0,0],0,0,0]"

 
def getSpeedName(js):
  if js >= 5000:     return "vmax"
  elif js >= 4000:  return "v4000"
  elif js >= 3000:  return "v3000"
  elif js >= 2500:  return "v2500"
  elif js >= 2000:  return "v2000"
  elif js >= 1500:  return "v1500"
  elif js >= 1000:  return "v1000"
  elif js >= 800:    return "v800"
  elif js >= 600:    return "v600"
  elif js >= 500:    return "v500"
  elif js >= 400:    return "v400"
  elif js >= 300:    return "v300"
  elif js >= 200:    return "v200"
  elif js >= 150:    return "v150"
  elif js >= 100:    return "v100"
  elif js >= 80:     return "v80"
  elif js >= 60:     return "v60"
  elif js >= 50:     return "v50"
  elif js >= 40:     return "v40"
  elif js >= 30:     return "v30"
  elif js >= 20:     return "v20"
  elif js >= 10:     return "v10"
  else:                  return "v5"


def getConfigs(motiontarget):
  joints = motiontarget.JointValues
  cfx = motiontarget.RobotConfig
  conf1=int(joints[0]/90.0)
  if joints[0]<0.0:
    conf1-=1
  conf4=int(joints[3]/90.0)
  if joints[0]<0.0:
    conf4-=1
  conf6=int(joints[5]/90.0)
  if joints[0]<0.0:
    conf6-=1
  return [conf1,conf4,conf6,cfx]


def getZone(motiontarget):
  if motiontarget.AccuracyMethod == VC_MOTIONTARGET_AM_DISTANCE:
    av = motiontarget.AccuracyValue
  if motiontarget.AccuracyMethod == VC_MOTIONTARGET_AM_TIME:
    av = motiontarget.CartesianSpeed * motiontarget.AccuracyValue
  if motiontarget.AccuracyMethod == VC_MOTIONTARGET_AM_VELOCITY:
    # gets complicated; let's cut the corners..
    av = motiontarget.AccuracyValue
  if av >= 200:    return "z200"
  elif av >= 150: return "z150"
  elif av >= 100: return "z100"
  elif av >= 80:   return "z80"
  elif av >= 60:   return "z60"
  elif av >= 50:   return "z50"
  elif av >= 40:   return "z40"
  elif av >= 30:   return "z30"
  elif av >= 20:   return "z20"
  elif av >= 15:   return "z15"
  elif av >= 10:   return "z10"
  elif av >= 5:     return "z5"
  elif av >= 1:     return "z1"
  elif av >= 0.3:  return "z0"
  else:                return "fine"


def getExternalJointValues(motiontarget):
  e = [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]
  i = 0
  for jointvalue in motiontarget.JointValues:
    if i > 5 and i < 12:
      e[i-6] = jointvalue
    i = i + 1
  return e


def writeBaseDefinition(output_file,statement,indentation):
  global motiontarget, bases
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    statement.writeToTarget(motiontarget)
    if motiontarget.BaseName != "" and motiontarget.BaseName not in bases:
      p = motiontarget.BaseMatrix.P
      q = motiontarget.BaseMatrix.getQuaternion()
      output_file.write("  PERS wobjdata %s:=[FALSE,TRUE,\"\",[[%g,%g,%g],[%g,%g,%g,%g]],[[0,0,0],[1,0,0,0]]];\n" %(motiontarget.BaseName,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W))
      bases.append(motiontarget.BaseName)


def writeToolDefinition(output_file,statement,indentation):
  global motiontarget, tools
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    statement.writeToTarget(motiontarget)
    if motiontarget.ToolName != "" and motiontarget.ToolName not in tools:
      p = motiontarget.ToolMatrix.P
      q = motiontarget.ToolMatrix.getQuaternion()
      w = 5.0
      load = getToolLoad(motiontarget.ToolName)
      output_file.write("  PERS tooldata %s:=[TRUE,[[%g,%g,%g],[%g,%g,%g,%g]],%s];\n" %(motiontarget.ToolName,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,load))
      tools.append(motiontarget.ToolName)


def writeTargetDefinition(output_file,statement,indentation):
  global motiontarget
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    sn = statement.Positions[0].Name
    statement.writeToTarget(motiontarget)
    p = motiontarget.Target.P
    q = motiontarget.Target.getQuaternion()
    c = getConfigs(motiontarget)
    e = getExternalJointValues(motiontarget)
    output_file.write("  PERS robtarget %s:=[[%g,%g,%g],[%g,%g,%g,%g],[%i,%i,%i,%i],[%g,%g,%g,%g,%g,%g]];\n" % (sn,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,c[0],c[1],c[2],c[3],e[0],e[1],e[2],e[3],e[4],e[5]))


def writeBreak(output_file,statement,indentation):
  output_file.write(" "*indentation+"Break;\n")


def writeCall(output_file,statement,indentation):
  output_file.write(" "*indentation+"%s;\n" % statement.getProperty("Routine").Value.Name)


def writeComment(output_file,statement,indentation):
  output_file.write(" "*indentation+"!%s\n" % (statement.Comment))


def writeDefineBase(output_file,statement,indentation):
  name = statement.Base.Name
  m = vcMatrix.new(statement.Position)
  motiontarget.BaseName = name
  if statement.IsRelative:
    m = motiontarget.BaseMatrix * m
  p = m.P
  q = m.getQuaternion()
  output_file.write(" "*indentation+"%s:=[FALSE,TRUE,\"\",[[%g,%g,%g],[%g,%g,%g,%g]],[[0,0,0],[1,0,0,0]]];\n" %(name,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W))


def writeDefineTool(output_file,statement,indentation):
  name = statement.Tool.Name
  m = vcMatrix.new(statement.Position)
  motiontarget.ToolName = name
  if statement.IsRelative:
    m = motiontarget.ToolMatrix * m
  p = m.P
  q = m.getQuaternion()
  load = getToolLoad(name)
  output_file.write(" "*indentation+"%s:=[TRUE,[[%g,%g,%g],[%g,%g,%g,%g]],%s];\n" %(name,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,load))


def writeDelay(output_file,statement,indentation):
  output_file.write(" "*indentation+"WaitTime %g;\n" % (statement.Delay))


def writeHalt(output_file,statement,indentation):
  output_file.write(" "*indentation+"Stop;\n")


def writeIf(output_file,statement,indentation):
  cnd = statement.Condition.strip()
  output_file.write(" "*indentation+"IF %s THEN\n" %(cnd))
  indentation += 2
  for s in statement.ThenScope.Statements:
    writeStatement[s.Type](output_file,s,indentation)
  indentation -= 2
  output_file.write(" "*indentation+"ELSE\n")
  indentation += 2
  for s in statement.ElseScope.Statements:
    writeStatement[s.Type](output_file,s,indentation)
  indentation -= 2
  output_file.write(" "*indentation+"ENDIF\n")


def writeLinMotion(output_file,statement,indentation):
  statement.writeToTarget(motiontarget)
  #MoveL Target1,v1000,fine,tool0\WObj:=wobj0;
  sp = getSpeedName(statement.MaxSpeed)
  zone = getZone(motiontarget)
  if motiontarget.ToolName == "":
    tn = "tool0"
  else:
    tn = motiontarget.ToolName
  if motiontarget.BaseName == "":
    bn = "wobj0"
  else:
    bn = motiontarget.BaseName
  output_file.write(" "*indentation+"MoveL %s,%s,%s,%s\WObj:=%s;\n" % (statement.Positions[0].Name,sp,zone,tn,bn))


def writePtpMotion(output_file,statement,indentation):
  global motiontarget
  statement.writeToTarget(motiontarget)
  #MoveJ Target1,v1000,fine,tool0\WObj:=wobj0;
  sp = getSpeedName(motiontarget.CartesianSpeed)
  zone = getZone(motiontarget)
  if motiontarget.ToolName == "":
    tn = "tool0"
  else:
    tn = motiontarget.ToolName
  if motiontarget.BaseName == "":
    bn = "wobj0"
  else:
    bn = motiontarget.BaseName
  output_file.write(" "*indentation+"MoveJ %s,%s,%s,%s\WObj:=%s;\n" % (statement.Positions[0].Name,sp,zone,tn,bn))


def writePrint(output_file,statement,indentation):
  output_file.write(" "*indentation+"TPWrite \"%s\"\n" % (statement.Message))


def writeReturn(output_file,statement,indentation):
  output_file.write(" "*indentation+"RETURN;\n")


def writeSetBin(output_file,statement,indentation):
  output_file.write(" "*indentation+"SetDO do%i,%i;\n" %(statement.OutputPort,statement.OutputValue))


def writeSetProperty(output_file,statement,indentation):
  ve = statement.ValueExpression.strip()
  output_file.write(" "*indentation+"%s := %s;\n" %(statement.TargetProperty,ve))


def writeWaitBin(output_file,statement,indentation):
  output_file.write(" "*indentation+"WaitDI di%i,%i;\n" %(statement.InputPort,statement.InputValue))


def writeWhile(output_file,statement,indentation):
  cnd = statement.Condition.strip()
  output_file.write(" "*indentation+"WHILE %s DO\n" %(cnd))
  indentation += 2
  for s in statement.Scope.Statements:
    writeStatement[s.Type](output_file,s,indentation)
  indentation -= 2
  output_file.write(" "*indentation+"ENDWHILE\n")


def writePath(output_file,statement,indentation):
  global motiontarget
  output_file.write(" "*indentation+"! Move along path %s\n" % (statement.Name))
  motiontarget.JointTurnMode = VC_MOTIONTARGET_TURN_NEAREST
  motiontarget.TargetMode = VC_MOTIONTARGET_TM_NORMAL
  motiontarget.MotionType = VC_MOTIONTARGET_MT_LINEAR    
  if statement.Base == None:
    motiontarget.BaseName = ""
  else:
    motiontarget.BaseName = statement.Base.Name
  if statement.Tool == None:
    motiontarget.ToolName = ""
  else:
    motiontarget.ToolName = statement.Tool.Name
  ej = statement.ExternalJointCount    
  for i in range( statement.getSchemaSize()):
    target = statement.getSchemaValue(i,"Position")
    motiontarget.Target = target
    jv = motiontarget.JointValues
    for j in range(ej):
      jv[6+j] = stat.getSchemaValue(j,"E%d" % (j+1))
    motiontarget.JointValues = jv
    #motiontarget.Target = target
    motiontarget.AccuracyMethod = statement.getSchemaValue(i,"AccuracyMethod")
    motiontarget.AccuracyValue = statement.getSchemaValue(i,"AccuracyValue")
    sp = getSpeedName(statement.getSchemaValue(i,"MaxSpeed"))
    zone = getZone(motiontarget)
    if motiontarget.ToolName == "":
      tn = "tool0"
    else:
      tn = motiontarget.ToolName
    if motiontarget.BaseName == "":
      bn = "wobj0"
    else:
      bn = motiontarget.BaseName
    p = motiontarget.Target.P
    q = motiontarget.Target.getQuaternion()
    c = getConfigs(motiontarget)
    e = getExternalJointValues(motiontarget)
    output_file.write(" "*indentation+"MoveL [[%g,%g,%g],[%g,%g,%g,%g],[%i,%i,%i,%i],[%g,%g,%g,%g,%g,%g]],%s,%s,%s\WObj:=%s;\n" % (p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,c[0],c[1],c[2],c[3],e[0],e[1],e[2],e[3],e[4],e[5],sp,zone,tn,bn))
  output_file.write(" "*indentation+"! End of path %s\n" % (statement.Name))
    

def unhandled(output_file,statement,indentation):
  print "Unhandled statement : %s %s" % (statement.Name,statement.Type)


def getAllStatementWriters():
  statementhandlers = {
VC_STATEMENT_BREAK:writeBreak,
VC_STATEMENT_CALL:writeCall,
VC_STATEMENT_COMMENT:writeComment,
VC_STATEMENT_DEFINE_BASE:writeDefineBase,
VC_STATEMENT_DEFINE_TOOL:writeDefineTool,
VC_STATEMENT_DELAY:writeDelay,
VC_STATEMENT_HALT:writeHalt,
VC_STATEMENT_IF:writeIf,
VC_STATEMENT_LINMOTION:writeLinMotion,
VC_STATEMENT_PRINT:writePrint,
VC_STATEMENT_PTPMOTION:writePtpMotion,
VC_STATEMENT_RETURN:writeReturn,
VC_STATEMENT_SETBIN:writeSetBin,
VC_STATEMENT_SETPROPERTY:writeSetProperty,
VC_STATEMENT_WAITBIN:writeWaitBin,
VC_STATEMENT_WHILE:writeWhile,
VC_STATEMENT_CONTINUE:unhandled,
VC_STATEMENT_CUSTOM:unhandled,
VC_STATEMENT_GRASP:unhandled,
VC_STATEMENT_HOME:unhandled,
VC_STATEMENT_PROG_SYNC:unhandled,
VC_STATEMENT_RELEASE:unhandled,
VC_STATEMENT_REMOTECALL:unhandled,
VC_STATEMENT_REMOTEWAIT:unhandled,
VC_STATEMENT_PATH:writePath
}
  return statementhandlers


