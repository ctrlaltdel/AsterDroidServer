#!/usr/bin/env python

PING_INTERVAL = 300 # seconds
ANDROID_JID = "phone1@jabber-server.domain"
#ANDROID_JID = "francois@jabber-server.domain"

from twisted.application import service, internet
from twisted.internet import reactor, defer
from starpy import fastagi
import os, logging, pprint, time
from basicproperty import common, propertied, basic
from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish

log = logging.getLogger( 'AsterDroidServer' )
log.setLevel( logging.INFO )

class JabberClient:
  xmlstream = None
  pingCounter = 0

  def __init__(self, myJid):
    self.myJid = myJid
    self.queue = defer.DeferredQueue()
  
  def authd(self,xmlstream):
    log.debug("authenticated")
    self.xmlstream = xmlstream
    presence = domish.Element(('jabber:client','presence'))
    xmlstream.send(presence)
    
    xmlstream.addObserver('/message',  self.messageReceived)
    xmlstream.addObserver('/presence', self.debug)
    xmlstream.addObserver('/iq',     self.debug)

    # Ping every PING_INTERVAL seconds for testing purposes
    #reactor.callLater(1, self.sendPing)

  def sendPing(self):
    self.pingCounter += 1

    log.debug("Sending out ping packet %d" % self.pingCounter)

    self.sendMessage(ANDROID_JID, "ping:%f:%d" % (time.time(), self.pingCounter))
    reactor.callLater(PING_INTERVAL, self.sendPing)

  def sendMessage(self, to, body):
    log.debug('jabber.sendMessage(%s, %s)' % (to, body))

    message = domish.Element(('jabber:client','message'))
    message['to'] = to
    message['type'] = 'chat'
    
    message.addElement('body',None,body)

    self.xmlstream.send(message)
    
  def debug(self, elem):
    print elem.toXml().encode('utf-8')
    print "="*20

  def messageReceived(self, elem):
    log.debug("Message from Android")

    action = str(elem.firstChildElement())
    queue.put(action)

def gotIncomingCall(agi):
  log.debug('gotIncomingCall')

  def onFailed(reason):
    log.error( "Failure: %s", reason.getTraceback())
    return None

  def onSuccess(result):
    log.debug("Success: %s", result)

  def handleCommand(cmd, agi):
    log.debug('handleCommand, cmd=%s', cmd)

    if cmd == 'hangup':
      return agi.hangup()

    if cmd == 'pickup_gsm':
      seq = fastagi.InSequence()
      seq.append(agi.answer)
      seq.append(agi.execute, 'Dial', '${TRUNK}/079XXXXXXX1')
      return seq()

    if cmd == 'pickup_voip':
      return defer.Deferred(agi.execute, 'Playback', 'invalid')

    # An unknown command was received
    log.error("Unknown command received: %s", cmd)

  def askAndroid(agi):
    log.debug('askAndroid')

    jabber.sendMessage(ANDROID_JID, "incoming:%s" % agi.variables["agi_callerid"])

    return queue.get().addCallback(handleCommand, agi)

  seq = fastagi.InSequence()
  seq.append(askAndroid, agi)
  seq.append(agi.finish)
  return seq().addErrback(onFailed).addCallback(onSuccess)

if __name__ == "__main__":
  # Logging
  #logging.basicConfig(filename="/tmp/asterdroid.log",level=logging.INFO,)
  logging.basicConfig()
  log.setLevel( logging.DEBUG )
  #fastagi.log.setLevel( logging.DEBUG )

  # Configuration
  import ConfigParser
  config = ConfigParser.RawConfigParser()
  config.read('server.cfg')

  queue = defer.DeferredQueue()

  # Jabber
  myJid = jid.JID('%s/AsterDroid' % config.get('jabber', 'username'))
  factory = client.basicClientFactory(myJid, config.get('jabber', 'password'))

  jabber = JabberClient(myJid)

  factory.addBootstrap('//event/stream/authd',jabber.authd)
  factory.addBootstrap("//event/client/basicauth/invaliduser", jabber.debug)
  factory.addBootstrap("//event/client/basicauth/authfailed", jabber.debug)
  factory.addBootstrap("//event/stream/error", jabber.debug)

  server = config.get('jabber', 'server')
  port   = config.getint('jabber', 'port')
  reactor.connectTCP(server, port, factory)

  # AGI
  f = fastagi.FastAGIFactory(gotIncomingCall)

  agiport = config.getint('asterisk', 'agi_port')
  reactor.listenTCP(agiport, f, 50, '0.0.0.0') # only binding on local interface

  #def _mark():
  #  print "I'm still alive and kicking"
  #  reactor.callLater(1, _mark)
  #reactor.callLater(1, _mark)

  reactor.run()
