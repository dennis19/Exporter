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

def getStatementProducer(line,filestring,producer_):
  if producer_=="ABB":
    statement_data_=IntermediateUploadABB.getStatement(line,filestring)
    #print "ABB"

  elif producer_=="FANUC":
    statement_data_ = getStatement(line, filestring)
  return statement_data_

def getStatement(line,filestring):
  if re.findall("  !", line):
    statement_type_ = "Comment"
    data_ = getComment(line)
    return [statement_type_, data_]
  elif re.findall(":J ", line):
    statement_type_ = "JointMovement"
    data_ = getMovementData(line, filestring, "joint")
    return [statement_type_, data_]
  elif re.findall(":L ", line):
    statement_type_ = "LinearMovement"
    data_ = getMovementData(line, filestring, "lin")
    return [statement_type_, data_]
  elif re.findall(" IF", line):
    statement_type_ = "If"
    data_ = getIf(line)
    return [statement_type_, data_]
  elif re.findall("DO" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket + eq, line):
    statement_type_ = "SetOutput"
    data_ = getSetDO(line)
    return [statement_type_, data_]
  elif re.findall("WAIT   " + "(?P<value>[\s.a-zA-Z0-9_]+)", line):
    statement_type_ = "WaitTime"
    data_ = getWait(line)
    return [statement_type_, data_]
  elif re.findall("WAIT ", line):
    statement_type_ = "Wait"
    data_ = getWait(line)
    return [statement_type_, data_]
  elif re.findall('SELECT', line):
    statement_type_ = "Switch"
    data_ = getSelect(line, filestring)
    return [statement_type_, data_]
  elif re.findall("CALL", line):
    statement_type_ = "Call"
    data_ = getCall(line)
    return [statement_type_, data_]
  elif re.findall("LBL", line) and not re.findall('JMP', line):
    statement_type_ = "Label"
    data_ = getLabel(line)
    return [statement_type_, data_]
  elif re.findall('JMP', line):
    statement_type_ = "Jump"
    data_ = getJMP(line)
    return [statement_type_, data_]
  elif re.findall('END', line):
    statement_type_ = "Return"
    data_ = ""
    return [statement_type_, data_]
  elif re.findall("MESSAGE", line):
    statement_type_ = "Print"
    data_ = getMessage(line)
    return [statement_type_, data_]
  elif re.findall('UTOOL', line):
    statement_type_ = "Tool"
    data_ = getGlobTool(line)
    return [statement_type_, data_]
  elif re.findall("UFRAME", line):
    statement_type_ = "Frame"
    data_ = getGlobFrame(line)
    return [statement_type_, data_]
  elif re.findall(
          r"(?P<var_type>[a-zA-Z/!]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket + eq,
          line):
    statement_type_ = "SetVariable"
    data_ = getSetVariable(line)
    return [statement_type_, data_]
  else:
    # print "Statement not translated : %s" %line
    statement_type_ = ""
    data_ = ""
    return [statement_type_, data_]
#read in JointMovement Data
def getMovementData(line_,filestring_,type_):
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
  speed_=0
  offset_data_=["",""]
  posname = re.search(pnum_,line_)
  #read in speed and coordinates
  if posname:
    point_="P["+posname.group('pnum')+"]"

    speed_=getSpeed(line_,type_)
    for lineFindPos in filestring_.split('\n'):
      FindPosMatch=re.findall('P'+obracket+posname.group('pnum')+cbracket+obrace,lineFindPos)
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
  if re.findall("Tool_Offset,PR",line_):
    offset_data_=getToolOffset(line_)

  #print "WPR %s,%s,%s point %s" %(idp,idr,idw,point_)

  coordinates_=[idx,idy,idz,idw,idp,idr]
  moveData=[point_,speed_,coordinates_,cfgData,base,tool,offset_data_]
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


def getSpeed(line_, type_):
  speed_data=["",""]
  if re.search(r" R" + obracket, line_):

    speed_ = re.search(rnum, line_)
    if speed_:

      comment = speed_.group('comment')
      register = speed_.group('pnum')
      speed_data[0] = register
      speed_data[1] = comment.split("]")[0]
  elif type_=="joint":


    speed_ = re.search(r"(?P<speed>[a-zA-Z0-9_]+)%", line_)
    speed_data[0] = speed_.group('speed')
    print "speed %s" % speed_data[0]
      #acc?
  elif type_ == "lin":
    speed_ = re.search(r"(?P<speed>[a-zA-Z0-9_]+)mm", line_)
    speed_data[0]=speed_.group('speed')
      # acc?

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
  variable_type_[i]=port_value_.group('var_type')
  variable_nr_[i]=port_value_.group('Nr')

  var_comment_ = port_value_.group('comment')
  var_comment_split_[i] = var_comment_.split(']')[0]
  value_def_ = re.search(variable_type_[i] + obracket + variable_nr_[i] + var_comment_split_[i] + cbracket + eq + r"(?P<value>[a-zA-Z0-9]+)", line)
  if value_def_:
    value_[i] = value_def_.group('value')
  if i<len(var_comment_.split(']'))-1:
    i = i + 1
  else:
    wait_data = [variable_type_, variable_nr_, value_, var_comment_split_]
    return wait_data
  while re.findall("OR",var_comment_.split(']')[i]) or re.findall("AND",var_comment_.split(']')[i]):
    port_value_ = re.search(
       r"(?P<var_type>[a-zA-Z/!]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' ,
      var_comment_.split(']')[i])
    variable_type_[i] = port_value_.group('var_type')
    variable_nr_[i] = port_value_.group('Nr')

    var_comment_split_[i] = port_value_.group('comment')

    value_def_ = re.search(
      variable_type_[i] + obracket + variable_nr_[i] + var_comment_split_[i] + eq + r"(?P<value>[a-zA-Z0-9]+)", var_comment_.split("]")[i]+var_comment_.split("]")[i+1])
    if value_def_:
      value_[i] = value_def_.group('value')
    if not i < len(var_comment_.split(']'))-1:
      break
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
  commentString = re.search("!(?P<comment>[a-zA-Z0-9_\-\s\:\/\=\>\[\]\.\,\(\)\!]+)", line)
  comment_=commentString.group('comment')
  return comment_

def getIf(line):
  then_data_=[]
  else_data=[]
  call_fct_=re.search(",CALL",line)
  if call_fct_:
    #sthen_="Call"
    then_data_.append(["Call",getCall(line)])
  elif re.findall(",JMP",line):
    #sthen_="Jump"
    then_data_.append(["Jump",getJMP(line)])
  elif re.findall(comma+r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq,line):
    #sthen_="SetVariable"
    then_data_.append(["SetVariable",getSetVariable(line)])
  else_data.append("")
  return [then_data_,else_data]

def getSelect(line,filestring):
  in_select_=0
  line_nr_=getLineNr(line)
  cases = []
  selse=[]
  case_number=[]
  #then_data_=[]
  for line_select_ in filestring.split('\n'):
    select_choices_= re.search(eq+"(?P<Nr>[0-9_]+)"+comma,line_select_)
    then_data_=[]
    if re.findall('ELSE,',line_select_):
      in_select_=0
      selse.append(getStatement(line_select_,filestring))

    if (line_nr_ == getLineNr(line_select_) and in_select_==0) or  (in_select_==1 and select_choices_):
      case_number.append(select_choices_.group('Nr'))
      #cases.append(getStatement(line_select_,filestring))
      call_fct_ = re.search(",CALL", line_select_)
      if call_fct_:
        # sthen_="Call"
        then_data_.append(["Call", getCall(line_select_)])
      elif re.findall(",JMP", line_select_):
        # sthen_="Jump"
        then_data_.append(["Jump", getJMP(line_select_)])
      elif re.findall(
              comma + r"(?P<var_type1>[a-zA-Z/!]+)" + obracket + "(?P<Nr1>[a-zA-Z0-9_]+)" + '(?P<comment1>(?:\s*:.*)?)' + cbracket + eq,
              line_select_):
        # sthen_="SetVariable"
        then_data_.append(["SetVariable", getSetVariable(line_select_)])
      cases.append(then_data_)
      if in_select_==1:
        pass
      in_select_=1
      continue

  return [cases,case_number,selse]

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

  if re.search(r"(?P<signs>[\(\)\!\s\,]+)", line[len(cond_all_) + char_skip]):
    conddef_ = re.search(r"(?P<signs>[\(\)\!\s\,]+)", line[len(cond_all_) + char_skip])
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

