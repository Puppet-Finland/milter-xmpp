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

    def __init__(self):
        """An instance of this class is created for every email""" 
        self.id = Milter.uniqueID()
        self.fp = io.StringIO() 
        self.data = {}
        self.xmpp_message = ""

    def header(self, field, value):
        self.data[field] = value
        return Milter.CONTINUE

    def eoh(self):
        """Add a subset of headers to the XMPP message"""
        self.xmpp_message += "Date: %s\n" % (self.data['Date'])
        self.xmpp_message += "From: %s\n" % (self.data['From'])
        self.xmpp_message += "Subject: %s\n" % (self.data['Subject'])
        return Milter.CONTINUE

    def body(self, chunk):
        """Add the body of the message to the XMPP message"""
        self.xmpp_message += "\n"
        self.xmpp_message += chunk.decode('utf-8')
        return Milter.CONTINUE

    def eom(self):
        """Send the message to the XMPP server"""
        xmpp_agent.send_message(self.xmpp_message)
        return Milter.CONTINUE

class XmppAgent:
    """Send an XMPP message"""

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("milter-xmpp.ini")
        self.jabberid = config.get("xmpp", "jabberid")
        self.password = config.get("xmpp", "password")
        self.room = config.get("xmpp", "room")
        self.server = config.get("xmpp", "server")

    def send_message(self, message):
        jid = xmpp.protocol.JID(self.jabberid)

        # Connect to XMPP server
        client = xmpp.Client(server=self.server)
        client.connect()
        client.auth(user=jid.getNode(), password=self.password, resource=jid.getResource())

        # Make us "present" on the server
        client.sendInitPresence(requestRoster=0)

        # Join a chatroom
        join = xmpp.Presence(to="%s/%s" % (self.room, jid.getNode()))
        join.setTag('x', namespace='http://jabber.org/protocol/muc')
        client.send(join)

        # Construct a message
        msg = xmpp.protocol.Message(body=message)
        msg.setType('groupchat')
        msg.setTag('x', namespace='http://jabber.org/protocol/muc#user')
        msg.setTo(self.room)

        # Send a message and sleep to ensure it does not get dropped by the
        # server
        client.send(msg)
        time.sleep(3)

        # Make ourselves unavailable (=leave chatroom)
        client.sendPresence(typ='unavailable')

def main():
  sys.stdout.flush()

  # Connect to the XMPP server once. We don't want to repeat this on every
  # email.
  xmpp_agent = XmppAgent()

  # Launch the mail filter daemon. It will forward emails from pre-defined email
  # addresses as XMPP messages,
  milter_timeout = 10
  Milter.factory = XmppForwardMilter
  Milter.runmilter("xmppforwardmilter",'inet:8894',milter_timeout)

if __name__ == "__main__":
  main()
