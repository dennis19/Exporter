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

x = r'X' + colon + r'(?P<x>'+real+')'
y = r'Y' + colon + r'(?P<y>'+real+')'
z = r'Z' + colon + r'(?P<z>'+real+')'
w = r'W' + colon + r'(?P<w>'+real+')'
p = r'P' + colon + r'(?P<p>'+real+')'
r = r'R' + colon + r'(?P<r>'+real+')'

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

def uploadvarABB_(program, infile):
  filestring = infile.read()
  infile.close()

  executor = program.Executor
  comp = executor.Component
  robCnt = executor.Controller
  tool_data_=[]
  pos_data_ = []
  var_data_ = []

  for line in filestring.split('\n'):
    if re.findall("tooldata",line) and not re.findall("LOCAL", line):
      tool_data_.append(getToolFrames(line))
    if (re.findall("robtarget",line) or re.findall("jointtarget",line))and not re.findall("LOCAL", line):
      pos_data_.append(getGlobPos(line))
    if (re.findall("num",line) or re.findall("bool",line) or re.findall("speeddata",line))and not re.findall("LOCAL", line):
      var_data_.append(getGlobVar(line))
  # endfor
  #print "tool %s" % tool_data_
  if tool_data_:
    #tools = re_frame.finditer(toolString)
    for t in tool_data_[0]:
      t_name_ = t[0]
      #print "tool %s" %t_name_
      xx = t[1][0]
      yy = t[1][1]
      zz = t[1][2]
      ww = t[1][3]
      pp = t[1][4]
      rr = t[1][5]
      #
      m = vcMatrix.new()
      m.translateAbs(xx, yy, zz)
      m.setWPR(ww, pp, rr)
      # if tindex > len(robCnt.Tools):
      tool = robCnt.addTool()
      tool.Name = t_name_
      # # endif
      #
      tool.PositionMatrix=m
  if pos_data_:
    base = 0
    tool = 0
    #posregs = re_posregcart.finditer(posregString)
    #print "pos_data_ %s" % pos_data_
    for p in pos_data_:
      p_name_ = p[0]
      #print "p_name %s" %p_name_
      # comment = preg_.group(3)
      # if comment:
      #   name_ = "PR[" + '%i' % pindex + ':' + comment + "]"
      # else:
      #   name_ = "PR[" + '%i' % pindex + "]"
      routine = program.findRoutine( "POSREG_"+p_name_)
      if routine:
        routine.clear()
      else:
        routine = program.addRoutine( "POSREG_"+p_name_)
      if p[3]=="coord":
        xx = p[1][0]
        yy = p[1][1]
        zz = p[1][2]
        ww = p[1][3]
        pp = p[1][4]
        rr = p[1][5]
      #cfg = preg_.group('fut')
      # if cfg == 'F': cfg = 'F U T'
      # if cfg == 'N': cfg = 'N U T'
      # jt1 = eval(preg_.group('t1'))
      #   jt2 = eval(preg_.group('t2'))
      #   jt3 = eval(preg_.group('t3'))
      #
        m = vcMatrix.new()
        m.translateAbs(xx, yy, zz)
        m.setWPR(ww, pp, rr)
      #
        stmt = routine.addStatement(VC_STATEMENT_PTPMOTION)
        posFrame = stmt.Positions[0]
        posFrame.PositionInReference = m
      elif p[3]=="joint":
        j1_deg_ = p[1][0]
        j2_deg_ = p[1][1]
        j3_deg_ = p[1][2]
        j4_deg_ = p[1][3]
        j5_deg_ = p[1][4]
        j6_deg_ = p[1][5]



        joints=[j1_deg_,j2_deg_,j3_deg_,j4_deg_,j5_deg_,j6_deg_]

        stmt = routine.addStatement(VC_STATEMENT_PTPMOTION)
        # read in jointvalues
        posFrame = stmt.Positions[0]
        mt = robCnt.createTarget()
        mt.MotionType = VC_MOTIONTARGET_MT_JOINT
        mt.UseJoints = True

        jv = mt.JointValues
        for i in xrange(len(jv)):
          jv[i] = joints[i]
        mt.JointValues = jv
        posFrame.PositionInReference = mt.Target

      #   posFrame.Configuration = cfg
      #   if base == 0:
      #     stmt.Base = robCnt.Bases[0]
      #   else:
      #     stmt.Base = robCnt.Bases[base - 1]
      #   # endif
      #   if tool == 0:
      #     stmt.Tool = robCnt.Tools[0]
      #   else:
      #     stmt.Tool = robCnt.Tools[tool - 1].Name
      #
      #   try:
      #     posFrame.JointTurns4 = jt1
      #     posFrame.JointTurns5 = jt2
      #     posFrame.JointTurns6 = jt3
      #   except:
      #     pass
      posFrame.Name = p_name_
      stmt.Base = robCnt.Bases[0]
      stmt.Tool = robCnt.Tools[-1]
      #
      #   # endif
      #   stmt.createProperty(VC_INTEGER, 'INDEX')
      #   stmt.INDEX = pindex
      # endfor

  # i=0
  # while i<len(robCnt.Tools):
  #   if robCnt.Tools[i].Name==tool.Name:
  #     print "name %s" %tool.Name
  #   i=i+1
      #robCnt.Tools[tindex - 1].PositionMatrix = m

  if var_data_:
    for v in var_data_:
      if not v==[]:
        #print "v1: %s" % v
        prop=[]
      #comment=delChars(n.group(3))
      #print "comment: %s" %comment
      # if val or comment:
        v_name_ = v[0]
      #print "v1: %s" %v[1]
        if len(v)>1:
          val = v[1]
          if len(v[1])==1:

            prop = comp.createProperty(VC_REAL, 'Registers::%s' % v_name_)  # + '%s' % comment)
          else:
          #print "v1: %s" % len(v[1])
            i=0
            while i<len(v[1]):
              prop.append(comp.createProperty(VC_REAL, 'Registers::%s' % v_name_+"_%s" %i))
              prop[i].Value = float(val[i])
              i+=1# + '%s' % comment)
        else:
          val=0
          prop = comp.createProperty(VC_REAL, 'Registers::%s' % v_name_)  # + '%s' % comment)
      #prop = comp.createProperty(VC_REAL, 'Registers::%s' % v_name_)# + '%s' % comment)

      #prop.Group = nindex
  return True

# def delChars(comment_):
#   # delete space
#   split_char_ = re.compile(r' ')
#   comment_split_ = split_char_.split(comment_)
#   if comment_split_:
#     i = 1
#     comment_ = ''
#     while i <= len(comment_split_):
#       comment_ += comment_split_[i - 1]
#       i = i + 1
#
#   #delete :
#   split_char_ = re.compile(r':')
#   comment_split_ = split_char_.split(comment_)
#   if comment_split_:
#     i = 1
#     comment_ = ''
#     while i <= len(comment_split_):
#
#       comment_ += comment_split_[i - 1]
#       i = i + 1
#
#
#   #delete /
#   split_char_ = re.compile(r'/')
#   comment_split_ = split_char_.split(comment_)
#   if comment_split_:
#     i = 1
#     comment_ = ''
#     while i <= len(comment_split_):
#
#       comment_ += comment_split_[i - 1]
#       i = i + 1
#
#   #delete .
#   split_char_ = re.compile(r'\.')
#   comment_split_ = split_char_.split(comment_)
#   if comment_split_:
#     i = 1
#     comment_ = ''
#     while i <= len(comment_split_):
#
#       comment_ += comment_split_[i - 1]
#       i = i + 1
#   return comment_


def getGlobVar(line):
  var_data_=[]

  if not re.findall("LOCAL", line) and re.findall("PERS num", line):

    var_def_=re.search("PERS num " + r"(?P<var>[a-zA-Z0-9_]+)",line)
    if var_def_:
      var_data_.append(var_def_.group('var'))
      #print "var_data %s" % var_data_
      if re.search(colon + eq + r"(?P<value>[a-zA-Z0-9_]+)",line):
        value_def_ = re.search(colon + eq + r"(?P<value>[a-zA-Z0-9_]+)",line)
        value_ = value_def_.group('value')
        var_data_.append(value_)
        #print "var_data %s" % var_data_

  elif not re.findall("LOCAL", line) and re.findall("PERS bool", line):
    var_def_=re.search("PERS bool " + r"(?P<var>[a-zA-Z0-9_]+)",line)
    if var_def_:
      var_data_.append(var_def_.group('var'))

      #print "var_data %s" %var_data_
      if re.search(colon+eq+r"(?P<value>[a-zA-Z0-9_]+)",line):
        value_def_=re.search(colon+eq+r"(?P<value>[a-zA-Z0-9_]+)",line)
        value_=value_def_.group('value')
        var_data_.append(value_)

  elif not re.findall("LOCAL", line) and re.findall("PERS speeddata", line):
    var_def_=re.search("PERS speeddata " + r"(?P<var>[a-zA-Z0-9_]+)",line)
    if var_def_:
      var_data_.append(var_def_.group('var'))


      if re.search(colon+eq+obracket+r"(?P<value>[a-zA-Z0-9_]+)",line):
        value_def_=re.search(colon+eq+obracket+r"(?P<value1>[a-zA-Z0-9_]+)"+comma+r"(?P<value2>[a-zA-Z0-9_]+)"+comma+r"(?P<value3>[a-zA-Z0-9_]+)"+comma+r"(?P<value4>[a-zA-Z0-9_]+)"+cbracket,line)
        value_=[value_def_.group('value1'),value_def_.group('value2'),value_def_.group('value3'),value_def_.group('value4')]
        var_data_.append(value_)
        #print "var_data %s" % var_data_

  return var_data_


def getToolFrames(line):
  tool_data_=[]
  if not re.findall("LOCAL", line) and re.findall("PERS tooldata", line):
    tool_def_ = re.findall(
      r"(?P<target>[a-zA-Z0-9_]+)" + ":=" +obracket +r"(?P<bool>[a-zA-Z]+)"+comma+obracket+obracket+
      "(?P<coordx>[0-9\.\-_]+)"+comma+"(?P<coordy>[0-9\.\-_]+)"+comma+"(?P<coordz>[0-9\.\-_]+)"+cbracket+comma+obracket+
      "(?P<orient1>[0-9\.\-_]+)"+comma+"(?P<orient2>[0-9\.\-_]+)"+comma+"(?P<orient3>[0-9\.\-_]+)"+comma+"(?P<orient4>[0-9\.\-_]+)"+cbracket,line)#"\[ *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *\]",
      #line)
    if tool_def_:
      m = vcMatrix.new()
      #print "tool %s" %tool_def_[0][2]
      tool_name_=tool_def_[0][0]
      m.setQuaternion(float(tool_def_[0][6]), float(tool_def_[0][7]), float(tool_def_[0][8]), float(tool_def_[0][5]))
      coordinates_ = [float(tool_def_[0][2]), float(tool_def_[0][3]), float(tool_def_[0][4]), m.WPR.X, m.WPR.Y, m.WPR.Z]
      #print "coord %s" %coordinates_
      tool_data_.append([tool_name_,coordinates_])
  return tool_data_


def getGlobPos(line):
  move_data_=None
  if not re.findall("LOCAL",line) and re.findall("PERS robtarget",line):
    rob_target_def = re.findall(
      r"(?P<target>[a-zA-Z0-9_]+)" + ":=" + "\[ *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *\]",
      line)
    targetname=rob_target_def[0]
    positionmatch = re.findall(
      "\[ *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *\]", line)
    # print "target: %s" % targetname

    # print "positionmatch: %s" % positionmatch
    # for mymatch in positionmatch:
    match = re.findall("[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", positionmatch[0])
    # print "match: %s" % match
    #   robtarget has 17 floating point values
    if len(match) == 17:
      m = vcMatrix.new()
      # m.P = vcVector.new(float(match[0]),float(match[1]),float(match[2]))
      m.setQuaternion(float(match[4]), float(match[5]), float(match[6]), float(match[3]))
      coordinates_ = [float(match[0]), float(match[1]), float(match[2]), m.WPR.X, m.WPR.Y, m.WPR.Z]
      config_data_ = [match[7], match[8], match[9], match[10]]
      #tool_ = getTool(line)
      #base_ = getBase(line)
      #speed_ = getSpeed(line)
      move_data_ = [targetname, coordinates_, config_data_,"coord"]

  elif not re.findall("LOCAL",line) and re.findall("PERS jointtarget",line):
    rob_target_def = re.findall(
      r"(?P<target>[a-zA-Z0-9_]+)" + ":=" +obracket + obracket+"(?P<joint1>[0-9\.\-_]+)"+comma+"(?P<joint2>[0-9\.\-_]+)"+comma+"(?P<joint3>[0-9\.\-_]+)"+comma+"(?P<joint4>[0-9\.\-_]+)"+comma+"(?P<joint5>[0-9\.\-_]+)"+comma+"(?P<joint6>[0-9\.\-_]+)"+cbracket,line)
      #line)
    #print "robtarget %s" %rob_target_def
    if rob_target_def:
      targetname = rob_target_def[0]
      #print "target: %s" % targetname[0]
      coordinates_ = [float(targetname[1]), float(targetname[2]), float(targetname[3]), float(targetname[4]), float(targetname[5]), float(targetname[6])]
      config_data_=[]
      move_data_=[targetname[0],coordinates_,config_data_,"joint"]

  return move_data_

def OnStart():
  
  program = uploadBackup.getActiveProgram()
  if not program:
    app.messageBox("No program selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return False
  #endif

  opencmd = app.findCommand("dialogOpen")
  uri = ""
  ok = True
  fileFilter = "FANUC Robot Program files (*.va)|*.va"
  opencmd.execute(uri,ok,fileFilter)
  if not opencmd.Param_2:
    print "No file selected for uploading, aborting command"
    return False
  #endif
  uri = opencmd.Param_1
  filename = uri[8:len(uri)]
  try:
    infile = open(filename,"r")
  except:
    print "Cannot open file \'%s\' for reading" % filename
    return
  #endtry
  uploadva_(program,infile)

  return True

#-------------------------------------------------------------------------------

addState(None)
