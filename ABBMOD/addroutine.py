from vcCommand import *
from vcHelpers.Application import *
import time
#-------------------------------------------------------------------------------
app = getApplication()

routineName = createProperty(VC_STRING, 'RoutineName')
button = createProperty(VC_BUTTON, 'OKAY')

def getActiveProgram():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

  return routine.Program

def OnStart():

  executeInActionPanel()

def onOkay( button ):

  program = getActiveProgram()
  if not program:
    app.messageBox("No program selected, aborting.","Warning",VC_MESSAGE_TYPE_WARNING,VC_MESSAGE_BUTTONS_OK)
    return
  #endin

  rname = routineName.Value

  executor = program.Executor
  comp = executor.Component
  routine = program.addRoutine( rname )

  note =  comp.findBehaviour( rname )
  if not note:
    note = comp.createBehaviour( VC_NOTE, rname )
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
  note.Note = header % (rname, rname, td, td)

  mainroutine = comp.getProperty('MainRoutine')
  if mainroutine:
    stepValues = mainroutine.StepValues
    stepValues.append(rname)
    mainroutine.StepValues = stepValues

button.OnChanged = onOkay

addState( None )
