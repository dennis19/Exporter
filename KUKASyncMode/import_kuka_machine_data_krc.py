from vcCommand import *
from vcHelpers.Selection import *
import vcVector
import vcMatrix
import re
from common import getTrack

DEBUG_MESSAGES = False

def first_state():
  print "Importing machine data..."
  
  componentname = getProperty("ComponentName").Value
  filename = getProperty("FileName").Value
  ErrorProperty = getProperty("ErrorString")
 
  if DEBUG_MESSAGES:
    print "componentname = %s" %componentname
    print "filename = %s" %filename
    
  rcomp = getApplication().findComponent(componentname)

  if not rcomp:
    ErrorProperty.Value = 'Component \'%\' not found, aborting command' % ComponentName
    print ErrorProperty.Value
    return

  track = getTrack(rcomp)
  
  if DEBUG_MESSAGES:
    if track:
      print "track found = %s" %track.Name
    else:
      print "no track found"
      
  global external_comps
  external_comps = []
  
  # Get robot controller
  robot = GetRobotController(rcomp)
  # Get RSL executor
  executor = GetRslExecutor(rcomp)
      
  if robot == None:
    ErrorProperty.Value = 'Robot not found, aborting command'
    print ErrorProperty.Value
    return
  
  if DEBUG_MESSAGES:
    print "controller found = %s" %robot.Name  
    if executor:
      print "executor found = %s" %executor.Name  
    else:
      print "no executor found"
      
  if filename == "":
    ErrorProperty.Value = 'Machine data file not found, aborting command'
    print ErrorProperty.Value
    return
    
  try:
    infile = open(filename,"r")
  except:
    ErrorProperty.Value = 'Cannot open machine data file %s, aborting command' % filename
    print ErrorProperty.Value
    return
  #endtry
  
  filestring = infile.read()
  infile.close()
  
  # Get external joints and connected components
  for j in robot.Joints:
    if j.ExternalController != None:
      exists = False
      for i in external_comps:
        if i.Name == j.Controller.Component.Name:
          exists = True
          break
      if exists == False:
        external_comps.append(j.Controller.Component)
     #endif
  #endfor
  
  for comp in external_comps:
    prop = comp.getProperty('EX_KIN')  
    if prop == None:
      ErrorProperty.Value = "EX_KIN property not found from component, aborting command"
      print ErrorProperty.Value
      return
     #endif
    ex_kin = prop.Value
    
    # Update name property: $ET3_NAME[]="DKP 400-1 #2"
    re_name = re.compile('\$' + ex_kin + r'_NAME\[\]=(?P<name>.*)', re.M+re.IGNORECASE)
    et_name = re_name.finditer(filestring)
    
    for i in et_name:
      comp_name = i.group('name')
      comp_name = comp_name.replace('"','')
      #UpdateBaseFrameStatements(executor, comp.Name, comp_name)
      comp.Name = comp_name
      if DEBUG_MESSAGES:
        print "updated component name to %s" % comp_name
      break
    #endfor
    
    # Update kinematics definition: DECL EX_KIN $EX_KIN={ET1 #EASYS,ET2 #NONE,ET3 #NONE,ET4 #NONE,ET5 #NONE,ET6 #NONE}
    startIndex = filestring.find('DECL EX_KIN $EX_KIN={')
  
    if startIndex < 0:
      ErrorProperty.Value = "Error parsing machine data (kinematic definition), aborting command"
      print ErrorProperty.Value
      return
    #endif
  
    endIndex = filestring.find('}', startIndex)
    old_kin_definition = filestring[startIndex:endIndex+1]
    startIndex = old_kin_definition.find(ex_kin)
  
    et_definition = old_kin_definition[startIndex:old_kin_definition.find(',',startIndex)]
    et_definition = et_definition.replace(ex_kin, '').lstrip().rstrip()
    et = comp.getProperty('ET')
    
    if et != None:
      et.Value = et_definition
      if DEBUG_MESSAGES:
        print "updated ET value to %s" % et_definition 
    #endif
    
    # Update exis definition: DECL ET_AX $ET1_AX={TR_A1 #E1,TR_A2 #E2,TR_A3 #NONE}
    ax_definition = r'\$' + ex_kin + '_AX={.*'
    re_ax_definition = re.compile(ax_definition, re.M+re.IGNORECASE)
    ax_defs = re_ax_definition.finditer(filestring)
  
    if ax_defs == None:
      ErrorProperty.Value = "Error parsing machine data (axis definitions), aborting command"
      print ErrorProperty.Value
      return
    #endif
    
    for i in ax_defs:
      from_str = i.group()
      to_str = from_str
    
      tr_a1 = comp.getProperty('TR_A1')   
      if tr_a1 != None:
        tr_a1_str = from_str[from_str.find('TR_A1') : from_str.find(',', from_str.find('TR_A1'))]
        tr_a1_str = tr_a1_str.replace('TR_A1', '')
        tr_a1_str = tr_a1_str.lstrip().rstrip()
        tr_a1.Value = tr_a1_str
        if DEBUG_MESSAGES:
          print "updated TR_A1 value to %s" % tr_a1_str
      #endif  
      
      tr_a2 = comp.getProperty('TR_A2') 
      if tr_a2 != None:
        tr_a2_str = from_str[from_str.find('TR_A2') : from_str.find(',', from_str.find('TR_A2'))]
        tr_a2_str = tr_a2_str.replace('TR_A2', '')
        tr_a2_str = tr_a2_str.lstrip().rstrip()
        tr_a2.Value = tr_a2_str
        if DEBUG_MESSAGES:
          print "updated TR_A2 value to %s" % tr_a2_str
      #endif 
    #endfor
    
    num   = r' *-?\d*\.?\d+(?:[eE][-+]?\d+)?'
    joint_offset = r'\$'+ex_kin+r'_(?P<name>.*)={X (?P<X>'+num+'),Y (?P<Y>'+num+'),Z (?P<Z>'+num+'),A (?P<A>'+num+'),B (?P<B>'+num+'),C (?P<C>'+num+')}.*'
    re_joint_offset = re.compile(joint_offset,re.M+re.IGNORECASE)
    joint_offsets = re_joint_offset.finditer(filestring)
    if joint_offsets == None:
      ErrorProperty.Value = "Error parsing machine data (joint offsets), aborting command"
      print ErrorProperty.Value
      return
    #endif

    for jo in joint_offsets:
      fp = comp.getProperty(jo.group('name'))
      if fp != None:
        m = vcMatrix.new()
        m.P = vcVector.new(eval(jo.group('X')),eval(jo.group('Y')),eval(jo.group('Z')))
        m.WPR = vcVector.new(eval(jo.group('C')),eval(jo.group('B')),eval(jo.group('A')))
        fp.Value = m
        if DEBUG_MESSAGES:
          print "updated value of %s" % fp.Name
      #endif
    #endfor
  
    #$RAT_MOT_AX[7]={N -346,D 10}
    gear_ratio = r'\$RAT_MOT_AX\[(?P<index>'+num+')\]={N (?P<N>'+num+'),D (?P<D>'+num+')}.*'
    re_gear_ratio = re.compile(gear_ratio,re.M+re.IGNORECASE)
    gear_ratios = re_gear_ratio.finditer(filestring)
    if gear_ratios == None:
      ErrorProperty.Value = "Error parsing machine data (gear ratios), aborting command"
      print ErrorProperty.Value
      return
    #endif

    for gr in gear_ratios:
      fp = comp.getProperty('RAT_MOT_AX_'+gr.group('index'))
      if fp != None:
        fp.Value = float(eval(gr.group('N')))/float(eval(gr.group('D')))
        if DEBUG_MESSAGES:
          print "updated value of " % fp.Name
        # this property is present only in case of a track (?), therefore, also mark the robot mounting to be be 'Custom'
        rm = comp.getProperty('RobotMounting')
        if rm:
          rm.Value = 'Custom'
      #endif
    #endfor
  #endfor
  print "Done!"
#enddef


addState( first_state )

def GetRobotController(comp):
  ctrls = comp.findBehavioursByType(VC_ROBOTCONTROLLER)
  
  if len(ctrls) > 0:
    return ctrls[0]
  else:
    return None
  #endif
#enddef

def GetRslExecutor(comp):
  execs = comp.findBehavioursByType(VC_ROBOTEXECUTOR)  
  if len(execs) > 0:
    return execs[0]
  else:
    return None
  #endif
#enddef

# for legacy rsl executor 
def UpdateBaseFrameStatements(executor, oldName, newName):
  if executor != None:
     routines = []
     routines.append(executor.MainRoutine)
     
     for i in executor.SubRoutines:
       routines.append(i)
     #endfor
     
     for routine in routines:
       for statement in routine.Statements:
         if statement.Type == VC_STATEMENT_DEFINE_BASE:
           if statement.Node.find('::') > 0:
             comp_string = statement.Node[0: statement.Node.find('::')]
             if comp_string == oldName:
               new_comp_string = comp_string.replace(oldName, newName)
               statement.Node = statement.Node.replace(comp_string, new_comp_string)
             #endif
           #endif
         #endif
       #endfor
     #endfor
   #endif
 #enddef
