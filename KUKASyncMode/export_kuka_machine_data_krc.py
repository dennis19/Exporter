from vcCommand import *
from common import *
import fpformat
import sys

DEBUG_MESSAGES = True

def first_state():
  program = getProgram()

  # ask file from the user
  uri = ""
  ok = True
  savecmd = app.findCommand("dialogSaveFile")
  savecmd.execute(uri,ok,None,'Choose File to save Robot Program file')

  uri = savecmd.Param_1

  
  program = getProgram()
  
  componentname = program.Executor.Component.getProperty("Name").Value #getProperty("ComponentName").Value
  filename = uri[8:]#getProperty("FileName").Value
  BakFileProperty = getProperty("BakFileName")
  ErrorProperty = getProperty("ErrorString")

  if DEBUG_MESSAGES:
    print "componentname = %s" %componentname
    print "uri = %s" %uri
    print "filename = %s" %filename	 
    print "prog = %s" %program
    
  comp = getApplication().findComponent(componentname)
  if not comp:
    ErrorProperty.Value = 'Robot not found, aborting command'
    print ErrorProperty.Value
    return
    
  global external_comps, ext_joints, num, robot_joint_count
 
  external_comps = []
  ext_joints = []
  
  robot_joint_count = 0
  
  num = r' *-?\d*\.?\d+(?:[eE][-+]?\d+)?'
      
  # Get robot controller
  robot = GetRobotController(comp)
 
  if robot == None:
    ErrorProperty.Value = 'Robot controller not found, aborting command'
    print ErrorProperty.Value
    return
    
  if DEBUG_MESSAGES:
    print "controller found = %s" %robot.Name  

  if filename == "":
    ErrorProperty.Value = 'Machine data file not found, aborting command'
    print ErrorProperty.Value
    return

  infile = None    
  # open machine data file
  try:
    infile = open(filename,"r")
  except:
    ErrorProperty.Value = 'Cannot open machine data file %s' % filename
    print ErrorProperty.Value + ', aborting command'
    return	   
  # read in machine data file
  try:
    filestring = infile.read()
    infile.close()
  except:
    infile.close()
    ErrorProperty.Value = 'Cannot read machine data file, aborting command'
    print ErrorProperty.Value
    return
  
  i = 1
  root, ext = os.path.splitext(filename)
  bakext = '.bk%d' % i
  bakfile = root+bakext
  while os.path.exists(bakfile):
    i += 1
    bakext = '.bk%d' % i
    bakfile = root+bakext
  #endwhile
  copyfile(filename,bakfile)
  BakFileProperty.Value = bakfile
  if DEBUG_MESSAGES:
    print "created backup file %s" %bakfile

  # Calculate the number of external joints and get connected components
  for j in robot.Joints:
    if j.ExternalController != None:
      ext_joints.append(j)   
      exists = False
      for i in external_comps:
        if i.Name == j.Controller.Component.Name:
          exists = True
          break
      if exists == False:
        external_comps.append(j.Controller.Component)
      #endif
    else:
      robot_joint_count += 1
  #endfor

  filestring = UpdateMachineDatFile(filestring)
  #print filestring
  f = open(filename, 'w')
  f.write(filestring)
  f.close()
  
  print "Done!"
#enddef

def GetRobotController(comp):
  ctrls = comp.findBehavioursByType(VC_ROBOTCONTROLLER)
  
  if len(ctrls) > 0:
    return ctrls[0]
  else:
    return None
  #endif
#enddef

def GetMachineDatFile():
  opencmd = getApplication().findCommand("dialogOpen")
  uri = ""
  ok = True
  filter = "Machine data file ($machine.dat)|$machine.dat"
 
  opencmd.execute(uri, ok, filter)
  
  if not opencmd.Param_2:
    return ""
  #endif
  
  uri = opencmd.Param_1
  filename = uri[8:len(uri)]
  return filename
#enddef

def UpdateMachineDatFile(filestring):
  global robot_joint_count
  
  # Update ex axis types: $AXIS_TYPE[7]=3
    
  re_ax_type = re.compile(r'\$AXIS_TYPE\[(?P<num>'+num+')\]=.*', re.M+re.IGNORECASE)
  ax_type = re_ax_type.finditer(filestring)
  
  if ax_type == None:
    print "Error parsing machine data (AXIS_TYPE), aborting command"
    return

  ext_joint = 0
  for i in ax_type:
    joint_index = int(i.group('num'))   
    if joint_index > robot_joint_count and ext_joint < len(ext_joints):
      joint_type = ext_joints[ext_joint].Type
      if joint_type == VC_JOINT_ROTATIONAL:
        joint_type = 3
      elif joint_type == VC_JOINT_TRANSLATIONAL:
        joint_type = 1
      #endif
      from_str = i.group()
      to_str = '$AXIS_TYPE[%s]=%s' %(i.group('num'), str(joint_type))
      filestring = filestring.replace(from_str, to_str, 1)
      ext_joint += 1
    #endif
  #endfor  
      
  # Update ex axis num: INT $EX_AX_NUM=2
  re_ax_num = re.compile(r'INT \$EX_AX_NUM=(?P<num>'+num+').*',re.M+re.IGNORECASE)
  ax_num = re_ax_num.finditer(filestring)

  if ax_num == None:
    print "Error parsing machine data (EX_AX_NUM), aborting command"
    return
    
  for i in ax_num:
    from_str = i.group()
    count = i.group('num')
    to_str = from_str.replace(count, str(len(ext_joints)), 1)
    filestring = filestring.replace(from_str, to_str)
  
  for i in external_comps:
    filestring = PopulateExternalMachineData(i, filestring)
  #endfor
  
  return filestring
#enddef

def PopulateExternalMachineData(comp, filestring):
  prop = comp.getProperty('EX_KIN')
  
  if prop == None:
    print "Error: EX_KIN property not found for component: " + comp.Name
    return filestring
  #endif
  
  ex_kin = prop.Value

  # Update kinematics definition: DECL EX_KIN $EX_KIN={ET1 #EASYS,ET2 #NONE,ET3 #NONE,ET4 #NONE,ET5 #NONE,ET6 #NONE}
  startIndex = filestring.find('DECL EX_KIN $EX_KIN={')
  
  if startIndex < 0:
    print "Error parsing machine data (kinematic definition), aborting command"
    return
  #endif
  
  endIndex = filestring.find('}', startIndex)
  old_kin_definition = filestring[startIndex:endIndex+1]
  startIndex = old_kin_definition.find(comp.EX_KIN)
  
  et_definition = old_kin_definition[startIndex:old_kin_definition.find(',',startIndex)]
  new_et_definition = et_definition.replace(et_definition, comp.EX_KIN + " " + comp.ET)
  new_kin_definition = old_kin_definition.replace(et_definition, new_et_definition)
  filestring = filestring.replace(old_kin_definition, new_kin_definition)
  
  # Update exis definition: DECL ET_AX $ET1_AX={TR_A1 #E1,TR_A2 #E2,TR_A3 #NONE}
  ax_definition = r'\$' + ex_kin + '_AX={.*'
  re_ax_definition = re.compile(ax_definition, re.M+re.IGNORECASE)
  ax_defs = re_ax_definition.finditer(filestring)
  
  if ax_defs == None:
    print "Error parsing machine data (axis definitions), aborting command"
    return
  #endif
  
  for i in ax_defs:
    from_str = i.group()
    to_str = from_str
    
    tr_a1 = comp.getProperty('TR_A1')   
    if tr_a1 != None:
      tr_a1_str = from_str[from_str.find('TR_A1') : from_str.find(',', from_str.find('TR_A1'))]
      to_str = from_str.replace(tr_a1_str, 'TR_A1 ' + comp.TR_A1)
    #endif
    
    tr_a2 = comp.getProperty('TR_A2') 
    if tr_a2 != None:
      tr_a2_str = from_str[from_str.find('TR_A2') : from_str.find(',', from_str.find('TR_A2'))]
      to_str = to_str.replace(tr_a2_str, 'TR_A2 ' + comp.TR_A2)
    #endif 
    filestring = filestring.replace(from_str, to_str)
  #endfor
  
  # Update name property: $ET<n>_NAME=[""]
  re_name = re.compile('\$' + ex_kin + r'_NAME\[\]=(?P<name>.*)', re.M+re.IGNORECASE)
  et_name = re_name.finditer(filestring)
  
  for i in et_name:
    from_str = i.group()
    to_str = '$%s_NAME[]="%s"' % (ex_kin, comp.Name)
    filestring = filestring.replace(from_str, to_str)
    break
  #endfor
    
  num = r' *-?\d*\.?\d+(?:[eE][-+]?\d+)?'
  joint_offset = r'\$'+ex_kin+r'_(?P<name>.*)={X (?P<X>'+num+'),Y (?P<Y>'+num+'),Z (?P<Z>'+num+'),A (?P<A>'+num+'),B (?P<B>'+num+'),C (?P<C>'+num+')}.*'
  re_joint_offset = re.compile(joint_offset,re.M+re.IGNORECASE)
  joint_offsets = re_joint_offset.finditer(filestring)
  if joint_offsets == None:
    print "Error parsing machine data (joint offsets), aborting command"
    return
  #endif
  
  # instead of updating the values in simulation model, we update the string
  for jo in joint_offsets:
    fp = comp.getProperty(jo.group('name'))
    if fp != None:
      from_str = jo.group()
      m = vcMatrix.new(fp.Value)
      to_str = '$%s_%s={X %f,Y %f,Z %f,A %f,B %f,C %f}' % (ex_kin,fp.Name,m.P.X,m.P.Y,m.P.Z,m.WPR.Z,m.WPR.Y,m.WPR.X)
      filestring = filestring.replace(from_str,to_str)
    #endif
  #endfor
  
  #$RAT_MOT_AX[7]={N -346,D 10}
  gear_ratio = r'\$RAT_MOT_AX\[(?P<index>'+num+')\]={N (?P<N>'+num+'),D (?P<D>'+num+')}.*'
  re_gear_ratio = re.compile(gear_ratio,re.M+re.IGNORECASE)
  gear_ratios = re_gear_ratio.finditer(filestring)
  if gear_ratios == None:
    print "Error parsing machine data (gear ratios), aborting command"
    return
  #endif

  for gr in gear_ratios:
    fp = comp.getProperty('RAT_MOT_AX_'+gr.group('index'))
    if fp != None:
      ratio = fp.Value
      from_str = gr.group()
      to_str =  '$RAT_MOT_AX[%s]={N %d,D %d}' % (gr.group('index'),ratio*10,10)
      filestring = filestring.replace(from_str,to_str)
    #endif
  #endfor
  
  return filestring
#enddef

def getProgram():
  teachcontext = app.TeachContext
  if teachcontext.ActiveRobot:
    executors = teachcontext.ActiveRobot.findBehavioursByType(VC_ROBOTEXECUTOR)
    if executors:
      return executors[0].Program
  return None

addState( first_state )
