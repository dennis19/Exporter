from vcScript import *

#
#       RESOURCE TOOLS
#
#       Version:        1.8
#       Date:           2008/08/28
#

VERBOSE = False

def debug_print_request( c, request, msg = "" ):
  if not VERBOSE:
    return
  print "[%s:%s] at time %g " % (c.Name, msg, getSimulation().SimTime)
  print "Request \'%s\'" % request.Name
  for prop in request.Properties:
    if prop.Type == "Ref<Component>" or prop.Type == "Ref<Behaviour>":
      if prop.Value:
        print "  ",prop.Name," ",prop.Value.Name, " ",prop.Value
      else:
        print "  ",prop.Name," ",prop.Value
    else:
      print "  ",prop.Name," ",prop.Value

#
#       atomic condition testing
#
def atomCondition(test, timeout, sim = getSimulation()):
  # Timeout management
  t = sim.SimTime
  dt = timeout

  while test() == False:
    condition(test,dt)
    # if VERBOSE:
    if timeout > 0.0:
      # print "DEBUG: AtomCondition test time = %g (timeout = %g)" %(sim.SimTime - t,timeout)
      d = sim.SimTime - t
      if d >= dt:
        return False
      else:
        dt -= d
        if abs(dt) < 0.0000001:
          return False
        t = sim.SimTime

  return True


#
#       Test with optional timeout if resource task is completed
#
def atomResourceCondition(res, actions, timeout, sim = getSimulation()):
  # Timeout management
  t = sim.SimTime + timeout
  dt = timeout

  # check if specified request is already in the pending list (replied)
  if actions.PendingActionCount > 0:
    for act in actions.PendingActions:
      if act.Sender == res and (act.Message == "Completed" or act.Message == "Aborted"):
        # print "DEBUG: atomResourceCondition resource = %s ready (%g)" % (res.Component.Name, sim.SimTime)
        return act

  # Wait next event to find out if it is specific resource event
  while True:
    triggerCondition(lambda: actions.PendingActionCount > 0, dt)
    for act in actions.PendingActions:
      if act.Sender == res and (act.Message == "Completed" or act.Message == "Aborted"):
        # print "DEBUG: atomResourceCondition resource = %s ready (%g)" % (res.Component.Name, sim.SimTime)
        return act
    
    if timeout > 0.0:
      if t <= sim.SimTime:
        return None
      dt = t - sim.SimTime

  return None


#
#       __resource_reserve__
#
#       customizatible by defining "OnResourceReserve" function with same arguments
#
#       Defines how resource is used for user specified action.
#       Action execution status is indicated with action messages using following
#       sequence:
#
#

def __resource_reserve__( request, resources, timeout):
  comp = resources.Component
  sim = getSimulation()
  debug_print_request(comp, request,"__resource_reserve__ called with properties")
  work_type = request.Name

  # Look first if any direct resource provider is available and reserve first
  # and return it to the caller
  # print "[%s] Find resource capable for action \'%s\'  at %g "% (comp.Name, request.Name, sim.SimTime)
  timeout_property = request.getProperty("Timeout")
  if timeout_property:
    timeout = timeout_property.Value
    # print "Timeout defined = ",timeout
  filter = request.Filter
  # print "Reserve filter \'%s\'" % filter
  res_list = resources.Providers
  for res in res_list:
    # print "Filter = \'%s\' Component = \'%s\' (%i)" % (filter,res.Component.Name,filter != "" and res.Component.Name.find(filter) != 0)
    if filter != "" and res.Component.Name.find(filter) != 0:
      continue
    # Reserve for no specific action
    if request.Name == "":
      if not res.Reserved:
        res.Reserved = resources
        # print "__resource_reserve__ (provider) STATION = %s, WORKER = %s" % (resources.Component.Name, res.Component.Name)
        return res
    # Reserve resource for a specific action (capability)
    for act in res.Actions:
      if act.Name == request.Name and not res.Reserved:
        res.Reserved = resources
        # print "__resource_reserve__ (provider) STATION = %s, WORKER = %s" % (resources.Component.Name, res.Component.Name)
        return res

  # If no direct resource provider is available, look thru direct brokers their availability
  worker = None
  res_list = resources.Brokers
  for res in res_list:
    # If broker has no available resources right now skip it
    if res.Processing:
      continue
    # Query resource with message from broker
    request.From = resources
    request.Sender = resources
    request.sendMessage( "Query", res )
    atomCondition(lambda: request.Sender == res and request.Message != "Query", 0.0, sim)
    reply = resources.popPending()
    if request.Message == "True":
      worker = request.To
      worker.Reserved = resources
      break

  #Send work request ("From" indicates original sender and "Sender" any sender in the way)
  request.From = resources
  request.Sender = resources
  if worker:
    # Available resource was found, return it to caller
    resources.deletePendingAction(request)
    # print "__resource_reserve__ (query) STATION = %s, WORKER = %s" % (resources.Component.Name, worker.Component.Name)
    return worker
  else:
    # No resources available at this time, backorder resource by sending request to all direct
    # providers and brokers (broadcast) and wait until any of them responds (or timeout expires).
    # print "[%s] No resource capable for action Begin \'%s\'  at %g (Backorder)"% (comp.Name, request.Name, sim.SimTime)
    request.Name = work_type
    request.sendMessage("BackorderReserve")
    if not atomCondition(lambda: request.Message != "BackorderReserve", timeout, sim):
      # print "Reserve timeout expired"
      resources.deletePendingAction(request)
      return None
    if request.Message == "BackorderReserve":
      # print "ERROR[%s] 1 at __resource_reserve__ for \"%s\"" % (comp.Name, request.From.Component.Name)
      resources.deletePendingAction(request)
      return None

    # print "[%s] No resource capable for action End \'%s\'  at %g (Backorder)"% (comp.Name, request.Name, sim.SimTime)

  # Wait replies using timeout if requested
  started = False
  while True:

    # Wait messages about resource usage status
    atomCondition(lambda: resources.PendingActionCount>0, timeout, sim)
    # print "DEBUG ",resources.PendingActionCount
    # If timeout exprired, return with error if no resource has started work
    if resources.PendingActionCount == 0: # Timeout
      if not started:
        # print "ERROR[%s] 2 at __resource_reserve__ for \"%s\"" % (comp.Name, request.From.Component.Name)
        return None

    # Process resource action status notifications
    reply = resources.popPending()
    if not reply:
      # print "[%s] Error: request was deleted before completing task at time %g" % (comp.Name, sim.SimTime)
      continue
    # print "[%s] Reply \'%s\'  = \'%s\' Sender \'%s\' at %g "% (comp.Name, reply.Name, reply.Message, reply.Sender.Component.Name, sim.SimTime)
    if reply.Message == "True":
      # Reserved resource is available
      worker = reply.To
      worker.Reserved = resources
      resources.deletePendingAction(reply)
      # print "__resource_reserve__ (backorder) STATION = %s, WORKER = %s" % (resources.Component.Name, worker.Component.Name)
      return worker
    else:
      # Reserved resource is not available, continue waiting
      # print "ERROR[%s] 3 at __resource_reserve__ for \"%s\"" % (comp.Name, request.From.Component.Name)
      continue
      resources.deletePendingAction(reply)
      return None

  return None


#
#       __resource_release__
#
#       customizatible by defining "OnResourceRelease" function with same arguments
#
#       Defines how resource is released (if reserved)
#

def __resource_release__( request, resource ):
  debug_print_request(resource.Reserved.Component, request,"__resource_release__ called with properties")
  resource.Reserved = resource
  Broker = None
  if len(resource.Clients)> 0:
    Broker = resource.Clients[0]
  elif len(resource.Brokers)> 0:
    Broker = resource.Brokers[0]

  # print "[%s] Release broker = %s" % (resource.Component.Name, Broker.Component.Name)

  resource.removePendingAction(request)
  request.From = None
  request.To = resource
  request.sendMessage( "Completed", Broker )

#
#       __resource_do__
#
#       customizatible by defining "OnResourceDo" function with same arguments
#
#       Defines how resource action is executed when dealing with resource directly
#

def __resource_do__( request, resources, timeout):
  # print "__resource_do__ RES = %s RESERVED = %s" % (resources.Component.Name, resources.Reserved.Component.Name)
  this = resources.Reserved
  resources.removePendingAction(request)
  request.From = this
  request.To = resources
  resources.Processing = True
  request.sendMessage( "Use", resources )
  comp = resources.Component
  sim = getSimulation()
  debug_print_request(comp, request,"__resource_do__ called with properties")

  # Wait replies using timeout if requested
  started = False
  while True:

    # Wait messages about resource usage status
    atomCondition(lambda: this.PendingActionCount>0, 0.0, sim)

    # If timeout exprired, return with error if no resource has started work
    if this.PendingActionCount == 0: # Timeout
      if not started:
        this.deletePendingAction(request)
        return False

    # Process resource action status notifications
    reply = this.popPending()
    if not reply:
      print "[%s] Error: request was deleted before completing task at time %g" % (comp.Name, sim.SimTime)
      continue
    # print "[%s] Reply \'%s\'  = \'%s\' Sender \'%s\' at %g "% (comp.Name, reply.Name, reply.Message, reply.Sender.Component.Name, sim.SimTime)
    if reply.Message == "Started":
      started = True
    if reply.Message == "Completed":
      this.deletePendingAction(reply)
      return True
    if reply.Message == "Aborted":
      this.deletePendingAction(reply)
      return False

  return False


#
#       __resource_start__
#
#       customizatible by defining "OnResourceStart" function with same arguments
#
#       Defines how resource action is started asyncronously when dealing with resource directly
#

def __resource_start__( request, resources ):
  this = resources.Reserved
  resources.removePendingAction(request)
  request.From = this
  request.To = resources
  resources.Processing = True
  request.sendMessage( "Use", resources )
  comp = resources.Component
  sim = getSimulation()
  debug_print_request(comp, request,"__resource_start__ called with properties")
  return request


#
#       __resource_wait__
#
#       customizatible by defining "OnResourceWait" function with same arguments
#
#       Waits until resource action is completed when dealing with resource directly
#       This works only when used together with __resource_start__
#

def __resource_wait__( resources, timeout):

  # Check if resource is already completed its processing
  if resources.Processing == False:
    # Cleanup possible work request
    if resources.Reserved:
      this = resources.Reserved
      for act in this.PendingActions:
        if act.Sender == resources:
          this.deletePendingAction(act)
          break
    return True

  this = resources.Reserved
  comp = resources.Component
  sim = getSimulation()

  # Wait replies using timeout if requested
  while True:

    # Wait request message
    reply = atomResourceCondition(resources, this, timeout, sim)

    # Timeout has occured
    if not reply:
      return False

    if reply.Message == "Completed":
      this.deletePendingAction(reply)
      return True
    if reply.Message == "Aborted":
      this.deletePendingAction(reply)
      return False

  return False


#
#       __resource_use__
#
#       customizatible by defining "OnResourceUse" function with same arguments
#
#       Defines how resource is used for user specified action.
#       Communication between resource client, providers and brokers uses following
#       sequence. Logic looks first available direct providers and next available brokers
#       and if there are no available resources, then all direct providers and brokers
#       will be sent "backorder". When first available resource starts operating with
#       backorder it will be automatically removed from other resources.
#
#       a) Simple case where PROVIDER is directly available
#
#       CLIENT                          PROVIDER                BROKER
#       Query directly ---------------> True
#       Use            --------------->
#                      <-------------- Started
#                      <-------------- Completed
#
#       b) Simple case where PROVIDER is reserved
#
#       CLIENT                          PROVIDER                BROKER
#       Query directly ---------------> False
#       Backorder      --------------->
#                      <--------------- Started
#                      <-------------- Completed
#
#       c) Case where PROVIDER is used via BROKER
#
#       CLIENT                          PROVIDER                BROKER
#       Query          --------------------------------------->
#                      <--------------------------------------- True
#       Use            --------------------------------------->
#                                                 <------------ Use
#                      <--------------- Started
#                                       Completed ------------>
#                      <--------------------------------------- Completed
#
#       d) Case where PROVIDER is used via BROKER (backorder)
#
#       CLIENT                          PROVIDER                BROKER
#       Query          --------------------------------------->
#                      <--------------------------------------- False
#       Backorder      --------------------------------------->
#                                                 <------------ Backorder
#                      <--------------- Started
#                                       Completed ------------>
#                      <--------------------------------------- Completed
#

def __resource_use__( request, resources, timeout):
  comp = resources.Component
  sim = getSimulation()
  debug_print_request(comp, request,"__resource_use__ called with properties")

  timeout_property = request.getProperty("Timeout")
  if timeout_property:
    timeout = timeout_property.Value
    # print "Timeout defined = ",timeout

  # Look first if any direct resource provider is available
  # print "[%s] Find resource capable for action \'%s\'  at %g "% (comp.Name, request.Name, sim.SimTime)
  worker = None
  filter = request.Filter
  res_list = resources.Providers
  for res in res_list:
    # print "Filter = \'%s\' Component = \'%s\' (%i)" % (filter,res.Component.Name,filter != "" and res.Component.Name.find(filter) != 0)
    if filter != "" and res.Component.Name.find(filter) != 0:
      continue
    for act in res.Actions:
      if act.Name == request.Name and not res.Reserved:
        # print "[%s] Capable resource \'%s\' found at %g" % (comp.Name, res.Component.Name, sim.SimTime)
        worker = res
        break
    if worker:
      break

  # If no direct resource provider is available, look thru direct brokers their availability
  if not worker:
    res_list = resources.Brokers
    for res in res_list:
      if res.Processing:
        continue
      request.From = resources
      request.Sender = resources
      # print "[%s] Request send to broker \'%s\' at %g" % (comp.Name, res.Component.Name, sim.SimTime)
      request.sendMessage( "Query", res )
      atomCondition(lambda: request.Sender == res and request.Message != "Query", 0.0, sim)
      reply = resources.popPending()
      if request.Message == "True":
        worker = request.To
        break

  # Send work request ("From" indicates original sender and "Sender" any sender in the way)
  request.From = resources
  request.Sender = resources
  if worker:
    # Available resource was found, send work request to it
    request.sendMessage("Use",worker)
  else:
    # No resource available, send backorder to all first level providers and brokers
    # print "[%s] No resource capable for action \'%s\'  at %g (Backorder)"% (comp.Name, request.Name, sim.SimTime)
    request.sendMessage("Backorder")
    if not atomCondition(lambda: request.Message != "Backorder", timeout, sim):
      # print "Use timeout expired"
      return False

    if request.Message == "Backorder":
      return False

  # Wait replies using timeout if requested
  started = False
  while True:

    # Wait messages about resource usage status
    atomCondition(lambda: resources.PendingActionCount>0, 0.0, sim)

    # If timeout exprired, return with error if no resource has started work
    if resources.PendingActionCount == 0: # Timeout
      if not started:
        resources.deletePendingAction(request)
        return False

    # Process resource action status notifications
    reply = resources.popPending()
    if not reply:
      print "[%s] Error: request was deleted before completing task at time %g" % (comp.Name, sim.SimTime)
      continue
    # print "[%s] Reply \'%s\'  = \'%s\' Sender \'%s\' at %g "% (comp.Name, reply.Name, reply.Message, reply.Sender.Component.Name, sim.SimTime)
    if reply.Message == "Started":
      started = True
    if reply.Message == "Completed":
      resources.deletePendingAction(reply)
      return True
    if reply.Message == "Aborted":
      resources.deletePendingAction(reply)
      return False

  return False


#
#       vcActionHandler
#
#       Resource action handler, which manages
#

class vcActionHandler:
  "Helpper class for cleaner definition of VC resource actions"
  def __init__(self,cont):
    "Initialize vcActionHandler"
    cont.clearPending()
    cont.Reserved = None
    cont.Processing = False
    cont.clear()
    self.ActionContainer=cont
    self.CmdHash = {}

  def addAction(self,actionName,function):
    self.CmdHash[actionName]=function
    self.ActionContainer.createAction(actionName)

  def waitAndDoActions(self):
    act=self.ActionContainer
    condition(lambda: act.PendingActionCount>0)
    act.Processing = True
    request = act.popPending()
    if not request:
      raise Exception('vcActionHandler had no request')
    Broker = None
    if len(act.Clients)> 0:
      Broker = act.Clients[0]
    elif len(act.Brokers)> 0:
      Broker = act.Brokers[0]
    try:
      cmd=self.CmdHash[request.Name]
    except:
      raise Exception( 'vcActionHandler does not have a member '+request.Name)
    request.Sender = act 
    request.sendMessage("Started", request.From)
    ret=cmd(request)   
    if ret==True:
      request.sendMessage("Completed", Broker)
    else:
      request.sendMessage("Aborted", Broker)
    act.Processing = False
    return ret
    
    
def UnloadHelper( to_container,to_position, part):
    "Unloads to  first ter, next term world or just world"
    if to_container:
      to_container.grab(part)
    else:
      sim=getSimulation()
      if to_position:
        part.PositionMatrix = to_position
        sim.World.attach(part, False)
      else:
        part.update()
        pos = part.WorldPositionMatrix
        sim.World.attach(part, False)
        part.PositionMatrix = pos
