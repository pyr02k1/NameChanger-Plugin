#
# Namechanger Detector Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 at ZeroAlpha - www.ZeroAlpha.us
# Coded/Modified by NRP|pyr0 for ZeroAlpha
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#  NOTES:
#  This plugin was brought together out of an annoyance that Namechanger scripts
#  cause on {zA} servers. Usually accompanied by a hack. This plugin is very heavily
#  based on the Aimbot Detector by Freelander as well as the Ascii and Color name
#  plugins. A small bit was learned from the PowerAdminURT plugin as well.
#  This plugin wouldn't of happened if not for their plugins (I'm not a python 
#  programmer) THIS PLUGIN WAS WRITTEN WITH Call Of Duty 4 IN MIND. IT MAY OR MAY
#  NOT WORK ON OTHER GAMES. Feel free to test it and let me know... I'll make a list
#  of supported games if I get a report of it working on other games.
#
# CHANGELOG
#
# 12-18-2011 - 0.1 - NRP|pyr0
#   * Initial programming started. Using Freelanders code as a base.
# 12-19-2011 - 0.2 - NRP|pyr0
#   * Using a simpler design versus original plan. Code from scratch.
# 12-20-2011 - 0.3 - NRP|pyr0 
#   * Modified a few lines to make it function
# 12-22-2011 - 0.4 - NRP|pyr0
#   * Added in Ignore Feature
# 12-23-2011 - 0.5 - NRP|pyr0
#   * Fixed IgnoreFeature, added reset on death option.
# 12-23-2011 - 0.6 - NRP|pyr0
#   * Added Notify feature, it didnt work.
# 12-24-2011 - 0.7 - NRP|pyr0
#   * Fixed Notify feature, changed kick/ban method a bit. Kick/ban was busted.
# 12-25-2011 - 0.8 - NRP|pyr0
#   * Fixed Kick/Ban again and fixed logging. 
# 12-26-2011 - 0.9 - NRP|pyr0
#   * Modified some lines, fixed some bugs
# 12-31-2011 - 0.91 - NRP|pyr0
#	* Added a few extra bits to try and get in line with B3 standards
#	  Should work, but needs testing. Still yet to test Perm Ban though.
# 
# 02-08-2012 - 0.99 - NRP|pyr0
#   * All SHOULD be functional. Unable to test tonight.
# 02-19-2012 - 1.0.0 - NRP|pyr0
#   * I've run this live on {zA} NY Dom for a week and some change now with no issue.
# 02-23-2012 - 1.0.1 - NRP|pyr0
#   * Coding added to limit log code and to allow disabling of it. Untested. 1.02 will
#     be the tested code. 1.01 is a dev revision to allow me to make sure it is updated
#     on github prior to testing and release
# 
#
#  ADDITIONAL NOTES:
#  Due to limitations in the CoD4 logging, name changers can only be spotted when
#  performing an action. This script will specifically look for kills, as that is
#  generally the most common reason to namechange. This script will be posted with
#  the php script used to locate namechangers on {zA} servers in hopes of helping
#  other server admins with their issue. The PHP script is very very rough, but it
#  functions as it should. This one will be complete for auto banning cheaters 
#  that use namechangers
#
#  Upcoming:
#  Ability to pick and choose what goes into messages. As is, it requires 2 variables
# (%s twice, once for name and one for GUID). I plan to make it so it can be set by
#  the user. (e.g. place one variable set for the calls wanted [GUID, ID, SLOT, NAME]
#  and then the %s can relate to those calls) I have no clue when I get around to this.
#
#  Numbering Scheme:
#  Until v1.0 it was on each feature added or fixed. After 1.0, it will be minor 
#  revision numbers for bugfixes (e.g. x.x.2). Minor will be related to minor features
#  being added (the current upcoming list is an example. These will be x.2.x). Major
#  will be limited to major features being added in (v2.x.x ... I honestly never
#  expect to reach this level. Not much can be added/improved.
#
#
## @file
#  This plugin checks for clients changing names to avoid admins. 

__author__  = 'NRP|pyr0'
__version__ = '1.0.1'

import b3
import b3.events
import b3.plugin
import time
import thread
import threading
import sys
import re
import os
import smtplib

class NamechangersPlugin(b3.plugin.Plugin):

    _reClean = re.compile(r'(\^.)|[\x00-\x20]|[\x7E-\xff]', re.I)
    
    
    def onStartup(self):
                # Get the admin plugin so we can register commands
        # ** This is for future updates
        self._adminPlugin = self.console.getPlugin('admin')
 
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return

        # Register events on client's connection
        self.verbose('Registering events')
        self.registerEvent(b3.events.EVT_CLIENT_KILL)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        
        
    def onLoadConfig(self):
        self.verbose('Loading Config File')
        
        try:
            self.logLevel = self.config.get('settings', 'LogLevel')
        except:
            self.logLevel = 'limited'
            self.callLog('debug', 'No Config Value Set. Defaulting to limited logging.')
        
        if (self.logLevel == 'all' || self.logLevel == 'limited' || self.logLevel == 'minimal')
            try:
                self.logLocation = self.config.get('settings', 'LogLocation')
                self.callLog('debug', ('LogLocation is set to %s' % self.logLocation))
            except:
                self.logLocation = 0
                self.callLog('debug', 'No Config Value Set. Logging to File Disabled.')
        
        try:
            self.namesMax = self.config.get('settings', 'NamesMax')
        except:
            self.namesMax = 10
            self.callLog('debug', 'No Config Value Set. Using Default Max Names of 10.')
        
        try:
            self.announceKick = self.config.get('messages', 'AnnounceKick')
        except:
            self.announceKick = "Kicking user %s for Too Many Namechanges (GUID: %s)"
            self.callLog('debug', 'No Config Value Set for AnnounceKick. Defaulting')
            
        try:
            self.announceTemp = self.config.get('messages', 'AnnounceTemp')
        except:
            self.announceTemp = "TempBan user %s for Too Many Namechanges (GUID: %s)"
            self.callLog('debug', 'No Config Value Set for AnnounceTemp. Defaulting')
           
        try:
            self.announceBan = self.config.get('messages', 'AnnounceBan')
        except:
            self.announceBan = "PermBan user %s for Too Many Namechanges (GUID: %s)"
            self.callLog('debug', 'No Config Value Set for AnnounceBan. Defaulting')
            
        try:
            self.resetOnDeath = self.config.get('settings', 'ResetOnDeath')
        except:
            self.resetOnDeath = 'off'
            self.callLog('debug', 'No Config Value Set. Will Not Reset Counters On Death')
            
        try:
            self.action = self.config.get('settings', 'Action')
        except:
            self.action = 1
            self.callLog('debug', 'No Config Value Set. Using Kick As Default Action') 
            
        if (self.action == 2):
            try:
                self.duration = self.config.get('settings', 'Duration')
            except:
                self.duration = '2h'
                self.callLog('debug', 'No Config Value set for TempBan, using 2 hours')
                
        self.roundCurrent = 1

        try:
            self.ignore = self.config.get('settings', 'Ignore')
        except:
            self.ignore = 'off'
            self.callLog('debug', 'No Config Value Set. Not Ignoring Any User Level')
            
        try:
            self.ignoreLevel = self.config.get('settings', 'IgnoreLevel')
        except:
            self.ignoreLevel = 0
            self.ignore = 'off'
            self.callLog('debug', 'No Config Value Set for Ignore Level. Setting to 0')
            
        try:
            self.notify = self.config.get('settings', 'Notify')
        except:
            self.notify = 'off'
            self.callLog('debug', 'No Config Value Set. Not Notifying any admins.')
        try:
            self.notifyLevel = self.config.get('settings', 'NotifyLevel')
        except:
            self.notifyLevel = 0
            self.notify = 'off'
            self.callLog('debug', 'No Config Value Set for Notify Level. Setting to 0')            
            
            
    def onEvent(self, event):
        if (event.type == b3.events.EVT_CLIENT_KILL):
            ## Set Client and Target vars
            client = event.client
            target = event.target
            
            ## Check if client (killer) has any previous name changes set up
            if not client.isvar(self, 'namechanges'):
                client.setvar(self, 'namechanges', 0)
                client.setvar(self, 'savedname', self.clean(event.client.exactName))
                client.setvar(self, 'roundCurrent', self.roundCurrent)
                self.callLog('debug', ('roundCurrent, namechanges and savedname being set for user %s' % event.client.exactName))
            ## Save current, cleaned name and saved round number off client (killer)
            name = self.clean(event.client.exactName)
            savedRound = client.var(self, 'roundCurrent').value
            if (savedRound == None):
                savedRound = self.roundCurrent
                client.setvar(self, 'roundCurrent', savedRound)
                self.callLog('debug', ('savedRound being set to %s for user %s' % (self.roundCurrent, event.client.exactName)))
            ## Check if current round matches saved round number. if not, update user
            if (int(savedRound) != int(self.roundCurrent)):
                client.setvar(self, 'namechanges', 0)
                client.setvar(self, 'roundCurrent', self.roundCurrent)
                self.callLog('debug', 'Round Numbers dont match to saved data. Updating user. Resetting Count')
            ## Check if names match
            if (name != client.var(self, 'savedname').value):
                n = client.var(self, 'namechanges').value + 1
                client.setvar(self, 'namechanges', n)
                
                prevname = client.var(self, 'savedname').value
                client.setvar(self, 'savedname', name)
                logData = '%s changed name %s times. His name was %s. Max is %s (GUID: %s) @%s' % (name, n, prevname, self.namesMax, client.guid, client.id)
                self.callLog('limited', logData)
                if self.notify == 'on':
                    clientdata = self.console.clients.getList()
                    self.callLog('debug', 'In Notify call. Notifying admins.')
                    for player in clientdata:
                        if int(player.maxLevel) >= int(self.notifyLevel):
                            logData = 'Admin: %s - Admin Level: %s - Admin ID: %s' % (player.exactName, player.maxLevel, player.cid)
                            self.callLog('debug', logData)
                            player.message('User %s has changed their name %s times (Prev: %s) Slot %s (@%s)' % (client.exactName, n, prevname, client.cid, client.id))
                                                 
                ## Check user level versus ignore level.
                if self.ignore == 'on':
                    self.callLog('debug', 'Ignore Enabled. Checking Data')
                    if (client.maxLevel < self.ignoreLevel):
                        self.runAction(client, n, name)
                        self.callLog('debug', 'User level below ignoreLevel. Continuing to action')
                    else:
                        logData = ('User %s ignored via Ignore enabled. Level: %s - MaxLevel: %s' % (name, client.maxLevel, self.ignoreLevel))
                        self.callLog('limited', logData)                
                else:
                    ## Check if greater then max allowed name changes.
                    self.runAction(client, n, name)
                    self.callLog('debug', 'Ignore Disabled. Continuing to action')
                    
            ## Reset on Death or no?            
            if self.resetOnDeath == 'on':
                target.setvar(self, 'namechanges', 0)
                logData = 'Resetting count for user %s as per config' % (event.target.exactName)
                self.callLog('debug', logData)
        
        ## New Round, increase round number
        elif (event.type == b3.events.EVT_GAME_ROUND_START):
            self.roundCurrent = self.roundCurrent + 1  
            self.callLog('debug' 'New Round Started. Incrementing Round Number.')
                
    ## Logging Feature... looks convoluted... hence the comments, self.writeLog checks for the physical logging     
    def callLog(self, logType, data):
        if self.logLevel == "all":
            self.debug(data)
            self.writeLog(data)
            ## Scenario: ALL. Write to both.
        elif self.logLevel == "debug":
            self.debug(data)
            ## Marked as Debug. Write ONLY to b3 log
        elif self.logLevel == "limited":
            if logType == "limited":
                self.writeLog(data)
                ## Under limited logging. Write all data to the physical log, b3 below
            elif logType == "minimal":
                self.debug(data)
                ## Still under limited. Log only kicks/bans to b3 log.
        elif self.logLevel == "minimal":
            if logType == "minimal":
                self.debug(data)
                self.writeLog(data)
                ## Minimal Logging only. Write to both.
            
    ## Write to physical log file.
    def writeLog(self, data):
        if self.logLocation != 0:
            filelog = ('%s' % self.logLocation)
            f = open(filelog, "a")
            f.write(data + '\n')
            f.close()
            ## if loglocation isnt 0, then get location, open, write and close, in that order.
    
    
    def runAction(self, client, n, name):
        if int(self.namesMax) <= int(n):
            logData = ('In runAction Action: %s - User: %s - n: %s %s' % (self.action, name, int(n), int(self.namesMax)))
            self.callLog('debug', logData)
            ## check action to take... 
            if int(self.action) == 1:
                logData = (self.announceKick % (name, client.guid))
                self.callLog('minimal', logData)
                client.kick(reason=logData, keyword="NameChanger", data="%s Namechanges" % n)
            elif int(self.action) == 2:
                logData = (self.announceTemp % (name, client.guid))
                self.callLog('minimal', logData)
                duration = '12h'
                client.tempban(reason=logData, keyword="NameChanger", duration=duration, data="%s Namechanges" % n)
            elif int(self.action) == 3:
                logData = (self.announceBan % (name, client.guid))
                self.callLog('minimal', logData)
                client.ban(reason=logData, keyword="NameChanger", data="%s Namechanges" % n)
                
                
    ## Clean function for cleaning usernames for comparison... should keep from false positives        
    def clean(self, data):
        return re.sub(self._reClean, '', data)[:20]    