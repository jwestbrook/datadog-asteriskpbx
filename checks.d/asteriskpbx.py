#
# requires pyst2 for Asterisk Manager Interface
# https://github.com/rdegges/pyst2
#
# requires re for regular expression matching on asterisk output
#
#

import asterisk.manager
import re
from checks import AgentCheck

###Internal, Inbound, Outbound Calls Classes
class Channel:
  def __init__(self,Channel,Context,Extension,Priority,State,Application,Data,CallerId,Duration,AccountCode,PeerAccount,BridgedTo):
    self.Channel        = Channel
    self.Context        = Context
    self.Extension      = Extension
    self.Priority       = Priority
    self.State          = State
    self.Application    = Application
    self.Data           = Data
    self.CallerId       = CallerId
    self.Duration       = Duration
    self.AccountCode    = AccountCode
    self.PeerAccount    = PeerAccount
    self.BridgedTo      = BridgedTo

class Call:
  def __init__(self,Caller,CallerChannel,Called,CalledChannel,BridgedChannel,CallType):
    self.Caller         = Caller
    self.CallerChannel  = CallerChannel
    self.Called         = Called
    self.CalledChannel  = CalledChannel
    self.BridgedChannel = BridgedChannel
    self.CallType       = CallType

class AsteriskCheck(AgentCheck):

    def check(self, instance):

        if 'host' not in instance:
            instance['host'] = 'localhost'
        if 'manager_user' not in instance:
            self.log.error('manager_user not defined, skipping')
            return
        if 'manager_secret' not in instance:
            self.log.error('manager_secret not defined, skipping')
            return

######  Connect
        mgr = asterisk.manager.Manager()
        try:
            if 'port' in instance:
                mgr.connect(instance['host'],instance['port'])
            else:
                mgr.connect(instance['host'])
            mgr.login(instance['manager_user'],instance['manager_secret'])
        except asterisk.manager.ManagerSocketException as e:
            self.log.error('Error connecting to Asterisk Manager Interface')
            mgr.close()
            return
        except asterisk.manager.ManagerAuthException as e:
            self.log.error('Error Logging in to Asterisk Manager Interface')
            mgr.close()
            return

##### Call Volume
        call_volume = mgr.command('core show calls')

        current_call_vol = call_volume.data.split('\n')

        procesed_call_vol = current_call_vol[1].replace(' calls processed','')
        current_call_vol = current_call_vol[0].replace('active call','')
        current_call_vol = current_call_vol.replace('s','')
        current_call_vol = current_call_vol.replace(' ','')

        self.gauge('asterisk.callsprocesed',procesed_call_vol)
        self.gauge('asterisk.callvolume',current_call_vol)

##### Internal, Inbound Outbound Calls

        extensionLength = instance['extension_length']

        current_channels = mgr.command('core show channels verbose')
        current_channels = current_channels.data.split('\n')
        current_channels[0] = None
        current_channels_size = len(current_channels)
        current_channels[current_channels_size-1] = None
        current_channels[current_channels_size-2] = None
        current_channels[current_channels_size-3] = None
        current_channels[current_channels_size-4] = None
        current_channels[current_channels_size-5] = None

        currentChannelsArray = []
        currentCalls = []

        for chan in current_channels:
            if chan != None:
                channel     = re.sub(' +',' ',chan[0:21]).lstrip(' ').rstrip(' ')
                context     = re.sub(' +',' ',chan[21:42]).lstrip(' ').rstrip(' ')
                extension   = re.sub(' +',' ',chan[42:59]).lstrip(' ').rstrip(' ')
                priority    = re.sub(' +',' ',chan[59:64]).lstrip(' ').rstrip(' ')
                state       = re.sub(' +',' ',chan[64:72]).lstrip(' ').rstrip(' ')
                application = re.sub(' +',' ',chan[72:85]).lstrip(' ').rstrip(' ')
                data        = re.sub(' +',' ',chan[85:111]).lstrip(' ').rstrip(' ')
                callerid    = re.sub(' +',' ',chan[111:127]).lstrip(' ').rstrip(' ')
                duration    = re.sub(' +',' ',chan[127:136]).lstrip(' ').rstrip(' ')
                accountcode = re.sub(' +',' ',chan[136:148]).lstrip(' ').rstrip(' ')
                peeraccount = re.sub(' +',' ',chan[148:160]).lstrip(' ').rstrip(' ')
                bridgedto   = re.sub(' +',' ',chan[160:181]).lstrip(' ').rstrip(' ')
                currentChannel = Channel(channel,context,extension,priority,state,application,data,callerid,duration,accountcode,peeraccount,bridgedto)

        internalCalls = 0
        outboundCalls = 0
        inboundCalls  = 0

        for currentChannel in currentChannelsArray:
            caller = "N/A"
            called = "N/A"
            callType = "N/A"

            if "Dial" == currentChannel.Application:
                currentCall = Call("N/A","N/A","N/A","N/A","N/A","N/A")
                currentCall.Caller = currentChannel.CallerId
                currentCall.CallerChannel = currentChannel.Channel
                currentCall.BridgedChannel = currentChannel.BridgedTo
                currentCalls.append(currentCall)

        for currentCall in currentCalls:
            caller = "N/A"
            called = "N/A"
            callType = "N/A"
            for currentChannel in currentChannelsArray:
                if "None" not in currentChannel.BridgedTo:
                    if currentCall.BridgedChannel == currentChannel.Channel:
                        currentCall.Called = currentChannel.CallerId
                        currentCall.CalledChannel = currentChannel.Channel

        for currentCall in currentCalls:
            if len(currentCall.Caller) <= extensionLength and len(currentCall.Called) <= extensionLength:
                currentCall.CallType = "Internal"
                internalCalls = internalCalls +1
            if len(currentCall.Caller) > extensionLength and len(currentCall.Called) <= extensionLength:
                currentCall.CallType = "Inbound"
                inboundCalls = inboundCalls + 1
            if len(currentCall.Caller) <= extensionLength and len(currentCall.Called) > extensionLength:
                currentCall.CallType = "Outbound"
                outboundCalls = outboundCalls + 1

        self.gauge('asterisk.calls.internal',internalCalls)
        self.gauge('asterisk.calls.inbound',inboundCalls)
        self.gauge('asterisk.calls.outbound',outboundCalls)
        
##### SIP Peers
        sip_result = mgr.command('sip show peers')

        sip_results = sip_result.data.split('\n')

        siptotals = sip_results[len(sip_results)-3]

        siptotal = re.findall(r'([0-9]+) sip peer',siptotals)[0]

        monitored_peers = re.findall(r'Monitored: ([0-9]+) online, ([0-9]+) offline',siptotals)[0]
        unmonitored_peers = re.findall(r'Unmonitored: ([0-9]+) online, ([0-9]+) offline',siptotals)[0]

        self.gauge('asterisk.sip.peers',siptotal)
        self.gauge('asterisk.sip.monitored.online',monitored_peers[0])
        self.gauge('asterisk.sip.monitored.offline',monitored_peers[1])
        self.gauge('asterisk.sip.unmonitored.online',unmonitored_peers[0])
        self.gauge('asterisk.sip.unmonitored.offline',unmonitored_peers[1])

##### SIP Trunks (You have to add '-trunk' string into your SIP trunk name to detect it as a Trunk)
        sip_total_trunks = 0
        sip_online_trunks = 0
        sip_offline_trunks = 0

        trunks = re.finditer('^.*-trunk.*([OK|UN].*)', sip_result.data, re.MULTILINE)

        for trunk in trunks:
            sip_total_trunks +=1
            if 'OK' in trunk.group():
                sip_online_trunks += 1
            else:
                sip_offline_trunks += 1
      
        self.gauge('asterisk.sip.trunks.total',sip_total_trunks)
        self.gauge('asterisk.sip.trunks.online',sip_online_trunks)
        self.gauge('asterisk.sip.trunks.offline',sip_offline_trunks)

##### PRI In Use

        pri = mgr.command('pri show channels')

        pri_channels = pri.data.split('\n')

        pri_channels[0] = None
        pri_channels[1] = None

        openchannels = 0
        for chan in pri_channels:
            if chan != None:
                chan_data = chan.split()
                if len(chan_data) > 2 and chan_data[3] == "No":
                    openchannels += 1

        self.gauge('asterisk.pri.channelsinuse',openchannels)

##### IAX2 Peers

        iax_result = mgr.command('iax2 show peers')

        iax_results = iax_result.data.split('\n')

        iax_total_line = iax_results[len(iax_results)-3]

        iax_peers_total = re.findall(r'([0-9]+) iax2 peers',iax_total_line)[0]
        iax_peers_online = re.findall(r'\[([0-9]+) online',iax_total_line)[0]
        iax_peers_offline = re.findall(r'([0-9]+) offline',iax_total_line)[0]
        iax_peers_unmonitored = re.findall(r'([0-9]+) unmonitored',iax_total_line)[0]

        self.gauge('asterisk.iax2.peers',iax_peers_total)
        self.gauge('asterisk.iax2.online',iax_peers_online)
        self.gauge('asterisk.iax2.offline',iax_peers_offline)
        self.gauge('asterisk.iax2.unmonitored',iax_peers_unmonitored)
   
##### DAHDI Channels  
    
        dahdi_result = mgr.command('dahdi show status')

        dahdi_results = dahdi_result.data.split('\n')

        dahdi_total_trunks = len(dahdi_results)-3

        dahdi_results[0] = None

        dahdi_online_trunks = 0
        dahdi_offline_trunks = 0

        for chan in dahdi_results:
            if chan != None:
                chan_data = chan.split()

                if len(chan_data) > 1:
                    if "Wildcard" in chan_data[0]:
                        if len(chan_data) > 2 and chan_data[2] == "OK":
                            dahdi_online_trunks += 1
                        if len(chan_data) > 2 and chan_data[2] == "RED":
                            dahdi_offline_trunks += 1

                    if "wanpipe" in chan_data[0]:
                        if len(chan_data) > 2 and chan_data[3] == "OK":
                            dahdi_online_trunks += 1
                        if len(chan_data) > 2 and chan_data[3] == "RED":
                            dahdi_offline_trunks += 1

        self.gauge('asterisk.dahdi.total',dahdi_total_trunks)
        self.gauge('asterisk.dahdi.online',dahdi_online_trunks)
        self.gauge('asterisk.dahdi.offline',dahdi_offline_trunks)
        
##### G729 Codecs 
        
        g729_result = mgr.command('g729 show licenses')

        g729_results = g729_result.data.split('\n')

        g729_total_line = g729_results[0]

        g729_total = re.findall(r'([0-9]+) licensed',g729_total_line)[0]
        g729_encoders = re.split('/',g729_total_line)[0]
        g729_decoders = re.findall(r'([0-9]+) encoders/decoders',g729_total_line)[0]

        self.gauge('asterisk.g729.total',g729_total)
        self.gauge('asterisk.g729.encoders',g729_encoders)
        self.gauge('asterisk.g729.decoders',g729_decoders)
        

##### Asterisk Uptime

        uptime_result = mgr.command('core show uptime')
        
        uptime_results = uptime_result.data.split('\n')
        
        system_total_line = uptime_results[0]
        asterisk_total_line = uptime_results[1]
        
        system_uptime_days = 0
        system_uptime_hours = 0
        system_uptime_minutes = 0
        system_uptime_seconds = 0
        
        system_uptime_days = 0
        system_uptime_hours = 0
        system_uptime_minutes = 0
        system_uptime_seconds = 0

        if "day" in system_total_line:
            system_uptime_days = re.findall(r'([0-9]+) day',system_total_line)[0]
        if "hour" in system_total_line:
            system_uptime_hours = re.findall(r'([0-9]+) hour',system_total_line)[0]
        if "minute" in system_total_line:
            system_uptime_minutes = re.findall(r'([0-9]+) minute',system_total_line)[0]
        if "second" in system_total_line:
            system_uptime_seconds = re.findall(r'([0-9]+) second',system_total_line)[0]

        system_uptime = ( int(system_uptime_days) * 86400) +  ( int(system_uptime_hours) * 3600) + ( int(system_uptime_minutes) * 60) + int(system_uptime_seconds)
        
        asterisk_last_reload_days = 0
        asterisk_last_reload_hours = 0
        asterisk_last_reload_minutes = 0
        asterisk_last_reload_seconds = 0
        
        if "day" in asterisk_total_line:
            asterisk_last_reload_days = re.findall(r'([0-9]+) day',asterisk_total_line)[0]
        if "hour" in asterisk_total_line:
            asterisk_last_reload_hours = re.findall(r'([0-9]+) hour',asterisk_total_line)[0]
        if "minute" in asterisk_total_line:
            asterisk_last_reload_minutes = re.findall(r'([0-9]+) minute',asterisk_total_line)[0]
        if "second" in asterisk_total_line:
            asterisk_last_reload_seconds = re.findall(r' ([0-9]+) second',asterisk_total_line)[0]

        asterisk_last_reload = ( int(asterisk_last_reload_days) * 86400) + ( int(asterisk_last_reload_hours) * 3600) + ( int(asterisk_last_reload_minutes) * 60) + int(asterisk_last_reload_seconds)

        self.gauge('asterisk.system.uptime',system_uptime)
        self.gauge('asterisk.last.reload',asterisk_last_reload)
        
##### MFCR2 Channels

        mfcr2_result = mgr.command('mfcr2 show channels')

        mfcr2_results = mfcr2_result.data.split('\n')

        mfcr2_total_channels = len(mfcr2_results)-3

        mfcr2_results[0] = None

        mfcr2_inuse_channels = 0
        mfcr2_available_channels = 0
        mfcr2_blocked_channels = 0

        for chan in mfcr2_results:
            if chan != None:
                chan_data = chan.split()
                if len(chan_data) > 2:
                    if "IDLE" in chan_data[6] and "IDLE" in chan_data[7] :
                        mfcr2_available_channels += 1
                    if "ANSWER" in chan_data[6] or "ANSWER" in chan_data[7] :
                        mfcr2_inuse_channels += 1
                    if "BLOCK" in chan_data[6] or "BLOCK" in chan_data[7] :
                        mfcr2_blocked_channels += 1
                        
        self.gauge('asterisk.mfcr2.total.channels',mfcr2_total_channels)
        self.gauge('asterisk.mfcr2.available.channels',mfcr2_available_channels)
        self.gauge('asterisk.mfcr2.inuse.channels',mfcr2_inuse_channels)
        self.gauge('asterisk.mfcr2.blocked.channels',mfcr2_blocked_channels)

##### SCCP Devices

        sccp_total_devices = 0
        sccp_online_devices = 0
        sccp_offline_devices = 0
        
        sccp_result = mgr.command('sccp show devices')

        if "No such command" not in sccp_result.data:
            
            sccp_devices = re.finditer('^.*.SEP.*', sccp_result.data, re.MULTILINE)

            for sccp_device in sccp_devices:
                sccp_total_devices +=1
                if '--' in sccp_device.group():
                    sccp_offline_devices += 1
                else:
                    sccp_online_devices += 1

        self.gauge('asterisk.sccp.devices.total',sccp_total_devices)
        self.gauge('asterisk.sccp.devices.online',sccp_online_devices)
        self.gauge('asterisk.sccp.devices.offline',sccp_offline_devices)
                    

##### Close connection

        mgr.close()
