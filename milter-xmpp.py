#!/usr/bin/env python3

from queue import Queue
import configparser
import Milter
import io
import os
import sys
import threading
import time
import xmpp

class XmppAgent(threading.Thread):
    """Send XMPP messages"""

    def __init__(self, jabberid, password, room, server):
        threading.Thread.__init__(self)

        self.jabberid = jabberid
        self.password = password
        self.room = room
        self.server = server
        self.jid = xmpp.protocol.JID(self.jabberid)
        self.user = self.jid.getNode()
        self.resource = self.jid.getResource()
        self.client = None
        self.queue = Queue()

    def establish_session(self):
        """Preparations required before sending messages"""
        self.connect()
        self.become_present()
        self.join_chatroom()

    def connect(self):
        """Connect to the XMPP server"""
        self.client = xmpp.Client(server=self.server)
        self.client.connect()
        self.client.auth(user=self.user, password=self.password, resource=self.resource)

    def become_present(self):
        """Make us present on the server"""
        self.client.sendInitPresence(requestRoster=0)

    def join_chatroom(self):
        """"Join a chatroom"""
        join = xmpp.Presence(to="%s/%s" % (self.room, self.user))
        join.setTag('x', namespace='http://jabber.org/protocol/muc')
        self.client.send(join)

    def leave_chatroom(self):
        # Make ourselves unavailable (=leave chatroom)
        self.client.sendPresence(type='unavailable')

    def run(self):
        while True:
            print(self.queue.get())
            self.queue.task_done()

    def send_message(self, message):
        """Send a XMPP message"""
        msg = xmpp.protocol.Message(body=message)
        msg.setType('groupchat')
        msg.setTag('x', namespace='http://jabber.org/protocol/muc#user')
        msg.setTo(self.room)

        # Send a message and sleep to ensure it does not get dropped by the
        # server
        self.client.send(msg)

class XmppForwardMilter(Milter.Base):
    """A mail filter that converts emails into XMPP messages"""

    # The XMPP agent that is responsible for forwarding the messages
    xmpp_agent = None
    valid_from = None
    port = 8894

    def __init__(self):
        """An instance of this class is created for every email""" 
        self.id = Milter.uniqueID()
        self.fp = io.StringIO() 
        self.data = {}
        self.xmpp_message = ""

    @Milter.noreply
    def header(self, field, value):
        self.data[field] = value
        return Milter.CONTINUE

    @Milter.noreply
    def eoh(self):
        """Add a subset of headers to the XMPP message"""
        self.xmpp_message += "Date: %s\n" % (self.data['Date'])
        self.xmpp_message += "From: %s\n" % (self.data['From'])
        self.xmpp_message += "Subject: %s\n" % (self.data['Subject'])
        return Milter.CONTINUE

    @Milter.noreply
    def body(self, chunk):
        """Add the body of the message to the XMPP message"""
        self.xmpp_message += "\n"
        self.xmpp_message += chunk.decode('utf-8')
        return Milter.CONTINUE

    def eom(self):
        """Send the message to the XMPP server"""
        #print(self.xmpp_message)
        self.__class__.xmpp_agent.queue.put(self.xmpp_message)
        return Milter.CONTINUE

def main():
  sys.stdout.flush()

  # Read the config file
  config = configparser.ConfigParser()
  config.read("milter-xmpp.ini")

  # Launch the XMPP agent thread. It will forward emails from pre-defined email
  # addresses as XMPP messages.
  jabberid = config.get("xmpp", "jabberid")
  password = config.get("xmpp", "password")
  room = config.get("xmpp", "room")
  server = config.get("xmpp", "server")
  xmpp_agent = XmppAgent(jabberid, password, room, server)
  xmpp_agent.establish_session()
  xmpp_agent.start()

  # Launch the mail filter. It parses incoming emails and forwards (some of)
  # them to the XMPP Agent which will forward them to an XMPP chatroom.
  milter_timeout = 10
  Milter.factory = XmppForwardMilter
  XmppForwardMilter.xmpp_agent = xmpp_agent
  XmppForwardMilter.port = config.get("milter", "port")
  XmppForwardMilter.valid_from = config.get("milter", "valid_from")
  Milter.runmilter("xmppforwardmilter",'inet:8894',milter_timeout)

if __name__ == "__main__":
  main()


