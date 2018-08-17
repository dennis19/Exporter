from vcCommand import *
from common import *

SYNC_BASE_NAMES = False
SYNC_TOOL_NAMES = False

DEBUG_MESSAGES = False

def first_state():
  print "Exporting configuration data..."
  componentname = getProperty("ComponentName").Value
  filename = getProperty("FileName").Value
  ErrorProperty = getProperty("ErrorString")
  
  if DEBUG_MESSAGES:
    print "componentname = %s" %componentname
    print "filename = %s" %filename
  
  comp = getApplication().findComponent(componentname)
  
  rc = GetRobotController(comp)
  
  if not rc:
    ErrorProperty.Value = 'Robot controller not found, aborting command'
    return
  
  if DEBUG_MESSAGES:
    print "controller found = %s" %rc.Name  
    
  track = getTrack(comp)
  
  if DEBUG_MESSAGES:
    if track:
      print "track found = %s" %track.Name
    else:
      print "no track found"
      
  tables, flanges = getTablesAndFlanges(comp)

  if DEBUG_MESSAGES:
    print "%s table(s) found" % len(tables)
    print "%s flange(s) found" % len(flanges)
    
  try:
    infile = open(filename,"r")
    filestring = infile.read()
  except:
    ErrorProperty.Value = 'Config file not found'
    infile.close()
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
    from_str = td.group()
    m = vcMatrix.new(tool.PositionMatrix)
    to_str = r'TOOL_DATA[%d]={X %f,Y %f,Z %f,A %f,B %f,C %f}' % (index+1,m.P.X,m.P.Y,m.P.Z,m.WPR.Z,m.WPR.Y,m.WPR.X)
    filestring = filestring.replace(from_str,to_str)
    if DEBUG_MESSAGES:
      print "updated position of tool index %s" % index

  #TOOL NAMES
  if SYNC_TOOL_NAMES:
    for tn in re_tool_name.finditer(filestring):
      index = eval(tn.group('index')) - 1
      try:
        tool = rc.Tools[index]
      except:
        print 'Error accessing tool # %d' % index
        continue
      if tool.Name[:10] == 'TOOL_DATA[':
        tname = ' '
      else:
        tname = tool.Name
      from_str = tn.group()
      to_str = r'TOOL_NAME[%d,]="%s"' % (index+1,tname)
      filestring = filestring.replace(from_str,to_str)
  
  #TOOL IPO MODES
  for tt in re_tool_type.finditer(filestring):
    index = eval(tt.group('index')) - 1
    try:
      tool = rc.Tools[index]
    except:
      print 'Error accessing tool # %d' % index
      continue
    ttype = '#NONE'
    if tool.IPOMode == VC_INTERPOLATION_MODE_BASE:
      ttype = '#BASE'
    if tool.IPOMode == VC_INTERPOLATION_MODE_TCP:
      ttype = '#TCP'
    from_str = tt.group()
    to_str = r'TOOL_TYPE[%d]=%s' % (index+1,ttype)
    filestring = filestring.replace(from_str,to_str)
    if DEBUG_MESSAGES:
      print "updated IPOMode of tool index %s" % index
      
  #BASE POSITIONS
  for bd in re_base_data.finditer(filestring):
    index = eval(bd.group('index')) - 1
    try:
      base = rc.Bases[index]
    except:
      print 'Error accessing base # %d' % index
      continue
    from_str = bd.group()
    m = vcMatrix.new(base.PositionMatrix)
    to_str = r'BASE_DATA[%d]={X %f,Y %f,Z %f,A %f,B %f,C %f}' % (index+1,m.P.X,m.P.Y,m.P.Z,m.WPR.Z,m.WPR.Y,m.WPR.X)
    filestring = filestring.replace(from_str,to_str)
    if DEBUG_MESSAGES:
      print "updated position of base index %s" % index
  
  # BASE NAMES
  if SYNC_BASE_NAMES:
    for bn in re_base_name.finditer(filestring):
      index = eval(bn.group('index')) - 1
      try:
        base = rc.Bases[index]
      except:
        print 'Error accessing base # %d' % index
        continue
      if base.Name[:10] == 'BASE_DATA[':
        bname = ' '
      else:
        bname = base.Name
      from_str = bn.group()
      to_str = r'BASE_NAME[%d,]="%s"' % (index+1,bname)
      filestring = filestring.replace(from_str,to_str)
    
  #BASE IPO MODES
  for bt in re_base_type.finditer(filestring):
    index = eval(bt.group('index')) - 1
    try:
      base = rc.Bases[index]
    except:
      print 'Error accessing base # %d' % index
      continue
    btype = '#NONE'
    if base.IPOMode == VC_INTERPOLATION_MODE_BASE:
      btype = '#BASE'
    if base.IPOMode == VC_INTERPOLATION_MODE_TCP:
      btype = '#TCP'
    from_str = bt.group()
    to_str = r'BASE_TYPE[%d]=%s' % (index+1,btype)
    filestring = filestring.replace(from_str,to_str)
    if DEBUG_MESSAGES:
      print "updated IPOMode of base index %s" % index
      
  # COMPONENT POSITIONS
  #find out robot world transformation matrix in the simulation world to calculate table locations in this reference
  rn = rc.RootNode
  while rn.Parent != rn.World:
    rn = rn.Parent
  m = vcMatrix.new(rn.PositionMatrix)
  m = m * rc.WorldTransformMatrix
  mi = vcMatrix.new(m)
  mi.invert()
  table_indices = {}
  for md in re_machine_def.finditer(filestring):
    from_str = md.group()
    index = eval(md.group('index')) - 1
    if index == 0: # Robot
      # the robot is always in zero
      m = vcMatrix.new()
      to_str = 'MACHINE_DEF[1]={NAME[] "%s",COOP_KRC_INDEX 1,PARENT[] "WORLD",ROOT {X %f,Y %f,Z %f,A %f,B %f,C %f},MECH_TYPE #ROBOT,GEOMETRY[] " "}' % (comp.Name,m.P.X,m.P.Y,m.P.Z,m.WPR.Z,m.WPR.Y,m.WPR.X)
    elif index <= len(tables):
      table = tables[index-1]
      m = mi*vcMatrix.new(table.WorldPositionMatrix)
      p = table.getProperty('ET')
      to_str = 'MACHINE_DEF[%d]={NAME[] "%s",COOP_KRC_INDEX 1,PARENT[] " ",ROOT {X %f,Y %f,Z %f,A %f,B %f,C %f},MECH_TYPE %s,GEOMETRY[] " "}' % (index+1,table.Name,m.P.X,m.P.Y,m.P.Z,m.WPR.Z,m.WPR.Y,m.WPR.X,p.Value)
      table_indices[table.Name] = index+1
    else:
      to_str = 'MACHINE_DEF[%d]={NAME[] " ",COOP_KRC_INDEX 0,PARENT[] " ",ROOT {X 0.0,Y 0.0,Z 0.0,A 0.0,B 0.0,C 0.0},MECH_TYPE #NONE,GEOMETRY[] " "}' % (index+1)
    filestring = filestring.replace(from_str,to_str)
  
  # BASE NODES
  for bn in re_base_node.finditer(filestring):
    from_str = bn.group()
    index = eval(bn.group('index')) - 1
    to_str = 'MACHINE_FRAME_DAT[%d]={MACH_DEF_INDEX 0,PARENT[] " ",GEOMETRY[] " "}' % (index+1)    
    try:
      base = rc.Bases[index]
    except:
      print 'Error accessing base # %d' % index
      continue
    if base.Node:
      for f in flanges:
        if f == base.Node:
          to_str = 'MACHINE_FRAME_DAT[%d]={MACH_DEF_INDEX %d,PARENT[] "%s",GEOMETRY[] " "}' % (index+1,table_indices[f.Component.Name],f.Component.Name)
    filestring = filestring.replace(from_str,to_str)
  
  #print filestring
  f = open(filename, 'w')
  f.write(filestring)
  f.close()
  
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

