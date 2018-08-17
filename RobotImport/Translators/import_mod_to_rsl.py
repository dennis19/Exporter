#-------------------------------------------------------------------------------
# Copyright 2013 Visual Components Ltd. All rights reserved.
#-------------------------------------------------------------------------------
from vcScript import *
from vcHelpers.Application import *
from vcCommand import *
from basicolp import *
import vcVector
import vcMatrix
import re
import time

app = getApplication()
file="C:\\Users\\D.Peuss\\Documents\\Visual Components\\4.1\\MyExports\\Test1.mod"
#subroutine=cre
#filename = filedialog.askopenfilename( filetypes=("All files","*.*") )
def firstState():
  program = getProgram()
  
  if not program: 
    print "no Program"
  else:
    subroutine=program.addRoutine('vcHelperMove')
    robot = app.CurrentContext.ActiveRobot
    defaultparams=app.findLayoutItem("DefaultParameters")
    controller = program.Executor.Controller
    print "program = %s" %program
    print "filename = %s" %file
    print "routine = %s" %subroutine
    print "robot = %s" %robot
    print "Controller = %s" %controller
    print "DefaultParameters = %s" %defaultparams
    importPath( app,file,subroutine )
	
	
def importPath(app,filename,subroutine):
  global program, routine, controller, basename, toolname, basenames, toolnames, robotconfig, robotconfigs
  program, routine, controller, basename, toolname, basenames, toolnames, robotconfig, robotconfigs = getSelectedRobotData()
  routine=subroutine
  program = getProgram()
  controller = program.Executor.Controller
  infile = open(filename,"r")
  try:
    infile = open(filename,"r")
  except:
    app.messageBox("Cannot open file \'%s\' for reading" % filename,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return False
  
  defaultparams=app.findLayoutItem("DefaultParameters")
  feedrate = 100#defaultparams.DefaultLINProcessSpeed
  
  #robtarget regular expression
  robtargetregex="\[ *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *, *\[[0-9+-eE,. ]+\] *\]"
  # floating point regular expression
  floatregex = "[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"
  # workobject regular expression
  wobjregex = r"\\WObj:=(?P<workobject>[a-zA-Z0-9]+)"
  # tool definition regular expression
  toolregex = r", *(?P<tooln>[a-zA-Z0-9]+)"  
  
  curlc = 0
  lc=get_file_linecount(infile)
  prevtime = time.clock()
  firstwarning=True
  
  while True:
    #Update line count
    curlc+=1
    
    #Read nci command
    myline=infile.readline()
    if not myline: break
    rtmatch=re.findall(robtargetregex, myline)
    for mymatch in rtmatch:    
      match=re.findall(floatregex, mymatch)
      
      # robtarget has 17 floating point values
      if len(match)==17:
        m = vcMatrix.new()
        m.P = vcVector.new(float(match[0]),float(match[1]),float(match[2]))
        m.setQuaternion(float(match[4]),float(match[5]),float(match[6]),float(match[3]))
        t = controller.createTarget(m)  
        if "MoveJ" in myline.lower():
          s = routine.addStatement(VC_STATEMENT_PTPMOTION)
        else:
          s = routine.addStatement(VC_STATEMENT_LINMOTION)
                  
        
        #cfx config
        t.RobotConfig=int(match[10])
        
        #joint turns for axis 1,4 and 6
        if s.Type== VC_STATEMENT_PTPMOTION:
          jointturnprops=["JointTurns1","JointTurns4","JointTurns6"]
          configindex=7
          for jointturnpropname in jointturnprops:
            jointturnprop=s.getProperty(jointturnpropname)
            if jointturnprop!=None:
              if float(match[configindex])>1:
                jointturnprop.Value=1
              elif float(match[configindex])<-2:
                jointturnprop.Value=-1
            configindex+=1
        
        s.readFromTarget(t)
        
        #set base based on workobject definition
        wobjdef = re.search(wobjregex,myline)
        if wobjdef:
          wobjname = wobjdef.group('workobject')
          if wobjname:
            #set base for statement only if the base is found from controller
            for b in controller.Bases:
              if b.Name == wobjname:
                s.Base=wobjname
            if s.Base!=wobjname and firstwarning:
              firstwarning=False
              app.messageBox("Undefined workobject \'%s\' in robot program" % wobjname,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
             
        #tool definition
        tooldef=None
        for tooldef in re.finditer(toolregex,myline):
          pass
        if tooldef:
          rtoolname = tooldef.group('tooln')
          #set base for statement only if the base is found from controller
          for b in controller.Tools:
            if b.Name == rtoolname:
              s.Tool=rtoolname
          if s.Tool!=rtoolname and firstwarning:
            firstwarning=False
            app.messageBox("Undefined tool \'%s\' in robot program" % rtoolname,"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
             
        # external axes
        for j in range(6):
          if match[j+11]!="9E+09" and match[j+11]!="9e+09":
            extjoint=s.getProperty("ExternalJoint"+str(j+1))
            if extjoint!=None:
              extjoint.Value=float(match[j+11])
            else:
              firstwarning=False
              app.messageBox("Undefined external axis \'%s\' in robot program" % (j+1),"Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
        
        if s.Type== VC_STATEMENT_LINMOTION:
          s.Acceleration = 0
          s.Deceleration = 0
          s.AngularAcceleration = 0
          s.AngularDeceleration = 0
          s.MaxSpeed = feedrate
      
    # Update progress 
    curtime = time.clock()
    if curtime - prevtime > 2.0:
      prevtime = curtime
      myprogress=float(curlc)/float(lc+1)
      app.ProgressStatus = "Importing targets: %d%% done " % int(100.0*myprogress)
      app.ProgressValue = myprogress
  
  infile.close()
  return True
  
def getProgram():
  teachcontext = app.TeachContext
  if teachcontext.ActiveRobot:
    executors = teachcontext.ActiveRobot.findBehavioursByType(VC_ROBOTEXECUTOR)
    if executors:
      return executors[0].Program
  return None
  
def getSelectedRobotData():
  global app
  program = None
  routine = None
  controller = None
  basename = '*NULL*'
  toolname = '*NULL*'
  basenames = []
  toolnames = []
  robotconfig = -1
  robotconfigs = []
  sel = app.SelectionManager
  try:
    robocomp = app.CurrentContext.ActiveRobot
    print "robocomp = %s" %robocomp
  except:
    try:
      robocomp = app.CurrentContext.ActiveComponent
      print "robocompComp = %s" %robocomp
    except:
      selected_components = sel.getSelection(VC_SELECTION_COMPONENT)
      print "robocompComp1 = %s" %robocomp
      if len(selected_components) == 1:
        robocomp = selected_components[0]
      else:
        robocomp = None
  if robocomp:
    print "robocompComp2 = %s" %robocomp
    #executors = robocomp.findBehavioursByType( VC_RSLEXECUTOR )
    #print "executors = %s" %executors
    program = getProgram()
    #if len(executors) == 1:
    #if len(program) == 1:
      #program = executors[0]
    print "program = %s" %program
    if not program:
      print "robocompComp3 = %s" %robocomp
      print "Current selection is not valid - Select a Robot RSL Program" 
      return None
    routine = program.Routines[0]
    print "routine = %s" %routine
    controller = program.Executor.Controller
    controller.clearTargets()
    motiontarget = controller.createTarget()
    basename = motiontarget.BaseName
    print "basename = %s" %basename
    if basename == '':
      basename = '*NULL*'
    #endif
    toolname = motiontarget.ToolName
    if toolname == '':
      toolname = '*NULL*'
    #endif
    robotconfig = motiontarget.RobotConfig
    motiontarget.TargetMode = VC_MOTIONTARGET_TM_NORMAL
    basenames = [ '*NULL*' ]
    for b in controller.Bases:
      basenames.append( b.Name )
    #endfor
    toolnames = [ '*NULL*' ]
    for t in controller.Tools:
      toolnames.append( t.Name )
    #endfor
    dummyStatement = routine.addStatement(VC_STATEMENT_PTPMOTION)
    for prop in dummyStatement.Properties:
      if prop.Name == 'Configuration':
        break
      else:
        prop = None
      #endif
    #endfor
    if prop == None:
      robotconfigs = ['Config1', 'Config2', 'Config3', 'Config4', 'Config5', 'Config6', 'Config7', 'Config8']
    else:
      robotconfigs = []
      for config in prop.StepValues:
        robotconfigs.append( config )
      #endfor
    #endif
    routine.deleteStatement( dummyStatement.Index )
    return (program,routine,controller,basename,toolname,basenames,toolnames,robotconfig,robotconfigs)
  else:
    print "Current selection is not valid - Select a Robot RSL Program" 
    return None
#-------------------------------------------------------------------------------
addState( firstState )

