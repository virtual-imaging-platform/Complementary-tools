########################################################################
# $Id: FutureHandler.py 18161 2009-11-11 12:07:09Z acasajus $
########################################################################

""" FutureHandler is the implementation of a future
    service in the DISET framework

"""

__RCSID__ = "$Id: GASWServiceHandler.py 18161 2011-06-04 16:43:09Z silva $"

# Imports
from DIRAC import S_OK
from DIRAC import gLogger
from DIRAC.Core.DISET.RequestHandler import RequestHandler
from types import *
import threading
import socket

# Workflows Dictionary
workflowsDict = {}

def initializeGASWServiceHandler(serviceInfo):

    gLogger.info("================================")
    gLogger.info("= Initializing GASW Service 0.1")
    gLogger.info("================================")
    return S_OK()

class GASWServiceHandler( RequestHandler ):

    def initialize(self):
        gLogger.info("Initializing Service")

    ###########################################################################
    #types_echo = [StringType, StringType, StringType]
    def export_echo(self, workflowID, jobID, minorStatus):
        gLogger.info("WorkflowID: " + workflowID)
        if workflowID in workflowsDict:
            connection = workflowsDict[workflowID]
            try:
                gLogger.info("Received " + jobID + " - " + minorStatus)
                msg = jobID + "###" + minorStatus
                connection.send(msg + "\n")
            except:
                connection.close()
                gLogger.info("Connection lost with " + workflowID)
                del workflowsDict[workflowID]

        return S_OK("OK")

###########################################################################
def GASWListener():
    while True:
        clientsocket, address = serversocket.accept()
        data = clientsocket.recv(1024)
        data = data.rstrip(b'\n')
        workflowsDict[data] = clientsocket
        gLogger.info(b"Connection initialized with " + data) # b added

###########################################################################

# Main execution
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((socket.gethostname(), 50009))
serversocket.listen(1)
GASWL = threading.Thread(None, GASWListener)
GASWL.start()


