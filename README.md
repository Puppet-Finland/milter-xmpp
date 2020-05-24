# milter-xmpp

A simple sendmail/postfix mail filter ("milter") that converts emails to XMPP
messages before they enter the MTA queue. It leverages the following libraries:

* [pymilter](https://www.pymilter.org/)
* [pyxmpppy](http://xmpppy.sourceforge.net/)

The main use-case is converting monitoring system email alerts into XMPP
messages. This is useful because email support in monitoring systems is
universal, but XMPP support is very spotty.

This program has been tested against [ejabberd XMPP server](https://www.ejabberd.im)
but it should in theory work with any XMPP server.

# Setup

Install pyxmpppy:

    $ pip3 install xmpppy

Copy milter-xmpp.ini.sample to milter-xmpp.ini and fill in the values.

# Testing

To test if sending XMPP messages works just do

    $ ./milter-xmpp.py

# Useful resources

The
[Ansible Jabber module](https://docs.ansible.com/ansible/latest/modules/jabber_module.html)
uses pyxmpppy and is a quite useful reference. Its source code is included in
the Ansible community modules
[available from Ansible Galaxy](https://galaxy.ansible.com/community/general).
