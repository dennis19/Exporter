# as these are common to all commands, makes sense to have only one copy
from string import *
import re
import vcVector
import vcMatrix
from vcHelpers.Selection import *
import os.path

def printVector(vs):
  str = '[ '
  for v in vs:
    str += '[ %.2F, %.2F, %.2F ], ' % (v.X,v.Y,v.Z)
  if len(str) > 2:
    str = str[:-2]
  str += ' ]'
  print str

def printMatrix(ms):
  for m in ms:
    printVector([m.P,m.WPR])

def getTrack(robot):
  track = robot
  if track:
    while track.Parent != track.World:
      track = track.Parent
  return track

def getTablesAndFlanges(robot):
  tables = []
  flanges = []
  if robot:
    rcs = robot.findBehavioursByType(VC_ROBOTCONTROLLER)
    if len(rcs) == 1:
      for j in rcs[0].Joints:
        c = j.Controller.Component
        p = c.getProperty('ET')
        if p and not p.Value == '#ERSYS' and not tables.count(c):
          tables.append(c)
          flanges.append(j.Controller.FlangeNode)
  return tables, flanges

def getRobotAndController(comp):
  robot = None
  robotcontroller = None
  for sc in comp.findBehavioursByType(VC_SERVOCONTROLLER):
    for j in sc.Joints:
      if j.Controller.Type == VC_ROBOTCONTROLLER:
        robotcontroller = j.Controller
        robot = robotcontroller.Component
        break
      elif j.ExternalController and j.ExternalController.Type == VC_ROBOTCONTROLLER:
        robotcontroller = j.ExternalController
        robot = robotcontroller.Component
        break
  return robot, robotcontroller

def ensure_dir(path):
  if  os.path.isdir(path):
    return True
  if  os.path.isfile(path):
    return False
  head, tail = os.path.split(path)
  if os.path.exists(head) or ensure_dir(head):
    os.mkdir(path)
    return os.path.isdir(path)

def copyfile(from_file,to_file):
  ensure_dir(os.path.dirname(to_file))
  infile = open(from_file, 'rb')
  outfile = open(to_file, 'wb')
  outfile.write(infile.read())
  outfile.close()
  infile.close()

def getFileString(filter,uri,createbakfile,filename=''):
  filestring = ''
  ok = False
  if not filename:
    opencmd = getApplication().findCommand('dialogOpen')
    opencmd.execute(uri, ok, filter)
    if opencmd.Param_2:
      uri = opencmd.Param_1
      filename = uri[8:len(uri)]
  if filename:
    try:
      infile = open(filename,"r")
      filestring = infile.read()
      ok = True
    except:
      pass
    infile.close()
    i = 1
    if createbakfile:
      root, ext = os.path.splitext(filename)
      bakext = '.bk%d' % i
      bakfile = root+bakext
      while os.path.exists(bakfile):
        i += 1
        bakext = '.bk%d' % i
        bakfile = root+bakext
      copyfile(filename,bakfile)
  return filestring, filename, ok, bakfile


# REGULAR EXPRESSIONS
int_expr     = r' *-?\d+'
num  = r' *-?\d*\.?\d+(?:[eE][-+]?\d+)?'

#TOOL_DATA[1]={X 107.147003,Y 6.19999992E-05,Z 313.237,A 0.0,B 45.0,C 0.0}  
tool_data = r'TOOL_DATA\[(?P<index>'+int_expr+')\]={X (?P<X>'+num+'),Y (?P<Y>'+num+'),Z (?P<Z>'+num+'),A (?P<A>'+num+'),B (?P<B>'+num+'),C (?P<C>'+num+')}'
re_tool_data = re.compile(tool_data,re.M+re.IGNORECASE)

#TOOL_NAME[1,]="GUN"
tool_name = r'TOOL_NAME\[(?P<index>'+int_expr+'),\]=\"(?P<name>.*)\".*'
re_tool_name = re.compile(tool_name,re.M+re.IGNORECASE)

#TOOL_TYPE[1]=#TCP
tool_type = r'TOOL_TYPE\[(?P<index>'+int_expr+')\]=(?P<type>.*)'
re_tool_type = re.compile(tool_type,re.M+re.IGNORECASE)

#BASE_DATA[1]={X 0.0,Y 0.0,Z 0.0,A 0.0,B 0.0,C 0.0}
base_data = r'BASE_DATA\[(?P<index>'+int_expr+')\]={X (?P<X>'+num+'),Y (?P<Y>'+num+'),Z (?P<Z>'+num+'),A (?P<A>'+num+'),B (?P<B>'+num+'),C (?P<C>'+num+')}.*'
re_base_data = re.compile(base_data,re.M+re.IGNORECASE)

#BASE_NAME[17,]="DKP_400_01"
base_name = r'BASE_NAME\[(?P<index>'+int_expr+'),\]=\"(?P<name>.*)\".*'
re_base_name = re.compile(base_name,re.M+re.IGNORECASE)

#BASE_TYPE[1]=#BASE
base_type = r'BASE_TYPE\[(?P<index>'+int_expr+')\]=(?P<type>.*)'
re_base_type = re.compile(base_type,re.M+re.IGNORECASE)

#MACHINE_DEF[1]={NAME[] "Robot",COOP_KRC_INDEX 1,PARENT[] "WORLD",ROOT {X 0.0,Y 0.0,Z 0.0,A 0.0,B 0.0,C 0.0},MECH_TYPE #ROBOT,GEOMETRY[] " "}
machine_def = r'MACHINE_DEF\[(?P<index>'+int_expr+')\]={NAME\[\] \"(?P<name>.*)\",COOP_KRC_INDEX (?P<cki>'+int_expr+'),PARENT\[\] \"(?P<parent>.*)\",ROOT {X (?P<X>'+num+'),Y (?P<Y>'+num+'),Z (?P<Z>'+num+'),A (?P<A>'+num+'),B (?P<B>'+num+'),C (?P<C>'+num+')},MECH_TYPE (?P<mt>.*),GEOMETRY\[\] \"(?P<geometry>.*)\"}'
re_machine_def = re.compile(machine_def,re.M+re.IGNORECASE)

#MACHINE_FRAME_DAT[17]={MACH_DEF_INDEX 2,PARENT[] "DKP_400_01",GEOMETRY[] " "}
base_node = r'MACHINE_FRAME_DAT\[(?P<index>'+int_expr+')\]={MACH_DEF_INDEX (?P<mdi>'+int_expr+'),PARENT\[\] \"(?P<parent>.*)\",GEOMETRY\[\] \"(?P<geometry>.*)\"}'
re_base_node = re.compile(base_node,re.M+re.IGNORECASE)

