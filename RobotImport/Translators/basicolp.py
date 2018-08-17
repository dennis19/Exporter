#-------------------------------------------------------------------------------
# Copyright 2012 Visual Components Ltd. All rights reserved.
#-------------------------------------------------------------------------------

from vcCommand import *
from vcHelpers.Application import *
from vcHelpers.Robot import *
import math
import vcVector
import vcMatrix

#Reverse statement order in given routine
def reverseOrder(routine):
  for s in routine.Statements:
    s.Index=0
    
#Set first statement in routine
def setFirstStatement(routine,firstindex):
  count=xrange(routine.StatementCount-firstindex)
  for c in count:
    s=routine.getStatement(routine.StatementCount-1)
    s.Index=0
   

#Set same given tool for all motion statements in a routine
def setTool(routine,toolname,usemarks):
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      if s.Tool!=toolname:
        s.Tool=toolname
        
# Return line count of already open file
# The function sets the file pointer to the start of the file
def get_file_linecount(infile):  
  i = 0
  for line in infile:
    i += 1
  infile.seek(0)
  return i

# Rotate orientations of every target
def adjustOrientations(routine,rolldelta,pitchdelta,yawdelta,usemarks):
  if rolldelta==0.0 and pitchdelta==0.0 and yawdelta==0.0:
    return
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      m = vcMatrix.new(s.Target)
      m.rotateRelZ(rolldelta)
      m.rotateRelY(pitchdelta)
      m.rotateRelX(yawdelta)
      s.Target = m

#Shift each target relative to targets own coordinate system
def relTranslateTargets(routine,shiftN,shiftO,shiftA,usemarks):
  if shiftN==0.0 and shiftO==0.0 and shiftA==0.0:
    return
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      m = vcMatrix.new(s.Target)
      m.translateRel(shiftN,shiftO,shiftA)
      s.Target = m


#Delete all or marked statements from given routine
def clearPath(routine,usemarks):
  if usemarks==False:
    for s in routine.Statements:
      routine.deleteStatement(0)
  else:
      for s in routine.Statements:  
        if s.getProperty("Mark")!=None:
          routine.deleteStatement(s.Index)


#This function negates surface normals of all motions statens in given routine  
def negateSurfaceNormals(routine,usemarks):
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      m = vcMatrix.new(s.Target)
      m.N=-1.0*m.N
      m.A=-1.0*m.A
      s.Target = m

#Translate all targets      
def absTranslateTargets(routine,offsetx,offsety,offsetz,usemarks):
  if offsetx==0.0 and offsety==0.0 and offsetz==0.0:
    return
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      m = vcMatrix.new(s.Target)
      m.translateAbs(offsetx,offsety,offsetz)
      s.Target = m

      
def setFixedOrientations(routine,usemarks):
  previousroll=0.0
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      m = vcMatrix.new(s.Target)
      
      roll=math.degrees(math.atan2(m.A.Y,m.A.X))
      pitch=math.degrees(math.atan2(math.sqrt(m.A.X**2+m.A.Y**2),m.A.Z))
      if roll<=0.0:
        roll2=roll+180.0
      else:
        roll2=roll-180.0
      
      if abs(roll-previousroll)>abs(roll2-previousroll):
        roll=roll2
        pitch=-pitch
        
      previousroll=roll
      
      tmpmtx = vcMatrix.new()
      tmpmtx.rotateRelZ(roll)
      tmpmtx.rotateRelY(pitch)
      m.N=tmpmtx.N
      m.O=tmpmtx.O
      m.A=tmpmtx.A
           
      s.Target = m


def setRotatingOrientations(routine,usemarks):
  previousroll=0.0
  lastnvec=vcVector.new(0.0,0.0,0.0)
  indices=xrange(routine.StatementCount)
  
  for idx in indices:
    s=routine.getStatement(idx)
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      m = vcMatrix.new(s.Target)
      next=vcMatrix.new(0.0,0.0,0.0)
      nvec=vcVector.new(0.0,0.0,0.0)      
      nextfound=False
      nextidx=idx+1

      while nextidx<routine.StatementCount:
        nextstatement=routine.getStatement(nextidx)
        #check that the next statement used for orientation calculation is motion statement
        if ((nextstatement.Type == VC_STATEMENT_LINMOTION) or (nextstatement.Type== VC_STATEMENT_PTPMOTION)):
          next=vcMatrix.new(nextstatement.Target)
          nvec=vcVector.new(next.P-m.P)
          #check that the next motion statement is not in same location as current statement
          if nvec.length()>0.0:
            nvec.normalize()
            #check that the next motion statement is not in same line defined by approach vector
            if abs(nvec*m.A)<=0.999:
              nextfound=True
              break
        nextidx+=1
      
      if nextfound==False and lastnvec.length()>0.0:
        nvec=lastnvec
      
      ovec=vcVector.new(0.0,0.0,0.0)
      
      if nvec.length()>0.0:
        # calculate orientation vector from approach and normal, orthonormalize
        if abs(nvec*m.A)<=0.999:
          ovec=m.A^nvec
          ovec.normalize()
          nvec=ovec^m.A
          nvec.normalize()
          lastnvec=nvec   
          m.N=nvec
          m.O=ovec
          s.Target = m
      
      
def orientationSmoothing(routine,usemarks):
  WINDOWSIZE=1
  
  indices=xrange(routine.StatementCount)
  for idx in indices:
    #print "loop:",idx
    s=routine.getStatement(idx)
    if ( (s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION) ):
      # Never smooth reference points. In addition, if the routine contain marked points, then smooths only these points.
      if s.getProperty("ReferencePoint")!=None or (usemarks==True and s.getProperty("Mark")==None):
        #print "skipping point:",idx
        continue  
      m = vcMatrix.new(s.Target)
      previous=vcMatrix.new()
      next=vcMatrix.new()
      nvec=vcVector.new(m.N)
      ovec=vcVector.new(m.O)
      
      previdx=idx-1
      windowcount=WINDOWSIZE
      while previdx>0 and windowcount>0:
        #print "index:",idx,"previdx:",previdx
        prevstatement=routine.getStatement(previdx)
        if ( (prevstatement.Type == VC_STATEMENT_LINMOTION) or (prevstatement.Type== VC_STATEMENT_PTPMOTION) ):
          previous=vcMatrix.new(prevstatement.Target)
          nvec=nvec+previous.N
          ovec=ovec+previous.O
          windowcount-=1
        previdx-=1
        
      nextidx=idx+1
      windowcount=WINDOWSIZE
      while nextidx<routine.StatementCount and windowcount>0:
        #print "index:",idx,"nextidx:",nextidx
        nextstatement=routine.getStatement(nextidx)
        if ( (nextstatement.Type == VC_STATEMENT_LINMOTION) or (nextstatement.Type== VC_STATEMENT_PTPMOTION) ):
          next=vcMatrix.new(nextstatement.Target)
          nvec=nvec+next.N
          ovec=ovec+next.O
          windowcount-=1
        nextidx+=1
           
      #print idx,"nvec",nvec.X,nvec.Y,nvec.Z
      #print idx,"ovec",ovec.X,ovec.Y,ovec.Z
      
      nvec.normalize()
      ovec.normalize()
      
      if abs(ovec*m.A)>0.999:
        ovec=m.A^nvec
        ovec.normalize()
        nvec=ovec^m.A
        nvec.normalize()
      else:
        nvec=ovec^m.A
        nvec.normalize()
        ovec=m.A^nvec
        ovec.normalize()
     
      m.N=nvec
      m.O=ovec
      s.Target = m
      
#-------------------------------------------------------------------------------
# Set base for all motion statements in routine
def setRoutineBase(controller,routine,usemarks,destinationbase,lockpositionstoworld):
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)) and (usemarks==False or s.getProperty("Mark")!=None):
      if s.Base != destinationbase:
        if lockpositionstoworld:
          newBase = None
          currentBase = None
          for b in controller.Bases:
            if b.Name == s.Base:
              currentBase = b
            if b.Name == destinationbase:
              newBase = b
            if newBase!=None and currentBase!=None:
              break
            #endif
          #endfor
          CiW=getBaseInWorld(currentBase,controller)
          NiW=getBaseInWorld(newBase,controller)
          NiW.invert()
          p2 = NiW * CiW * s.Target
          s.Target = p2
        #endif
        s.Base = destinationbase
      #endif
    #endif

# def insertLINStatement(index,rapid,rapidspeed,pospath):
  # t = controller.createTarget()
  # s = routine.createStatement(VC_STATEMENT_LINMOTION)
  # s.MaxSpeed = fedrat
  # rapidproperty=addProperty(s, VC_BOOLEAN, "RapidSpeed",True,False,False,False,None,"")
  # addProperty(statement, VC_STRING, "PosPath",True,False,False,defaultparams.PosPath,None,"")
  # if rapid:
    # rapidproperty.Value=True
    # s.MaxSpeed = rapidspeed
  
  # s.readFromTarget(t)
  # s.Acceleration = 0
  # s.Deceleration = 0
  # s.AngularAcceleration = 0
  # rapid = False
  # s.AngularDeceleration = 0
  
# add linear motion statement into given routine
# the target parameter is used to get current robot setting (tool, base..)
# the m parameter defines target matrix
def addLINStatement(routine,target,m):
  #t = controller.createTarget(m)
  # create a motion statement and read its values from the newly created robot target
  s = routine.createStatement(VC_STATEMENT_LINMOTION)
  s.readFromTarget(target)
  s.Target=m
  # by setting the accelerations and decelarations to 0, the resulting motion is continuous
  s.Acceleration = 0
  s.Deceleration = 0
  s.AngularAcceleration = 0
  s.AngularDeceleration = 0
  return s  
  
def setSpeed(routine,LINProcessSpeed,LINRapidSpeed,PTPProcessSpeed,PTPRapidSpeed,usemarks):
  for s in routine.Statements:
    if s.Type == VC_STATEMENT_LINMOTION:
      if usemarks==False or (usemarks==True and s.getProperty("Mark")!=None):
        if s.getProperty("RapidSpeed"):
          s.MaxSpeed=LINRapidSpeed
        else:
          s.MaxSpeed=LINProcessSpeed
    elif s.Type== VC_STATEMENT_PTPMOTION:
      if usemarks==False or (usemarks==True and s.getProperty("Mark")!=None):
        if s.getProperty("RapidSpeed"):
          s.JointSpeed=PTPRapidSpeed
        else:
          s.JointSpeed=PTPProcessSpeed
  
  
#Set Fanuc positioning path (accuracy) value for all motion statements in routine
def setRoutinePositioningPath(routine,pospath,usemarks):
  for s in routine.Statements:
    if ((s.Type == VC_STATEMENT_LINMOTION) or (s.Type== VC_STATEMENT_PTPMOTION)):
      if usemarks==False or (usemarks==True and s.getProperty("Mark")!=None):
        if s.getProperty("PosPath")==None:
          addProperty(s, VC_STRING, "PosPath",True,False,False,pospath,None,"")
        else:
          s.PosPath=pospath
        #Currently seems to affect only in cases with external axis
        if s.PosPath=="FINE":
          s.JointForce=100.0
        else:
          s.JointForce=0.0
          
#Set Fanuc positioning path (accuracy) value for given statement
def setPositioningPath(statement,pospath):
  if statement.getProperty("PosPath")==None:
    addProperty(statement, VC_STRING, "PosPath",True,False,False,pospath,None,"")
  else:
    statement.PosPath=pospath
  #Currently seems to affect only in cases with external axis
  if statement.PosPath=="FINE":
    statement.JointForce=100.0
  else:
    statement.JointForce=0.0
          
# Update statement's grid color based on statement's property values
def updateStatementGridColor(statement):
  v = vcVector.new()
  found=False
  if statement.getProperty("VerbatimComment"):
    v.X = 0.9
    v.Y = 1.0
    v.Z = 0.0
    found=True
  if statement.getProperty("RapidSpeed"):
    v.X = 0.0
    v.Y = 1.0
    v.Z = 1.0
    found=True  
  if statement.getProperty("SkipPoint"):
    v.X = 0.25
    v.Y = 0.25
    v.Z = 0.25
    found=True
  if statement.getProperty("ReferencePoint"):
    v.X = 1.0
    v.Y = 1.0
    v.Z = 0.0
    found=True
  if statement.getProperty("Mark"):
    v.X = 1.0
    v.Y = 0.5
    v.Z = 0.0
    found=True
  
  if found:
    addProperty(statement,VC_VECTOR,"GridColor",False,False,False,v,None,"")
  elif statement.getProperty("GridColor"):
    statement.deleteProperty(statement.getProperty("GridColor"))

#loop through the routine and return true if any statement has a mark
def isAnyMarksInRoutine(routine):
  for s in routine.Statements:
    if s.getProperty("Mark")!=None:
      return True
  return False
  
#-------------------------------------------------------------------------------
# returns given robot base location in world coordinate system
def getBaseInWorld(base,controller):  
  if base:
    # check if the base is attached to the node
    if base.Node:
      BiW = base.Node.WorldPositionMatrix * base.PositionMatrix
    else:
      #standard case, base attached to robot world frame
      dummytarget = controller.createTarget()
      root_to_worldframe=dummytarget.getRootNodeToRobotRoot()
      root_to_worldframe.invert()
      BiW = controller.RootNode.WorldPositionMatrix * root_to_worldframe * base.PositionMatrix
    #endif
  else:
    # no base (NULL), return robot world frame
    dummytarget = controller.createTarget()
    root_to_worldframe=dummytarget.getRootNodeToRobotRoot()
    root_to_worldframe.invert()
    BiW = controller.RootNode.WorldPositionMatrix * root_to_worldframe
  #endif
  return BiW  

  
    