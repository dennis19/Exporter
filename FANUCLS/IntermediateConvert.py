from vcCommand import *
import time
from decimal import *
import download
import re
import IntermediateConvertABB
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
#-------------------------------------------------------------------------------
app = getApplication()

def getActiveRoutine():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

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
  global text, statementCount, routine, uframe_num, utool_num, label
  routine = getActiveRoutine()
  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller

  if not routine:
    app.messageBox("No Routine selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif
  routine = program.MainRoutine
  if routine.Name=="Main":
    routine.Name="PNS0001"
  rname = routine.Name
  #if routine.Name == 'PositionRegister': return

  # print 'Converting %s to LS' % routine.Name


  for routine in program.Routines:
    if not re.findall("POSREG_PR",rname):
      convertRoutine(comp,routine)
    else:
      print " Routine %s is Position Register" %rname
  #k=0
  # while k<len(comp.Properties):
  #   if re.findall("Registers::",comp.Properties[k].Name):
  #     #print "%s" %comp.Properties[k].Name
  #     pass
  #   k+=1



#   note =  comp.findBehaviour( rname )
#   if not note:
#     note = comp.createBehaviour( VC_NOTE, rname )
#   #endif
#
#   comp.createProperty(VC_BOOLEAN,"%s::SkipExecution"%rname)
#
#
#
#   header = """/PROG  %s
# /ATTR
# OWNER           = MNEDITOR;
# COMMENT         = "%s";
# PROG_SIZE       = 0;
# CREATE          = %s;
# MODIFIED        = %s;
# FILE_NAME       = ;
# VERSION         = 0;
# LINE_COUNT      = 0;
# MEMORY_SIZE     = 0;
# PROTECT         = READ_WRITE;
# TCD:  STACK_SIZE        = 0,
#       TASK_PRIORITY     = 50,
#       TIME_SLICE        = 0,
#       BUSY_LAMP_OFF     = 0,
#       ABORT_REQUEST     = 0,
#       PAUSE_REQUEST     = 0;
# DEFAULT_GROUP   = 1,*,*,*,*;
# CONTROL_CODE    = 00000000 00000000;
# /APPL
# /MN
# """
#   td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
#   text = header % (rname, rname, td, td)
#
#   mainroutine = comp.getProperty('MainRoutine')
#   if mainroutine:
#     stepValues = mainroutine.StepValues
#     if rname not in stepValues:
#       stepValues.append(rname)
#       mainroutine.StepValues = stepValues
#     #endif
#   #endif
#
#   label = 1
#   uframe_num = -1
#   utool_num = -1
#   statementCount = 1
#   ##for statement in getAllStatements(routine):
#   for statement in routine.Statements:
#     writeStatement( statement )
#   #endfor
#   pos_="""/POS\n"""
#   text+=pos_
#   positions = []
#   for s in routine.Statements:
#     if s.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
#       if s.getProperty('INDEX'):
#         num = s.INDEX
#       else:
#         pName = s.Positions[0].Name
#         num = int(pName[pName.rindex('_')+1:])
#       #endif
#       positions.append((num, s))
#     #endif
#   #endif
#   positions.sort()
#
#   for n,s in positions:
#     text+=doWriteTargetDefinition(n,s)
#
#   note.Note = text

# def writeLocalCoords(statement):
#   global text
#
#   getcontext().prec=3
#   line =""
#   if statement.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
#     pName = statement.Positions[0].Name
#     if not pName[:2] == 'PR':
#
#         #statement.Positions[0].PositionInReference.P.X
#       line+="\n%s{\n" %pName
#       line+=      "   GP1:\n" \
#                   "     UF : %s, UT %s: ,     CONFIG: '%s'\n" %(getFrame(statement),getTool(statement),getConfig(statement))
#       line+=      "     X =%s%s  mm,  Y =%s%s  mm,  Z =%s%s  mm\n" %(getIndentation(format(statement.Positions[0].PositionInReference.P.X,'.3f'),10),format(statement.Positions[0].PositionInReference.P.X,'.3f'),getIndentation(format(statement.Positions[0].PositionInReference.P.Y,'.3f'),10),format(statement.Positions[0].PositionInReference.P.Y,'.3f'),getIndentation(format(statement.Positions[0].PositionInReference.P.Z,'.3f'),10),format(statement.Positions[0].PositionInReference.P.Z,'.3f'))
#       line+=            "     W =%s%s deg,  P =%s%s deg,  R =%s%s deg" %(getIndentation(format(statement.Positions[0].PositionInReference.WPR.X,'.3f'),10),format(statement.Positions[0].PositionInReference.WPR.X,'.3f'),getIndentation(format(statement.Positions[0].PositionInReference.WPR.Y,'.3f'),10),format(statement.Positions[0].PositionInReference.WPR.Y,'.3f'),getIndentation(format(statement.Positions[0].PositionInReference.WPR.Z,'.3f'),10),format(statement.Positions[0].PositionInReference.WPR.Z,'.3f'))
#
#       line+="\n};"
#   text+=line

def convertRoutine(comp,routine):

  global controller
  global text, statementCount, uframe_num, utool_num, label
  print 'Converting %s to LS' % routine.Name
  rname = routine.Name

  # k=0
  # while k<len(comp.Properties):
  #   if re.findall("Registers::",comp.Properties[k].Name):
  #     #print "%s" %comp.Properties[k].Name
  #     pass
  #   k+=1

  note = comp.findBehaviour(rname)
  if not note:
    note = comp.createBehaviour(VC_NOTE, rname)
  # endif

  comp.createProperty(VC_BOOLEAN, "%s::SkipExecution" % rname)

  header = """/PROG  %s
  /ATTR
  OWNER           = MNEDITOR;
  COMMENT         = "%s";
  PROG_SIZE       = 0;
  CREATE          = %s;
  MODIFIED        = %s;
  FILE_NAME       = ;
  VERSION         = 0;
  LINE_COUNT      = 0;
  MEMORY_SIZE     = 0;
  PROTECT         = READ_WRITE;
  TCD:  STACK_SIZE        = 0,
        TASK_PRIORITY     = 50,
        TIME_SLICE        = 0,
        BUSY_LAMP_OFF     = 0,
        ABORT_REQUEST     = 0,
        PAUSE_REQUEST     = 0;
  DEFAULT_GROUP   = 1,*,*,*,*;
  CONTROL_CODE    = 00000000 00000000;
  /APPL
  /MN
  """
  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  text = header % (rname, rname, td, td)

  mainroutine = comp.getProperty('MainRoutine')
  if mainroutine:
    stepValues = mainroutine.StepValues
    if rname not in stepValues:
      stepValues.append(rname)
      mainroutine.StepValues = stepValues
    # endif
  # endif

  label = 1
  uframe_num = -1
  utool_num = -1
  statementCount = 1
  ##for statement in getAllStatements(routine):
  for statement in routine.Statements:
    writeStatement(statement)
  # endfor
  pos_ = """/POS\n"""
  text += pos_
  positions = []
  for s in routine.Statements:
    if s.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
      if s.getProperty('INDEX'):
        num = s.INDEX
      else:
        pName = s.Positions[0].Name
        num = int(pName[pName.rindex('_') + 1:])
      # endif
      positions.append((num, s))
    # endif
  # endif
  positions.sort()

  for n, s in positions:
    text += doWriteTargetDefinition(n, s)

  note.Note = text


def getStatementData( statement ):
  global text, statementCount, uframe_num, utool_num, label
  line_data_=["",""]
  # line = "%4i:  " % statementCount

  if statement.Type == VC_STATEMENT_CALL:
    line_data_[0]=getCall(statement)[0]
    line_data_[1]=getCall(statement)[1]

  elif statement.Type == VC_STATEMENT_DELAY:
    line_data_[0]="WaitTime"
    line_data_[1]=getDelay(statement)
  elif statement.Type == VC_STATEMENT_COMMENT:
    line_data_[0]="Comment"
    line_data_[1]=getComment(statement)

  elif statement.Type == VC_STATEMENT_SETBIN:
    line_data_[0]="SetOutput"
    line_data_[1]=getSetOutput(statement)
    #endif

  elif statement.Type == VC_STATEMENT_WAITBIN:
    line_data_[0]="Wait"
    line_data_[1]=getWAIT(statement)

  elif statement.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
    line_data_[0]="Movement"
    line_data_[1]=getMotion(statement)

  elif statement.Type == VC_STATEMENT_SETPROPERTY:
    line_data_[0]="SetVariable"
    line_data_[1]=getSetVariable(statement)

  elif statement.Type == VC_STATEMENT_IF:
    line_data_[0]="If"
    line_data_[1]=getIf(statement)
  elif statement.Type== VC_STATEMENT_PRINT:
    line_data_[0]="Message"
    line_data_[1]=getMessage(statement)
  elif statement.Type == "Process":

    if re.findall("LBL",statement.Name):
      line_data_[0]="Label"
      line_data_[1] = getLabel(statement)
    elif re.findall("ToolOffset",statement.Name):
      line_data_[0]="Movement"
      line_data_[1]=getMotion(statement)
    elif re.search("CALL", statement.Name):
      line_data_[0] = getCall(statement)[0]
      line_data_[1] = getCall(statement)[1]
    elif re.search("WAIT_", statement.Name):
      line_data_[0] = getCall(statement)[0]
      line_data_[1] = getCall(statement)[1]
    elif re.findall("WAIT",statement.Name):
      line_data_[0] = "Wait"
      line_data_[1] = getWAIT(statement)
    elif re.findall("JMP",statement.Name):
      line_data_[0]="Jump"
      line_data_[1] = getJMP(statement)
    elif re.findall("LinearPosReg",statement.Name):
      line_data_[0]="Movement"
      line_data_[1]=getMotion(statement)
  elif statement.Type==VC_STATEMENT_RETURN:
    line_data_[0]="Return"
    line_data_[1]=getReturn(statement)
  else:
    print "Statement %s not translated" %statement.Type


  #endif

  # statementCount += 1
  # text += line
  return line_data_

def getTarget(routine):
  #routine = getActiveRoutine()
  positions = []
  targets=[]
  for s in routine.Statements:
    if s.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
      if s.getProperty('INDEX'):
        num = s.INDEX
      else:
        pName = s.Positions[0].Name
        num = int(pName[pName.rindex('_') + 1:])
      # endif
      positions.append((num, s))
    # endif
  # endif
  positions.sort()
  for n, s in positions:
    targets.append(getTargetDefinition(n, s))
  return targets

def getTargetDefinition(statement_nr,statement):
  routine = getActiveRoutine()
  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller
  target_data_=[]
  uf = download.GetBaseIndex( statement,controller )
  ut = download.GetToolIndex( statement,controller )
  target_data_.append(uf)
  target_data_.append(ut)
  posFrame = statement.Positions[0]
  t4 = download.getValue( posFrame, 'JointTurns4', 0 )
  t5 = download.getValue( posFrame, 'JointTurns5', 0 )
  t6 = download.getValue( posFrame, 'JointTurns6', 0 )
  cf =download. getValue( posFrame, 'Configuration', 'F U T' )

  config=[cf,t4,t5,t6]
  #config = '%s, %i, %i, %i' % (cf, t4, t5, t6 )
  target_data_.append(config)
  group = 1
  #print "pos %s" %posFrame.Name
  # try:
  if re.findall(obracket + "(?P<Nr>[0-9_]+)" + '(?P<comment>(\s*:.*)?)' + cbracket, posFrame.Name):
    match_ = re.search(obracket + "(?P<Nr>[0-9_]+)" + '(?P<comment>(\s*:.*)?)' + cbracket, posFrame.Name)
    if not match_.group('comment') == "":
      comment = ":"+match_.group('comment')
    else:
      comment = match_.group('comment')
  elif re.findall("P(?P<Nr>[0-9]+)" ,posFrame.Name):
    comment=""
  else:
    comment = ":"+posFrame.Name
  #print "comment:%s" %comment
  # except:
  #   comment = None
  target_data_.append(comment)
  target_data_.append(str(statement_nr))
  # if comment and comment != str(statement_nr):
  #   line='P[%i%s]{ \n' % (statement_nr,comment)
  # else:
  #   line='P[%i%s]{ \n' % (statement_nr,comment)
  #endif
  # line+="    GP%i:\n" % group
  # line +="         UF : %i, UT : %i," % (uf, ut)
  m = posFrame.PositionInReference
  p = m.P
  a = m.WPR
  target_data_.append([p.X,p.Y,p.Z,a.X,a.Y,a.Z])
  # line +="              CONFIG : '%s',\n" % config
  # line +="         X = %8.2f  mm,     Y = %8.2f  mm,     Z = %8.2f  mm,\n" % (p.X,p.Y,p.Z)
  # line +="         W = %8.2f deg,     P = %8.2f deg,     R = %8.2f deg" % (a.X,a.Y,a.Z)
  # internalAxes = len(posFrame.InternalJointValues)
  # i = 0
  # for j, joint in enumerate( posFrame.ExternalJointValues ):
  #   if groups[j+internalAxes] == group:
  #     if j == 0: line+=",\n    "
  #     else: line+=","
  #   else:
  #     i = 0
  #     line +="\n"
  #     group = groups[j+internalAxes]
  #     line +="    GP%i:\n" % group
  #     line +="         UF : %i, UT : %i,\n    " % (uf, ut)
  #   #endif
  #   if i > 0 and i%3 == 0:
  #     ls.write("\n    ")
  #   #endif
  #   if group == 1:
  #     line +="     E%i = %8.2f %s" % (j+1, joint.Value, jUnits[internalAxes+j])
  #   else:
  #     line +="     J%i = %8.2f %s" % (i+1, joint.Value, jUnits[internalAxes+j])
  #   #endif
  #   i += 1
  # #endfor
  # line +="\n"
  # line +="};\n"
  return target_data_


def getCall(statement):
  call_data = ["", "", ""]
  if statement.getProperty("Parameter_1"):
    call_data[0]=statement.getProperty("CallRoutine").Value
    call_data[1]=statement.getProperty("Parameter_1").Value
    #line="CALL %s(%s" %(statement.getProperty("CallRoutine").Value,statement.getProperty("Parameter_1").Value)
    if statement.getProperty("Parameter_2"):
      call_data[2]=statement.getProperty("Parameter_2").Value
      #line+=",%s" %statement.getProperty("Parameter_2").Value
    #line+=");\n"
    state_ = "Call"
  else:
    if re.findall("POSREG_PR",statement.Routine.Name):
      call_data=getMotion(statement.Routine.Statements[0])
      state_="Movement"
      #line=writeMotion(statement.Routine.Statements[0])
    #   line = "\n;"
    # else :
    else:
      call_data[0] = statement.Routine.Name
      state_ = "Call"
  #print "call_data %s" %call_data[0]
  return [state_,call_data]

def getDelay(statement):
  delay_data=statement.Delay
  return  delay_data

def getComment(statement):
  comment_data_=""
  if statement.Comment[:2] == '++':
    comment_data_ = statement.Comment[2:]
  else:
    comment_data_ = statement.Comment
  return comment_data_

def getSetOutput(statement):
  set_output_data_=["","",""]
  if statement.OutputPort < 1000:
    set_output_data_[0]=statement.OutputPort
    # if statement.OutputValue==1:
    #   set_output_data_[2] ="ON"
    # elif statement.OutputValue==0:
    set_output_data_[2] =statement.OutputValue
    if not statement.Name=="":
      set_output_data_[1]=statement.Name
  # endif
  return set_output_data_

def getWAIT(statement):
  wait_data_=[]
  if statement.Type=="Process":
    # line="WAIT ("
    i=0
    while statement.getProperty("Variable %s" %(i)):
      if not statement.getProperty("Variable %s" %(i)).Value =="":
        if re.search(r"(?P<var_type>[a-zA-Z]+)", statement.getProperty("Variable %s" % i).Value):
        #print "wait:%s" %statement.getProperty("Variable %s" %i).Value
          type_def_=re.search(
          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)",# + r"(?P<comment>[a-zA-Z]?)",
          statement.getProperty("Variable %s" % i).Value)
        #reg_type=type_def_.group("regType")
          type_ = type_def_.group("var_type")
          index_=type_def_.group("Nr")
          comment_=statement.getProperty("Comment %s" % i).Value#type_def_.group("comment")
        # if not comment_=="":
        #   comment_=":"+comment_

          if not (type_=="R" or type_=="F" or type_=="M"):
            if statement.getProperty("Value %s" % i).Value == 1:
              value_ = "ON"
            elif statement.getProperty("Value %s" % i).Value == 0:
              value_ = "OFF"
          else: value_=str(statement.getProperty("Value %s" % i).Value)
          wait_data_.append([type_, index_, comment_, value_])
        #line+=type_+"["+index_+comment_+']='+str(statement.getProperty("Value %s" %i).Value)
        # if statement.getProperty("Variable %s" % (i + 2)):
        #   if not statement.getProperty("Variable %s" % (i + 1)).Value=="":
        #     line += " OR "
        elif re.search("(?P<Nr>[0-9_]+)",statement.getProperty("Variable %s" %i).Value):
          nr_def = re.search("(?P<Nr>[0-9_]+)", statement.getProperty("Variable %s" % i).Value)
        #type_ = nr_def.group("var_type")
        #print "type: %s" % type_
        # if not type=="DI":
        #   wait_data_.append([type_,nr_def.group("Nr"), statement.getProperty("Comment %s" % i).Value, ""])
        #   #line += type_ + "[" + nr_def.group("Nr") + ":" + statement.getProperty("Comment %s" % i).Value + "]"
        # else:
          if statement.getProperty("Value %s" %i).Value==1:
            value_="ON"
          elif statement.getProperty("Value %s" % i).Value == 0:
            value_ = "OFF"
          wait_data_.append(["DI", nr_def.group("Nr"), statement.getProperty("Comment %s" % i).Value, value_])
          #line+="DI"+"["+nr_def.group("Nr")+":"+statement.getProperty("Comment %s" %i).Value+"]"
        # if statement.getProperty("Variable %s" %(i+2)):
        #   if not statement.getProperty("Variable %s" % (i + 1)).Value=="":
        #     line += " OR "

      i+=1

    # line+=");\n"
  else:
    if statement.InputPort < 1000:
      #
      # wait_data_[0]=statement.InputPort
      # wait_data_[2] = statement.InputValue
      # if not statement.Name == "":
      #   wait_data_[1] = statement.Name
      if statement.InputValue:
        value_ = "ON"
      else:
        value_ += "OFF"
      wait_data_.append(["DI",str(statement.InputPort),statement.Name,value_])
    # endif
  return wait_data_

def getSetVariable(statement):
  set_var_data=["","","","","",""]
  type_def_=re.search(
          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]+)",
    statement.TargetProperty)
  if type_def_:
    target_property_ = type_def_.group("var_type")+"["+type_def_.group("Nr")+":"+type_def_.group("comment")+"]"
    if not re.findall("Parameter",target_property_):
      set_var_data[0:2] = [type_def_.group("var_type"), type_def_.group("Nr"), type_def_.group("comment")]
  elif re.search(          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
    statement.TargetProperty):
    type_def_ = re.search(
      r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
      statement.TargetProperty)
    set_var_data[0:2] = [type_def_.group("var_type"), type_def_.group("Nr"), ""]

    target_property_ = type_def_.group("var_type") + "[" + type_def_.group("Nr") + "]"
    # if re.findall("TIMER", target_property_):
    #   pass

  else:

    target_property_=statement.TargetProperty

    if not re.findall("Parameter_",target_property_):
      #print "prop %s" % target_property_
      set_var_data[0:2] = [target_property_, "", ""]


  type_def_=re.search(
          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]+)",
    statement.ValueExpression)
  var_=""
  index_=""
  comment_=""
  if type_def_:
    value_expression_ = type_def_.group("var_type")+"["+type_def_.group("Nr")+":"+type_def_.group("comment")+"]"
    if not re.findall("Parameter",value_expression_):
      var_=type_def_.group("var_type")
      index_=type_def_.group("Nr")
      comment_=type_def_.group("comment")

  elif re.search(          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
    statement.ValueExpression):
    type_def_ = re.search(
      r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
      statement.ValueExpression)
    #value_expression_ = type_def_.group("var_type") + "[" + type_def_.group("Nr") + "]"
    var_ = type_def_.group("var_type")
    index_ = type_def_.group("Nr")
  elif re.findall("Parameter_",statement.ValueExpression):
    nr_def_=re.search("Parameter_"+"(?P<Nr>[0-9]+)",statement.ValueExpression)
    #value_expression_="AR["+nr_def_.group("Nr")+"]"
    var_ = "AR"
    index_ = nr_def_.group("Nr")
  else:
    #print "setvar %s" %set_var_data[0]
    if not (set_var_data[0] == "R" or set_var_data[0] == "F" or set_var_data[0] == "M"):
      if statement.ValueExpression == "1":
        var_ = "ON"
      elif statement.ValueExpression=="0":
        var_ = "OFF"
      else:
        var_ = statement.ValueExpression
    else:
        var_=statement.ValueExpression

  set_var_data[3:5]=[var_,index_,comment_]

  return set_var_data

def getIf(statement):
  global label,statementCount
  text_part_=""
  line=""
  if_data_=[]
  #thenlabel = label
  #label += 1
  thenlabel=[]
  elselabel = []
  #label += 1
  if statement.ParentRoutine.Program.Executor.Controller.Name=="R30iA":
    condition_=transformConditionFanuc(statement)
  elif statement.ParentRoutine.Program.Executor.Controller.Name=="IRC5":
    condition_ = transformConditionAbb(statement)
  if_data_.append(condition_)
  #print "condition %s" %condition_
  for s in statement.ThenScope.Statements:
    #print "state %s" %s.Type
    state=getStatementData(s)
    #print "state %s" %state
    thenlabel.append(state)
  # if statement.ThenScope.Statements[0].Type == "Process":
  #   if statement.ThenScope.Statements[0].getProperty("LabelNr"):
  #     # thenlabel=statement.ThenScope.Statements[0].getProperty("LabelNr").Value
  #     thenlabel=["Jump",getJMP(statement.ThenScope.Statements[0])]
  #     #line += "IF %s,JMP LBL[%s];\n" % (condition_, thenlabel)
  #   elif statement.ThenScope.Statements[0].getProperty("CallRoutine"):
  #     thenlabel = getCall(statement.ThenScope.Statements[0])
  #     # thenlabel=statement.ThenScope.Statements[0].getProperty("CallRoutine").Value
  #     # if statement.ThenScope.Statements[0].getProperty("Parameter_1"):
  #     #   line += "IF %s,CALL %s(%s" % (condition_, thenlabel,statement.ThenScope.Statements[0].getProperty("Parameter_1").Value)
  #     #   if statement.ThenScope.Statements[0].getProperty("Parameter_2"):
  #     #     line += ",%s" % (
  #     #     statement.ThenScope.Statements[0].getProperty("Parameter_2").Value)
  #     #   line+=");\n"
  # elif statement.ThenScope.Statements[0].Type == VC_STATEMENT_CALL:
  #   thenlabel = getCall(statement.ThenScope.Statements[0])
    # thenlabel=statement.ThenScope.Statements[0].Routine.Name
    # line += "IF %s,CALL %s;\n" % (
    #   condition_, thenlabel)
  if_data_.append(thenlabel)

  #statementCount += 1

  for s in statement.ElseScope.Statements:
    elselabel.append(getStatementData(s))
  if_data_.append(elselabel)
  text_part_ += line
  #   statementCount += 1
  #line = "%4i: JMP LBL[%i];\n" % (statementCount, elselabel)
  #text_part_ += line
  #statementCount += 1
  #line = "%4i: LBL[%s];\n" % (statementCount, thenlabel)
  #text_part_ += line
  #statementCount += 1
  # for s in statement.ThenScope.Statements:
  #   writeStatement(s)
  #   statementCount += 1
  # #line = "%4i: LBL[%i];\n" % (statementCount, elselabel)
  #text_part_+=line
  return if_data_

def getMotion(statement):
  line=""
  #global uframe_num, utool_num,statementCount,controller
  routine = getActiveRoutine()
  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller
  if not statement.getProperty('INDEX'):
    indices = {}
    maxIndex = 0
    for s in statement.ParentRoutine.Statements:
      if s.getProperty('INDEX'):
        indices[s.INDEX] = True
        if s.INDEX > maxIndex: maxIndex = s.INDEX
      # endif
    # endfor
    sName = statement.Positions[0].Name
    try:
      num = int(sName[sName.rindex('_') + 1:])
    except:
      try:
        for i in range(len(sName) - 1, -1, -1):
          if not sName[i:].isdigit():
            num = int(sName[i + 1:])
            break
          # endif
        # endfor
      except:
        num = maxIndex + 1
      # endtry
    # endtry

    statement.createProperty(VC_INTEGER, 'INDEX')

    statement.INDEX = num
    if indices.get(num, False):
      statement.INDEX = maxIndex + 1
      """
      for i in range( 1, routine.StatementCount+2):
        if not indices.get( num, False ):
          statement.INDEX = i
          break
        #endif
      #endfor
      """
    # endif
  # endif

  pointIndex = statement.INDEX

  uf = statement.Base.Name#download.GetBaseIndex(statement, controller)
  #if uframe_num != uf:
    #uframe_num = uf
    #line += "UFRAME_NUM = %i ;\n" % (uf)
    #statementCount += 1
    #line += "%4i:  " % statementCount
    # endif

  ut = statement.Tool.Name#download.GetToolIndex(statement, controller)
  #if utool_num != ut:
    #utool_num = ut
    #line += "UTOOL_NUM = %i ;\n" % (ut)
    # += 1
    #line += "%4i:  " % statementCount
    # endif


  if statement.getProperty("AccuracyRegister"):
    zone=statement.getProperty("AccuracyRegister").Value
    zone_def_=re.search("R"+"(?P<Nr>[0-9_]+)",zone)
    zone="CNT R["+zone_def_.group('Nr')+":"+zone[1+len(zone_def_.group('Nr')):]+"]"

  elif statement.AccuracyValue:
    zone = statement.AccuracyValue
    if zone == "0":
      zone = 'FINE'
    else:
      zone = "CNT"+str(int(zone))
  else:
    zone="FINE"

  if statement.getProperty("SpeedRegister"):
    speed_=statement.getProperty("SpeedRegister").Value
    speed_def_=re.search("R"+"(?P<Nr>[0-9_]+)",speed_)
    speed_="R["+speed_def_.group('Nr')+":"+speed_[1+len(speed_def_.group('Nr')):]+"]"
  else:
    if statement.Type == VC_STATEMENT_LINMOTION:
      speed_=int(statement.MaxSpeed)
    elif statement.Type == VC_STATEMENT_PTPMOTION:
      speed_=int(statement.JointSpeed)
    else:
      speed_=statement.getProperty('Speed').Value
  pName = statement.Positions[0].Name
  #print "name:%s" %pName
  if pName[:2] == 'PR':

    #offset = 15
    posType = 'PR'
    index_def_=re.search("PR"+obracket+"(?P<Nr>[0-9_]+)",pName)
    pointIndex=index_def_.group('Nr')
    # line = "%4i:   ;\n" % statementCount
    # statementCount += 1
    # line += "%4i:  PR[%i,1:XYP] = PR[%i,1:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
    # statementCount += 1
    # line += "%4i:  PR[%i,2:XYP] = PR[%i,2:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
    # statementCount += 1
    # line += "%4i:  PR[%i,3:XYP] = PR[%i,3:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
    # statementCount += 1
    # line += "%4i:   ;\n" % statementCount
    # statementCount += 1
    # line += "%4i:  " % statementCount
  else:
    posType = 'P'
  # endif

  if statement.Type == VC_STATEMENT_LINMOTION:
    # print "pos %s" %statement.Positions[0].PositionInWorld.P.X
    motion_data_=[uf,ut,"lin",posType,pointIndex,pName, speed_, zone,"",""]
    #line += "L %s[%i%s]  %gmm/sec %s" % (posType, pointIndex, pName, statement.MaxSpeed, zone)
  elif statement.Type == VC_STATEMENT_PTPMOTION:
    motion_data_ = [uf, ut, "joint", posType, pointIndex, pName, speed_, zone,"",""]
    #line += "J %s[%i%s]  %g%% %s" % (posType, pointIndex, pName, statement.JointSpeed * 100, zone)
  else:
    motion_data_ = [uf, ut, "lin", posType, pointIndex, pName, speed_, zone, "",""]
    # print "pos %s" %statement.Positions[0].PositionInWorld.P.X
    #line += "L %s[%i%s]  %gmm/sec %s" % (posType, pointIndex, pName, int(statement.getProperty('Speed').Value), zone)
  # endif

  if statement.getProperty('Position'):
    motion_data_[8]=statement.getProperty('Position').Value
  if statement.getProperty('Register'):
    motion_data_[9]=statement.getProperty('Register').Value
    #line+=" ToolOffset,%s" %statement.getProperty('Register').Value

  #line+=" ;\n"
  return motion_data_

def getLabel(statement):
  return [str(statement.getProperty("LabelNr").Value),str(statement.getProperty("Comment").Value)]

def getJMP(statement):
  return str(statement.getProperty("LabelNr").Value)

def getReturn(statement):
  return ""

def getMessage(statement):
  return statement.Message

def transformConditionFanuc(statement):
  i=0
  transformed_condition_=""

  while i<len(statement.Condition):
    #transformed_condition_+=statement.Condition[i]
    #print "cond %s" % statement.Condition[i]
    if re.findall(r"(?P<signs>[\!\=\&\|]+)",statement.Condition[i]):
      sign_def = re.search(r"(?P<signs>[\!\=\&\|]+)",statement.Condition[i:i+2])
      sign_ = sign_def.group("signs")
      i = i + len(sign_)
      if sign_=="==":
        sign_="="
      elif sign_=="!=":
        sign_="<>"
      elif sign_=="&&":
        sign_="AND"
      elif sign_=="||":
        sign_="OR"
      transformed_condition_ += sign_
    elif re.findall("Parameter_"+"(?P<Nr>[0-9_]+)", statement.Condition[i:i+11]):
      type_def_=re.search("Parameter_"+"(?P<Nr>[0-9_]+)", statement.Condition[i:i+11])
      type_="AR["+type_def_.group('Nr')+"]"
      transformed_condition_+=type_
      i+=len("Parameter_"+type_def_.group('Nr'))
    elif re.findall(r"(?P<var_type>[a-zA-Z]+)",statement.Condition[i]):
      type_def_=re.search(r"(?P<var_type>[a-zA-Z]+)"+obracket+"(?P<Nr>[0-9_]+)"+cbracket,statement.Condition[i:i+9])

      if type_def_:
        value_=""
        sign_=""
        equal_=0
        equal_def_=re.search(r"(?P<signs>[\=\!]+)"+"(?P<value>[0-9_]+)",statement.Condition[i:i+11])

        type_ = type_def_.group("var_type")
        #print "nr :%s" %type_def_.group("value")
        if equal_def_:
          value_=equal_def_.group("value")
          sign_ = equal_def_.group("signs")
          equal_=len(equal_def_.group('signs')+equal_def_.group("value"))
          #print "char %s" % sign_

        #i = i + len(sign_)
        if sign_ == "==":
          sign_ = "="
        elif sign_=="!=":
          sign_="<>"
        if value_=='0':
          value_="OFF"
        elif  value_=='1':
          value_="ON"

        if type_=="IN":
          #print "nr %s"%type_def_.group("Nr")
          type_="DI"+"["+type_def_.group("Nr")+statement.getProperty("Comment%s"%type_def_.group("Nr")).Value+"]"+sign_+value_
          transformed_condition_ +=type_
          i+=len("IN"+"["+type_def_.group("Nr")+"]")+equal_
        elif type_=="OUT":
          type_="DO"+"["+type_def_.group("Nr")+statement.getProperty("Comment%s"%type_def_.group("Nr")).Value+"]"
          transformed_condition_ +=type_
          i+=len("OUT"+"["+type_def_.group("Nr")+"]")

        else:
          transformed_condition_ += type_
          i=i+len(type_)

      elif re.search(r"(?P<regType>[a-zA-Z]+)"+"::",statement.Condition[i:i+12]):
        type_def_=re.search(
          r"(?P<regType>[a-zA-Z]+)" + "::" + r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z0-9\._]+)",
          statement.Condition[i:])
        reg_type=type_def_.group("regType")
        type_ = type_def_.group("var_type")
        index_=type_def_.group("Nr")
        comment_=type_def_.group("comment")
        #print "ccomment :%s" %comment_


        transformed_condition_ += type_+"["+index_+":"+comment_+"]"#statement.Condition[i]
        #print "char:%s" % statement.Condition[i]
        i=i+len(reg_type+type_+index_+comment_)+2
        #i=i+1


      else:
        #print "char:%s" %statement.Condition[i]
        transformed_condition_ += statement.Condition[i]
        i=i+1



    else:
      transformed_condition_ += statement.Condition[i]
      i=i+1


  return transformed_condition_

def transformConditionAbb(statement):
  i=0
  transformed_condition_=""

  while i<len(statement.Condition):
    #transformed_condition_+=statement.Condition[i]
    #print "cond %s" % statement.Condition[i]
    if re.findall(r"(?P<signs>[\!\=\&\|]+)",statement.Condition[i]):
      sign_def = re.search(r"(?P<signs>[\!\=\&\|]+)",statement.Condition[i:i+2])
      sign_ = sign_def.group("signs")
      i = i + len(sign_)
      if sign_=="==":
        sign_="="
      elif sign_=="!=":
        sign_="<>"
      elif sign_=="&&":
        sign_="AND"
      elif sign_=="||":
        sign_="OR"
      transformed_condition_ += sign_
    elif re.findall("Parameter_"+"(?P<Nr>[0-9_]+)", statement.Condition[i:i+11]):
      type_def_=re.search("Parameter_"+"(?P<Nr>[0-9_]+)", statement.Condition[i:i+11])
      type_="AR["+type_def_.group('Nr')+"]"
      transformed_condition_+=type_
      i+=len("Parameter_"+type_def_.group('Nr'))
    elif re.findall(r"(?P<var_type>[a-zA-Z]+)",statement.Condition[i]):
      type_def_=re.search(r"(?P<var_type>[a-zA-Z]+)"+obracket+"(?P<Nr>[0-9_]+)"+cbracket,statement.Condition[i:i+9])

      if type_def_:
        value_=""
        sign_=""
        equal_=0
        equal_def_=re.search(r"(?P<signs>[\=\!]+)"+"(?P<value>[0-9_]+)",statement.Condition[i:i+11])

        type_ = type_def_.group("var_type")
        #print "nr :%s" %type_def_.group("value")
        if equal_def_:
          value_=equal_def_.group("value")
          sign_ = equal_def_.group("signs")
          equal_=len(equal_def_.group('signs')+equal_def_.group("value"))
          #print "char %s" % sign_

        #i = i + len(sign_)
        if sign_ == "==":
          sign_ = "="
        # elif sign_=="!=":
        #   sign_="<>"
        # if value_=='0':
        #   value_="OFF"
        # elif  value_=='1':
        #   value_="ON"

        if type_=="IN":
          #print "nr %s"%type_def_.group("Nr")
          type_="DI"+"_"+type_def_.group("Nr")+"_"+statement.getProperty("Comment%s"%type_def_.group("Nr")).Value+sign_+value_
          transformed_condition_ +=type_
          i+=len("IN"+"["+type_def_.group("Nr")+"]")+equal_
        elif type_=="OUT":
          type_="DO"+"_"+type_def_.group("Nr")+"_"+statement.getProperty("Comment%s"%type_def_.group("Nr")).Value
          transformed_condition_ +=type_
          i+=len("OUT"+"["+type_def_.group("Nr")+"]")

        else:
          transformed_condition_ += type_
          i=i+len(type_)

      elif re.search(r"(?P<regType>[a-zA-Z]+)"+"::",statement.Condition[i:i+12]):
        type_def_=re.search(
          r"(?P<regType>[a-zA-Z]+)" + "::" + r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z0-9\._]+)",
          statement.Condition[i:])
        reg_type=type_def_.group("regType")
        type_ = type_def_.group("var_type")
        index_=type_def_.group("Nr")
        comment_=type_def_.group("comment")
        #print "ccomment :%s" %comment_


        transformed_condition_ += type_+"["+index_+":"+comment_+"]"#statement.Condition[i]
        #print "char:%s" % statement.Condition[i]
        i=i+len(reg_type+type_+index_+comment_)+2
        #i=i+1


      else:
        #print "char:%s" %statement.Condition[i]
        transformed_condition_ += statement.Condition[i]
        i=i+1



    else:
      transformed_condition_ += statement.Condition[i]
      i=i+1


  return transformed_condition_


def getConfig(statement):
  cfg=statement.Positions[0].Configuration
  #print "cfg:%s" %cfg[0]
  if cfg[0]=="N":
    cfg+=", 0"
  elif cfg[0]=="F":
    cfg+=", 1"
  if cfg[2]=="U":
    cfg+=", 0"
  elif cfg[2]=="D":
    cfg+=", 1"
  if cfg[4]=="T":
    cfg+=", 0"
  elif cfg[4]=="B":
    cfg+=", 1"
  return cfg

def getIndentation(string,length):
  indentation = ""
  if not length - len(string) == 0:
    indentationcount = length - len(string)
    while indentationcount > 0:
      indentation += " "
      indentationcount = indentationcount - 1
  return indentation

addState( None )
