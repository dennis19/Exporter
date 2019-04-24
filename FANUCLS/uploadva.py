from vcCommand import *
import re
import os.path
import vcMatrix
import uploadBackup
import uploadvarABB
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

def uploadGlobalData(program,infile,controller):
  if (controller=="IRC5"):
    global_data_=uploadvarABB.uploadvarABB_(   infile)

  elif controller == "R30iA":
    global_data_=uploadva_(infile)
  createGlobalData(program,global_data_)

  return True

def uploadva_( infile):
  filestring = infile.read()
  infile.close()

  register=[]
  frames=[]
  position=[]

  # executor = program.Executor
  # comp = executor.Component
  # robCnt = executor.Controller

  blocks = {}
  lineBuffer = ''
  currentSection = ''
  for line in filestring.split('\n'):

    SYSFRAME = re.match(sysframe + end, line)
    if SYSFRAME:
      if currentSection: blocks[currentSection] = lineBuffer
      lineBuffer = ''
      currentSection = SYSFRAME.group(1)
      continue
    # endif

    POSREG = re.match(posreg + end, line)
    if POSREG:
      if currentSection: blocks[currentSection] = lineBuffer
      lineBuffer = ''
      currentSection = POSREG.group(1)
      continue
    # endif

    NUMREG = re.match(numreg + end, line)
    if NUMREG:
      if currentSection: blocks[currentSection] = lineBuffer
      lineBuffer = ''
      currentSection = NUMREG.group(1)
      continue
    # endif

    lineBuffer += line + '\n'
  # endfor
  if currentSection: blocks[currentSection] = lineBuffer

  numregString = blocks.get('$NUMREG', '')
  if numregString:

    numregs = re_numreg.finditer(numregString)
    for n in numregs:
      val = eval(n.group(2))
      comment=delChars(n.group(3))
      #print "comment: %s" %comment
      # if val or comment:
      nindex = eval(n.group(1))
      # prop = comp.createProperty(VC_REAL, 'Registers::R%i' % nindex + '%s' % comment)
      # prop.Value = val
      # prop.Group = nindex
      register.append(["R%i" %nindex+ '%s' % comment,[val]])
      # endif
    # endfor
  # endif

  baseString = blocks.get('$MNUFRAME', '')
  if baseString:
    bases = re_frame.finditer(baseString)
    for b in bases:
      bindex = eval(b.group(2))
      xx = eval(b.group('x'))
      yy = eval(b.group('y'))
      zz = eval(b.group('z'))
      ww = eval(b.group('w'))
      pp = eval(b.group('p'))
      rr = eval(b.group('r'))
      coord=[xx,yy,zz,ww,pp,rr]
      # m = vcMatrix.new()
      # m.translateAbs(xx, yy, zz)
      # m.setWPR(ww, pp, rr)
      #
      # if bindex > len(robCnt.Bases):
      #   base = robCnt.addBase()
      name_ = 'Uframe%i' % bindex
      # # endif
      # robCnt.Bases[bindex - 1].PositionMatrix = m
      frames.append(["Base",name_,coord])
    # endfor
  # endif

  toolString = blocks.get('$MNUTOOL', '')
  if toolString:
    tools = re_frame.finditer(toolString)
    for t in tools:
      tindex = eval(t.group(2))
      xx = eval(t.group('x'))
      yy = eval(t.group('y'))
      zz = eval(t.group('z'))
      ww = eval(t.group('w'))
      pp = eval(t.group('p'))
      rr = eval(t.group('r'))
      coord = [xx, yy, zz, ww, pp, rr]
      # m = vcMatrix.new()
      # m.translateAbs(xx, yy, zz)
      # m.setWPR(ww, pp, rr)
      # if tindex > len(robCnt.Tools):
      #   tool = robCnt.addTool()
      name_ = 'Utool%i' % tindex
      # # endif
      #
      # robCnt.Tools[tindex - 1].PositionMatrix = m
      frames.append(["Tool", name_, coord])
    # endfor
  # endif

  posregString = blocks.get('$POSREG', '')
  if posregString:
    base = 0
    tool = 0
    posregs = re_posregcart.finditer(posregString)
    if posregs:
      for preg_ in posregs:
        pindex = eval(preg_.group(2))
        comment = preg_.group(3)
        if comment:
          name_ = "PR[" + '%i' % pindex + ':' + comment + "]"
        else:
          name_ = "PR[" + '%i' % pindex + "]"

        # routine = program.findRoutine('POSREG_' + name_)
        # if routine:
        #   routine.clear()
        # else:
        #   routine = program.addRoutine('POSREG_' + name_)

        xx = eval(preg_.group('x'))
        yy = eval(preg_.group('y'))
        zz = eval(preg_.group('z'))
        ww = eval(preg_.group('w'))
        pp = eval(preg_.group('p'))
        rr = eval(preg_.group('r'))
        coord = [xx, yy, zz, ww, pp, rr]
        cfg = preg_.group('fut')
        if cfg == 'F': cfg = 'F U T'
        if cfg == 'N': cfg = 'N U T'
        jt1 = eval(preg_.group('t1'))
        jt2 = eval(preg_.group('t2'))
        jt3 = eval(preg_.group('t3'))

        # m = vcMatrix.new()
        # m.translateAbs(xx, yy, zz)
        # m.setWPR(ww, pp, rr)

        # stmt = routine.addStatement(VC_STATEMENT_PTPMOTION)
        # posFrame = stmt.Positions[0]
        # posFrame.PositionInReference = m
        # posFrame.Configuration = cfg
        # if base == 0:
        #   stmt.Base = robCnt.Bases[0]
        # else:
        #   stmt.Base = robCnt.Bases[base - 1]
        # # endif
        # if tool == 0:
        #   stmt.Tool = robCnt.Tools[0]
        # else:
        #   stmt.Tool = robCnt.Tools[tool - 1].Name
        #
        # try:
        #   posFrame.JointTurns4 = jt1
        #   posFrame.JointTurns5 = jt2
        #   posFrame.JointTurns6 = jt3
        # except:
        #   pass
        # posFrame.Name = name_
        #
        # # endif
        # stmt.createProperty(VC_INTEGER, 'INDEX')
        # stmt.INDEX = pindex
        position.append(['Cartesian',name_,coord,cfg,base,tool])
      # endfor
    if re_posregjoint.finditer(posregString):
      posregs=re_posregjoint.finditer(posregString)
      for preg_ in posregs:
        pindex = eval(preg_.group(2))
        comment = preg_.group(3)
        if comment:
          name_ = "PR[" + '%i' % pindex + ':' + comment + "]"
        else:
          name_ = "PR[" + '%i' % pindex + "]"

        # routine = program.findRoutine('POSREG_' + name_)
        # if routine:
        #   routine.clear()
        # else:
        #   routine = program.addRoutine('POSREG_' + name_)

        j1_deg_ = eval(preg_.group('j1'))
        j2_deg_ = eval(preg_.group('j2'))
        j3_deg_ = eval(preg_.group('j3'))
        j4_deg_ = eval(preg_.group('j4'))
        j5_deg_ = eval(preg_.group('j5'))
        j6_deg_ = eval(preg_.group('j6'))



        joints=[j1_deg_,j2_deg_,j3_deg_,j4_deg_,j5_deg_,j6_deg_]

        # stmt = routine.addStatement(VC_STATEMENT_PTPMOTION)
        # # read in jointvalues
        # posFrame = stmt.Positions[0]
        # mt = robCnt.createTarget()
        # mt.MotionType = VC_MOTIONTARGET_MT_JOINT
        # mt.UseJoints = True
        #
        # jv = mt.JointValues
        # for i in xrange(len(jv)):
        #   jv[i] = joints[i]
        # mt.JointValues = jv
        #
        # #convert into cartesian
        # posFrame.PositionInReference = mt.Target
        if j4_deg_ >=0: cfg = 'F U T'
        if j4_deg_ <= 0: cfg = 'N U T'
        # posFrame.Configuration = cfg
        # if base == 0:
        #   stmt.Base = robCnt.Bases[0]
        # else:
        #   stmt.Base = robCnt.Bases[base - 1]
        # # endif
        # if tool == 0:
        #   stmt.Tool = robCnt.Tools[0]
        # else:
        #   stmt.Tool = robCnt.Tools[tool - 1].Name

        # posFrame.Name = name_

        # endif
        # stmt.createProperty(VC_INTEGER, 'INDEX')
        # stmt.INDEX = pindex
        position.append(['Joint',name_,joints,cfg,base,tool])


  # endif

  return [register,frames,position]

def delChars(comment_):
  # delete space
  split_char_ = re.compile(r' ')
  comment_split_ = split_char_.split(comment_)
  if comment_split_:
    i = 1
    comment_ = ''
    while i <= len(comment_split_):
      comment_ += comment_split_[i - 1]
      i = i + 1

  #delete :
  split_char_ = re.compile(r':')
  comment_split_ = split_char_.split(comment_)
  if comment_split_:
    i = 1
    comment_ = ''
    while i <= len(comment_split_):

      comment_ += comment_split_[i - 1]
      i = i + 1


  #delete /
  split_char_ = re.compile(r'/')
  comment_split_ = split_char_.split(comment_)
  if comment_split_:
    i = 1
    comment_ = ''
    while i <= len(comment_split_):

      comment_ += comment_split_[i - 1]
      i = i + 1

  #delete .
  split_char_ = re.compile(r'\.')
  comment_split_ = split_char_.split(comment_)
  if comment_split_:
    i = 1
    comment_ = ''
    while i <= len(comment_split_):

      comment_ += comment_split_[i - 1]
      i = i + 1
  #delete #
  split_char_ = re.compile(r'\#')
  comment_split_ = split_char_.split(comment_)
  if comment_split_:
    i = 1
    comment_ = ''
    while i <= len(comment_split_):

      comment_ += comment_split_[i - 1]
      i = i + 1
  return comment_


def OnStart():
  
  program = uploadBackup.getActiveProgram()
  if not program:
    app.messageBox("No program selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return False
  #endif
  executor = program.Executor
  comp = executor.Component
  robCnt = executor.Controller
  # opencmd = app.findCommand("dialogOpen")
  # uri = ""
  ok = True
  if (robCnt.Name=="IRC5"):
    file_=uploadBackup.readABBVar(program)
    #uploadvarABB.uploadvarABB_(program_, infile_sum_)
  elif robCnt.Name == "R30iA":
    opencmd = app.findCommand("dialogOpen")
    uri = ""
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
    file_=[infile,filename]
  #endtry
  uploadGlobalData(program,file_[0],robCnt.Name)
  # global_data_= uploadva_(infile)
  # createGlobalData(program,global_data_)
  return True

def createGlobalData(program,global_data_):
  executor = program.Executor
  comp = executor.Component
  robCnt = executor.Controller
  prop=[]

  if not  global_data_[0]==[]:
    for data_ in global_data_[0]:
      if len(data_[1]) > 1:
        val = data_[1]
        if len(data_[1]) == 1:

          prop = comp.createProperty(VC_REAL, 'Registers::%s' % data_[0])  # + '%s' % comment)
        else:
          # print "v1: %s" % len(v[1])
          i = 0
          while i < len(data_[1]):
            prop.append(comp.createProperty(VC_REAL, 'Registers::%s' % data_[0] + "_%s" % i))
            prop[i].Value = float(val[i])
            i += 1  # + '%s' % comment)
      else:
        #print "data %s" %data_[1]
        val = data_[1][0]
        prop = comp.createProperty(VC_REAL, 'Registers::%s' % data_[0])
        prop.Value = float(val)
      #prop = comp.createProperty(VC_REAL, 'Registers::' +data_[0])

      #prop.Value = data_[1]

    #prop.Group = nindex
  if not global_data_[1] == []:
    for data_ in global_data_[1]:
      m = vcMatrix.new()
      m.translateAbs(data_[2][0], data_[2][1], data_[2][2])
      m.setWPR(data_[2][3], data_[2][4], data_[2][5])
      if data_[0]=="Base":
        if data_[1] > len(robCnt.Bases):
          base = robCnt.addBase()
          base.Name = data_[1]#'Uframe%i' % data_[1]
        # endif
        for base in robCnt.Bases:
          if base.Name==data_[1]:
            base.PositionMatrix=m
        #robCnt.Bases[data_[1]  - 1].PositionMatrix = m
      elif data_[0]=="Tool":
        if data_[1]  > len(robCnt.Tools):
          tool = robCnt.addTool()
          tool.Name = data_[1]#'Utool%i' % data_[1]
      # endif
        for tool in robCnt.Tools:
          if tool.Name==data_[1]:
            tool.PositionMatrix=m
          #robCnt.Tools[data_[1]  - 1].PositionMatrix = m

  if not global_data_[2] == []:
    for data_ in global_data_[2]:

      routine = program.findRoutine('POSREG_' + data_[1])
      if routine:
        routine.clear()
      else:
        routine = program.addRoutine('POSREG_' + data_[1])

      stmt = routine.addStatement(VC_STATEMENT_PTPMOTION)
      posFrame = stmt.Positions[0]

      if data_[0]=="Cartesian":
        m = vcMatrix.new()
        m.translateAbs(data_[2][0], data_[2][1], data_[2][2])
        m.setWPR(data_[2][3], data_[2][4], data_[2][5])
        posFrame.PositionInReference = m
      elif data_[0]=="Joint":
        mt = robCnt.createTarget()
        mt.MotionType = VC_MOTIONTARGET_MT_JOINT
        mt.UseJoints = True

        jv = mt.JointValues
        for i in xrange(len(jv)):
          jv[i] = data_[2][i]
        mt.JointValues = jv

      # convert into cartesian
        posFrame.PositionInReference = mt.Target
      if not data_[3]==[]:
        posFrame.Configuration = data_[3]

      if data_[4] == 0:
        stmt.Base = robCnt.Bases[0]
      else:
        stmt.Base = robCnt.Bases[data_[4] - 1]
    # endif
      if data_[5] == 0:
        stmt.Tool = robCnt.Tools[0]
      else:
        stmt.Tool = robCnt.Tools[data_[5] - 1].Name

      posFrame.Name = data_[1]

#-------------------------------------------------------------------------------

addState(None)
