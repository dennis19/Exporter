from vcCommand import *
import time

#-------------------------------------------------------------------------------
app = getApplication()

def getActiveRoutine():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

  return routine
  
def getAllStatements(routine):
  allstatements = []
  for s in routine.Statements:
    allstatements = extendStatements(s, allstatements)
  return allstatements

def extendStatements(statement,statements):
  statements.append(statement)
  if statement.Type == VC_STATEMENT_WHILE:
    for s in statement.Scope.Statements:
      statements = extendStatements(s,statements)
  elif statement.Type == VC_STATEMENT_IF:
    for s in statement.ThenScope.Statements:
      statements = extendStatements(s,statements)
    for s in statement.ElseScope.Statements:
      statements = extendStatements(s,statements)
  return statements

def OnStart():
  global controller
  global text, statementCount, routine, uframe_num, utool_num, label

  routine = getActiveRoutine()
  if not routine:
    app.messageBox("No Routine selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endif

  if routine.Name == 'PositionRegister': return

  print 'Converting %s to LS' % routine.Name

  program = routine.Program
  executor = program.Executor
  comp = executor.Component
  controller = executor.Controller

  rname = routine.Name

  note =  comp.findBehaviour( rname )
  if not note:
    note = comp.createBehaviour( VC_NOTE, rname )
  #endif

  comp.createProperty(VC_BOOLEAN,"%s::SkipExecution"%rname)

  header = """/PROG  %s
/ATTR
OWNER           = MNEDITOR;
COMMENT         = "%s";
PROG_SIZE       = 0;
CREATE          = %s;
MODIFIED        = %s;
FILE_NAME       = ;
VERSION         = 0;
LINE_COUNT      = 0;
MEMORY_SIZE     = 0;
PROTECT         = READ_WRITE;
TCD:  STACK_SIZE        = 0,
      TASK_PRIORITY     = 50,
      TIME_SLICE        = 0,
      BUSY_LAMP_OFF     = 0,
      ABORT_REQUEST     = 0,
      PAUSE_REQUEST     = 0;
DEFAULT_GROUP   = 1,*,*,*,*;
CONTROL_CODE    = 00000000 00000000;
/APPL
/MN
"""
  td = time.strftime("DATE %y-%m-%d  TIME %H:%M:%S")
  text = header % (rname, rname, td, td)

  mainroutine = comp.getProperty('MainRoutine')
  if mainroutine:
    stepValues = mainroutine.StepValues
    if rname not in stepValues:
      stepValues.append(rname)
      mainroutine.StepValues = stepValues
    #endif
  #endif

  label = 1
  uframe_num = -1
  utool_num = -1
  statementCount = 1
  ##for statement in getAllStatements(routine):
  for statement in routine.Statements:
    writeStatement( statement )
  #endfor
  note.Note = text

def writeStatement( statement ):
  global text, statementCount, uframe_num, utool_num, label

  line = "%4i:  " % statementCount 

  if statement.Type == VC_STATEMENT_CALL:
    line += "CALL %s;\n" % (statement.RoutineName)

  elif statement.Type == VC_STATEMENT_DELAY:
    line += "WAIT %6.2f(sec) ;\n" % (statement.Delay)

  elif statement.Type == VC_STATEMENT_COMMENT:
    if statement.Comment[:2] == '++':
      line += "%s;\n" % (statement.Comment[2:])
    else:
      line += "!%s;\n" % (statement.Comment)

  elif statement.Type == VC_STATEMENT_SETBIN:
    if statement.OutputPort < 1000:
      line += "DO[%i: %s]=" %(statement.OutputPort, statement.Name)
    else:
      line += "RO[%i: %s]=" %(statement.OutputPort-1000, statement.Name)
    #endif
    if statement.OutputValue:
      line += "ON ;\n"
    else:
      line += "OFF ;\n"
    #endif

  elif statement.Type == VC_STATEMENT_WAITBIN:
    if statement.InputPort < 1000:
      line += "WAIT DI[%i: %s]=" %(statement.InputPort, statement.Name)
    else:
      line += "WAIT RI[%i: %s]=" %(statement.InputPort-1000, statement.Name)
    #endif
    if statement.InputValue:
      line += "ON ;\n" 
    else:
      line += "OFF ;\n"
    #endif

  elif statement.Type in [VC_STATEMENT_LINMOTION, VC_STATEMENT_PTPMOTION]:
    if not statement.getProperty('INDEX'):
      indices = {}
      maxIndex = 0
      for s in routine.Statements:
        if s.getProperty('INDEX'):
          indices[s.INDEX] = True 
          if s.INDEX > maxIndex: maxIndex = s.INDEX
        #endif
      #endfor
      sName = statement.Positions[0].Name
      try:
        num = int(sName[sName.rindex('_')+1:])
      except:
        try:
          for i in range(len(sName)-1,-1,-1):
            if not sName[i:].isdigit():
              num = int(sName[i+1:]) 
              break
            #endif
          #endfor
        except:
          num = maxIndex + 1
        #endtry
      #endtry

      statement.createProperty( VC_INTEGER, 'INDEX' )

      statement.INDEX = num 
      if indices.get( num, False ):
        statement.INDEX = maxIndex + 1
        """
        for i in range( 1, routine.StatementCount+2):
          if not indices.get( num, False ):
            statement.INDEX = i
            break
          #endif
        #endfor
        """
      #endif
    #endif

    pointIndex = statement.INDEX

    bName = statement.Base
    for i, b in enumerate(controller.Bases):
      if b.Name == bName:
        uf = i+1
        break
      #endif
    else:
      uf = 0
    #endfor

    if uframe_num != uf:
      uframe_num = uf
      line += "UFRAME_NUM = %i ;\n" % (uf)
      statementCount += 1
      line += "%4i:  " % statementCount 
    #endif

    tName = statement.Tool
    for i, t in enumerate(controller.Tools):
      if t.Name == tName:
        ut = i+1
        break
      #endif
    else:
      ut = 0
    #endfor

    if utool_num != ut:
      utool_num = ut
      line += "UTOOL_NUM = %i ;\n" % (ut)
      statementCount += 1
      line += "%4i:  " % statementCount 
    #endif

    zone = 'FINE'
    pName = statement.Positions[0].Name
    if pName[:2] == 'PR':
      offset = 15
      posType = 'PR'
      line = "%4i:   ;\n" % statementCount 
      statementCount += 1
      line  += "%4i:  PR[%i,1:XYP] = PR[%i,1:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex,offset)
      statementCount += 1
      line += "%4i:  PR[%i,2:XYP] = PR[%i,2:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex,offset)
      statementCount += 1
      line += "%4i:  PR[%i,3:XYP] = PR[%i,3:XYP]+R[%i:X_P];\n" % (statementCount, pointIndex, pointIndex,offset)
      statementCount += 1
      line += "%4i:   ;\n" % statementCount 
      statementCount += 1
      line += "%4i:  " % statementCount 
    else:
      posType = 'P'
    #endif

    if statement.Type == VC_STATEMENT_LINMOTION:
      line += "L %s[%i: %s]  %gmm/sec %s ;\n" % (posType, pointIndex, pName, statement.MaxSpeed,zone)
    elif statement.Type == VC_STATEMENT_PTPMOTION:
      line += "J %s[%i: %s]  %g%% %s ;\n" % (posType, pointIndex, pName, statement.JointSpeed*100,zone)
    #endif

  elif statement.Type == VC_STATEMENT_SETPROPERTY:
    line += "%s = %s;\n" %(statement.TargetProperty, statement.ValueExpression)

  elif statement.Type == VC_STATEMENT_IF:
    thenlabel = label
    label += 1
    elselabel = label
    label += 1
    line += "IF %s,JMP LBL[%i];\n" % (statement.Condition, thenlabel)
    text += line
    statementCount += 1
    for s in statement.ElseScope.Statements:
      writeStatement( s )
    line = "%4i: JMP LBL[%i];\n" % (statementCount, elselabel)
    text += line
    statementCount += 1
    line = "%4i: LBL[%i];\n" % (statementCount, thenlabel)
    text += line
    statementCount += 1
    for s in statement.ThenScope.Statements:
      writeStatement( s )
    line = "%4i: LBL[%i];\n" % (statementCount, elselabel)
    
  else:
    print statement.Type
    return 

  #endif

  statementCount += 1
  text += line
  return


addState( None )
