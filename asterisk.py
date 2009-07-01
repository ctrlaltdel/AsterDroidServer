#!/usr/bin/env python

PING_INTERVAL = 300 # seconds
ANDROID_JID = "phone1@jabber-server.domain"

from twisted.application import service, internet
from twisted.internet import reactor, defer
from starpy import manager, fastagi, utilapplication, menu
import os, logging, pprint, time
from basicproperty import common, propertied, basic
from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish

log = logging.getLogger( 'AsterDroidServer' )
log.setLevel( logging.INFO )

class AsterDroidTracker:
  def main( self ):
    amiDF = APPLICATION.amiSpecifier.login(
    ).addCallback( self.onAMIConnect ).addErrback( self.onAMIFailure )

  def onAMIConnect( self, ami ):
    log.debug( 'onAMIConnect' )

    ami.status().addCallback( self.onStatus, ami=ami )
    ami.registerEvent( 'Newchannel', self.onChannelNew )
    ami.registerEvent( 'Hangup', self.onChannelHangup )

  def onAMIFailure( self, ami ):
    log.error( 'onAMIFailure' )

  def onStatus( self, events, ami=None ):
    """Integrate the current status into our set of channels"""

    log.debug( """Initial channel status retrieved""" )

  def onChannelNew( self, ami, event ):
    """Handle creation of a new channel"""
    log.debug( """Start on channel %s""", event )

  def onChannelHangup( self, ami, event ):
    """Handle hangup of an existing channel"""
    log.debug( """Hangup on channel %s""", event )

def AGIHandler ( agi ):
  """Give time for some time a bit in the future"""
  log.debug( 'AGIHandler' )

  def onFailed( reason ):
    log.error( "Failure: %s", reason.getTraceback())
    return None

  def cleanup( result ):
    #agi.finish()
    return result

  APPLICATION.jabber.sendMessage(ANDROID_JID, agi.variables["agi_callerid"])
  
  df = agi.wait(1)

  return df.addErrback(
    onFailed
  ).addCallback(
    cleanup
  )


APPLICATION = utilapplication.UtilApplication()

class JabberClient:
  xmlstream = None
  pingCounter = 0

  def __init__(self, myJid):
    self.myJid = myJid
    
  
  def authd(self,xmlstream):
    log.debug("authenticated")
    self.xmlstream = xmlstream
    presence = domish.Element(('jabber:client','presence'))
    xmlstream.send(presence)
    
    xmlstream.addObserver('/message',  self.messageReceived)
    xmlstream.addObserver('/presence', self.debug)
    xmlstream.addObserver('/iq',     self.debug)

    # Ping every PING_INTERVAL seconds for testing purposes
    reactor.callLater(1, self.sendPing)

  def sendPing(self):
    self.pingCounter += 1

    log.debug("Sending out ping packet %d" % self.pingCounter)

    self.sendMessage(ANDROID_JID, "ping:%f:%d" % (time.time(), self.pingCounter))
    reactor.callLater(PING_INTERVAL, self.sendPing)

  def sendMessage(self, to, body):
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

    if action and action[:5] == "pong:":
      log.debug ("Received pong packet")

      try:
        (dummy, timestamp, counter) = action.split(':')
        timestamp = float(timestamp)
        counter = int(counter)

        now = time.time()
        log.debug("Timestamp: %f, Now: %f" % (timestamp, now))

        # delta in ms
        delta = (time.time() - timestamp) * 1000
      except Exception:
        print "Invalid pong packet received"

      log.info("PONG %d %f %f %f" % (counter, delta, timestamp, now))
    
    if action == "reject":
      log.info("Received reject command")

if __name__ == "__main__":
  #logging.basicConfig(filename="/tmp/asterdroid.log",level=logging.INFO,)
  logging.basicConfig()

  log.setLevel( logging.DEBUG )
  manager.log.setLevel( logging.DEBUG )
  fastagi.log.setLevel( logging.DEBUG )

  # Manager
  #tracker = AsterDroidTracker()
  #reactor.callWhenRunning( tracker.main )

  # AGI
  f = fastagi.FastAGIFactory(AGIHandler)
  reactor.listenTCP(4574, f, 50, '127.0.0.1') # only binding on local interface

  # Jabber
  myJid = jid.JID('asterisk@jabber-server.domain/twisted_words')
  factory = client.basicClientFactory(myJid, 'gdsgefgds')

  jabber = JabberClient(myJid)
  APPLICATION.jabber = jabber

  factory.addBootstrap('//event/stream/authd',jabber.authd)
  factory.addBootstrap("//event/client/basicauth/invaliduser", jabber.debug)
  factory.addBootstrap("//event/client/basicauth/authfailed", jabber.debug)
  factory.addBootstrap("//event/stream/error", jabber.debug)

  reactor.connectTCP('jabber-server.domain',5222,factory)

  reactor.run()
