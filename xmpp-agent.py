#!/usr/bin/env python3

import configparser
import io
import os
import queue
import sys
import threading
import time
import xmpp

class XmppAgentThread(threading.Thread):
    """Listen for messages and forward them to an XMPP server"""

    def __init__(self):
        threading.Thread.__init__(self)

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

    def run(self):
        self.xmpp_connect()
        self.xmpp_become_present()
        self.xmpp_join_chatroom()
        self.xmpp_send_message("Test")
        self.xmpp_leave_chatroom()
        return

    def xmpp_connect(self):
        """Connect to the XMPP server"""
        self.client = xmpp.Client(server=self.server)
        self.client.connect()
        self.client.auth(user=self.user, password=self.password, resource=self.resource)

    def xmpp_become_present(self):
        """Make us present on the server"""
        self.client.sendInitPresence(requestRoster=0)

    def xmpp_join_chatroom(self):
        """"Join a chatroom"""
        join = xmpp.Presence(to="%s/%s" % (self.room, self.user))
        join.setTag('x', namespace='http://jabber.org/protocol/muc')
        self.client.send(join)

    def xmpp_leave_chatroom(self):
        # Make ourselves unavailable (=leave chatroom)
        self.client.sendPresence(type='unavailable')

    def xmpp_send_message(self, message):
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
  agent = XmppAgentThread()
  agent.start()


  time.sleep(30)


if __name__ == "__main__":
  main()
