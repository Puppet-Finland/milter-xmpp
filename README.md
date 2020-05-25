# milter-xmpp

A simple Python 3 sendmail/postfix mail filter ("milter") that converts emails
to XMPP messages before they enter the MTA queue. It leverages the following
libraries:

* [pymilter](https://www.pymilter.org/)
* [pyxmpppy](http://xmpppy.sourceforge.net/)

The main use-case is converting monitoring system email alerts into XMPP
messages. This is useful because email support in monitoring systems is
universal, but XMPP support is very spotty.

This program has been tested against [ejabberd XMPP server](https://www.ejabberd.im)
but it should in theory work with any XMPP server.

# Application structure

This application is composed of three components:

* **XmppAgent**: an instance of this class is responsible for connecting to the XMPP server, becoming present, joining a chatroom and finally sending messages to the chatroom. Runs as a separate thread that picks up messages from a queue as they arrive.
* **XmppForwardMilter**: an instance of this class is created for each email that arrives to the MTA. The instance converts the email into a format more suitable for an XMPP message. If the email came from a valid sender (=has desired "From" field) then the constructed message is added to the XmppAgent's queue.
* **Main program**: the main program parser the config file and validates the settings. It then launches the XmppAgent thread and the mail filter thread with correct settings.

The mail filter component listen for MTA's requests on a TCP port (default:
8894). It could probably be made to listen on an UNIX domain socket as well,
but I ran into file owner issues with postfix so I went with TCP instead. 

# Setup

Install xmpppy and pymilter:

    $ pip3 install xmpppy pymilter

Copy [milter-xmpp.ini.sample](milter-xmpp.ini.sample) to milter-xmpp.ini and
fill in the proper values. The **\[xmpp\]** section:

* **jabberid**: the jabber ID for the XMPP agent (bot)
* **password**: the password for the agent
* **room**: the chatroom
* **server**: the server to connect to

The **\[milter\]** section:

* **iface**: the IP or name of the interface the milter will listen on. It is recommended to use a localhost address here, e.g. 127.0.0.1.
* **port**: the port to listen on for MTA connections. Defaults to 8894.
* **proto**: the protocol to use (inet, inet6). Defaults to inet.
* **valid_from**: only forward emails whose "From" field matches this exactly. Do not quote the value, even if you use something like "NMS <nms@nms.example.org>".

More details on the mail filter socket options (port, iface, proto) are available
[here](https://pythonhosted.org/pymilter/namespacemilter.html).

In production you probably want to launch this application as a (systemd)
service. The provided xmpp-milter.service is tested on Ubuntu 18.04 but it
probably works on other platforms as well.

# TODO

While this program definitely works, there is probably much space for improvement:

* Right now it is not possible to exit the program with CTRL-C. You really
need to forcibly kill it with SIGKILL.
* There is no support for (automatically) reconnecting to the XMPP server if the connection goes down for whatever reason.
* The classes could be split into separate files to make the whole a bit easier to read.
* There are probably corner-cases where this fails.

# Useful resources

The [Ansible Jabber module](https://docs.ansible.com/ansible/latest/modules/jabber_module.html)
uses pyxmpppy and is a quite useful reference. Its source code is included in
the Ansible community modules
[available from Ansible Galaxy](https://galaxy.ansible.com/community/general).

