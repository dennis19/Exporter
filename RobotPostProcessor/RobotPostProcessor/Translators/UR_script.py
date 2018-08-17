from vcCommand import *
import vcMatrix, os.path, math

def writeSetProperty(output_file,statement):
  value_expression = statement.ValueExpression.strip()
  output_file.write(indentation*depth + "%s = %s\n" % (statement.TargetProperty, value_expression))

def writePrint(output_file,statement):
  output_file.write(indentation*depth + 'textmsg("%s")\n' % statement.Message)

def writeIf(output_file,statement):
  global depth
  _condition = statement.Condition.strip()
  output_file.write(indentation*depth + "if %s:\n" % _condition)
  depth += 1
  if not statement.ThenScope.Statements:
    # not sure if UR script supports "pass" statement => test
    output_file.write(indentation*depth + "pass\n" )
  for s in statement.ThenScope.Statements:
    translator = statement_translators.get(s.Type, unknown)
    translator(output_file,s)
  depth -= 1
  output_file.write(indentation*depth + "else:\n")
  depth += 1
  if not statement.ElseScope.Statements:
    # not sure if UR script supports "pass" statement => test
    output_file.write(indentation*depth + "pass\n" )
  for s in statement.ElseScope.Statements:
    translator = statement_translators.get(s.Type, unknown)
    translator(output_file,s)
  depth -= 1
  output_file.write(indentation*depth + "end #if\n")

def writeReturn(output_file,statement):
  output_file.write(indentation*depth + "return\n")

def writeHalt(output_file,statement):
  output_file.write(indentation*depth + "halt\n")

def writeContinue(output_file,statement):
  output_file.write(indentation*depth + "continue\n")

def writeBreak(output_file,statement):
  output_file.write(indentation*depth + "break\n")

def writeWhile(output_file,statement):
  global depth
  _condition = statement.Condition.strip()
  output_file.write(indentation*depth + "while %s:\n" % _condition )
  depth += 1
  if not statement.Scope.Statements:
    # not sure if UR script supports "pass" statement => test
    output_file.write(indentation*depth + "pass\n" )
  for s in statement.Scope.Statements:
    translator = statement_translators.get(s.Type, unknown)
    translator(output_file,s)
  depth -= 1
  output_file.write(indentation*depth + "end #while\n")

def writeWaitBin(output_file, statement):
  #optionally
  # - get_euromap_input(n) # n: An integer specifying one of the available Euromap67 input signals.
  # - get_standard_digital_in(n) # n:The number (id) of the input, integer: [0:7]
  # - get_tool_digital_in(n) # n: The number (id) of the input, integer: [0:1]
  # - read_input_boolean_register(address) # address: Address of the register (0:63)
  if not statement.InputValue:
    output_file.write(indentation*depth + "while not get_configurable_digital_in(%i):\n" %(statement.InputPort))
  else:
    output_file.write(indentation*depth + "while get_configurable_digital_in(%i):\n" %(statement.InputPort))
  output_file.write(indentation*depth + "  sleep 0.05\n") #20hz polling
  output_file.write(indentation*depth + "  end\n")

def writeSetBin(output_file, statement):
  # optionally
  # - set_euromap_output(portnumber,signalvalue)
  # - set_standard_digital_out(n,b)
  # - set_tool_digital_out(n,b)
  # - write_output_boolean_register(address,value)
  output_file.write(indentation*depth + "set_configurable_digital_out(%i,%s)\n" %(statement.OutputPort,statement.OutputValue))

def writeDelay(output_file, statement):
  output_file.write(indentation*depth + "sleep(%.3f)\n" % statement.Delay)

def writeComment(output_file, statement):
  output_file.write(indentation*depth + "# %s\n" % statement.Comment)

def writeCall(output_file, statement):
  if statement.getProperty("Routine").Value:
    output_file.write(indentation*depth + "%s() #subroutine call\n" % statement.getProperty("Routine").Value.Name )

def writeLinMotion(output_file, statement):
  output_file.write(indentation*depth + "movel(")
  statement.writeToTarget(motiontarget)
  p = motiontarget.Target.P
  ori = motiontarget.Target.getAxisAngle()
  x,y,z       = p.X/1000.0, p.Y/1000.0, p.Z/1000.0
  ax, ay, az  = math.radians(ori.W)*ori.X, math.radians(ori.W)*ori.Y, math.radians(ori.W)*ori.Z
  output_file.write("p[%f, %f, %f, %f, %f, %f]" % (x,y,z, ax, ay, az) )
  output_file.write(",v=%f)\n" % (statement.MaxSpeed/1000.0))

def writePtpMotion(output_file, statement):
  output_file.write(indentation*depth + "movej([")
  for j in range(6):
    val = statement.Positions[0].JointValues[j]
    output_file.write("%f" % math.radians(val))
    if j<5:
      output_file.write(",")
  #100% joint speed equals 2pi/s joint speed.
  output_file.write("],v=%f)\n" % (statement.JointSpeed*math.pi*2) )

def writePath(output_file,statement):
  output_file.write(indentation*depth + "# <START PATH: %s>\n" % (statement.Name))
  motiontarget.JointTurnMode = VC_MOTIONTARGET_TURN_NEAREST
  motiontarget.TargetMode = VC_MOTIONTARGET_TM_NORMAL
  motiontarget.MotionType = VC_MOTIONTARGET_MT_LINEAR    
  if statement.Base == None:
    motiontarget.BaseName = ""
  else:
    motiontarget.BaseName = statement.Base.Name
  if statement.Tool == None:
    motiontarget.ToolName = ""
  else:
    motiontarget.ToolName = statement.Tool.Name
  for i in range( statement.getSchemaSize()):
    target = statement.getSchemaValue(i,"Position")
    motiontarget.Target = target
    jv = motiontarget.JointValues
    motiontarget.JointValues = jv
    motiontarget.AccuracyMethod = statement.getSchemaValue(i,"AccuracyMethod")
    motiontarget.AccuracyValue = statement.getSchemaValue(i,"AccuracyValue")
    speed = statement.getSchemaValue(i,"MaxSpeed")
    p = motiontarget.Target.P
    ori = motiontarget.Target.getAxisAngle()
    x,y,z       = p.X/1000.0, p.Y/1000.0, p.Z/1000.0
    ax, ay, az  = math.radians(ori.W)*ori.X, math.radians(ori.W)*ori.Y, math.radians(ori.W)*ori.Z
    output_file.write(indentation*depth + "movel(")
    output_file.write("p[%f, %f, %f, %f, %f, %f]" % (x,y,z, ax, ay, az) )
    output_file.write(",v=%f)\n" % (speed/1000.0))
  output_file.write(indentation*depth + "# <END PATH: %s>\n" % (statement.Name))

def unknown(output_file, statement):
  print '> Unsupported statement type skipped:', statement.Type

def translateRoutine( routine, name, output_file):
  global depth
  output_file.write("def %s():\n" % name)
  depth = 1
  pointCount = 0
  statementCount = 0
  for statement in routine.Statements:
    translator = statement_translators.get(statement.Type, unknown)
    translator(output_file,statement)
    #WriteStatement(output_file,statement)
  output_file.write("end #%s\n\n" % name)
  output_file.write("\n")


def postProcess(app,program,uri):
  global motiontarget
  head, tail = os.path.split(uri)
  mainName = tail[:len(tail)-7]
  motiontarget = program.Executor.Controller.createTarget()
  with open(uri,"w") as output_file:
    translateRoutine(program.MainRoutine, mainName, output_file)
    # subroutines
    for routine in program.Routines:
      translateRoutine(routine, routine.Name, output_file)
    output_file.write("%s()\n" % mainName)
    return True,[uri]
  return False,[uri]

indentation = '  '
statement_translators = {
VC_STATEMENT_SETPROPERTY:writeSetProperty,
VC_STATEMENT_PRINT:writePrint,
VC_STATEMENT_IF:writeIf,
VC_STATEMENT_RETURN:writeReturn,
VC_STATEMENT_HALT:writeHalt,
VC_STATEMENT_CONTINUE:writeContinue,
VC_STATEMENT_BREAK:writeBreak,
VC_STATEMENT_WHILE:writeWhile,
VC_STATEMENT_WAITBIN:writeWaitBin,
VC_STATEMENT_SETBIN:writeSetBin,
VC_STATEMENT_DELAY:writeDelay,
VC_STATEMENT_COMMENT:writeComment,
VC_STATEMENT_CALL:writeCall,
VC_STATEMENT_LINMOTION:writeLinMotion,
VC_STATEMENT_PTPMOTION:writePtpMotion,
VC_STATEMENT_PATH:writePath}

