from vcCommand import *
import time
import re
#-------------------------------------------------------------------------------
app = getApplication()

def getActiveRoutine():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine
  else: 
    print 'please select routine'
  return routine
  
def getAllStatements(routine):
  allstatements = []
  for s in routine.Statements:
    allstatements = extendStatements(s, allstatements)
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

def OnStart():
  global controller
  global text, statementCount, routine, uframe_num, utool_num, label, motiontarget, bases, tools, writestatement, loads

  routine = getActiveRoutine()
  if not routine:
    app.messageBox("No Routine selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif

  if routine.Name == 'PositionRegister': return

  print 'Converting %s to Mod' % routine.Name

  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller
  loads = getLoads(program)
  rname = routine.Name
  
  for statement in routine.Statements:
    if statement.Type==VC_STATEMENT_COMMENT:
      notename=statement.Comment
      break  

  
  motiontarget = controller.createTarget()
  bases = []
  tools = []
  # Function dictionary organized by statement type
  writestatement = getAllStatementWriters()
  note =  comp.findBehaviour( notename )
  if not note:
    note = comp.createBehaviour( VC_NOTE, notename )
  prev_note=None	
  #endif

  comp.createProperty(VC_BOOLEAN,"%s::SkipExecution"%rname)

  if routine== program.MainRoutine:
    for routines in program.Routines:
      for statement in routines.Statements:
        if statement.Type==VC_STATEMENT_COMMENT:
          notename=statement.Comment
          if comp.findBehaviour( notename ):
            comp.findBehaviour( notename ).delete()
          break

	
 #maybe include header

  mainroutine = comp.getProperty('MainRoutine')
  if mainroutine:
    stepValues = mainroutine.StepValues
    if rname not in stepValues:
      stepValues.append(rname)
      mainroutine.StepValues = stepValues
    #endif
  #endif

  label = 1
  uframe_num = -1
  utool_num = -1
  statementCount = 1
  indentation = 4
  ##for statement in getAllStatements(routine):
  allstatements= getAllStatements(program)
  line=""
  
      # Bases
  for statement in allstatements:
    line=writeBaseDefinition(statement,indentation,line)
    # Tools	
  for statement in allstatements:
    line=writeToolDefinition(statement,indentation,line)
    # Targets
  for statement in allstatements:
    line=writeTargetDefinition(statement,indentation,line)
  
  line+= "\n PROC %s()\n" %routine.Name
  for statement in program.MainRoutine.Statements:	
    line=writestatement[statement.Type](statement,indentation,line)
  line+= "ENDPROC\n\n"
  note.Note=line	
  line=""
  

  
  
  for routineiter in program.Routines:
    
    for statement in routineiter.Statements:
      if statement.Type==VC_STATEMENT_COMMENT:
        note_name=statement.Comment
        break
    note=comp.findBehaviour( note_name )
    if not note:
      note = comp.createBehaviour( VC_NOTE, note_name )
    
    line+= "PROC %s()\n" %routineiter.Name
    
    for statement in routineiter.Statements:
      line=writestatement[statement.Type](statement,indentation,line)
    
    line+= "ENDPROC\n\n"  
    note.Note += line
    line=""


def writeLineABB(line_data_):

  #line= "%4i:  " % state_count_
  line=""
  if line_data_[0]=="Call":

    line+=writeCall(line_data_[1])

  elif line_data_[0]=="WaitTime":
    line +=writeDelay(line_data_[1])

  elif line_data_[0]=="Comment":
    line+=writeComment(line_data_[1])


  elif line_data_[0]=="SetOutput":
    line+=writeSetOutput(line_data_[1])

    #endif

  elif line_data_[0]=="Wait":
    line+=writeWAIT(line_data_[1])

  elif line_data_[0]=="Movement":
    line+=writeMotion(line_data_[1])

  elif line_data_[0]=="SetVariable":
    line += writeSetVariable(line_data_[1])

  elif line_data_[0]=="If":
    line+=writeIf(line_data_[1])
  elif line_data_[0]=="Message":
    line+=writeMessage(line_data_[1])

  elif line_data_[0]=="Label":
    line+=writeLabel(line_data_[1])

  elif line_data_[0]=="Jump":
    line+=writeJMP(line_data_[1])
  elif line_data_[0]=="Return":
    line+=writeReturn(line_data_[1])
  else:
    print "Statement %s not translated" %line_data_[0]
  #line+=";\n"
  #statement_count_=state_count_
  #statement_count_+=1
  print "line %s" %line
  return line

def writeMotion(motion_data_):
  #statement.writeToTarget(motiontarget)
  #MoveL Target1,v1000,fine,tool0\WObj:=wobj0;
  if motion_data_[2]=="joint":
    line=" "*4+"MoveJ "
    sp = int(motion_data_[6])*1000
  elif motion_data_[2]=="lin":
    line =" "*4+ "MoveL "
    sp = int(motion_data_[6])
  zone = "fine"
  bn=motion_data_[0]
  tn = motion_data_[1]
  name=motion_data_[5]
  line+="%s, v%s, %s, %s\WObj:=%s;\n" % (name,sp,zone,tn,bn)
  return line
  #endif
  # line+="\n;"
  #statementCount += 1
  #text += line
  #return line

  # print "line_data_ %s" %line_data_
  # return line

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
  
def writeBaseDefinition(statement,indentation,line):
  global motiontarget, bases
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    statement.writeToTarget(motiontarget)
    if motiontarget.BaseName != "" and motiontarget.BaseName not in bases:
      p = motiontarget.BaseMatrix.P
      q = motiontarget.BaseMatrix.getQuaternion()
      line+= "  PERS wobjdata %s:=[FALSE,TRUE,\"\",[[%g,%g,%g],[%g,%g,%g,%g]],[[0,0,0],[1,0,0,0]]];\n" %(motiontarget.BaseName,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W)
      bases.append(motiontarget.BaseName)
  return line

def writeToolDefinition(statement,indentation,line):
  global motiontarget, tools
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    statement.writeToTarget(motiontarget)
    if motiontarget.ToolName != "" and motiontarget.ToolName not in tools:
      p = motiontarget.ToolMatrix.P
      q = motiontarget.ToolMatrix.getQuaternion()
      w = 5.0
      load = getToolLoad(motiontarget.ToolName)
      line+="  PERS tooldata %s:=[TRUE,[[%g,%g,%g],[%g,%g,%g,%g]],%s];\n" %(motiontarget.ToolName,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,load)
      tools.append(motiontarget.ToolName)
  return line

def writeTargetDefinition(statement,indentation,line):
  global motiontarget
  if statement.Type == VC_STATEMENT_LINMOTION or statement.Type == VC_STATEMENT_PTPMOTION:
    sn = statement.Positions[0].Name
    statement.writeToTarget(motiontarget)
    p = motiontarget.Target.P
    q = motiontarget.Target.getQuaternion()
    c = getConfigs(motiontarget)
    e = getExternalJointValues(motiontarget)
    line+= "  PERS robtarget %s:=[[%g,%g,%g],[%g,%g,%g,%g],[%i,%i,%i,%i],[%g,%g,%g,%g,%g,%g]];\n" % (sn,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,c[0],c[1],c[2],c[3],e[0],e[1],e[2],e[3],e[4],e[5])
  return line

def writeBreak(statement,indentation,line):
  line= " "*indentation+"BREAK;\n"
  return line 
  #output_file.write(" "*indentation+"Break;\n")


def writeCall(call_data_):
  line= " "*4+"%s " % call_data_[0]
  if not call_data_[1]=="":
    line+='"%s" ' %call_data_[1]
    if not call_data_[2] == "":
      line += ',"%s"' % call_data_[2]
  line+=";\n"
  return line 
  #output_file.write(" "*indentation+"%s;\n" % statement.getProperty("Routine").Value.Name)


def writeComment(comment_data_):
  line= " "*4+"!%s\n" % (comment_data_)
  return line 
  #output_file.write(" "*indentation+"!%s\n" % (statement.Comment))

def writeLabel(label_data_):
  return " "*4+str(label_data_[0])+label_data_[1]+ ":\n"

def writeJMP(jump_data_):
  return " "*4+"GOTO "+str(jump_data_)+" ;\n"

def writeDefineBase(statement,indentation,line):
  name = statement.Base.Name
  m = vcMatrix.new(statement.Position)
  motiontarget.BaseName = name
  if statement.IsRelative:
    m = motiontarget.BaseMatrix * m
  p = m.P
  q = m.getQuaternion()
  line+= " "*indentation+"%s:=[FALSE,TRUE,\"\",[[%g,%g,%g],[%g,%g,%g,%g]],[[0,0,0],[1,0,0,0]]];\n" %(name,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W)
  return line 
  #output_file.write(" "*indentation+"%s:=[FALSE,TRUE,\"\",[[%g,%g,%g],[%g,%g,%g,%g]],[[0,0,0],[1,0,0,0]]];\n" %(name,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W))


def writeDefineTool(statement,indentation,line):
  name = statement.Tool.Name
  m = vcMatrix.new(statement.Position)
  motiontarget.ToolName = name
  if statement.IsRelative:
    m = motiontarget.ToolMatrix * m
  p = m.P
  q = m.getQuaternion()
  load = getToolLoad(name)
  line+=" "*indentation+"%s:=[TRUE,[[%g,%g,%g],[%g,%g,%g,%g]],%s];\n" %(name,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,load)
  return line 
  #output_file.write(" "*indentation+"%s:=[TRUE,[[%g,%g,%g],[%g,%g,%g,%g]],%s];\n" %(name,p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,load))


def writeDelay(delay_data_):
  line=" "*4+"WaitTime %g;\n" % (delay_data_)
  return line 
  #output_file.write(" "*indentation+"WaitTime %g;\n" % (statement.Delay))


def writeHalt(statement,indentation):
  line=" "*indentation+"Stop;\n"
  return line 
  #output_file.write(" "*indentation+"Stop;\n")


def writeIf(if_data_):
  indentation=4
  line = " "*indentation+"IF "+if_data_[0]+" THEN\n"
  indentation+=2
  for data_ in if_data_[1]:

    line+=" "*indentation+writeLineABB(data_)
  indentation-=2
  if not if_data_[2]==[]:

    line +=" "*indentation+ "ELSE\n"
    indentation+=2
    for data_ in if_data_[2]:

      line+=" "*indentation+writeLineABB(data_)
    indentation-=2
  print " indentaion %s" %indentation
  line+=" "*indentation+"     ENDIF\n"
  #state_count_ += 1
  # cnd = statement.Condition.strip()
  # ifcondregex ="(?P<cond>[a-zA-Z0-9_]+)(?P<equal>[^a-zA-Z0-9_]+)(?P<value>[a-zA-Z0-9_]+)"
  # conddef=re.search(ifcondregex,cnd)
  # if conddef.group('equal')== "==":
  #   equal = "="
  # cond=conddef.group('cond')+equal+conddef.group('value')
  # line += " "*indentation+"IF %s THEN\n" %(cond)
  # #output_file.write(" "*indentation+"IF %s THEN\n" %(cnd))
  # indentation += 2
  # for s in statement.ThenScope.Statements:
  #   line=writestatement[s.Type](s,indentation,line)
  # indentation -= 2
  # line+=" "*indentation+"ELSE\n"
  # #output_file.write(" "*indentation+"ELSE\n")
  # indentation += 2
  # for s in statement.ElseScope.Statements:
  #   line=writestatement[s.Type](s,indentation,line)
  # indentation -= 2
  # line+=" "*indentation+"ENDIF\n"
  # return line
  #output_file.write(" "*indentation+"ENDIF\n")
  return line


def writeLinMotion(statement,indentation,line):
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
  line+=" "*indentation+"MoveL %s,%s,%s,%s\WObj:=%s;\n" % (statement.Positions[0].Name,sp,zone,tn,bn)
  return line 
  #output_file.write(" "*indentation+"MoveL %s,%s,%s,%s\WObj:=%s;\n" % (statement.Positions[0].Name,sp,zone,tn,bn))

def writeMessage(mess_data_):
  return " "*4+'TPWrite '+mess_data_+'";\n'

def writePtpMotion(statement,indentation,line):
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
  line+=" "*indentation+"MoveJ %s,%s,%s,%s\WObj:=%s;\n" % (statement.Positions[0].Name,sp,zone,tn,bn)
  return line


def writePrint(statement,indentation,line):
  line+=" "*indentation+"TPWrite \"%s\"\n" % (statement.Message)
  return line 
  #output_file.write(" "*indentation+"TPWrite \"%s\"\n" % (statement.Message))


def writeReturn(statement,indentation,line):
  line+=" "*indentation+"RETURN;\n"
  return line 
  #output_file.write(" "*indentation+"RETURN;\n")

def writeSetOutput(set_out_data):
  # if statement.OutputPort < 1000:
  #   if not statement.Name=="":
  #     line = "DO[%i%s]=" % (statement.OutputPort, statement.Name)
  #   else:
  #     line = "DO[%i]=" % (statement.OutputPort)
  # else:
  #   line = "RO[%i: %s]=" % (statement.OutputPort - 1000, statement.Name)
  # # endif
  # if statement.OutputValue:
  #   line += "ON ;\n"
  # else:
  #   line += "OFF ;\n"

  line =" "*4+"SetDO %s,%s;\n" %(set_out_data[1],set_out_data[2])
  # if not set_out_data[1]=="":
  #   line+="%s" %set_out_data[1]
  # line+="=%s"%set_out_data[2]

  return line

def writeSetBin(statement,indentation,line):
  line+=" "*indentation+"SetDO do%i,%i;\n" %(statement.OutputPort,statement.OutputValue)
  return line 
  #output_file.write(" "*indentation+"SetDO do%i,%i;\n" %(statement.OutputPort,statement.OutputValue))


def writeSetProperty(statement,indentation,line):
  ve = statement.ValueExpression.strip()
  line+=" "*indentation+"%s := %s;\n" %(statement.TargetProperty,ve)
  return line 
  #output_file.write(" "*indentation+"%s := %s;\n" %(statement.TargetProperty,ve))

def writeSetVariable(set_var_data_):
  line=""
  if set_var_data_[0]:
    line=" "*4+set_var_data_[0]
    if set_var_data_[1]:
      line+='[%s' %set_var_data_[1]
      if set_var_data_[2]:
        line += ':%s' % set_var_data_[2]
      line+="]"
    line+="="
    line+=set_var_data_[3]
    if set_var_data_[4]:
      line+='[%s' %set_var_data_[4]
      if set_var_data_[5]:
        line += ':%s' % set_var_data_[5]
      line+="]"
    line+=";\n"
  return line

def writeWaitBin(statement,indentation,line):
  line+=" "*indentation+"WaitDI di%i,%i;\n" %(statement.InputPort,statement.InputValue)
  return line 
  #output_file.write(" "*indentation+"WaitDI di%i,%i;\n" %(statement.InputPort,statement.InputValue))


def writeWhile(statement,indentation,line):
  cnd = statement.Condition.strip()
  line+=" "*indentation+"WHILE %s DO\n" %(cnd)
  #output_file.write(" "*indentation+"WHILE %s DO\n" %(cnd))
  indentation += 2
  for s in statement.Scope.Statements:
    line=writestatement[s.Type](s,indentation,line)
  indentation -= 2
  line+=" "*indentation+"ENDWHILE\n"
  return line 
  #output_file.write(" "*indentation+"ENDWHILE\n")


def writePath(statement,indentation,line):
  global motiontarget
  #output_file.write(" "*indentation+"! Move along path %s\n" % (statement.Name))
  line+=" "*indentation+"! Move along path %s\n" % (statement.Name)
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
    line=" "*indentation+"MoveL [[%g,%g,%g],[%g,%g,%g,%g],[%i,%i,%i,%i],[%g,%g,%g,%g,%g,%g]],%s,%s,%s\WObj:=%s;\n" % (p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,c[0],c[1],c[2],c[3],e[0],e[1],e[2],e[3],e[4],e[5],sp,zone,tn,bn)
    #output_file.write(" "*indentation+"MoveL [[%g,%g,%g],[%g,%g,%g,%g],[%i,%i,%i,%i],[%g,%g,%g,%g,%g,%g]],%s,%s,%s\WObj:=%s;\n" % (p.X,p.Y,p.Z,q.X,q.Y,q.Z,q.W,c[0],c[1],c[2],c[3],e[0],e[1],e[2],e[3],e[4],e[5],sp,zone,tn,bn))
  line+=" "*indentation+"! End of path %s\n" % (statement.Name)
  return line 
  #output_file.write(" "*indentation+"! End of path %s\n" % (statement.Name))
    

def unhandled(statement,indentation,line):
  print "Unhandled statement : %s %s" % (statement.Name,statement.Type)	
	
def getToolLoad(toolname):
  global loads
  i = 0
  for tn, load in loads:
    if toolname==tn:
      return load
    i = i + 1
  return "[5,[0,0,0.001],[1,0,0,0],0,0,0]"
 
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
  
def getExternalJointValues(motiontarget):
  e = [9E+09,9E+09,9E+09,9E+09,9E+09,9E+09]
  i = 0
  for jointvalue in motiontarget.JointValues:
    if i > 5 and i < 12:
      e[i-6] = jointvalue
    i = i + 1
  return e

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
  
def writeStatement( statement ):
  global text, statementCount, uframe_num, utool_num, label, motiontarget, tools, bases, writestatement

  indentation = 4
  #line = "%4i:  " % statementCount 
  line = ""
  #if statement.Type == VC_STATEMENT_CALL:
    #line += "CALL %s;\n" % (statement.RoutineName)
  #Base Definition
  line+=writeBaseDefinition(statement,indentation)  
  
  #Tool Definition
  line+=writeToolDefinition(statement,indentation)
  
  #Robtarget Definition
  line+=writeTargetDefinition(statement,indentation)
	
  line+= "PROC %s()\n" %routine.Name
	
  line+=writestatement[statement.Type](statement,indentation)
	
  if statement.Type == VC_STATEMENT_DELAY:
    line += "WAIT %6.2f(sec) ;\n" % (statement.Delay)

  elif statement.Type == VC_STATEMENT_COMMENT:
    if statement.Comment[:2] == '++':
      line += "%s;\n" % (statement.Comment[2:])
    else:
      line += "!%s;\n" % (statement.Comment)

  elif statement.Type == VC_STATEMENT_SETBIN:
    if statement.OutputPort < 1000:
      line += "DO[%i: %s]=" %(statement.OutputPort, statement.Name)
    else:
      line += "RO[%i: %s]=" %(statement.OutputPort-1000, statement.Name)
    #endif
    if statement.OutputValue:
      line += "ON ;\n"
    else:
      line += "OFF ;\n"
    #endif

  elif statement.Type == VC_STATEMENT_WAITBIN:
    if statement.InputPort < 1000:
      line += "WAIT DI[%i: %s]=" %(statement.InputPort, statement.Name)
    else:
      line += "WAIT RI[%i: %s]=" %(statement.InputPort-1000, statement.Name)
    #endif
    if statement.InputValue:
      line += "ON ;\n" 
    else:
      line += "OFF ;\n"
    #endif

  elif statement.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
    if not statement.getProperty('INDEX'):
      indices = {}
      maxIndex = 0
      for s in routine.Statements:
        if s.getProperty('INDEX'):
          indices[s.INDEX] = True 
          if s.INDEX > maxIndex: maxIndex = s.INDEX
        #endif
      #endfor
      sName = statement.Positions[0].Name
      try:
        num = int(sName[sName.rindex('_')+1:])
      except:
        try:
          for i in range(len(sName)-1,-1,-1):
            if not sName[i:].isdigit():
              num = int(sName[i+1:]) 
              break
            #endif
          #endfor
        except:
          num = maxIndex + 1
        #endtry
      #endtry

      statement.createProperty( VC_INTEGER, 'INDEX' )

      statement.INDEX = num 
      if indices.get( num, False ):
        statement.INDEX = maxIndex + 1
        """
        for i in range( 1, routine.StatementCount+2):
          if not indices.get( num, False ):
            statement.INDEX = i
            break
          #endif
        #endfor
        """
      #endif
    #endif

    pointIndex = statement.INDEX

    bName = statement.Base
    for i, b in enumerate(controller.Bases):
      if b.Name == bName:
        uf = i+1
        break
      #endif
    else:
      uf = 0
    #endfor

    if uframe_num != uf:
      uframe_num = uf
      line += "UFRAME_NUM = %i ;\n" % (uf)
      statementCount += 1
      line += "%4i:  " % statementCount 
    #endif

    tName = statement.Tool
    for i, t in enumerate(controller.Tools):
      if t.Name == tName:
        ut = i+1
        break
      #endif
    else:
      ut = 0
    #endfor

    if utool_num != ut:
      utool_num = ut
      line += "UTOOL_NUM = %i ;\n" % (ut)
      statementCount += 1
      line += "%4i:  " % statementCount 
    #endif

    zone = 'FINE'
    pName = statement.Positions[0].Name
    if pName[:2] == 'PR':
      offset = 15
      posType = 'PR'
      line = "%4i:   ;\n" % statementCount 
      statementCount += 1
      line  += "%4i:  PR[%i,1:XYP] = PR[%i,1:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex,offset)
      statementCount += 1
      line += "%4i:  PR[%i,2:XYP] = PR[%i,2:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex,offset)
      statementCount += 1
      line += "%4i:  PR[%i,3:XYP] = PR[%i,3:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex,offset)
      statementCount += 1
      line += "%4i:   ;\n" % statementCount 
      statementCount += 1
      line += "%4i:  " % statementCount 
    else:
      posType = 'P'
    #endif

    if statement.Type == VC_STATEMENT_LINMOTION:
      line += "L %s[%i: %s]  %gmm/sec %s ;\n" % (posType, pointIndex, pName, statement.MaxSpeed,zone)
    elif statement.Type == VC_STATEMENT_PTPMOTION:
      line += "J %s[%i: %s]  %g%% %s ;\n" % (posType, pointIndex, pName, statement.JointSpeed*100,zone)
    #endif

  elif statement.Type == VC_STATEMENT_SETPROPERTY:
    line += "%s = %s;\n" %(statement.TargetProperty, statement.ValueExpression)

  elif statement.Type == VC_STATEMENT_IF:
    thenlabel = label
    label += 1
    elselabel = label
    label += 1
    line += "IF %s,JMP LBL[%i];\n" % (statement.Condition, thenlabel)
    text += line
    statementCount += 1
    for s in statement.ElseScope.Statements:
      writeStatement( s )
    line = "%4i: JMP LBL[%i];\n" % (statementCount, elselabel)
    text += line
    statementCount += 1
    line = "%4i: LBL[%i];\n" % (statementCount, thenlabel)
    text += line
    statementCount += 1
    for s in statement.ThenScope.Statements:
      writeStatement( s )
    line = "%4i: LBL[%i];\n" % (statementCount, elselabel)
    
  else:
    print statement.Type
    return 

  #endif

  statementCount += 1
  text += line
  return




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
  
  
addState( None )
