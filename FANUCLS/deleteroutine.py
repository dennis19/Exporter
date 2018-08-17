from vcCommand import *
#-------------------------------------------------------------------------------
app = getApplication()

def getActiveRoutine():

  teach = app.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

  return routine

def OnStart():

  routine = getActiveRoutine()
  if routine == routine.Program.MainRoutine: return

  rname = routine.Name
  program = routine.Program
  comp = program.Executor.Component
  program.deleteRoutine( routine )
  note = comp.findBehaviour( rname )
  if note: note.delete() 
  mainroutine = comp.getProperty('MainRoutine')
  if mainroutine:
    stepValues = mainroutine.StepValues
    if rname in stepValues:
      stepValues.remove(rname)
    if mainroutine.Value == rname:
      if len(stepValues):
        mainroutine.Value = stepValues[0]
      else:
        mainroutine.Value = ""
    mainroutine.StepValues = stepValues
  for p in comp.Properties:
    if rname+'::' in p.Name:
      comp.deleteProperty(p)

addState( None )
