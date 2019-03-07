from vcCommand import *
import re
import os.path
import vcMatrix
import uploadBackup
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


  coordinates_=[idx,idy,idz,idp,idr,idw]
  moveData=[point_,speed_,coordinates_,cfgData,base,tool]
  return moveData

def getSpeed(line_, type_):
  speed_data=["",""]
  if type_=="joint":
    speed_ = re.search(r"(?P<speed>[a-zA-Z0-9_]+)%", line_)
    #speed_ = int(speed_.group('speed')) / 100
    speed_data[0] = speed_.group('speed')
      #acc?
  elif type_ == "lin":
    speed_ = re.search(r"(?P<speed>[a-zA-Z0-9_]+)mm", line_)
    #speed_ = int(speed_.group('speed'))
    speed_data[0]=speed_.group('speed')
      # acc?
  if re.search(r",R" + obracket, line_):
    speed_ = re.search("," + rnum, line_)
    if speed_:
      comment = speed.group('comment')
      register = +speed.group('pnum')
      speed_data[0] = register
      speed_data[1] = comment
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
  var_comment_split_=["","",""]
  value_=["","",""]
  variable_type_=["","",""]
  variable_nr_=["","",""]
  port_value_ = re.search(
    "WAIT "+orbracket+r"(?P<var_type>[a-zA-Z]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' + cbracket ,
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
  value_[i] = value_def_.group('value')
  if i<len(var_comment_.split(']'))-1:
    print "i:%s" % len(var_comment_.split(']'))
    i = i + 1
  else:
    wait_data = [variable_type_, variable_nr_, value_, var_comment_split_]
    return wait_data
  #print " line %s" % (var_comment_.split(']')[1]+var_comment_.split(']')[2])
  while re.findall("OR",var_comment_.split(']')[i]) or re.findall("AND",var_comment_.split(']')[i]):
    #i=i+1
    print "len:%s" %i
    port_value_ = re.search(
       r"(?P<var_type>[a-zA-Z]+)" + obracket + "(?P<Nr>[a-zA-Z0-9_]+)" + '(?P<comment>(?:\s*:.*)?)' ,
      var_comment_.split(']')[i])

    variable_type_[i] = port_value_.group('var_type')
    variable_nr_[i] = port_value_.group('Nr')

    var_comment_split_[i] = port_value_.group('comment')

    value_def_ = re.search(
      variable_type_[i] + obracket + variable_nr_[i] + var_comment_split_[i] + eq + r"(?P<value>[a-zA-Z0-9]+)", var_comment_.split("]")[i]+var_comment_.split("]")[i+1])
    value_[i] = value_def_.group('value')
    #print "%s" % var_comment_split_[i]
    if not i < len(var_comment_.split(']'))-1:
      break
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


  set_data = [variable_type_, variable_nr_, value_]
  return set_data

def getComment(line):
  commentString = re.search("!(?P<comment>[a-zA-Z0-9_\-\s\:\/]+)", line)
  comment_=commentString.group('comment')
  return comment_

def getIf(line):
  cond=getCondition()
  return cond

def getCondition(line,cond_all_,char_skip):
  condition_ = ["", "", "","","","",""]

  if re.search(r"(?P<signs>[\(\)\!\s]+)", line[len(cond_all_) + char_skip]):
    conddef_ = re.search(r"(?P<signs>[\(\)\!\s]+)", line[len(cond_all_) + char_skip])
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


    #cond=conddef_.group('var_type')+'['+conddef_.group('Nr')+comment[0]+']'
    value_def_=re.search(conddef_.group('var_type')+obracket+conddef_.group('Nr')+comment[0]+cbracket+eq+r"(?P<value>[a-zA-Z0-9]+)",line[len(cond_all_) + char_skip:])
    condition_[6]=""
    condition_[5]=""
    if value_def_:
      condition_[6]= value_def_.group('value')
      condition_[5] = "="
    #condition_=[cond,eq_str_,value_,comment[0],conddef_.group('Nr')]
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
  # + comma + '(?P<param2>(?:\s*:.*)?)' +
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

def getToolOffset(line):
  pass