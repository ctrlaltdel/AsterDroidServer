#!/usr/bin/env python

PING_INTERVAL = 300 # seconds
#ANDROID_JID = "phone1@jabber-server.domain"
ANDROID_JID = "francois@jabber-server.domain"

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

  def blah(agi):
    log.debug('blah')

    jabber.sendMessage(ANDROID_JID, "incoming:%s" % agi.variables["agi_callerid"])

    result = queue.get()
    print result

    return agi.sayAlpha('ABC')

  seq = fastagi.InSequence()

  seq.append(agi.answer)
  seq.append(blah, agi)
  seq.append(agi.finish)

  return seq().addErrback(onFailed).addCallback(onSuccess)

if __name__ == "__main__":
  #logging.basicConfig(filename="/tmp/asterdroid.log",level=logging.INFO,)
  logging.basicConfig()

  log.setLevel( logging.DEBUG )
  #fastagi.log.setLevel( logging.DEBUG )

  queue = defer.DeferredQueue()

  # Jabber
  myJid = jid.JID('asterisk@jabber-server.domain/twisted_words')
  factory = client.basicClientFactory(myJid, 'gdsgefgds')

  jabber = JabberClient(myJid)

  factory.addBootstrap('//event/stream/authd',jabber.authd)
  factory.addBootstrap("//event/client/basicauth/invaliduser", jabber.debug)
  factory.addBootstrap("//event/client/basicauth/authfailed", jabber.debug)
  factory.addBootstrap("//event/stream/error", jabber.debug)

  reactor.connectTCP('jabber-server.domain',5222,factory)

  # AGI
  f = fastagi.FastAGIFactory(gotIncomingCall)
  reactor.listenTCP(4574, f, 50, '127.0.0.1') # only binding on local interface


  reactor.run()
