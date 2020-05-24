#!/usr/bin/env python3

import configparser
import Milter
import io
import os
import sys
import time
import xmpp

class XmppForwardMilter(Milter.Base):
    """A mail filter that converts emails into XMPP messages"""
    
    # The XMPP agent that is responsible for sending the messages
    xmpp_agent = None

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
        self.__class__.xmpp_agent.send_message(self.xmpp_message)
        return Milter.CONTINUE

class XmppAgent():
    """Send XMPP messages"""

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("milter-xmpp.ini")
        self.jabberid = config.get("xmpp", "jabberid")
        self.password = config.get("xmpp", "password")
        self.room = config.get("xmpp", "room")
        self.server = config.get("xmpp", "server")
        self.jid = xmpp.protocol.JID(self.jabberid)
        self.user = self.jid.getNode()
        self.resource = self.jid.getResource()
        self.client = None

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

    def send_message(self, message):
        """Send a XMPP message"""
        msg = xmpp.protocol.Message(body=message)
        msg.setType('groupchat')
        msg.setTag('x', namespace='http://jabber.org/protocol/muc#user')
        msg.setTo(self.room)

        # Send a message and sleep to ensure it does not get dropped by the
        # server
        self.client.send(msg)
        time.sleep(3)

def main():
  sys.stdout.flush()

  # Connect to the XMPP server once. We don't want to repeat this on every
  # email.

  # Launch the mail filter daemon. It will forward emails from pre-defined email
  # addresses as XMPP messages,
  milter_timeout = 10
  Milter.factory = XmppForwardMilter
  xmpp_agent = XmppAgent()
  xmpp_agent.connect()
  xmpp_agent.become_present()
  xmpp_agent.join_chatroom()

  XmppForwardMilter.xmpp_agent = xmpp_agent

  Milter.runmilter("xmppforwardmilter",'inet:8894',milter_timeout)

if __name__ == "__main__":

  main()


