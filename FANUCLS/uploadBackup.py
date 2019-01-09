from vcCommand import *
import re
import os.path
import vcMatrix
from vcApplication import *
import upload
import uploadva
import uploadsum
import glob
#from pathlib import Path

app_ = getApplication()

def cleanUp():
  setNextState(None)

#-------------------------------------------------------------------------------
def OnAbort():
  cleanUp()

#-------------------------------------------------------------------------------
def OnStop():
  cleanUp()

#-------------------------------------------------------------------------------
def getActiveProgram():
  teach = app_.TeachContext
  routine = teach.ActiveScope
  if routine:
    if routine.ParentStatement:
      routine = routine.ParentStatement.Routine

  return routine.Program

def OnStart():
  program_ = getActiveProgram()
  if not program_:
    app_.messageBox("No program selected, aborting.", "Warning", VC_MESSAGE_TYPE_WARNING, VC_MESSAGE_BUTTONS_OK)
    return
  # endif

  #read in summary.dg
  opencmd_ = app_.findCommand("dialogOpen")
  uri_ = ""
  file_filter_ = "FANUC Robot Program files (*.dg)|summary.dg"
  opencmd_.execute(uri_, True, file_filter_)
  if not opencmd_.Param_2:
    print "No file selected for uploading, aborting command"
    return
    # endif
  uri_ = opencmd_.Param_1
  filename_ = uri_[8:len(uri_)]
  file_length_=len(os.path.basename(filename_))
  try:
    infile_sum_ = open(filename_, "r")
    uploadsum.uploadsum_(program_, infile_sum_)
  except:
    print "Cannot open file \'%s\' for reading" % filename_
    return


  posreg_file_ = glob.glob(filename_[0:len(filename_) - file_length_] + "POSREG.va")
  try:
    infile_pos_reg_ = open(posreg_file_[0], "r")
    uploadva.uploadva_(program_, infile_pos_reg_)
  except:
    print "Cannot open file \'%s\' for reading" % posreg_file_
    return
    # endtry

  posnum_file_ = glob.glob(filename_[0:len(filename_) - file_length_] + "NUMREG.va")
  try:
    infile_num_reg_ = open(posnum_file_[0], "r")
    uploadva.uploadva_(program_, infile_num_reg_)
  except:
    print "Cannot open file \'%s\' for reading" % posreg_file_
    return
    # endtry

  posframe_file_ = glob.glob(filename_[0:len(filename_) - file_length_] + "SYSFRAME.va")
  try:
    infile_pos_frame_ = open(posframe_file_[0], "r")
    uploadva.uploadva_(program_, infile_pos_frame_)
  except:
    print "Cannot open file \'%s\' for reading" % posframe_file_
    return
    # endtry

  return True

#-------------------------------------------------------------------------------

addState(None)
