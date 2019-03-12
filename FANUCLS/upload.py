from vcCommand import *
import re
import os.path
import vcMatrix
import uploadva
import uploadBackup
import IntermediateUpload
import glob
sp = r'\s+'
eq = r'\s*=\s*'
comma = r'\s*,\s*'
colon = r'\s*:\s*'
semicolon = r'\s*;\s*'
orbracket = r'\s*\(\s*'
crbracket = r'\s*\)\s*'
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
prnum= r'PR'+obracket+'(?P<pnum>'+integer+')'+ '(?P<comment>(?:\s*:.*)?)' + cbracket
uf = r'UF '+colon+' (?P<uf>'+integer+')'
ut = r'UT '+colon+' (?P<ut>'+integer+')'
ufhelp=r'UF ' +colon + sp 
fut = r'(?P<fut>[FN]\s*[UD]*\s*[TB]*)'
t1 = r'(?P<t1>'+integer+')'
t2 = r'(?P<t2>'+integer+')'
t3 = r'(?P<t3>'+integer+')'
cfg = r'CONFIG' + colon + '\''+ fut + comma + t1 + comma + t2 + '(?:'+comma + t3 +')?\s*\''

x = r'X ' + eq + r' (?P<x>'+real+')' + sp + 'mm'
y = r'Y ' + eq + r' (?P<y>'+real+')' + sp + 'mm'
z = r'Z ' + eq + r' (?P<z>'+real+')' + sp + 'mm'
w = r'W ' + eq + r' (?P<w>'+real+')' + sp + 'deg'
p = r'P ' + eq + r' (?P<p>'+real+')' + sp + 'deg'
r = r'R ' + eq + r' (?P<r>'+real+')' + sp + 'deg'

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

app_ = getApplication()
depth=0

glob_tool_=0
def cleanUp():
  setNextState(None)

#-------------------------------------------------------------------------------
def OnAbort():
  cleanUp()

#-------------------------------------------------------------------------------
def OnStop():
  cleanUp()

def addScript(comp_):
  script_ = comp_.findBehaviour( 'LSExecutor' )
  if not script:
    script_ = comp_.createBehaviour( VC_SCRIPT, 'LSExecutor' )
  if script_.Script != lsScript():
    script_.Script = lsScript()
  return

def upload_programs(program_,infile,filename_):
  # initialization
  ###
  routine_nr_=0
  global lineskip_, depth
  depth=0
  lineskip_ = [0, 0, 0, 0, 0, 0, 0, 0, 0,0,0,0,0,0,0,0,0,0,0]
  lineskip_[depth] = 0

  scope_ = None
  inst_flag_ = False
  instructions_ = ''
  executor_ = program_.Executor

  filestring_ = infile.read()
  infile.close()
  file_length_ = len(os.path.basename(filename_))
  rob_cnt_ = executor_.Controller


  # read in lines of file
  for line_ in filestring_.split('\n'):

    prog_ = re.match(r'/PROG' + sp + galphanum + '(?:\s+Macro)?' + end, line_)
    # create routine for file, if not there yet
    if prog_:
      progname_ = prog_.group(1)
      print "Prog:%s" % progname_
      program_.deleteRoutine(progname_)
      if progname_ == 'PNS0001':
        routine_ = program_.MainRoutine
      else:
        routine_ = program_.findRoutine(progname_)
        if not routine_:
          routine_ = program_.addRoutine(progname_)
      if len(routine_.Statements)>=3:
        routine_.clear()
      ###continue
    # endif

    # read from main till position
    mn_ = re.match(r'/MN' + end, line_)
    if mn_:
      inst_flag_ = True
      ###continue
    # endif

    pos_ = re.match(r'/POS' + end, line_)
    if pos_:
      break
    # endif
    # create statements, if if then skip lines
    if inst_flag_:
      if lineskip_[depth] != 0:
        lineskip_[depth] = lineskip_[depth] - 1
        continue
      else:
        createStatement(line_, rob_cnt_, routine_, program_, filestring_, scope_);
    # endif
    instructions_ += line_ + '\n'
  # endfor
  routine_instructions_=''
  for routine in routine_.Program.Routines:
    print "routine %s" %routine.Name
    if not routine.Name== "PNS0001" and not routine== routine_:
      print "Reading routine %s" %routine.Name
      routine_file_ = glob.glob(filename_[0:len(filename_) - file_length_] + routine.Name+".ls" )
      if routine_file_:
        if len(routine.Statements)<3:
          routine_file_main_ = open(routine_file_[0], "r")
          upload_programs(program_, routine_file_main_, filename_)
      #   # endif
        routine_instructions_ += line_ + '\n'
      else:
        print " \'%s\' is not a program file" % routine.Name
  routine_nr_=routine_nr_+1


  return True


def OnStart():
  program_ = uploadBackup.getActiveProgram()
  if not program_:
    app_.messageBox("No program selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif
  routine_nr_=0
  global lineskip_, depth
  depth=0
  lineskip_ = [0, 0, 0, 0, 0, 0, 0, 0, 0,0,0,0,0,0,0,0,0,0,0]
  lineskip_[depth] = 0

  scope_ = None
  inst_flag_ = False
  instructions_ = ''
  executor_ = program_.Executor
  #file_length_ = len(os.path.basename(filename_))
  rob_cnt_ = executor_.Controller

  ok_=True
  #read in .ls files in backup folder
  opencmd_ = app_.findCommand("dialogOpen")
  uri_ = ""
  file_filter_ = "FANUC Robot Program files (*.ls)|*.ls"
  opencmd_.execute(uri_,ok_,file_filter_)
  if not opencmd_.Param_2:
    print "No file selected for uploading, aborting command"
    return
  #endif
  uri_ = opencmd_.Param_1
  filename_ = uri_[8:len(uri_)]
  print "%s" % uri_
  try:
    infile = open(filename_,"r")
  except:
    print "Cannot open file \'%s\' for reading" % filename_
    return
  filestring_ = infile.read()
  infile.close()
  #endtry

  for line_ in filestring_.split('\n'):

    prog_ = re.match(r'/PROG' + sp + galphanum + '(?:\s+Macro)?' + end, line_)
    # create routine for file, if not there yet
    if prog_:
      progname_ = prog_.group(1)
      print "Prog:%s" % progname_
      program_.deleteRoutine(progname_)
      if progname_ == 'PNS0001':
        routine_ = program_.MainRoutine
      else:
        routine_ = program_.findRoutine(progname_)
        if not routine_:
          routine_ = program_.addRoutine(progname_)
      if len(routine_.Statements)>=3:
        routine_.clear()
      ###continue
    # endif

    # read from main till position
    mn_ = re.match(r'/MN' + end, line_)
    if mn_:
      inst_flag_ = True
      ###continue
    # endif

    pos_ = re.match(r'/POS' + end, line_)
    if pos_:
      break
    # endif
    # create statements, if if then skip lines
    if inst_flag_:
      if lineskip_[depth] != 0:
        lineskip_[depth] = lineskip_[depth] - 1
        continue
      else:
        createStatement(line_, rob_cnt_, routine_, program_, filestring_, scope_);
    # endif
    instructions_ += line_ + '\n'
  # endfor

  #upload_programs(program_,infile,filename_)
  return True
#function parameter structure to follow: line,robCnt,routine,program,filestring,scope!
def createStatement(line,robCnt,routine,program,filestring,scope):
  global depth
  depth=depth+1
  if re.findall("  !",line):
    s=createComment(line,routine,scope)
    depth = depth - 1
    return s
  elif re.findall(":J ",line):
    s=createPTP(line,robCnt,routine,filestring,scope,program)#+
    depth = depth - 1
    return s
  elif re.findall(":L ",line):
    s=createLinear(line,robCnt,routine,filestring,scope,program)#+
    depth = depth - 1
    return s
  elif re.findall(" IF",line):
    s=createIF(line,routine,filestring,scope,program)#+
    depth = depth - 1
    return s
  elif re.findall("DO"+obracket+"(?P<Nr>[a-zA-Z0-9_]+)"+ '(?P<comment>(?:\s*:.*)?)'+cbracket+eq,line):
    s=createSetDO(line,routine,scope)#+
    depth = depth - 1
    return s
  elif re.findall("WAIT   "+"(?P<value>[\s.a-zA-Z0-9_]+)",line):
    s=createDelay(line,routine,scope)
    depth = depth - 1
    return s
  elif re.findall("WAIT ",line):
    s=createWaitDI(line,routine,scope)#+
    depth = depth - 1
    return s
  elif re.findall('SELECT',line):
    s=createSELECT(line,robCnt,routine,filestring,scope,program)
    depth = depth - 1
    return s
  elif re.findall("CALL",line):
    s=createCall(line,routine,scope,program)
    depth = depth - 1
    return s
  elif re.findall("LBL",line)and not re.findall('JMP',line):
    s=createLBL(line,routine,scope)
    depth = depth - 1
    return s
  elif re.findall('JMP',line):
    s=createJMP(line,routine,scope)
    depth = depth - 1
    return s
  elif re.findall('END',line):
    s=createReturn(routine,scope)
    depth = depth - 1
    return s
  elif re.findall("MESSAGE",line):
    s=createMessage(line,routine,scope)
    depth = depth - 1
    return s
  elif re.findall('UTOOL',line):
    setGlobTool(line)
    depth = depth - 1
  elif re.findall(r"(?P<var_type>[a-zA-Z/!]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket+eq,line):
    s= createAssignStatement(line,routine,scope)
    depth = depth - 1
    return s
  else:
    depth = depth - 1
#endfct

def createMessage(line,routine,scope):
  s=addStatement(scope,routine,VC_STATEMENT_PRINT)
  s.Message=IntermediateUpload.getMessage(line)

  return s

def setGlobTool(line):
  global glob_tool_
  tool_def_=re.search("UTOOL_NUM"+eq+"(?P<Nr>[0-9_]+)",line)
  glob_tool_=tool_def_.group('Nr')

#find PosName
def readPos(s,line,robCnt,filestring,type,program):
  global glob_tool_
  exec_ = program.Executor
  rob_cnt_ = exec_.Controller
  kin_ = rob_cnt_.Kinematics
  comp_ = kin_.Component
  #[point,speed,coordinates,configuration,base,tool]
  move_data_=IntermediateUpload.getMovementData(line,filestring,type)
  if type=="joint":
    if move_data_[1][1] == "":
      s.JointSpeed = int(move_data_[1][0])/100
    else:
      if comp_.getProperty("R" + move_data_[1][0] + uploadva.delChars(move_data_[1][1])):
        s.JointSpeed = int(comp_.getProperty("R" + move_data_[1][0] + uploadva.delChars(move_data_[1][1])).Value) / 100

  elif type=="lin":

    if move_data_[1][1]=="":
      s.MaxSpeed = int(move_data_[1][0])
    else:

      if comp_.getProperty("Registers::R" + move_data_[1][0] + uploadva.delChars(move_data_[1][1])):
        s.MaxSpeed = int(comp_.getProperty("Registers::R" + move_data_[1][0] + uploadva.delChars(move_data_[1][1])).Value)


  m = vcMatrix.new()
  m.translateAbs(move_data_[2][0], move_data_[2][1], move_data_[2][2])
  m.setWPR( move_data_[2][3],  move_data_[2][4],  move_data_[2][5])

  posFrame = s.Positions[0]
  posFrame.PositionInReference = m
  posFrame.Name = move_data_[0]
  posFrame.Configuration = move_data_[3]
  if move_data_[4]== 0:
    s.Base = robCnt.Bases[0]
  else:
    s.Base = robCnt.Bases[move_data_[4]-1]
  #endif
  if move_data_[5] == 0:
    s.Tool = robCnt.Tools[0]
  else:
    s.Tool = robCnt.Tools[move_data_[5]-1].Name

def readTool(line):
  toolMatch=re.search(ut,line)
  toolDef=0
  if toolMatch:
    toolDef= int(toolMatch.group('ut'))
  return toolDef	
	
def readBase(line):
  baseMatch=re.search(uf,line)
  baseDef=0
  if baseMatch:
    baseDef= int(baseMatch.group('uf'))
  return baseDef	

def readToolOffset(line,program,routine_,scope_):

  if re.findall(",PR",line):

    pos_reg_off_def_=re.search(","+prnum,line)
    if pos_reg_off_def_:
      callRoutine = program.findRoutine("POSREG_PR[" + pos_reg_off_def_.group('pnum') + pos_reg_off_def_.group('comment') + "]" )

      if callRoutine:
        offset_vec_vc_=vcMatrix.new()
        offset_statement_=callRoutine.Statements[0]
        offset_vec_=offset_statement_.Positions[0].PositionInReference.P
        offset_vec_vc_.translateAbs(-offset_vec_.Z,-offset_vec_.X,offset_vec_.Y)
        offset_vec_vc_.WPR=offset_statement_.Positions[0].PositionInReference.WPR

    pos_def_ = re.search(prnum, line)
    if pos_def_:
      callRoutine = program.findRoutine(
        "POSREG_PR[" + pos_def_.group('pnum') + pos_def_.group('comment').split("]")[0] + "]")

      if callRoutine:
        pos_statement_ = callRoutine.Statements[0]
        pos_=vcMatrix.new()
        pos_vec_ = pos_statement_.Positions[0].PositionInReference.P
        pos_wpr_ = pos_statement_.Positions[0].PositionInReference.WPR
        pos_.translateAbs(pos_vec_.X,pos_vec_.Y,pos_vec_.Z)
        pos_.WPR=pos_wpr_
        pos_.translateRel(offset_vec_.X,offset_vec_.Y,offset_vec_.Z)

    exec_ = program.Executor
    rob_cnt_ = exec_.Controller
    kin_ = rob_cnt_.Kinematics
    comp_ = kin_.Component

    s = addStatement(scope_, routine_, 'Process')

    ph_ = comp_.createBehaviour('rPythonProcessHandler', 'ToolOffset')
    pos=s.createPosition("PR[" + pos_def_.group('pnum') + pos_def_.group('comment').split("]")[0] + "]")
    ph_.Script = TOOL_OFFSET_SCRIPT()
    s.Process = ph_
    s.Name = 'ToolOffset'
    s.Base=pos_statement_.Base
    if not glob_tool_ == 0:
      s.Tool = rob_cnt_.Tools[int(glob_tool_)-1].Name
    else:
      s.Tool = pos_statement_.Tool
    print "tool mat %s" %s.Tool.PositionMatrix.getWPR().X

    pos.PositionInReference = pos_
    return s

		  
def setConfiguration(line):
  cfgMatch = re.search(cfg,line)
  cfgDef=""
  if cfgMatch:
    cfgDef= cfgMatch.group('fut')
  return cfgDef	
		  
def setCoordinates(matchString,matchVar,line):
  matched=re.search(matchString,line)
  idmatched=0
  if matched:
    idmatched = float(matched.group(matchVar))	
  return idmatched

def createSELECT(line,robCnt,routine,filestring,scope,program):
  global lineskip_,depth
  in_select_=0
  line_nr_=getLineNr(line)
  for line_select_ in filestring.split('\n'):
    select_choices_= re.search(eq+"(?P<Nr>[0-9_]+)"+comma,line_select_)
    if re.findall('ELSE,',line_select_):
      in_select_=0
      selse=createStatement(line_select_,robCnt,routine,program,filestring,s.ElseScope)
      if selse:
        s.ElseScope.Statements.append(selse)
        setLineSkip()

    if (line_nr_ == getLineNr(line_select_) and in_select_==0) or  (in_select_==1 and select_choices_):
      s = addStatement(scope, routine, VC_STATEMENT_IF)
      call_fct_=re.search(",CALL",line_select_)
      jmp_fct_ = re.search(",JMP", line_select_)
      if call_fct_:
        sthen = createCall(line_select_,routine, s.ThenScope, program)
        s.ThenScope.Statements.append(sthen)
      elif jmp_fct_:
        sthen = createJMP(line_select_,routine,s.ThenScope)
        s.ThenScope.Statements.append(sthen)
      s.Condition = makeConodition(line, 'SELECT')+select_choices_.group("Nr")
      if in_select_==1:
        setLineSkip()
      in_select_=1
      continue
  return s

def createIF(line,routine,filestring,scope,program):
  #create IfStatement
  s = addStatement(scope, routine, VC_STATEMENT_IF)
  s.Condition=makeConodition(line,'IF')

  line_nr_=getLineNr(line)

  #create Statements in if
  for lineIf in filestring.split('\n'):

    if line_nr_==getLineNr(lineIf):
      call_fct_=re.search(",CALL",lineIf)
      createJMP(lineIf,routine,s.ThenScope)
      if call_fct_:
        sthen=createCall(lineIf,routine, s.ThenScope, program)
        s.ThenScope.Statements.append(sthen)
        break
      elif re.findall(comma+r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq,line):
        sthen=createAssignStatement(line,routine,s.ThenScope)
        s.ThenScope.Statements.append(sthen)
  return s

def createPTP(line,robCnt,routine,filestring,scope,program):
  posr_name_= re.search(prnum,line)
  if posr_name_:
    callRoutine = program.findRoutine("POSREG_PR[" + posr_name_.group('pnum') + posr_name_.group('comment') + "]")
    s = addStatement(scope, routine, VC_STATEMENT_CALL)
    s.Routine = callRoutine
  else:
    s = addStatement(scope, routine, VC_STATEMENT_PTPMOTION)
    readPos(s,line,robCnt,filestring,"joint",program)
  return s
  
def createLinear(line,robCnt,routine,filestring,scope,program):
  posr_name_= re.search(prnum,line)
  if re.findall("Tool_Offset,", line):
    s= readToolOffset(line,program,routine,scope)
  else:
    if posr_name_:
      callRoutine = program.findRoutine("POSREG_PR[" + posr_name_.group('pnum') + posr_name_.group('comment') + "]")
      s = addStatement(scope, routine, VC_STATEMENT_CALL)
      s.Routine = callRoutine
    else:
      s = addStatement(scope, routine, VC_STATEMENT_LINMOTION)
      readPos(s,line,robCnt,filestring,"lin",program)
  return s
  
def createSetDO(line,routine,scope):

  s = addStatement(scope, routine, VC_STATEMENT_SETBIN)

  set_data=IntermediateUpload.getSetDO(line)
  s.OutputPort=int(set_data[1])
  if set_data[2] == 'ON':
    s.OutputValue=1
  elif set_data[2] == 'OFF':
    s.OutputValue=0
  
  return s  

def createDelay(line, routine, scope):
  wait_data = IntermediateUpload.getWait(line)

  s=addStatement(scope, routine, VC_STATEMENT_DELAY)

  s.Delay= float(wait_data[2][0])

  return s

def createWaitDI(line,routine,scope):
  #print"%s" %line
  wait_data=IntermediateUpload.getWait(line)

  if wait_data[0][0]=="DI":
    s = addStatement(scope, routine, VC_STATEMENT_WAITBIN)

    s.InputPort=int(wait_data[1][0])
    if wait_data[2][0] == 'ON':
      s.InputValue=1
    elif wait_data[2][0] == 'OFF':
      s.InputValue=0
  else:
    i =0
    var_=["","","",""]
    var_value_=["","","",""]
    var_comment_=["","","",""]
    while i<=len(wait_data[0])-1:
      #print "%s" %wait_data[0][i]
      if wait_data[0][i]=="F":
        wait_data[0][i] = "Flags::F"
      elif wait_data[0][i]=="R":
        wait_data[0][i] = "Registers::R"
      elif wait_data[0][i] == "DI":
        wait_data[0][i] = "IN"
      var_value_[i]=wait_data[2][i]
      var_comment_[i]=uploadva.delChars(wait_data[3][i])
      if wait_data[0][i] == "IN":
        var_[i] = wait_data[1][i]
      else:
        var_[i] = wait_data[0][i]  + wait_data[1][i] + var_comment_[i]
      if var_value_[i]=='ON':
        var_value_[i]=1
      elif var_value_[i]=='OFF' or var_value_[i]=="":
        var_value_[i]=0
      i=i+1
    s=WAIT(scope,routine,var_,var_comment_,var_value_)
  return s	    
  
def createComment(line,routine,scope):
  s = addStatement(scope, routine, VC_STATEMENT_COMMENT)
  s.Comment=IntermediateUpload.getComment(line)
  return s

def createCall(line,routine,scope,program):
  exec_ = routine.Program.Executor
  rob_cnt_ = exec_.Controller
  kin_ = rob_cnt_.Kinematics
  comp_ = kin_.Component
  propertyCounter = 0
  call_data=IntermediateUpload.getCall(line)
  if call_data[1]:

    s = addStatement(scope, routine, 'Process')
    ph_ = comp_.createBehaviour('rPythonProcessHandler', 'ParamCallScript')
    ph_.Script = CALL_PARAM_HANDLER_SCRIPT()
    s.Process = ph_

    s.createProperty(VC_STRING, 'CallRoutine')
    s.getProperty('CallRoutine').Value = call_data[0]

    callRoutine = program.findRoutine( call_data[0] )
    if not callRoutine:
      callRoutine = program.addRoutine( call_data[0] )
      print "Routine %s created" %callRoutine.Name
    if call_data[1]:
      i=0
      s.createProperty(VC_INTEGER, 'Parameter_1')
      s.getProperty('Parameter_1').Value = int(call_data[1])
      if not callRoutine.getProperty('Parameter_1'):
        callRoutine.createProperty(VC_INTEGER, 'Parameter_1')
      if len(callRoutine.Statements)==0:
        createAssign(callRoutine, scope, callRoutine.getProperty('Parameter_1').Name, call_data[2])
      else:
        while callRoutine.Statements[i]:
          if callRoutine.Statements[i].Type == VC_STATEMENT_SETPROPERTY:
            propertyCounter += 1
          if i == len(callRoutine.Statements)-1:
            break
          i += 1
        if propertyCounter<1:
          createAssign(callRoutine, scope, callRoutine.getProperty('Parameter_1').Name, call_data[2])

    if call_data[2]:
      s.createProperty(VC_INTEGER, 'Parameter_2')
      s.getProperty('Parameter_2').Value = int(call_data[2])
      if not callRoutine.getProperty('Parameter_2'):
        callRoutine.createProperty(VC_INTEGER, 'Parameter_2')
      if len(callRoutine.Statements)==0:
        createAssign(callRoutine, scope, callRoutine.getProperty('Parameter_2').Name, call_data[2])
      else:
        while callRoutine.Statements[i]:
          if callRoutine.Statements[i].Type == VC_STATEMENT_SETPROPERTY:
            propertyCounter += 1
          if i==len(callRoutine.Statements)-1:
            break
          i += 1
        if propertyCounter<2:
          createAssign(callRoutine, scope, callRoutine.getProperty('Parameter_2').Name, call_data[2])
    s.Name='CALL ' +s.getProperty('CallRoutine').Value
  else:
    s = addStatement(scope, routine, VC_STATEMENT_CALL)

    callRoutine = program.findRoutine( call_data[0] )
    if not callRoutine:
      callRoutine = program.addRoutine( call_data[0] )
      print "Routine %s created" % callRoutine.Name
    s.Routine=callRoutine

  return s
  
def readSpeed(line,s):
    if s.Type==VC_STATEMENT_PTPMOTION:
      speed=re.search(r"(?P<speed>[a-zA-Z0-9_]+)%",line)
      s.JointSpeed=int(speed.group('speed'))/100
    elif s.Type==VC_STATEMENT_LINMOTION:
      speed=re.search(r"(?P<speed>[a-zA-Z0-9_]+)mm" ,line)
      s.MaxSpeed=int(speed.group('speed'))


def createJMP(line,routine_,scope):
  JmpLblGroup = re.search("JMP (?P<JmpLbl>[a-zA-Z0-9\[\]\:_]+)", line)
  if JmpLblGroup:
    JmpLbl = JmpLblGroup.group('JmpLbl')
    JmpLblNrGroup = re.search("LBL" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)", JmpLbl)
    nr_ = JmpLblNrGroup.group('Nr')

    exec_ = routine_.Program.Executor
    rob_cnt_=exec_.Controller
    kin_=rob_cnt_.Kinematics
    comp_=kin_.Component
    s=addStatement(scope,routine_,'Process')

    #create Processhandler
    ph_ = comp_.createBehaviour('rPythonProcessHandler', 'JMPProcessHandler')
    ph_.Script = JMP_GET_PROCESS_HANDLER_SCRIPT()
    s.Process = ph_
    s.createProperty(VC_STRING, "LabelNr")
    s.getProperty("LabelNr").Value = nr_

    s.Name = "JMP"+str(s.getProperty("LabelNr").Value)
    return s
  else:
    return None

def WAIT(scope_,routine_,var_,var_comment_,var_value_,):
  exec_ = routine_.Program.Executor
  rob_cnt_ = exec_.Controller
  kin_ = rob_cnt_.Kinematics
  comp_ = kin_.Component

  s=addStatement(scope_,routine_,'Process')

  # create Processhandler
  ph_ = comp_.createBehaviour('rPythonProcessHandler', 'WAITProcessHandler')
  ph_.Script = WAIT_GET_PROCESS_HANDLER_SCRIPT()
  s.Process = ph_
  i=0
  while i<=len(var_)-1:
    s.createProperty(VC_STRING, "Variable %s"%i)
    s.createProperty(VC_INTEGER, "Value %s"%i)
    s.getProperty("Variable %s"%i).Value = var_[i]
    s.getProperty("Value %s"%i).Value = int(var_value_[i])
    i=i+1
  s.Name = "WAIT"
  return s

def createLBL(line_,routine_,scope_):
  exec_ = routine_.Program.Executor
  rob_cnt_ = exec_.Controller
  kin_ = rob_cnt_.Kinematics
  comp_ = kin_.Component

  s=addStatement(scope_,routine_,'Process')
  nr_match_=re.search("LBL" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket,line_)
  nr_=nr_match_.group('Nr')
  # create Processhandler
  ph_ = comp_.createBehaviour('rPythonProcessHandler', 'LBLProcessHandler')
  s.Process = ph_
  s.createProperty(VC_INTEGER, "LabelNr")
  s.getProperty("LabelNr").Value = int(nr_)

  s.Name = "LBL"+str(s.getProperty("LabelNr").Value)
  return s

def createReturn(routine_,scope_):
  s=addStatement(scope_,routine_,VC_STATEMENT_RETURN)
  return s
def createAssignStatement(line,routine,scope):
  set_var_data_=IntermediateUpload.getSetVariable(line)
  if not set_var_data_[0]=="":
    s = addStatement(scope,routine,VC_STATEMENT_SETPROPERTY)

    var_=set_var_data_[0]+set_var_data_[1]+uploadva.delChars(set_var_data_[2])
    value_ = set_var_data_[3] + set_var_data_[4] + uploadva.delChars(set_var_data_[5])
    if re.findall("ON",value_):
      value_=1
    elif re.findall("OFF",value_):
      value_=0
    elif value_=="AR1":
      value_=routine.getProperty("Parameter_1").Name
    elif value_ == "AR2":
      value_ = routine.getProperty("Parameter_2").Name
    s.TargetProperty = str(var_)
    s.ValueExpression= str(value_)
    return s

def createAssign(routine_,scope_,var_,value_):
  i = 0
  s = routine_.addStatement(VC_STATEMENT_SETPROPERTY)
  if routine_.Statements[i].Type==VC_STATEMENT_SETPROPERTY:
    s.TargetProperty=str(var_)
  return s

def makeConodition(line,if_sel_):
  cond_all_=''
  cond_all_conv_=''
  cond=''
  char_skip=0
  g_int_=0
  if if_sel_=='IF':
    char_skip=10
  elif if_sel_=='SELECT':
    char_skip=14
  while re.search(r"(?P<signs>[\(\)\!\s\,]+)", line[len(cond_all_) + char_skip]) or re.search(r"(?P<var_type>[a-zA-Z]+)" + obracket ,
                 line[len(cond_all_) + char_skip:len(cond_all_) + char_skip + 4]) or re.search(r"(?P<logic>[a-zA-Z]+)", line[len(cond_all_) + char_skip]):
    condition_=IntermediateUpload.getCondition(line,cond_all_,char_skip)
    cond_all_+=condition_[0]+condition_[1]+condition_[2]+condition_[3]+condition_[4]+condition_[5]+condition_[6]
    if re.findall('DI', condition_[0]):
      condition_[0] = 'IN[' + condition_[2] + ']'
    elif re.findall('R' + obracket, condition_[0]+condition_[1]):
      condition_[3]=uploadva.delChars(condition_[3])
      condition_[0] = "Registers::" + condition_[0]+condition_[2]+condition_[3]
    elif re.findall('RI' + obracket, condition_[0]+condition_[1]):
      condition_[3]=uploadva.delChars(condition_[3])
      condition_[0] = "RobotInput::" + condition_[0]+condition_[2]+condition_[3]
    elif re.findall('UO' + obracket, condition_[0]+condition_[1]):
      condition_[3]=uploadva.delChars(condition_[3])
      condition_[0] = "UserOutput::" + condition_[0]+condition_[2]+condition_[3]
    elif re.findall('UI' + obracket, condition_[0]+condition_[1]):
      condition_[3]=uploadva.delChars(condition_[3])
      condition_[0] = "UserInput::" + condition_[0]+condition_[2]+condition_[3]
    elif re.findall('F' + obracket, condition_[0]+condition_[1]):
      condition_[3]=uploadva.delChars(condition_[3])
      condition_[0]= "Flags::" +condition_[0]+condition_[2]+condition_[3]
    elif re.findall ('SI'+obracket,condition_[0]+condition_[1]):
      condition_[3]=uploadva.delChars(condition_[3])
      condition_[0]= condition_[0]+condition_[2]+condition_[3]
    elif condition_[0] == "AND":
      condition_[0] = '&&'
    elif condition_[0] == "OR":
      condition_[0] = '||'
    elif condition_[0]==',':
      break
    if condition_[6] == "ON":
      condition_[6] = '1'
    elif condition_[6] == "OFF":
      condition_[6] = '0'
    if condition_[5] == "=":
      condition_[5] = '=='
    elif condition_[5]=='<>':
      condition_[5]="!="
    if if_sel_=='SELECT':
      condition_[6]=""

    cond_all_conv_ += condition_[0]+condition_[5]+condition_[6]#+condition_[1]+condition_[2]
  return cond_all_conv_

def addStatement(scope_,routine_,vc_type_):
  if scope_:
    if scope_.ParentStatement.Type == VC_STATEMENT_IF or scope_.ParentStatement.Type == VC_STATEMENT_WHILE:
      s = scope_.addStatement(vc_type_)
  else:
    s = routine_.addStatement(vc_type_)
  return s

def getLineNr(line):
  line_nr_match=re.search("(?P<line_number_>[\s0-9_]+):",line)
  if line_nr_match:
    line_nr_=line_nr_match.group('line_number_')
    return line_nr_
  else:
    return ""
def setLineSkip():
  global lineskip_,depth
  i=0

  while i<=depth-1:
    lineskip_[i]=lineskip_[i]+1
    i=i+1


def WAIT_GET_PROCESS_HANDLER_SCRIPT():
  return """
from vcRslProcessHandler import *
from vcBehaviour import *
import vcMatrix
app = getApplication()
comp = getComponent()

#---------------- STATEMENT EXECUTION -----------------
def OnStatementExecute(exec_, stat):
  i=0
  property=["","","","",""]
  curr_state_=exec_.CurrentStatement
  while True:
    i=0
    cont_=0
    while i<=2:
      if comp.getProperty(curr_state_.getProperty("Variable %s" %i).Value):
        if comp.getProperty(curr_state_.getProperty("Variable %s" %i).Value).Value==curr_state_.getProperty("Value %s" %i).Value:
          cont_=1
          break

      elif exec_.DigitalInputSignals.input(int(curr_state_.getProperty("Variable %s" %i).Value)):
        cont_=1
        break
      print "Waiting for %s" %curr_state_.getProperty("Variable %s" %i).Value
      i=i+1
      delay(0.1)
    if cont_==1:
      break
  

"""

def JMP_GET_PROCESS_HANDLER_SCRIPT():
  return """
from vcRslProcessHandler import *
from vcBehaviour import *
import vcMatrix
app = getApplication()
comp = getComponent()

#---------------- STATEMENT EXECUTION -----------------
def OnStatementExecute(exec_, stat):
  i=0
  index=0
  curr_state_=exec_.CurrentStatement
  print "start"
  while index<=len(curr_state_.ParentRoutine.Statements)-1:
    if exec_.CurrentStatement==curr_state_.ParentRoutine.Statements[index]:
      break
    if curr_state_.ParentRoutine.Statements[index].Type=="IfElse":
      state=curr_state_.ParentRoutine.Statements[index].ThenScope.Statements[0].Type
      #print "state %s" %state
      if exec_.CurrentStatement==curr_state_.ParentRoutine.Statements[index].ThenScope.Statements[0]:
        index=index+1
        break


      #break
    index=index+1
  label_nr_=curr_state_.getProperty("LabelNr").Value
  #print "index:%s" %index
  while i<= len(curr_state_.ParentRoutine.Statements)-1:
    if curr_state_.ParentRoutine.Statements[i].Name=="LBL%s" %label_nr_:
      print "%s" %i
      break
    i=i+1
  if i<index:
    while i<index-1:
      print "i<index%s" %i
      CallState(curr_state_.ParentRoutine.Statements[i+1],exec_)
      delay(0.01)  
      i=i+1
      
  if i>index:
    print "i%s" %i
    k=index
    #while i<len(curr_state_.ParentRoutine.Statements)-1:
    #  CallState(curr_state_.ParentRoutine.Statements[i+1],exec_)
    #  delay(0.01)

      #print "i>index%s" %i
    #  i=i+1

    while index<=k<len(curr_state_.ParentRoutine.Statements)-1:
      curr_state_.ParentRoutine.Statements.remove(curr_state_.ParentRoutine.Statements[k])
      print "state deleted%s" %curr_state_.ParentRoutine.Statements[k].Type
      #print "deleted"
      k=k+1

def CallState(statement_,exec_):
  z=0
  #if statement_.Type=="IfElse":
  #  while z<len(statement_.ThenScope.Statements):
  #    CallState(statement_.ThenScope.Statements[z],exec_)
      #print "%s"%z
  #    z=z+1
  #else:
  #  exec_.callStatement(statement_,False)
  #  print "state executed%s" %statement_.Type
  exec_.callStatement(statement_,False)
  print "state executed%s" %statement_.Type
"""

def TOOL_OFFSET_SCRIPT():
  return """
from vcRslProcessHandler import *
from vcBehaviour import *
import vcMatrix
app = getApplication()
comp = getComponent()

#---------------- STATEMENT EXECUTION -----------------
def OnStatementExecute(exec_, stat):
  exec_.Controller.moveTo(stat.Positions[0].PositionInReference)

"""


def CALL_PARAM_HANDLER_SCRIPT():
  return """
from vcRslProcessHandler import *
from vcBehaviour import *
#from vcHelper import *
import vcMatrix
app = getApplication()
comp = getComponent()

#---------------- STATEMENT EXECUTION -----------------
def OnStatementExecute(exec_, stat):
  curr_state_=exec_.CurrentStatement
  routine_=exec_.Program.findRoutine(curr_state_.getProperty('CallRoutine').Value)
  if curr_state_.getProperty('Parameter_1'):
    routine_.Statements[0].ValueExpression=str(curr_state_.getProperty('Parameter_1').Value)
  if curr_state_.getProperty('Parameter_2'):
    routine_.Statements[1].ValueExpression=str(curr_state_.getProperty('Parameter_2').Value)

  exec_.callRoutine(routine_,False,False)

"""


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
