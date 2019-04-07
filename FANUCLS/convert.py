from vcCommand import *
import time
from decimal import *
import download
import re
import IntermediateConvert
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
  convertRoutine(comp,routine)
  #rname = routine.Name
  #if routine.Name == 'PositionRegister': return

  # print 'Converting %s to LS' % routine.Name


  for routine_ in program.Routines:
    if not re.findall("POSREG_PR",routine_.Name):
      convertRoutine(comp,routine_)
    else:
      print "Routine %s is Position Register" %routine_.Name
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
  program_=routine.Program
  executor_ = program_.Executor
  rob_cnt_ = executor_.Controller

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


  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
    #print "name %s" %rob_cnt_.Name
  if rob_cnt_.Name=="IRC5":
    producer_="ABB"
    header="MODULE %s\n" %rname
    pos_ = """ENDMODULE\n"""
    #head_ = 'MODULE'
    #filter_="*.mod"
    #upload_programs(program_,infile,filename_)
  elif rob_cnt_.Name=="R30iA":
    producer_ = "FANUC"
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
    """ % (rname, rname, td, td)
    pos_ = """/POS\n"""
    #head_ = '/PROG'
    #filter_ = "*.ls"
  text = header #

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
    #text+= "%4i:  " % statementCount
    line_data_=IntermediateConvert.getStatementData(statement)
    text+= writeLine(line_data_,producer_)#+";\n"
  # endfor

  text += pos_
  # positions = []
  # for s in routine.Statements:
  #   if s.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
  #     if s.getProperty('INDEX'):
  #       num = s.INDEX
  #     else:
  #       pName = s.Positions[0].Name
  #       num = int(pName[pName.rindex('_') + 1:])
  #     # endif
  #     positions.append((num, s))
  #   # endif
  # # endif
  # positions.sort()
  targets=IntermediateConvert.getTarget(routine)
  for t in targets:
    text += doWriteTargetDefinition(t)

  note.Note = text

def writeLine(line_data_,producer_):
  global text, statementCount, uframe_num, utool_num, label
  if producer_=="ABB":
    line=IntermediateConvertABB.writeLineABB(line_data_)

  elif producer_=="FANUC":
    line = "%4i:  " % statementCount
    line+=writeLineFanuc(line_data_)+";\n"

  return line

def writeLineFanuc( line_data_ ):
  global text, statementCount, uframe_num, utool_num, label
  statementCount += 1
  line=""
  # if line_data_=="":
  #   pass
    #line_data_=IntermediateConvert.getStatementData(statement)

  #print "data %s" %line_data_[0]
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


  #endif
  # line+="\n;"
  #statementCount += 1
  #text += line
  return line

def doWriteTargetDefinition(target_data_):

  # uf = download.GetBaseIndex( statement,controller )
  # ut = download.GetToolIndex( statement,controller )
  #
  # posFrame = statement.Positions[0]
  # t4 = download.getValue( posFrame, 'JointTurns4', 0 )
  # t5 = download.getValue( posFrame, 'JointTurns5', 0 )
  # t6 = download.getValue( posFrame, 'JointTurns6', 0 )
  # cf =download. getValue( posFrame, 'Configuration', 'F U T' )
  # config = '%s, %i, %i, %i' % (cf, t4, t5, t6 )
  #
  # group = 1
  # #print "pos %s" %posFrame.Name
  # # try:
  # if re.findall(obracket + "(?P<Nr>[0-9_]+)" + '(?P<comment>(\s*:.*)?)' + cbracket, posFrame.Name):
  #   match_ = re.search(obracket + "(?P<Nr>[0-9_]+)" + '(?P<comment>(\s*:.*)?)' + cbracket, posFrame.Name)
  #   if not match_.group('comment') == "":
  #     comment = ":"+match_.group('comment')
  #   else:
  #     comment = match_.group('comment')
  # elif re.findall("P(?P<Nr>[0-9]+)" ,posFrame.Name):
  #   comment=""
  # else:
  #   comment = ":"+posFrame.Name
  # #print "comment:%s" %comment
  # except:
  #   comment = None

  if target_data_[3] and target_data_[3] != target_data_[4]:
    line='P[%s%s]{ \n' % (target_data_[4],target_data_[3])
  else:
    line='P[%s%s]{ \n' % (target_data_[4],target_data_[3])
  #endif
  line+="    GP1:\n"
  line +="         UF : %i, UT : %i," % (target_data_[0], target_data_[1])
  # m = posFrame.PositionInReference
  # p = m.P
  # a = m.WPR
  line +="              CONFIG : '%s, %s, %s, %s',\n" % (target_data_[2][0],target_data_[2][1],target_data_[2][2],target_data_[2][3])
  line +="         X = %8.2f  mm,     Y = %8.2f  mm,     Z = %8.2f  mm,\n" % (target_data_[5][0],target_data_[5][1],target_data_[5][2])
  line +="         W = %8.2f deg,     P = %8.2f deg,     R = %8.2f deg" % (target_data_[5][3],target_data_[5][4],target_data_[5][5])
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
  #endfor
  line +="\n"
  line +="};\n"
  return line


def writeCall(call_data_):
  line="CALL %s" % (call_data_[0])
  if not call_data_[1]=="":
    line+="(%s" %call_data_[1]
    if not call_data_[2] == "":
      line += ",%s" % call_data_[2]
    line+=")"
  #line+=";\n"

  return line

def writeDelay(delay_data):
  return  "WAIT %6.2f(sec)" % (delay_data)

def writeComment(comment_data):
  if comment_data[:2] == '++':
    line = "%s" % (comment_data[2:])
  else:
    line = "!%s" % (comment_data)
  return line

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

  if set_out_data[2] == 1:
    set_out_data[2] = "ON"
  elif set_out_data[2] == 0:
    set_out_data[2] = "OFF"

  line = "DO[%i" %set_out_data[0]
  if not set_out_data[1]=="":
    line+="%s" %set_out_data[1]
  line+="]=%s"%set_out_data[2]

  return line

def writeWAIT(wait_data_):
  line = "WAIT "
  i=0
  if len(wait_data_)>1:
    line+="( "
    while i<=len(wait_data_)-1:
      line+=wait_data_[i][0]+"["+wait_data_[i][1]+":"+wait_data_[i][2]+"]=" +wait_data_[i][3]

      if i<len(wait_data_)-1 :
        if not wait_data_[i+1][0]=="":
          line+=" OR "
      i = i + 1
    line+=")"
  else:

    line += wait_data_[i][0] + "[" + wait_data_[i][1] + wait_data_[i][2] + "]=" +wait_data_[i][3]
  #line+=";\n"
  # if statement.Type=="Process":
  #   line="WAIT ("
  #   i=0
  #   while statement.getProperty("Variable %s" %(i+1)):
  #
  #     if re.search(r"(?P<var_type>[a-zA-Z]+)",statement.getProperty("Variable %s" %i).Value):
  #       #print "wait:%s" %statement.getProperty("Variable %s" %i).Value
  #       type_def_=re.search(
  #         r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]?)",
  #         statement.getProperty("Variable %s" % i).Value)
  #       #reg_type=type_def_.group("regType")
  #       type_ = type_def_.group("var_type")
  #       index_=type_def_.group("Nr")
  #       comment_=type_def_.group("comment")
  #       if not comment_=="":
  #         comment_=":"+comment_
  #       line+=type_+"["+index_+comment_+']='+str(statement.getProperty("Value %s" %i).Value)
  #       if statement.getProperty("Variable %s" % (i + 2)):
  #         if not statement.getProperty("Variable %s" % (i + 1)).Value=="":
  #           line += " OR "
  #     elif re.search("(?P<Nr>[0-9_]+)",statement.getProperty("Variable %s" %i).Value):
  #       nr_def=re.search("(?P<Nr>[0-9_]+)",statement.getProperty("Variable %s" %i).Value)
  #       #type_ = nr_def.group("var_type")
  #       type_="DI"
  #       if statement.getProperty("Value %s" %i).Value==1:
  #         value_="ON"
  #       elif statement.getProperty("Value %s" % i).Value == 0:
  #         value_ = "OFF"
  #       #print "type: %s" % type_
  #       if not type_=="DI":
  #         line += type_ + "[" + nr_def.group("Nr") + ":" + statement.getProperty("Comment %s" % i).Value + "]"
  #       else:
  #         line+="DI"+"["+nr_def.group("Nr")+":"+statement.getProperty("Comment %s" %i).Value+"]"+"="+value_
  #       if statement.getProperty("Variable %s" %(i+2)):
  #         if not statement.getProperty("Variable %s" % (i + 1)).Value=="":
  #           line += " OR "
  #     i+=1
  #
  #   line+=");\n"
  # else:
  #   if statement.InputPort < 1000:
  #     if not statement.Name == "":
  #       line = "WAIT DI[%i%s]=" % (statement.InputPort, statement.Name)
  #     else:
  #       line = "WAIT DI[%i]=" % (statement.InputPort)
  #   else:
  #     line = "WAIT RI[%i: %s]=" % (statement.InputPort - 1000, statement.Name)
  #   # endif
  #   if statement.InputValue:
  #     line += "ON ;\n"
  #   else:
  #     line += "OFF ;\n"
  # endif
  return line

def writeSetVariable(set_var_data_):

  line=set_var_data_[0]
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
  #line+=";\n"
  # type_def_=re.search(
  #         r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]+)",
  #   statement.TargetProperty)
  # if type_def_:
  #   target_property_ = type_def_.group("var_type")+"["+type_def_.group("Nr")+":"+type_def_.group("comment")+"]"
  #   if re.findall("Parameter",target_property_):
  #     return ";\n"
  # elif re.search(          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
  #   statement.TargetProperty):
  #   type_def_ = re.search(
  #     r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
  #     statement.TargetProperty)
  #   target_property_ = type_def_.group("var_type") + "[" + type_def_.group("Nr") + "]"
  #   # if re.findall("TIMER", target_property_):
  #   #   pass
  #
  # else:
  #
  #   target_property_=statement.TargetProperty
  #   #print "prop %s" % target_property_
  #   if re.findall("Parameter_",target_property_):
  #     return";\n"
  #
  # type_def_=re.search(
  #         r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]+)",
  #   statement.ValueExpression)
  # if type_def_:
  #   value_expression_ = type_def_.group("var_type")+"["+type_def_.group("Nr")+":"+type_def_.group("comment")+"]"
  #   if re.findall("Parameter",value_expression_):
  #     return ";\n"
  # elif re.search(          r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
  #   statement.ValueExpression):
  #   type_def_ = re.search(
  #     r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9]+)" ,
  #     statement.ValueExpression)
  #   value_expression_ = type_def_.group("var_type") + "[" + type_def_.group("Nr") + "]"
  # elif re.findall("Parameter_",statement.ValueExpression):
  #   nr_def_=re.search("Parameter_"+"(?P<Nr>[0-9]+)",statement.ValueExpression)
  #   value_expression_="AR["+nr_def_.group("Nr")+"]"
  # else:
  #   value_expression_=statement.ValueExpression

  return line

def writeIf(if_data_):
  global label,statementCount
  #text_part_=""
  #line=""
  #thenlabel = label
  #label += 1
  #elselabel = label
  #label += 1
  #condition_=if_data_[0]
  #print "line_data_ %s" %if_data_[1]
  if_data_[0]=transformCondition(if_data_[0])
  line = "IF %s," % (if_data_[0])
  for data_ in if_data_[1]:
    line+=writeLineFanuc(data_)

  #line +=";\n"
  # if statement.ThenScope.Statements[0].Type == "Process":
  #   if statement.ThenScope.Statements[0].getProperty("LabelNr"):
  #     thenlabel=statement.ThenScope.Statements[0].getProperty("LabelNr").Value
  #     line += "IF %s,JMP LBL[%s];\n" % (condition_, thenlabel)
  #   elif statement.ThenScope.Statements[0].getProperty("CallRoutine"):
  #     thenlabel=statement.ThenScope.Statements[0].getProperty("CallRoutine").Value
  #     if statement.ThenScope.Statements[0].getProperty("Parameter_1"):
  #       line += "IF %s,CALL %s(%s" % (condition_, thenlabel,statement.ThenScope.Statements[0].getProperty("Parameter_1").Value)
  #       if statement.ThenScope.Statements[0].getProperty("Parameter_2"):
  #         line += ",%s" % (
  #         statement.ThenScope.Statements[0].getProperty("Parameter_2").Value)
  #       line+=");\n"
  # elif statement.ThenScope.Statements[0].Type == VC_STATEMENT_CALL:
  #   thenlabel=statement.ThenScope.Statements[0].Routine.Name
  #   line += "IF %s,CALL %s;\n" % (
  #     condition_, thenlabel)
  #text_part_ += line

  #statementCount += 1

  if not if_data_[2]==[]:
    line += "ELSE"
  for s in if_data_[2]:
    #print "if_data %s" % if_data_[2]
    line+=writeLineFanuc(s)
  #text_part_ += line
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
  return line

def writeMotion(motion_data_):
  line=""
  global uframe_num, utool_num,statementCount
  # if not statement.getProperty('INDEX'):
  #   indices = {}
  #   maxIndex = 0
  #   for s in routine.Statements:
  #     if s.getProperty('INDEX'):
  #       indices[s.INDEX] = True
  #       if s.INDEX > maxIndex: maxIndex = s.INDEX
  #     # endif
  #   # endfor
  #   sName = statement.Positions[0].Name
  #   try:
  #     num = int(sName[sName.rindex('_') + 1:])
  #   except:
  #     try:
  #       for i in range(len(sName) - 1, -1, -1):
  #         if not sName[i:].isdigit():
  #           num = int(sName[i + 1:])
  #           break
  #         # endif
  #       # endfor
  #     except:
  #       num = maxIndex + 1
  #     # endtry
    # endtry

    # statement.createProperty(VC_INTEGER, 'INDEX')

    # statement.INDEX = num
    # if indices.get(num, False):
    #   statement.INDEX = maxIndex + 1
    #   """
    #   for i in range( 1, routine.StatementCount+2):
    #     if not indices.get( num, False ):
    #       statement.INDEX = i
    #       break
    #     #endif
    #   #endfor
    #   """
    # endif
  # endif

  # pointIndex = statement.INDEX

  if re.search("(?P<Nr>[0-9_]+)",motion_data_[0]):
    uf_def_=re.search("(?P<Nr>[0-9_]+)",motion_data_[0])
    motion_data_[0]=uf_def_.group('Nr')
    #print "motion %s" % motion_data_[0]
  if re.search("(?P<Nr>[0-9_]+)",motion_data_[1]):
    ut_def_=re.search("(?P<Nr>[0-9_]+)",motion_data_[1])
    motion_data_[1]=ut_def_.group('Nr')
  #print "statement count %s" % statementCount
  # uf = download.GetBaseIndex(statement, controller)
  if uframe_num != motion_data_[0]:
    uframe_num = motion_data_[0]
    line += "UFRAME_NUM = %s ;\n" % (motion_data_[0])

    line += "%4i:  " % statementCount
    statementCount += 1
    # endif
  #print "line %s" %line
  # ut = download.GetToolIndex(statement, controller)
  if utool_num != motion_data_[1]:
    utool_num = motion_data_[1]
    line += "UTOOL_NUM = %s ;\n" % (motion_data_[1])

    line += "%4i:  " % statementCount
    statementCount += 1
    # endif

  # zone = 'FINE'
  # pName = statement.Positions[0].Name
  # #print "name:%s" %pName
  # if pName[:2] == 'PR':
  #
  #   offset = 15
  #   posType = 'PR'
  #   index_def_=re.search("PR"+obracket+"(?P<Nr>[0-9_]+)",pName)
  #   pointIndex=index_def_.group('Nr')
  #   # line = "%4i:   ;\n" % statementCount
  #   # statementCount += 1
  #   # line += "%4i:  PR[%i,1:XYP] = PR[%i,1:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
  #   # statementCount += 1
  #   # line += "%4i:  PR[%i,2:XYP] = PR[%i,2:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
  #   # statementCount += 1
  #   # line += "%4i:  PR[%i,3:XYP] = PR[%i,3:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
  #   # statementCount += 1
  #   # line += "%4i:   ;\n" % statementCount
  #   # statementCount += 1
  #   # line += "%4i:  " % statementCount
  # else:
  #   posType = 'P'
  # # endif



  # if re.findall(obracket+"(?P<Nr>[0-9_]+)"+'(?P<comment>(\s*:.*)?)'+cbracket,pName):
  #   match_=re.search(obracket+"(?P<Nr>[0-9_]+)"+'(?P<comment>(\s*:.*)?)'+cbracket,pName)
  #   if not match_.group('comment')=="":
  #     if  match_.group('comment').split(":"):
  #       pName=":"+match_.group('comment').split(":")[1]
  #       #print "name:%s" % pName
  #   else:
  #     pName=match_.group('comment')
  # elif re.findall("P(?P<Nr>[0-9]+)", pName):
  #     pName = ""
  # else:
  #   pName=":"+pName

  # if statement.Type == VC_STATEMENT_LINMOTION:
  #   # print "pos %s" %statement.Positions[0].PositionInWorld.P.X
  #   line += "L %s[%s%s]  %gmm/sec %s" % (posType, pointIndex, pName, statement.MaxSpeed, zone)
  # elif statement.Type == VC_STATEMENT_PTPMOTION:
  #   line += "J %s[%s%s]  %g%% %s" % (posType, pointIndex, pName, statement.JointSpeed * 100, zone)
  # else:
  #   # print "pos %s" %statement.Positions[0].PositionInWorld.P.X
  #   line += "L %s[%s%s]  %gmm/sec %s" % (posType, pointIndex, pName, int(statement.getProperty('Speed').Value), zone)
  # # endif
  #
  # if statement.getProperty('Position'):
  #   line+=" ToolOffset,%s" %statement.getProperty('Register').Value

  if re.findall(obracket+"(?P<Nr>[0-9_]+)"+'(?P<comment>(\s*:.*)?)'+cbracket,motion_data_[5]):
    match_=re.search(obracket+"(?P<Nr>[0-9_]+)"+'(?P<comment>(\s*:.*)?)'+cbracket,motion_data_[5])
    if not match_.group('comment')=="":
      if  match_.group('comment').split(":"):
        motion_data_[5]=":"+match_.group('comment').split(":")[1]
        #print "name:%s" % pName
    else:
      motion_data_[5]=match_.group('comment')
  elif re.findall("P(?P<Nr>[0-9]+)", motion_data_[5]):
    motion_data_[5] = ""
  else:
    motion_data_[5]=":"+pName

  if motion_data_[2] == "joint":
    line += "J %s[%s%s]  %g%%"%(motion_data_[3], motion_data_[4], motion_data_[5],100*motion_data_[6])
  else:
    # print "pos %s" %statement.Positions[0].PositionInWorld.P.X
    line += "L %s[%s%s]  %gmm/sec" %(motion_data_[3], motion_data_[4], motion_data_[5], motion_data_[6])
  # endif

  line+=" %s" % (motion_data_[7])

  if not motion_data_[8]=="":
    line+=" ToolOffset,%s" %motion_data_[8]

  #line+=" ;\n"
  return line

def writeLabel(label_data_):
  return "LBL["+str(label_data_[0])+label_data_[1]+"] "

def writeJMP(jump_data_):
  return "JMP LBL["+str(jump_data_)+"] "

def writeReturn(return_data_):
  return "END "

def writeMessage(mess_data_):
  return "MESSAGE["+mess_data_+"] "

def transformCondition(data_):
  i=0
  transformed_condition_=""

  while i<len(data_):
    #transformed_condition_+=statement.Condition[i]
    #print "cond %s" % statement.Condition[i]
    if re.findall(r"(?P<signs>[\!\=\&\|]+)",data_[i]):
      sign_def = re.search(r"(?P<signs>[\!\=\&\|]+)",data_[i:i+2])
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
    elif re.findall("Parameter_"+"(?P<Nr>[0-9_]+)", data_[i:i+11]):
      type_def_=re.search("Parameter_"+"(?P<Nr>[0-9_]+)", data_[i:i+11])
      type_="AR["+type_def_.group('Nr')+"]"
      transformed_condition_+=type_
      i+=len("Parameter_"+type_def_.group('Nr'))
    elif re.findall(r"(?P<var_type>[a-zA-Z]+)",data_[i]):
      type_def_=re.search(r"(?P<var_type>[a-zA-Z]+)"+obracket+"(?P<Nr>[0-9_]+)"+cbracket,data_[i:i+9])

      if type_def_:
        value_=""
        sign_=""
        equal_=0
        equal_def_=re.search(r"(?P<signs>[\=\!]+)"+"(?P<value>[0-9_]+)",data_[i:i+11])

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

      elif re.search(r"(?P<regType>[a-zA-Z]+)"+"::",data_[i:i+12]):
        type_def_=re.search(
          r"(?P<regType>[a-zA-Z]+)" + "::" + r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z0-9\._]+)",
          data_[i:])
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
        transformed_condition_ += data_[i]
        i=i+1



    else:
      transformed_condition_ += data_[i]
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
