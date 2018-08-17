from vcCommand import *
#-------------------------------------------------------------------------------
import Tkinter as tk
import re

colon = r'\s*:\s*'
semicolon = r'\s*;\s*'
integer = r'-?\d+'
nl = r' *\r?[\n\0]'
end = r'\s*$'
lnum = r'\s*(?P<lnum>'+integer+')' + colon 

class LSEditor(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs) 
        self.wm_attributes("-topmost",1)
        self.protocol("WM_DELETE_WINDOW", self.destroy )
	self.InSimMode = True
        self.changed = False
        self.routineName = None
        self.frame = tk.Frame( self )

        self.text = tk.Text(self.frame,width=60,height=10, wrap='word')
	"""
        self.scrollbar = tk.Scrollbar(self.frame)
        self.text = tk.Text(self.frame,width=60,height=10, wrap='word', yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.text.yview)
        self.scrollbar.pack(side='right',fill='y', expand=False)
	"""
        self.text.pack(side='top', fill='both', expand=True)
        self.text.tag_configure("current_line", background="#e9e9e9")
        self.updateButton = tk.Button(self.frame, text='Update Note', command=self._update )
        self.deleteButton = tk.Button(self.frame, text='Delete Line', command=self._deleteLine )
        self.frame.pack(fill='both', expand=True)
        self._highlight_current_line()
        
    def on_closing(self):
        self.destroy()

    def _update(self):
	pos = self.text.index('insert')
        progtext = self.text.get(1.0,'end')

	text = ''
        lineNumber = 0
        header = True
        for line in progtext.split('\n'):
          if header:
            text += line + '\n'
            if re.match(r'/MN' + end, line): header = False
            continue
          #endif
          if len(line)<2: continue
          lineNumber += 1
          LNUM = re.match(lnum + '(.*)' + semicolon + end, line)
          if LNUM:
            line = '%4i%s\n' % (lineNumber, line[line.index(':'):])
          else:
            line = '%4i:  %s\n' % (lineNumber,line)
          #endif
          text += line
        #endfor
        note = comp.findBehaviour( self.routineName )
        note.Note = text

	self.text.config(state='normal')
        self.text.delete(1.0, 'end')
        self.text.insert('end', text)

        self.text.mark_set('insert',pos)
        self.text.see('insert')
      
    def _deleteLine(self):
        self.text.delete('insert linestart', 'insert lineend+1c')
        self.changed = True

    def _highlight_current_line(self, interval=100):
	if self.routineName != comp.CurrentRoutine:
          self.routineName = comp.CurrentRoutine
          note = comp.findBehaviour( self.routineName )
	  if note:
	    self.title( comp.Name+'::'+note.Name )
	    self.text.config(state='normal')
            self.text.delete(1.0, 'end')
	    self.text.insert('end', note.Note)
	    pos = self.text.search('/MN', 1.0 )
	    if pos:
              self.text.mark_set('insert',pos)
              self.text.see('insert')
	    #endif
	  #endif
	#endif

	line = addStatement()
	if line:  
          self.text.mark_set('insert', 'insert lineend' )
          self.text.insert('insert','\n'+line)
          self.text.mark_set('insert', 'insert-1c' )
	  self.changed = True
	#endif

	if self.changed:
	  self._update()
	  self.changed = False
 	#endif

	if sim.IsRunning:
	  if not self.InSimMode:
	    self.updateButton.pack_forget()
	    self.deleteButton.pack_forget()
	    self.InSimMode = True
          #endif
        
	  self.text.config(state='disabled')
	  pos = self.text.search(comp.CurrentLine, 1.0 )
	  if pos:
            self.text.mark_set('insert',pos)
            self.text.see('insert')
          #endif
	elif self.InSimMode and sim.SimTime == 0.0:
          self.updateButton.pack(side='left')
          self.deleteButton.pack(side='left')
          self.InSimMode = False
	  self.text.config(state='normal')
        #endif
        '''Updates the 'current line' highlighting every "interval" milliseconds'''
        self.text.tag_remove("current_line", 1.0, "end")
        self.text.tag_add("current_line", "insert linestart", "insert lineend+1c")
        self.after(interval, self._highlight_current_line)


app = getApplication()
sim = getSimulation()
cmd = getCommand()

selstatement = app.getSelection(VC_SELECTION_RSLSTATEMENT)
selroutine = app.getSelection(VC_SELECTION_RSLROUTINE)

def routineChange( selection ):
  if selection.Count:
    comp.CurrentRoutine = selection.Objects[0].Name
  #endif

def OnStart():
  global comp, note, lseditor, currentStatement

  if selroutine.Count != 1: return

  routine = selroutine.Objects[0]
  if routine.Name == 'PositionRegister': return
  program = routine.Program
  comp = program.Component

  note =  comp.findBehaviour( routine.Name )
  if note:
    currentStatement = None
    if cmd.Name == 'FanucAddStatement':
      text = note.Note

      end = text.rindex(';')
      last = text[:end].rindex('\n')
      colon = text[last:end].index(':')
      statementCount = int(text[last+1:last+colon]) + 1
      line = addStatement( statementCount )
      if line:
        note.Note += line + '\n'
      #endif
    else:
      comp.CurrentRoutine = selroutine.Objects[0].Name
      selroutine.OnPostChange = routineChange
      lseditor = LSEditor()
      lseditor.mainloop()
      selroutine.OnPostChange = None
    #endif
  #endif

def addStatement( statementCount = 0 ):
  global currentStatement

  if selstatement.Count != 1: return None

  statement = selstatement.Objects[0]
  if statement == currentStatement: return None
  currentStatement = statement

  routine = statement.Routine

  line = "%4i:  " % statementCount 

  if statement.Type == VC_STATEMENT_CALL:
    line += "CALL %s;" % (statement.RoutineName)

  elif statement.Type == VC_STATEMENT_DELAY:
    line += "WAIT %6.2f(sec) ;" % (statement.Delay)

  elif statement.Type == VC_STATEMENT_COMMENT:
    line += "!%s;" % (statement.Comment)

  elif statement.Type == VC_STATEMENT_SETBIN:
    if statement.Output < 1000:
      line += "DO[%i: %s]=" %(statement.Output, statement.Name)
    else:
      line += "RO[%i: %s]=" %(statement.Output-1000, statement.Name)
    #endif
    if statement.Value:
      line += "ON ;"
    else:
      line += "OFF ;"
    #endif

  elif statement.Type == VC_STATEMENT_WAITBIN:
    if statement.Input < 1000:
      line += "WAIT DI[%i: %s]=" %(statement.Input, statement.Name)
    else:
      line += "WAIT RI[%i: %s]=" %(statement.Input-1000, statement.Name)
    #endif
    if statement.Value:
      line += "ON ;" 
    else:
      line += "OFF ;"
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

      sName = statement.Name
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
      #endif
    #endif

    pointIndex = statement.INDEX

    zone = 'FINE'
    if statement.Type == VC_STATEMENT_LINMOTION:
      line += "L P[%i: %s]  %gmm/sec %s ;" % (pointIndex, statement.Name, statement.MaxSpeed,zone)
    elif statement.Type == VC_STATEMENT_PTPMOTION:
      line += "J P[%i: %s]  %g%% %s ;" % (pointIndex, statement.Name, statement.JointSpeed,zone)
    #endif

  else:
    return None
  #endif

  return line

addState( None )
