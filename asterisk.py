#!/usr/bin/env python

HOST     = '127.0.0.1'
PORT     = 5038
USERNAME = 'francois'
SECRET   = 'Thu6aim3'

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
    ).addCallback( self.onAMIConnect )
    # XXX do something useful on failure to login...

  def onAMIConnect( self, ami ):
    """Register for AMI events"""
    # XXX should do an initial query to populate channels...
    # XXX should handle asterisk reboots (at the moment the AMI 
    # interface will just stop generating events), not a practical
    # problem at the moment, but should have a periodic check to be sure
    # the interface is still up, and if not, should close and restart
    log.debug( 'onAMIConnect' )

    ami.status().addCallback( self.onStatus, ami=ami )
    ami.registerEvent( 'Newchannel', self.onChannelNew )
    ami.registerEvent( 'Hangup', self.onChannelHangup )

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
    agi.finish()
    return result

  #APPLICATION.jabber.sendMessage("francois@jabber-server.domain", agi.variables["agi_callerid"])
  APPLICATION.jabber.sendMessage("phone1@jabber-server.domain", agi.variables["agi_callerid"])
  
  df = agi.wait(1)

  return df.addErrback(
    onFailed
  ).addCallback(
    cleanup
  )


APPLICATION = utilapplication.UtilApplication()

class JabberClient:
    xmlstream = None

    def __init__(self, myJid):
        self.myJid = myJid
        
    
    def authd(self,xmlstream):
        print "authenticated"
        self.xmlstream = xmlstream
        presence = domish.Element(('jabber:client','presence'))
        xmlstream.send(presence)
        
        xmlstream.addObserver('/message',  self.debug)
        xmlstream.addObserver('/presence', self.debug)
        xmlstream.addObserver('/iq',       self.debug)   
        #reactor.callLater(5, self.sendMessage, 'francois@jabber-server.domain','test','test')

    def sendMessage(self, to, body):
        message = domish.Element(('jabber:client','message'))
        message['to'] = to
        message['type'] = 'chat'
        
        message.addElement('body',None,body)
        
        self.xmlstream.send(message)
        

    def debug(self, elem):
        print elem.toXml().encode('utf-8')
        print "="*20


if __name__ == "__main__":
  logging.basicConfig()
  log.setLevel( logging.DEBUG )
  manager.log.setLevel( logging.DEBUG )
  fastagi.log.setLevel( logging.DEBUG )

  # Manager
  tracker = AsterDroidTracker()
  reactor.callWhenRunning( tracker.main )

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
