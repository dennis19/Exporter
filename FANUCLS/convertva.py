from vcCommand import *
import time
from decimal import *
import download
import re
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
  if not routine:
    app.messageBox("No Routine selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif

  if routine.Name == 'PositionRegister': return

  print 'Converting %s to LS' % routine.Name

  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller

  writeNumReg(comp)



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

def writeNumReg(comp):
  k = 0
  line = ""
  while k < len(comp.Properties):
    if re.findall("Registers::", comp.Properties[k].Name):
      reg_def_ = re.search("R" + "(?P<Nr>[0-9_]+)" + r'(.*)', comp.Properties[k].Name)
      if reg_def_:
        nr_ = reg_def_.group('Nr')
        comment_ = reg_def_.group(2)
        if int(nr_) > 200:
          comment_ = nr_[3:]
          nr_ = nr_[0:3]
        line += "  [" + nr_ + "] = " + str(comp.Properties[k].Value) + "  '" + comment_ + "'" + "\n"
    k += 1

  rname = "NUMREG"

  note = comp.findBehaviour(rname)
  if not note:
    note = comp.createBehaviour(VC_NOTE, rname)
  # endif

  comp.createProperty(VC_BOOLEAN, "%s::SkipExecution" % rname)

  header = """[*NUMREG*]$NUMREG  Storage: CMOS  Access: RW  : ARRAY[200] OF Numeric Reg
  """
  end_ = """
  [*NUMREG*]$MAXREGNUM  Storage: CMOS  Access: RW  : INTEGER = 200"""
  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  text = header
  text += line
  text += end_
  note.Note = text

def writeStatement( statement ):
  global text, statementCount, uframe_num, utool_num, label

  line = "%4i:  " % statementCount 

  if statement.Type == VC_STATEMENT_CALL:
    line+=writeCall(statement)

  elif statement.Type == VC_STATEMENT_DELAY:
    line +=writeDelay(statement)

  elif statement.Type == VC_STATEMENT_COMMENT:
    line+=writeComment(statement)


  elif statement.Type == VC_STATEMENT_SETBIN:
    line+=writeSetOutput(statement)

    #endif

  elif statement.Type == VC_STATEMENT_WAITBIN:
    line+=writeWAIT(statement)

  elif statement.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
    line+=writeMotion(statement)

  elif statement.Type == VC_STATEMENT_SETPROPERTY:
    line += writeSetVariable(statement)

  elif statement.Type == VC_STATEMENT_IF:
    line+=writeIf(statement)
  elif statement.Type == "Process":
    if re.findall("LBL",statement.Name):
      line+=writeLabel(statement)
    elif re.findall("WAIT",statement.Name):
      line+=writeWAIT(statement)
    elif re.findall("CALL", statement.Name):
      line += writeCall(statement)
    elif re.findall("JMP",statement.Name):
      line+=writeJMP(statement)
  elif statement.Type==VC_STATEMENT_RETURN:
    line+=writeReturn(statement)
  else:
    print statement.Type
    return 

  #endif

  statementCount += 1
  text += line
  return

def doWriteTargetDefinition(statement_nr,statement):

  uf = download.GetBaseIndex( statement,controller )
  ut = download.GetToolIndex( statement,controller )

  posFrame = statement.Positions[0]
  t4 = download.getValue( posFrame, 'JointTurns4', 0 )
  t5 = download.getValue( posFrame, 'JointTurns5', 0 )
  t6 = download.getValue( posFrame, 'JointTurns6', 0 )
  cf =download. getValue( posFrame, 'Configuration', 'F U T' )
  config = '%s, %i, %i, %i' % (cf, t4, t5, t6 )

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

  if comment and comment != str(statement_nr):
    line='P[%i%s]{ \n' % (statement_nr,comment)
  else:
    line='P[%i%s]{ \n' % (statement_nr,comment)
  #endif
  line+="    GP%i:\n" % group
  line +="         UF : %i, UT : %i," % (uf, ut)
  m = posFrame.PositionInReference
  p = m.P
  a = m.WPR
  line +="              CONFIG : '%s',\n" % config
  line +="         X = %8.2f  mm,     Y = %8.2f  mm,     Z = %8.2f  mm,\n" % (p.X,p.Y,p.Z)
  line +="         W = %8.2f deg,     P = %8.2f deg,     R = %8.2f deg" % (a.X,a.Y,a.Z)
  internalAxes = len(posFrame.InternalJointValues)
  i = 0
  for j, joint in enumerate( posFrame.ExternalJointValues ):
    if groups[j+internalAxes] == group:
      if j == 0: line+=",\n    "
      else: line+=","
    else:
      i = 0
      line +="\n"
      group = groups[j+internalAxes]
      line +="    GP%i:\n" % group
      line +="         UF : %i, UT : %i,\n    " % (uf, ut)
    #endif
    if i > 0 and i%3 == 0:
      ls.write("\n    ")
    #endif
    if group == 1:
      line +="     E%i = %8.2f %s" % (j+1, joint.Value, jUnits[internalAxes+j])
    else:
      line +="     J%i = %8.2f %s" % (i+1, joint.Value, jUnits[internalAxes+j])
    #endif
    i += 1
  #endfor
  line +="\n"
  line +="};\n"
  return line


def writeCall(statement):
  if statement.getProperty("Parameter_1"):
    line="CALL %s(%s" %(statement.getProperty("CallRoutine").Value,statement.getProperty("Parameter_1").Value)
    if statement.getProperty("Parameter_2"):
      line+=",%s" %statement.getProperty("Parameter_2").Value
    line+=");\n"
  else:
    line = "CALL %s;\n" % (statement.Routine.Name)
  return line

def writeDelay(statement):
  return  "WAIT %6.2f(sec) ;\n" % (statement.Delay)

def writeComment(statement):
  if statement.Comment[:2] == '++':
    line = "%s;\n" % (statement.Comment[2:])
  else:
    line = "!%s;\n" % (statement.Comment)
  return line

def writeSetOutput(statement):
  if statement.OutputPort < 1000:
    if not statement.Name=="":
      line = "DO[%i%s]=" % (statement.OutputPort, statement.Name)
    else:
      line = "DO[%i]=" % (statement.OutputPort)
  else:
    line = "RO[%i: %s]=" % (statement.OutputPort - 1000, statement.Name)
  # endif
  if statement.OutputValue:
    line += "ON ;\n"
  else:
    line += "OFF ;\n"
  return line

def writeWAIT(statement):
  if statement.Type=="Process":
    line="WAIT ("
    i=0
    while statement.getProperty("Variable %s" %(i+1)):

      if re.search(r"(?P<regType>[a-zA-Z]+)"+"::",statement.getProperty("Variable %s" %i).Value):
        type_def_=re.search(
          r"(?P<regType>[a-zA-Z]+)" + "::" + r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]+)",
          statement.getProperty("Variable %s" % i).Value)
        reg_type=type_def_.group("regType")
        type_ = type_def_.group("var_type")
        index_=type_def_.group("Nr")
        comment_=type_def_.group("comment")
        line+=type_+"["+index_+":"+comment_+']='+str(statement.getProperty("Value %s" %i).Value)
      elif re.search("(?P<Nr>[0-9_]+)",statement.getProperty("Variable %s" %i).Value):
        nr_def=re.search("(?P<Nr>[0-9_]+)",statement.getProperty("Variable %s" %i).Value)

        line+="DI"+"["+nr_def.group("Nr")+":"+statement.getProperty("Comment %s" %i).Value+"]"
      if statement.getProperty("Variable %s" %(i+2)):
        line+=" OR "
      i+=1

    line+=");\n"
  else:
    if statement.InputPort < 1000:
      if not statement.Name == "":
        line = "WAIT DI[%i%s]=" % (statement.InputPort, statement.Name)
      else:
        line = "WAIT DI[%i]=" % (statement.InputPort)
    else:
      line = "WAIT RI[%i: %s]=" % (statement.InputPort - 1000, statement.Name)
    # endif
    if statement.InputValue:
      line += "ON ;\n"
    else:
      line += "OFF ;\n"
  # endif
  return line

def writeSetVariable(statement):
  return "%s = %s;\n" %(statement.TargetProperty, statement.ValueExpression)

def writeIf(statement):
  global label,statementCount
  text_part_=""
  line=""
  thenlabel = label
  label += 1
  elselabel = label
  label += 1
  condition_=transformCondition(statement)
  if statement.ThenScope.Statements[0].Type == "Process":
    if statement.ThenScope.Statements[0].getProperty("LabelNr"):
      thenlabel=statement.ThenScope.Statements[0].getProperty("LabelNr").Value
      line += "IF %s,JMP LBL[%s];\n" % (condition_, thenlabel)
    elif statement.ThenScope.Statements[0].getProperty("CallRoutine"):
      thenlabel=statement.ThenScope.Statements[0].getProperty("CallRoutine").Value
      if statement.ThenScope.Statements[0].getProperty("Parameter_1"):
        line += "IF %s,CALL %s(%s" % (condition_, thenlabel,statement.ThenScope.Statements[0].getProperty("Parameter_1").Value)
        if statement.ThenScope.Statements[0].getProperty("Parameter_2"):
          line += ",%s" % (
          statement.ThenScope.Statements[0].getProperty("Parameter_2").Value)
        line+=");\n"
  elif statement.ThenScope.Statements[0].Type == VC_STATEMENT_CALL:
    thenlabel=statement.ThenScope.Statements[0].Routine.Name
    line += "IF %s,CALL %s;\n" % (
      condition_, thenlabel)
  text_part_ += line
  #statementCount += 1
  for s in statement.ElseScope.Statements:
    writeStatement(s)
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
  return text_part_

def writeMotion(statement):
  line=""
  global uframe_num, utool_num,statementCount
  if not statement.getProperty('INDEX'):
    indices = {}
    maxIndex = 0
    for s in routine.Statements:
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

  uf = download.GetBaseIndex(statement, controller)
  if uframe_num != uf:
    uframe_num = uf
    line += "UFRAME_NUM = %i ;\n" % (uf)
    statementCount += 1
    line += "%4i:  " % statementCount
    # endif

  ut = download.GetToolIndex(statement, controller)
  if utool_num != ut:
    utool_num = ut
    line += "UTOOL_NUM = %i ;\n" % (ut)
    statementCount += 1
    line += "%4i:  " % statementCount
    # endif

  zone = 'FINE'
  pName = statement.Positions[0].Name
  if pName[:2] == 'PR':
    offset = 15
    posType = 'PR'
    line = "%4i:   ;\n" % statementCount
    statementCount += 1
    line += "%4i:  PR[%i,1:XYP] = PR[%i,1:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
    statementCount += 1
    line += "%4i:  PR[%i,2:XYP] = PR[%i,2:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
    statementCount += 1
    line += "%4i:  PR[%i,3:XYP] = PR[%i,3:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex, offset)
    statementCount += 1
    line += "%4i:   ;\n" % statementCount
    statementCount += 1
    line += "%4i:  " % statementCount
  else:
    posType = 'P'
  # endif

  if re.findall(obracket+"(?P<Nr>[0-9_]+)"+'(?P<comment>(\s*:.*)?)'+cbracket,pName):
    match_=re.search(obracket+"(?P<Nr>[0-9_]+)"+'(?P<comment>(\s*:.*)?)'+cbracket,pName)
    if not match_.group('comment')=="":
      pName=":"+match_.group('comment')
    else:
      pName=match_.group('comment')
  elif re.findall("P(?P<Nr>[0-9]+)", pName):
      pName = ""
  else:
    pName=":"+pName

  if statement.Type == VC_STATEMENT_LINMOTION:
    # print "pos %s" %statement.Positions[0].PositionInWorld.P.X
    line += "L %s[%i%s]  %gmm/sec %s ;\n" % (posType, pointIndex, pName, statement.MaxSpeed, zone)
  elif statement.Type == VC_STATEMENT_PTPMOTION:
    line += "J %s[%i%s]  %g%% %s ;\n" % (posType, pointIndex, pName, statement.JointSpeed * 100, zone)
  # endif
  return line

def writeLabel(statement):
  return "LBL["+str(statement.getProperty("LabelNr").Value)+str(statement.getProperty("Comment").Value)+"] ;\n"

def writeJMP(statement):
  return "JMP LBL["+str(statement.getProperty("LabelNr").Value)+"] ;\n"

def writeReturn(statement):
  return "END ;\n"

def transformCondition(statement):
  i=0
  transformed_condition_=""

  while i<len(statement.Condition):
    #transformed_condition_+=statement.Condition[i]
    #print "cond %s" % statement.Condition[i]
    if re.findall(r"(?P<var_type>[a-zA-Z]+)",statement.Condition[i]):
      type_def_=re.search(r"(?P<var_type>[a-zA-Z]+)"+obracket+"(?P<Nr>[0-9_]+)"+cbracket,statement.Condition[i:i+6])

      if type_def_:
        type_ = type_def_.group("var_type")
      #print "char %s" % type_
        if type_=="IN":
          #print "nr %s"%type_def_.group("Nr")
          type_="DI"+"["+type_def_.group("Nr")+statement.getProperty("Comment%s"%type_def_.group("Nr")).Value+"]"
          transformed_condition_ +=type_
          i+=len("DI"+"["+type_def_.group("Nr")+"]")
        else:
          transformed_condition_ += type_
          i=i+len(type_)

      elif re.search(r"(?P<regType>[a-zA-Z]+)"+"::",statement.Condition[i:i+11]):
        type_def_=re.search(
          r"(?P<regType>[a-zA-Z]+)" + "::" + r"(?P<var_type>[a-zA-Z]+)" + "(?P<Nr>[0-9_]+)" + r"(?P<comment>[a-zA-Z]+)",
          statement.Condition[i:])
        reg_type=type_def_.group("regType")
        type_ = type_def_.group("var_type")
        index_=type_def_.group("Nr")
        comment_=type_def_.group("comment")

        transformed_condition_ += type_+"["+index_+":"+comment_+"]"#statement.Condition[i]
        #print "char:%s" % statement.Condition[i]
        i=i+len(reg_type+type_+index_+comment_)+2
        #i=i+1
      else:
        #print "char:%s" %statement.Condition[i]
        transformed_condition_ += statement.Condition[i]
        i=i+1
    elif re.findall(r"(?P<signs>[\=\&\|]+)",statement.Condition[i]):
      sign_def = re.search(r"(?P<signs>[\=\&\|]+)",statement.Condition[i:i+2])
      sign_ = sign_def.group("signs")
      i = i + len(sign_)
      if sign_=="==":
        sign_="="
      elif sign_=="&&":
        sign_="AND"
      elif sign_=="||":
        sign_="OR"
      transformed_condition_ += sign_


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
