#!/usr/bin/env python3

## A very simple milter to prevent mixing of internal and external mail.  
# Internal is defined as using one of a list of internal top level domains.
#  This code is open-source on the same terms as Python.

import Milter
import time
import sys
import os
import io
from Milter.utils import parse_addr
from shutil import chown

class XmppForwardMilter(Milter.Base):

  def __init__(self):  # A new instance with each new connection.
    self.id = Milter.uniqueID()  # Integer incremented with each call.
    self.fp = io.StringIO() 
    self.data = {}
    self.xmpp_message = ""

  def hello(self, hostname):
      return Milter.CONTINUE
    
  def header(self, field, value):
      self.data[field] = value
      return Milter.CONTINUE

  def eoh(self):
      self.xmpp_message += "Date: %s\n" % (self.data['Date'])
      self.xmpp_message += "From: %s\n" % (self.data['From'])
      self.xmpp_message += "Subject: %s\n" % (self.data['Subject'])
      return Milter.CONTINUE

  def body(self, chunk):
      self.xmpp_message += "\n"
      self.xmpp_message += chunk.decode('utf-8')
      return Milter.CONTINUE

  def eom(self):
      """Send the message to the XMPP server"""
      print(self.xmpp_message)
      return Milter.CONTINUE

def main():

  #os.umask(0o117)
  #socket_path = "/var/spool/postfix/milter_xmpp.socket"
  #socket_owner = "postfix"
  #socket_group = "root"

  timeout = 10
  Milter.factory = XmppForwardMilter
  #print("%s milter startup" % time.strftime('%Y%b%d %H:%M:%S'))
  sys.stdout.flush()
  Milter.runmilter("xmppforwardmilter",'inet:8894',timeout)
  #chown(socket_path, 'postfix', 'root')
  #logq.put(None)
  #bt.join()


  #print("%s nomix milter shutdown" % time.strftime('%Y%b%d %H:%M:%S'))


if __name__ == "__main__":
  main()
