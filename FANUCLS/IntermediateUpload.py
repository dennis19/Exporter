from vcCommand import *
import re
import os.path
import vcMatrix
import uploadBackup
import IntermediateUploadABB
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

nl = r' *\r?[\n\0]'
sl = r'\A|\n'
end = r'\s*$'

pnum_ = r'P'+obracket+'(?P<pnum>'+integer+')'+ '(?P<comment>(?:\s*:.*)?)' + cbracket
prnum= r'PR'+obracket+'(?P<pnum>'+integer+')'+ '(?P<comment>(?:\s*:.*)?)' + cbracket
rnum= r'R'+obracket+'(?P<pnum>'+integer+')'+ '(?P<comment>(?:\s*:.*)?)' + cbracket
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

j1=r'J1' + eq + r'(?P<j1>'+real+')' + sp + 'deg'
j2=r'J2' + eq + r'(?P<j2>'+real+')' + sp + 'deg'
j3=r'J3' + eq + r'(?P<j3>'+real+')' + sp + 'deg'
j4=r'J4' + eq + r'(?P<j4>'+real+')' + sp + 'deg'
j5=r'J5' + eq + r'(?P<j5>'+real+')' + sp + 'deg'
j6=r'J6' + eq + r'(?P<j6>'+real+')' + sp + 'deg'

j= j1+ sp +j2+ sp +j3+ sp +j4+ sp +j5+ sp +j6

xyzwpr = x + sp + y + sp + z + sp + w + sp + p + sp + r 

fut = r'(?P<fut>[FN]\s*[UD]*\s*[TB]*)'
t1 = r'(?P<t1>'+integer+')'
t2 = r'(?P<t2>'+integer+')'
t3 = r'(?P<t3>'+integer+')'
config = r'Config' + colon + fut + comma + t1 + comma + t2 + comma + t3 

frame = obracket + ginteger + comma + ginteger + cbracket + eq + 'Group' + colon + ginteger + sp + config + sp + xyzwpr
re_frame = re.compile( frame, re.M )

posregistercart = obracket + ginteger + comma + ginteger + cbracket + eq + r"\'(.*)\'"  + sp + 'Group' + colon + ginteger + sp + config + sp + xyzwpr
re_posregcart = re.compile( posregistercart, re.M )

posregisterjoint = obracket + ginteger + comma + ginteger + cbracket + eq + r"\'(.*)\'"  + sp + 'Group' + colon + ginteger + sp  +j#+ config + sp + xyzwpr
re_posregjoint = re.compile( posregisterjoint, re.M )



numregister = obracket + ginteger + cbracket + eq + greal + r"\s*\'(.*)\'"
re_numreg = re.compile( numregister, re.M )

sysframe = r'\[\*SYSTEM\*\]' + r'(?P<FrameID>\$[a-zA-Z]+\w*)' + r'(.*)'
posreg = r'\[\*POSREG\*\]' + r'(?P<FrameID>\$[a-zA-Z]+\w*)' + r'(.*)'
numreg = r'\[\*NUMREG\*\]' + r'(?P<FrameID>\$[a-zA-Z]+\w*)' + r'(.*)'

app = getApplication()

def cleanUp():
  setNextState(None)

#-------------------------------------------------------------------------------
def OnAbort():
  cleanUp()

#-------------------------------------------------------------------------------
def OnStop():
  cleanUp()

#translate statement depending on producer in intermediate language
def getStatementProducer(line,filestring,producer_,line_cnt_,skip):

  #print "line cnt %s" %line_cnt_
  if producer_=="ABB":
    statement_data_=IntermediateUploadABB.getStatement(line,filestring,line_cnt_,skip)

  elif producer_=="FANUC":

    statement_data_ = getStatement(line, filestring)
    statement_data_.append(0)
  line_cnt_=statement_data_[2]
  statement_data_.append(line_cnt_)
  return statement_data_

# read in line to find command and get data for statement (FANUC)
def getStatement(line,filestring):

  if re.findall("//",line):
    statement_type_=""
    data_=""
  elif re.findall("  !", line):
    statement_type_ = "Comment"
    data_ = getComment(line)
  elif re.findall(":J ", line):
    statement_type_ = "JointMovement"
    data_ = getMovementData(line, filestring, "joint")
  elif re.findall(":L ", line):
    statement_type_ = "LinearMovement"
    data_ = getMovementData(line, filestring, "lin")
  elif re.findall(" IF", line):
    statement_type_ = "If"
    data_ = getIf(line,filestring)
  elif re.findall("DO" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket + eq, line):
    statement_type_ = "SetOutput"
    data_ = getSetDO(line)
  elif re.findall("WAIT   " + "(?P<value>[\s.a-zA-Z0-9_]+)", line):
    statement_type_ = "WaitTime"
    data_ = getWait(line)
  elif re.findall("WAIT ", line):
    statement_type_ = "Wait"
    data_ = getWait(line)
  elif re.findall('SELECT', line):
    statement_type_ = "Switch"
    data_ = getSelect(line, filestring)
  elif re.findall("CALL", line):
    statement_type_ = "Call"
    data_ = getCall(line)
  elif re.findall("LBL", line) and not re.findall('JMP', line):
    statement_type_ = "Label"
    data_ = getLabel(line)
  elif re.findall('JMP', line):
    statement_type_ = "Jump"
    data_ = getJMP(line)
  elif re.findall('END', line):
    statement_type_ = "Return"
    data_ = ""
  elif re.findall("MESSAGE", line):
    statement_type_ = "Print"
    data_ = getMessage(line)
  elif re.findall('UTOOL', line):
    statement_type_ = "Tool"
    data_ = getGlobTool(line)
  elif re.findall("UFRAME", line):
    statement_type_ = "Frame"
    data_ = getGlobFrame(line)
  elif re.findall(
          r"(?P<var_type>[a-zA-Z/!]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket + eq,
          line):
    statement_type_ = "SetVariable"
    data_ = getSetVariable(line)
  else:
    print "Statement not translated : %s" %line
    statement_type_ = ""
    data_ = ""

  return [statement_type_, data_]

#read in JointMovement Data
def getMovementData(line_,filestring_,type_):
  joints=[0,0,0,0,0,0]
  idx=0
  idy=0
  idz=0
  idp=0
  idr=0
  idw=0
  cfgData=""
  tool=0
  base=0
  skip = 1
  point_=""
  speed_=[100,""]
  acc_=[0,""]
  accel_ = [0, ""]
  offset_data_=["",""]
  posname = re.search(pnum_,line_)
  #read in speed and coordinates

  if posname:
    point_="P["+posname.group('pnum')+"]"

    speed_=getSpeed(line_,type_)
    acc_=getAccuracy(line_)
    accel_=getAcceleration(line_)
    for lineFindPos in filestring_.split('\n'):
      FindPosMatch=re.findall('P'+obracket+posname.group('pnum')+ '(?P<comment>(?:\s*:.*)?)'+cbracket+obrace,lineFindPos)
      if FindPosMatch:
        for lineFindCoord in filestring_.split('\n'):
          if lineFindCoord != lineFindPos and skip==1:
             continue
          else:
            skip=0

          if re.findall("};",lineFindCoord):
            skip=1
            break
          if idx==0:
            idx=getCoordinates(x,'x',lineFindCoord)
          if idy==0:
            idy=getCoordinates(y,'y',lineFindCoord)
          if idz==0:
            idz=getCoordinates(z,'z',lineFindCoord)
          if idp==0:
            idp=getCoordinates(p,'p',lineFindCoord)
          if idr==0:
            idr=getCoordinates(r,'r',lineFindCoord)
          if idw==0:
            idw=getCoordinates(w,'w',lineFindCoord)
          if joints[0]==0:
            joints[0]=getCoordinates(j1,'j1',lineFindCoord)
            #print "joints [00 %s" %joints[0]
          if joints[1] == 0:
            joints[1] = getCoordinates(j2, 'j2', lineFindCoord)
          if joints[2] == 0:
            joints[2] = getCoordinates(j3, 'j3', lineFindCoord)
          if joints[3] == 0:
            joints[3] = getCoordinates(j4, 'j4', lineFindCoord)
          if joints[4] == 0:
            joints[4] = getCoordinates(j5, 'j5', lineFindCoord)
          if joints[5] == 0:
            joints[5] = getCoordinates(j6, 'j6', lineFindCoord)
          if cfgData=="":
            cfgData=getConfiguration(lineFindCoord)

          if tool == 0:
            tool=getTool(lineFindCoord)
          if base==0:
            base=getBase(lineFindCoord)
  elif re.search(prnum,line_):
    posr_name_=re.search(prnum,line_)
    point_="PR["+posr_name_.group('pnum') + posr_name_.group('comment')+"]"
    speed_=getSpeed(line_,type_)
    acc_ = getAccuracy(line_)
    accel_=getAcceleration(line_)
  # get Tooloffset
  if re.findall("Tool_Offset,PR",line_):
    offset_data_=getToolOffset(line_)


  coordinates_=[idx,idy,idz,idw,idp,idr]
  moveData=[point_,speed_,coordinates_,cfgData,base,tool,offset_data_,acc_,joints,accel_]
  return moveData

def getToolOffset(line):

  if re.findall(",PR",line):

    pos_reg_off_def_=re.search(","+prnum,line)
    if pos_reg_off_def_:
      offset_pos_="PR["+pos_reg_off_def_.group('pnum') + pos_reg_off_def_.group('comment')+"]"

    pos_def_ = re.search(prnum, line)
    if pos_def_:
      pos_="PR[" + pos_def_.group('pnum') + pos_def_.group('comment').split("]")[0] + "]"

    return [offset_pos_,pos_]


def getAccuracy(line):
  # print "line %s" %line
  acc_data_=["",""]
  if re.search("CNT"+"(?P<Nr>[0-9_]+)",line):
    acc_def_=re.search("CNT"+"(?P<Nr>[0-9_]+)",line)
    acc_data_[0]=acc_def_.group('Nr')
  elif re.search("CNT "+rnum,line):
    acc_def_=re.search("CNT "+rnum, line)
    comment = acc_def_.group('comment')
    register = acc_def_.group('pnum')
    acc_data_[0] = register
    acc_data_[1] = comment.split("]")[0]
  elif re.search("FINE",line):
    acc_data_[0]="fine"

  return acc_data_

def getAcceleration(line):
  accel_data_=["",""]
  #print "line %s" %line
  if re.search("ACC"+"(?P<Nr>[0-9_]+)",line):
    print " accel %s" % accel_data_
    acc_def_=re.search("ACC"+"(?P<Nr>[0-9_]+)",line)
    accel_data_[0]=acc_def_.group('Nr')
  elif re.search("ACC "+rnum,line):
    acc_def_=re.search("ACC "+rnum, line)
    comment = acc_def_.group('comment')
    register = acc_def_.group('pnum')
    accel_data_[0] = register
    accel_data_[1] = comment.split("]")[0]
  # elif re.search("FINE",line):
  #   acc_data_[0]="fine"
  return accel_data_

def getSpeed(line_, type_):
  speed_data=["",""]
  print "hii"
  if re.search(sp+r"R" + obracket, line_) and (re.search(cbracket+"%", line_) or re.search(cbracket+"mm", line_)) :
    speed_ = re.search(rnum, line_)
    if speed_:

      comment = speed_.group('comment')
      register = speed_.group('pnum')
      speed_data[0] = register
      speed_data[1] = comment.split("]")[0]
  elif type_=="joint":
    speed_ = re.search(r"(?P<speed>[a-zA-Z0-9_]+)%", line_)
    speed_data[0] = speed_.group('speed')
  elif type_ == "lin":
    speed_ = re.search(r"(?P<speed>[a-zA-Z0-9_]+)mm", line_)
    speed_data[0]=speed_.group('speed')


  return speed_data

def getConfiguration(line):
  cfgMatch = re.search(cfg,line)
  cfgDef=""
  if cfgMatch:
    cfgDef= cfgMatch.group('fut')
  return cfgDef

def getCoordinates(matchString,matchVar,line):
  matched=re.search(matchString,line)
  idmatched=0
  if matched:
    #print "matched %s" %line
    idmatched = float(matched.group(matchVar))
  return idmatched


def getJoint(matchString,matchVar,line):

  matched=re.search(matchString,line)
  idmatched=0
  if matched:
    #print "matched %s" %line
    idmatched = float(matched.group(matchVar))
  return idmatched

def getTool(line):
  toolMatch = re.search(ut, line)
  toolDef = 0
  if toolMatch:
    toolDef = int(toolMatch.group('ut'))
  return toolDef


def getBase(line):
  baseMatch = re.search(uf, line)
  baseDef = 0
  if baseMatch:
    baseDef = int(baseMatch.group('uf'))
  return baseDef

def getWait(line):
  i=0
  var_comment_split_=["","","",""]
  value_=["","","",""]
  variable_type_=["","","",""]
  variable_nr_=["","","",""]

  port_value_ = re.search(
     "WAIT  "+"(?P<value>[\s.a-zA-Z0-9_]+)"  ,
     line)
  if port_value_:
    value_[i]=port_value_.group('value')
    wait_data = [variable_type_, variable_nr_, value_, var_comment_split_]

    return wait_data
  port_value_ = re.search(
    "WAIT "+orbracket+r"(?P<var_type>[a-zA-Z/!]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket ,
    line)
  if not port_value_:
    port_value_ = re.search(
      "WAIT "  + r"(?P<var_type>[a-zA-Z]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket,
      line)
  if not port_value_:
    port_value_ = re.search(
      "WAIT " + orbracket+orbracket+ r"(?P<var_type>[a-zA-Z]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket,
      line)
  variable_type_[i]=port_value_.group('var_type')
  variable_nr_[i]=port_value_.group('Nr')

  var_comment_ = port_value_.group('comment')
  var_comment_split_[i] = var_comment_.split(']')[0]
  value_def_ = re.search(variable_type_[i] + obracket + variable_nr_[i] + var_comment_split_[i] + cbracket +r"(?P<eq>[\=\<\>]+)" + r"(?P<value>[a-zA-Z0-9]+)", line)
  if value_def_:
    value_[i] = value_def_.group('value')
  # if len(var_comment_.split(']'))<2:
  #   wait_data = [variable_type_, variable_nr_, value_, var_comment_split_]
  #   return wait_data
  if i<len(var_comment_.split(']'))-1:
    i = i + 1
  else:
    wait_data = [variable_type_, variable_nr_, value_, var_comment_split_]
    return wait_data

  while re.findall("OR",var_comment_.split(']')[i]) or re.findall("AND",var_comment_.split(']')[i]):
    port_value_ = re.search(
       r"(?P<var_type>[a-zA-Z/!]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' ,
      var_comment_.split(']')[i])
    print "var%s" %var_comment_.split(']')[i]
    variable_type_[i] = port_value_.group('var_type')
    variable_nr_[i] = port_value_.group('Nr')

    var_comment_split_[i] = port_value_.group('comment')

    if not i < len(var_comment_.split(']'))-1:
      break
    value_def_ = re.search(
      variable_type_[i] + obracket + variable_nr_[i] + var_comment_split_[i]  +r"(?P<eq>[\=\<\>]+)" + r"(?P<value>[a-zA-Z0-9]+)", var_comment_.split("]")[i]+var_comment_.split("]")[i+1])
    if value_def_:
      value_[i] = value_def_.group('value')

    if re.search(orbracket,var_comment_.split(']')[i+1]):
      print "break"
    i = i + 1

  wait_data=[variable_type_,variable_nr_,value_,var_comment_split_]

  return wait_data

def getSetDO(line):
  port_value_ = re.search(
    r"(?P<var_type>[a-zA-Z]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket + eq + "(?P<value>[a-zA-Z0-9_]+)",
    line)

  variable_type_=port_value_.group('var_type')
  variable_nr_=port_value_.group('Nr')
  value_=port_value_.group('value')
  comment_=port_value_.group('comment')


  set_data = [variable_type_, variable_nr_, value_,comment_]
  return set_data

def getComment(line):
  #print "line %s" %line
  commentString = re.search(r"!(.*)",line)#("!(?P<comment>[a-zA-Z0-9_\-\s\:\/\=\>\[\]\.\,\(\)\!\*\?\+]+)", line)
  comment_=commentString.group(0)[1:-1]
  return comment_

def getIf(line,filestring):
  then_data_=[]
  else_data=[]

  cond_def_=re.search("IF "+r'(.*)'+comma,line)
  if not cond_def_:
    cond_def_=re.search("IF "+r'(.*)'+"THEN",line)
  cond_=cond_def_.group(0)
  print "cond %s" %cond_
  #condition_
  then_data_.append(getStatement(line[7:],filestring))
  else_data.append("")
  return [cond_,then_data_,else_data]

def getSelect(line,filestring):
  in_select_=0
  line_nr_=getLineNr(line)
  cases = []
  selse=[]
  case_number=[]
  cond_def_=re.search("SELECT "+r'(.*)'+comma,line)
  cond_=cond_def_.group(0)

  for line_select_ in filestring.split('\n'):
    select_choices_= re.search(eq+"(?P<Nr>[0-9_]+)"+comma,line_select_)
    then_data_=[]
    if re.findall('ELSE,',line_select_) and in_select_:
      in_select_=0
      selse.append(getStatement(line_select_,filestring))

    if (line_nr_ == getLineNr(line_select_) and in_select_==0) or  (in_select_==1 and select_choices_):
      case_number.append(select_choices_.group('Nr'))
      call_fct_ = re.search(",CALL", line_select_)
      if call_fct_:
        then_data_.append(["Call", getCall(line_select_)])
      elif re.findall(",JMP", line_select_):
        then_data_.append(["Jump", getJMP(line_select_)])
      elif re.findall(
              comma + r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq,
              line_select_):
        then_data_.append(["SetVariable", getSetVariable(line_select_)])
      cases.append(then_data_)
      if in_select_==1:
        pass
      in_select_=1
      continue

  return [cond_,cases,case_number,selse]

def getGlobFrame(line):
  tool_def_=re.search("UFRAME_NUM"+eq+"(?P<Nr>[0-9_]+)",line)
  return tool_def_.group('Nr')

def getGlobTool(line):
  tool_def_=re.search("UTOOL_NUM"+eq+"(?P<Nr>[0-9_]+)",line)
  return tool_def_.group('Nr')
  #return

def getLineNr(line):
  line_nr_match=re.search("(?P<line_number_>[\s0-9_]+):",line)
  if line_nr_match:
    line_nr_=line_nr_match.group('line_number_')
    return line_nr_
  else:
    return ""

def getCondition(line,cond_all_,char_skip):
  condition_ = ["", "", "","","","",""]

  if re.search(r"(?P<signs>[\(\)\!\s\,\$\.]+)", line[len(cond_all_) + char_skip]):
    conddef_ = re.search(r"(?P<signs>[\(\)\!\s\,\$\.]+)", line[len(cond_all_) + char_skip])
    cond=conddef_.group('signs')
    condition_[0] = cond
  elif re.search(r"(?P<var_type>[a-zA-Z]+)" + obracket ,
                 line[len(cond_all_) + char_skip:len(cond_all_) + char_skip + 4]):
    conddef_=re.search(
      r"(?P<var_type>[a-zA-Z]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket ,
      line[len(cond_all_) + char_skip:])

    condition_[0]=conddef_.group('var_type')
    condition_[1]='['
    condition_[2]=conddef_.group('Nr')

    comment=conddef_.group('comment')
    comment=comment.split("]")
    condition_[3]=comment[0]
    condition_[4]=']'
    value_def_=re.search(conddef_.group('var_type')+obracket+conddef_.group('Nr')+comment[0]+cbracket+r"(?P<eq>[\=\<\>]+)"+r"(?P<value>[a-zA-Z0-9]+)",line[len(cond_all_) + char_skip:])
    condition_[6]=""
    condition_[5]=""
    if value_def_:
      condition_[6]= value_def_.group('value')
      condition_[5] = value_def_.group('eq')
  elif re.search(r"(?P<logic>[a-zA-Z]+)", line[len(cond_all_) + char_skip]):
    conddef_ = re.search(
      r"(?P<logic>[a-zA-Z]+)" ,line[len(cond_all_) + char_skip:])
    logic_=conddef_.group('logic')
    logic_=logic_.split(' ')
    cond=logic_[0]
    condition_[0] = cond

  return condition_

def getCall(line):
  call_data=["","",""]
  callDef = re.search(
    "CALL (?P<routine>[a-zA-Z0-9_]+)" + orbracket + '(?P<param1>[a-zA-Z0-9_]+)' + comma + '(?P<param2>[a-zA-Z0-9_]+)' + crbracket,
    line)
  if callDef:
    call_data=[callDef.group('routine'),callDef.group('param1'),callDef.group('param2')]
  elif re.search(
    "CALL (?P<routine>[a-zA-Z0-9_]+)" + orbracket + '(?P<param1>[a-zA-Z0-9_]+)' + crbracket,
    line):
    callDef=re.search(
    "CALL (?P<routine>[a-zA-Z0-9_]+)" + orbracket + '(?P<param1>[a-zA-Z0-9_]+)' + crbracket,
    line)
    call_data = [callDef.group('routine'), callDef.group('param1'),""]
  else:
    callDef=re.search(
    "CALL (?P<routine>[a-zA-Z0-9_]+)",
    line)
    call_data = [callDef.group('routine'), "",""]
  return call_data

def getLabel(line):
  nr_match_=re.search("LBL" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket,line)
  nr_=nr_match_.group('Nr')
  comment_=nr_match_.group('comment')

  return [nr_,comment_]
def getJMP(line):
  JmpLblGroup = re.search("JMP (?P<JmpLbl>[a-zA-Z0-9\[\]\:_]+)", line)
  jmp_data_=""
  if JmpLblGroup:
    JmpLbl = JmpLblGroup.group('JmpLbl')
    JmpLblNrGroup = re.search("LBL" + obracket + "(?P<Nr>[a-zA-Z0-9\[\]_]+)"+cbracket, JmpLbl)
    jmp_data_ = JmpLblNrGroup.group('Nr')
  return jmp_data_

def getSetVariable(line):
  set_var_data=["","","","","",""]
  set_var_def_ = re.search(
      comma+r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq + "(?P<value>[\(\)\.a-zA-Z0-9_]+)",
      line)
  if set_var_def_:
    variable_type1_ = set_var_def_.group('var_type1')
    variable_nr1_ = set_var_def_.group('Nr1')
    var_comment1_ = set_var_def_.group('comment1')
    value_ = set_var_def_.group('value')

    set_var_data = [variable_type1_, variable_nr1_, var_comment1_, value_, "", ""]
    return set_var_data

  set_var_def_ = re.search(
      r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq + r"(?P<var_type2>[a-zA-Z/!]+)" + obracket + "(?P<Nr2>[a-zA-Z0-9_]+)" + '(?P<comment2>(?:\s*:.*)?)' + cbracket,
      line)
  if set_var_def_:
    variable_type1_ = set_var_def_.group('var_type1')
    variable_nr1_ = set_var_def_.group('Nr1')
    var_comment1_ = set_var_def_.group('comment1')
    variable_type2_ = set_var_def_.group('var_type2')
    variable_nr2_ = set_var_def_.group('Nr2')
    var_comment2_ = set_var_def_.group('comment2')
    set_var_data=[variable_type1_,variable_nr1_,var_comment1_,variable_type2_,variable_nr2_,var_comment2_]


  else:
    set_var_def_ = re.search(
      r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq + "(?P<value>[\(\)\.a-zA-Z0-9_]+)",
      line)
    variable_type1_ = set_var_def_.group('var_type1')
    variable_nr1_ = set_var_def_.group('Nr1')
    var_comment1_ = set_var_def_.group('comment1')
    value_ = set_var_def_.group('value')
    set_var_data = [variable_type1_, variable_nr1_, var_comment1_, value_, "", ""]


  return set_var_data

def getMessage(line):
  message_def_=re.search("MESSAGE"+obracket+r'(.*)'+cbracket,line)
  message=""

  if message_def_:
    message=message_def_.group(0)[8:len(message_def_.group(0))-2]
  return message

def setLineSkip():
  global lineskip_,depth
  i=0

  while i<=depth-1:
    lineskip_[i]=lineskip_[i]+1
    i=i+1

