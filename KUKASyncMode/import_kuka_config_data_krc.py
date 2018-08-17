from vcCommand import *
from common import *

SYNC_BASE_NAMES = False
SYNC_TOOL_NAMES = False

DEBUG_MESSAGES = False

def first_state():
  print "Importing configuration data..."
  
  componentname = getProperty("ComponentName").Value
  filename = getProperty("FileName").Value
  ErrorProperty = getProperty("ErrorString")
  
  if DEBUG_MESSAGES:
    print "componentname = %s" %componentname
    print "filename = %s" %filename
  
  comp = getApplication().findComponent(componentname)
  
  if not comp:
    ErrorProperty.Value = 'Component \'%\' not found, aborting command' % componentname
    print ErrorProperty.Value
    return 
    
  rc = GetRobotController(comp)
  
  if not rc:
    ErrorProperty.Value = 'Robot not found, aborting command'
    print ErrorProperty.Value
    return
    
  if DEBUG_MESSAGES:
    print "controller found = %s" %rc.Name 
    
  try:
    infile = open(filename,"r")
    filestring = infile.read()
  except:
    ErrorProperty.Value = 'Cannot open configuration data file %s, aborting command' % filename
    infile.close()
    print ErrorProperty.Value
    return
    
  infile.close()

  # TOOL POSITIONS
  for td in re_tool_data.finditer(filestring):
    index = eval(td.group('index')) - 1
    try:
      tool = rc.Tools[index]
    except:
      print 'Error accessing tool # %d' % index
      continue
    m = vcMatrix.new()
    m.P = vcVector.new(eval(td.group('X')),eval(td.group('Y')),eval(td.group('Z')))
    m.WPR = vcVector.new(eval(td.group('C')),eval(td.group('B')),eval(td.group('A')))
    tool.PositionMatrix = m
    if DEBUG_MESSAGES:
      print "updated position of %s" % tool.Name
  
  # TOOL NAMES
  if SYNC_TOOL_NAMES:
    for tn in re_tool_name.finditer(filestring):
      index = eval(tn.group('index')) - 1
      try:
        tool = rc.Tools[index]
      except:
        print 'Error accessing tool # %d' % index
        continue
      tname = tn.group('name')
      if tname.strip() == '':
        tool.Name = 'TOOL_DATA[%d]' % (index+1)
      else:
        tool.Name = tname

  # TOOL IPO MODES
  for tt in re_tool_type.finditer(filestring):
    index = eval(tt.group('index')) - 1
    try:
      tool = rc.Tools[index]
    except:
      print 'Error accessing tool # %d' % index
      continue
    ttype = tt.group('type').strip()
    if ttype == '#NONE':
      tool.IPOMode = VC_INTERPOLATION_MODE_NONE
    elif ttype == '#BASE':
      tool.IPOMode = VC_INTERPOLATION_MODE_BASE
    elif ttype == '#TCP':
      tool.IPOMode = VC_INTERPOLATION_MODE_TCP
    if DEBUG_MESSAGES:
      print "updated IPOMode of %s" % tool.Name
    
  # BASE POSITIONS
  for bd in re_base_data.finditer(filestring):
    index = eval(bd.group('index')) - 1
    try:
      base = rc.Bases[index]
    except:
      print 'Error accessing base # %d' % index
      continue
    m = vcMatrix.new()
    m.P = vcVector.new(eval(bd.group('X')),eval(bd.group('Y')),eval(bd.group('Z')))
    m.WPR = vcVector.new(eval(bd.group('C')),eval(bd.group('B')),eval(bd.group('A')))
    base.PositionMatrix = m
    if DEBUG_MESSAGES:
      print "updated position of %s" % base.Name

  # BASE NAMES
  if SYNC_BASE_NAMES:
    for bn in re_base_name.finditer(filestring):
      index = eval(bn.group('index')) - 1
      try:
        base = rc.Bases[index]
      except:
        print 'Error accessing base # %d' % index
        continue
      bname = bn.group('name')
      if bname.strip() == '':
        base.Name = 'BASE_DATA[%d]' % (index+1)
      else:
        base.Name = bname
    
  # BASE IPO MODES
  for bt in re_base_type.finditer(filestring):
    index = eval(bt.group('index')) - 1
    try:
      base = rc.Bases[index]
    except:
      print 'Error accessing base # %d' % index
      continue
    btype = bt.group('type').strip()
    if btype == '#NONE':
      base.IPOMode = VC_INTERPOLATION_MODE_NONE
    elif btype == '#BASE':
      base.IPOMode = VC_INTERPOLATION_MODE_BASE
    elif btype == '#TCP':
      base.IPOMode = VC_INTERPOLATION_MODE_TCP
    if DEBUG_MESSAGES:
      print "updated IPOMode of %s" % base.Name  

  # we should not modify the robot / track location in simulation world,
  # instead we map the tables to the world transform matrix
  rn = rc.RootNode
  while rn.Parent != rn.World:
    rn = rn.Parent
  rm = rn.PositionMatrix
  rm = rm * rc.WorldTransformMatrix
  rmi = vcMatrix.new(rm)
  rmi.invert()
  # COMPONENT POSITIONS (ROBOT/TRACK & POSITIONERS)
  for md in re_machine_def.finditer(filestring):
    mt = md.group('mt')
    if mt != '#NONE':
      index = eval(md.group('index')) - 1
      m = vcMatrix.new()
      m.P = vcVector.new(eval(md.group('X')),eval(md.group('Y')),eval(md.group('Z')))
      m.WPR = vcVector.new(eval(md.group('C')),eval(md.group('B')),eval(md.group('A')))
      if mt == '#ROBOT':
        pass # this is never modified, assumption is, that the matrix is zero
      else:
        for j in rc.Joints:
          c = j.Controller.Component
          p = c.getProperty('ET')
          if p and p.Value == mt:
            mm = rm * m
            c.PositionMatrix = mm
            if DEBUG_MESSAGES:
              print "update position of component %s" %c.Name
               
  for bn in re_base_node.finditer(filestring):
    index = eval(bn.group('index')) - 1
    try:
      base = rc.Bases[index]
    except:
      print 'Error accessing base # %d' % index
      continue
    mdi = eval(bn.group('mdi'))
    if mdi > 0 :
      for md in re_machine_def.finditer(filestring):
        mdii = eval(md.group('index'))
        if mdi == mdii:
          mt = md.group('mt')
          for j in rc.Joints:
            c = j.Controller.Component
            p = c.getProperty('ET')
            if p and p.Value == mt:
              fn = j.Controller.FlangeNode
              base.Node = fn

  getApplication().render()
  
  print "Done!"

addState( first_state )

def GetRobotController(comp):
  ctrls = comp.findBehavioursByType(VC_ROBOTCONTROLLER)
  
  if len(ctrls) > 0:
    return ctrls[0]
  else:
    return None
  #endif
#enddef
