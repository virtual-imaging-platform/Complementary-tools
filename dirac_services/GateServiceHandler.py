########################################################################
# $Id: GateServiceHandler.py 18161 2009-11-11 12:07:09Z acasajus $
########################################################################

""" GateServiceHandler is the implementation of a future
    service in the DISET framework

"""

__RCSID__ = "$Id: GateServiceHandler.py 18161 2009-11-11 12:07:09Z acasajus $"

from types import *
from DIRAC.Core.DISET.RequestHandler import RequestHandler
from DIRAC import gLogger, S_OK, S_ERROR

particules = 0
response = 'contiune'
import os

import socket
import sys
import threading
import time

h_socket = {}
h_checksim = {}

######################################################


def initializeGateServiceHandler( serviceInfo ):

  gLogger.info("Initializing Gate Service v0.1.1")
  print particules  
  return S_OK()

class GateServiceHandler( RequestHandler ):

  types_echo = [StringType]
  def export_echo(self,input):
    """ Echo input to output
    """
    msg = input
    msg = eval(msg)
    id_wf = msg[0]
    print 'message recu du job', msg
    if msg[1]=='check':
		if id_wf in h_socket:
			find = h_checksim[id_wf]
			if find =='true':
			   input= 'stop'
			else:
				   input= 'continue'
		else:
			input='stop'
    elif (msg[1]=='finalmsg') and (id_wf in h_socket):
		finalmsg = msg[1]+","+msg[2]+","+str(msg[3])
		print 'final message-------',finalmsg
		envoi(id_wf,finalmsg)
    else:
      msgtomoteur = msg[1:3]
      print 'sending msg to workflow: ',msgtomoteur
      msgtomoteur = msgtomoteur[0]+","+str(msgtomoteur[1])
      envoi(id_wf,msgtomoteur)    	
    return S_OK(input) 

	
###########**** sending to Workflows from Htable************#################
def getWflStatus(idW):
        cmd = "moteur_client-status https://data-manager.grid.creatis.insa-lyon.fr/cgi-bin/m2Server-prod/moteur_server  status " + idW + " 2> /dev/null"
        try:
                 wfl_status=os.popen( cmd ).read()
                 #wfl_status=open("wfl_status.txt","rb").read()
		 #print cmd
		 #print wfl_status
        except ValueError:
                wfl_status = "except"
        running_status='RUNNING'
        if wfl_status.strip().lower() != running_status.lower():
                print ("WFL " + idW + " is NOT running")
                return 6
        return 0

		
##############** listenning to new Workflow****##########
def GateListenner():
  while 1:
	#s.listen(1)
	conn, addr = s.accept()
	print 'Connected by', addr, conn
	data = conn.recv(1024)
	data= data.rstrip('\n')
	print 'data=', repr(data)
	if data.upper() =='STOP':
		idwf=conn.recv(1024)	
		idwf = idwf.rstrip('\n')
		print 'Workflow ',idwf,' demande stop de la simulation'
		h_checksim[idwf]='true'
	elif data.upper() =='ENDCONNEXION':
		idwf=conn.recv(1024)
		idwf=idwf.rstrip('\n')
		print 'Closing connexion with ',idwf
		try:
			del h_socket[idwf]
			del h_checksim[idwf]
		except:
			print ("Warning: cannot delete socket or checksim for wfl " + idwf)
	else:		
		h_checksim[data]='false'
		h_socket[data]=conn	
		conn.send("connexion established\n")
		print 'Connexion avec ',data
	print h_socket
	print h_checksim
	#for idW in h_socket.keys():
		#if getWflStatus(idW) != 0:
			#print ("WFL " + idW + " is NOT running")
			#del h_socket[idW]
			#del h_checksim[idW]
		#else:
			#print ("WFL " + idW + " is running")
			



def envoi(idW,msg):
	print 'sending to client: ', msg
	print h_socket
	if idW in h_socket:
		connexion=h_socket[idW]
		try:
			connexion.send(msg+"\n")
		except:
			print ' connexion lost with ',idW
			del h_socket[idW]
			del h_checksim[idW]
			if getWflStatus(idW) != 0:
				print ("WFL " + idW + " is NOT running")
            		else:
				print ("Warning: connection lost, but WFL " + idW + " still running")


HOST = ''
PORT= 50008
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
GateL= threading.Thread(None, GateListenner, None, )
GateL.start()
gLogger.info("Lancemenent du service Gate")








