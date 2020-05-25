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

        # FIXME: this does not make this thread die when the main program 
        # exits.
        self.daemon = True

        # XMPP settings
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
        """Take messages from the queue and send it via XMPP"""
        while True:
            message = self.queue.get()
            self.send_message(message)
            self.queue.task_done()

    def send_message(self, message):
        """Send a XMPP message"""
        msg = xmpp.protocol.Message(body=message)
        msg.setType('groupchat')
        msg.setTag('x', namespace='http://jabber.org/protocol/muc#user')
        msg.setTo(self.room)
        self.client.send(msg)

class XmppForwardMilter(Milter.Base):
    """A mail filter that converts emails into XMPP messages"""

    # The XMPP agent that is responsible for forwarding the messages
    xmpp_agent = None
    valid_from = None

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
        """Send the message to the XMPP server if it is from a valid sender"""
        if self.data['From'] == self.__class__.valid_from:
          self.__class__.xmpp_agent.queue.put(self.xmpp_message)
        return Milter.CONTINUE

def main():
    sys.stdout.flush()
  
    # Read the config file
    config = configparser.ConfigParser()
    config.read("milter-xmpp.ini")
  
    # Parse XMPP options
    try:
        xmpp_jabberid = config.get("xmpp", "jabberid")
    except:
        print("ERROR: jabberid parameter missing from xmpp section in config file!")
        sys.exit(1)
    try:
        xmpp_password = config.get("xmpp", "password")
    except:
        print("ERROR: password parameter missing from xmpp section in config file!")
        sys.exit(1)
    try:
        xmpp_room = config.get("xmpp", "room")
    except:
        print("ERROR: room parameter missing from xmpp section in config file!")
        sys.exit(1)
    try:
        xmpp_server = config.get("xmpp", "server")
    except:
        print("ERROR: server parameter missing from xmpp section in config file!")
        sys.exit(1)
  
    # Parse milter options
    try:
        milter_valid_from = config.get("milter", "valid_from")
    except configparser.NoOptionError:
        print("ERROR: valid_from parameter missing from milter section in config file!")
        sys.exit(1)
  
    try:
        milter_proto = config.get("milter", "proto")
    except configparser.NoOptionError:
        milter_proto = "inet"
  
    try:
        milter_iface = "@%s" % (config.get("milter", "iface"))
    except configparser.NoOptionError:
        milter_iface = ""
  
    try:
        milter_port = config.get("milter", "port")
    except configparser.NoOptionError:
        milter_port = 8894
  
    milter_socket = "%s:%s%s" % (milter_proto, milter_port, milter_iface)
  
    # Launch the XMPP agent thread. It will forward emails from pre-defined email
    # addresses as XMPP messages.
    xmpp_agent = XmppAgent(xmpp_jabberid, xmpp_password, xmpp_room, xmpp_server)
    xmpp_agent.setDaemon(True)
    xmpp_agent.establish_session()
    xmpp_agent.start()
  
    # Launch the mail filter. Whenever an email is received a new instance
    # XmppForwardMilter is launched. Common settings like the XMPP Agent object
    # are stored as class variables so that each instance can access them.
    milter_timeout = 10
    Milter.factory = XmppForwardMilter
    XmppForwardMilter.xmpp_agent = xmpp_agent
    XmppForwardMilter.valid_from = milter_valid_from
    Milter.runmilter("xmppforwardmilter", milter_socket, milter_timeout)
  
if __name__ == "__main__":
  main()
