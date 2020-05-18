#!/usr/bin/env python3
import xmpp
import time
import configparser

class MilterXmpp:
    """Convert emails into XMPP messages in a mail filter (milter)"""

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("milter_xmpp.ini")
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
    instance = MilterXmpp()
    instance.send_message("Test message from milter_xmpp.py")

if __name__ == "__main__":
    main()
