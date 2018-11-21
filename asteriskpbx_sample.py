#
# requires pyst2 for Asterisk Manager Interface
# https://github.com/rdegges/pyst2
#
# requires re for regular expression matching on asterisk output
#
#
# This is a python script that illustrates the output from Asterisk do not use with DataDog Agent
#
# update the host/user/secret variables below
#
# Usage : python asteriskpbx_sample.py
#

import asterisk.manager
import re


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

host    = "localhost"
port    = 5038
user    = "user"
secret  = "secret"

extensionLength = 5

mgr = asterisk.manager.Manager()
mgr.connect(host,port)
mgr.login(user,secret)

#Call volume

call_volume = mgr.command('core show calls')

current_call_vol = call_volume.data.split('\n')

procesed_call_vol = current_call_vol[1].replace(' calls processed','')
current_call_vol = current_call_vol[0].replace('active call','')
current_call_vol = current_call_vol.replace('s','')
current_call_vol = current_call_vol.replace(' ','')

print('Current Call Volume')
print(current_call_vol)

print('Current Call Processed')
print(procesed_call_vol)


#Internal, Inbound, Outbound Calls

#Get All Active Channels
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
        #print chan
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
        #print channel+context+extension+priority+state+application+data+callerid+duration+accountcode+peeraccount+bridgedto
        currentChannelsArray.append(currentChannel)
        #print currentChannel

#print(currentChannelsArray)
#print(current_channels)

internalCalls = 0
outboundCalls = 0
inboundCalls  = 0
conferenceCalls = 0

#Obtengo los canales que fueron levantados en "Dial" y los pongo como llamadas
for currentChannel in currentChannelsArray:
    caller = "N/A"
    called = "N/A"
    callType = "N/A"

    '''
    print("Channel:"+currentChannel.Channel\
          +",Context:"+currentChannel.Context\
          +",Extension:"+currentChannel.Extension\
          +",Application:"+currentChannel.Application\
          +",Data:"+currentChannel.Data\
          +",BridgedTo:"+currentChannel.BridgedTo)
    '''

    if "Dial" == currentChannel.Application  or "Queue" == currentChannel.Application::
        currentCall = Call("N/A","N/A","N/A","N/A","N/A","N/A")
        currentCall.Caller = currentChannel.CallerId
        currentCall.CallerChannel = currentChannel.Channel
        currentCall.BridgedChannel = currentChannel.BridgedTo
        #print "Caller:"+currentCall.Caller+",Channel:"+currentCall.CallerChannel+",BridgedChannel:"+currentCall.BridgedChannel
        currentCalls.append(currentCall)

    if "ConfBridge" == currentChannel.Application:
        currentCall = Call("N/A","N/A","N/A","N/A","N/A","N/A")
        currentCall.Caller = currentChannel.CallerId
        currentCall.CallerChannel = currentChannel.Channel
        calledConference = currentChannel.Data.split(',')
        calledConference = calledConference[0]
        currentCall.Called = calledConference
        currentCall.CalledChannel = currentChannel.Channel
        conferenceCalls = conferenceCalls +1


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
    #print "Caller:"+currentCall.Caller+",CallerChannel:"+currentCall.CallerChannel+",BridgedChannel:"+currentCall.BridgedChannel+",Called:"+currentCall.Called+",CalledChannel:"+currentCall.CalledChannel+",CallType:"+currentCall.CallType

print('Internal Calls:')
print(internalCalls)

print('Inbound Calls:')
print(inboundCalls)

print('Outbound Calls:')
print(outboundCalls)

print('Conference Calls:')
print(conferenceCalls)

#PRI Channels

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

print('Current in use PRI Channels')
print(openchannels)

#SIP Peers

sip_result = mgr.command('sip show peers')

sip_results = sip_result.data.split('\n')

siptotals = sip_results[len(sip_results)-3]

siptotal = re.findall(r'([0-9]+) sip peer',siptotals)[0]

monitored_peers = re.findall(r'Monitored: ([0-9]+) online, ([0-9]+) offline',siptotals)[0]
unmonitored_peers = re.findall(r'Unmonitored: ([0-9]+) online, ([0-9]+) offline',siptotals)[0]

print('Total SIP Peers')
print(siptotal)
print('Monitored SIP Peers online/offline')
print(monitored_peers)
print('Unmonitored SIP Peers online/offline')
print(unmonitored_peers)

#IAX2 Peers

iax_result = mgr.command('iax2 show peers')

iax_results = iax_result.data.split('\n')

iax_total_line = iax_results[len(iax_results)-3]

iax_peers_total = re.findall(r'([0-9]+) iax2 peers',iax_total_line)[0]
iax_peers_online = re.findall(r'\[([0-9]+) online',iax_total_line)[0]
iax_peers_offline = re.findall(r'([0-9]+) offline',iax_total_line)[0]
iax_peers_unmonitored = re.findall(r'([0-9]+) unmonitored',iax_total_line)[0]


print('Total IAX2 Peers')
print(iax_peers_total)
print('IAX2 Peers Online')
print(iax_peers_online)
print('IAX2 Peers Offline')
print(iax_peers_offline)
print('IAX2 Peers Unmonitored')
print(iax_peers_unmonitored)

#DAHDI Trunks

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
            #Digium Cards
            if "Wildcard" in chan_data[0]:
                if len(chan_data) > 2 and chan_data[2] == "OK":
                    dahdi_online_trunks += 1
                if len(chan_data) > 2 and chan_data[2] == "RED":
                    dahdi_offline_trunks += 1
            #Sangoma Cards
            if "wanpipe" in chan_data[0]:
                if len(chan_data) > 2 and chan_data[3] == "OK":
                    dahdi_online_trunks += 1
                if len(chan_data) > 2 and chan_data[3] == "RED":
                    dahdi_offline_trunks += 1

print('Total Dahdi Trunks')
print(dahdi_total_trunks)

print('DAHDI Online Trunks')
print(dahdi_online_trunks)

print('DAHDI Offline Trunks')
print(dahdi_offline_trunks)

#SIP Trunks (You have to add '-trunk' string into your SIP trunk name to detect it as a Trunk)

sip_results[0] = None

sip_online_trunks = 0
sip_offline_trunks = 0
sip_total_trunks = 0

for chan in sip_results:
    if chan != None:
        chan_data = chan.split()

        if len(chan_data) > 1:
            if "-trunk" in chan_data[0]:
                sip_total_trunks += 1
                if len(chan_data) > 2 and "OK" in chan_data[5]:
                    sip_online_trunks += 1
                if len(chan_data) > 2 and chan_data[5] == "UNREACHABLE":
                    sip_offline_trunks += 1

print('Total SIP Trunks')
print(sip_total_trunks)

print('SIP Online Trunks')
print(sip_online_trunks)

print('SIP Offline Trunks')
print(sip_offline_trunks)

##### G729 Codecs 

g729_result = mgr.command('g729 show licenses')

g729_results = g729_result.data.split('\n')

g729_total_line = g729_results[0]

g729_total = re.findall(r'([0-9]+) licensed',g729_total_line)[0]
g729_encoders = re.split('/',g729_total_line)[0]
g729_decoders = re.findall(r'([0-9]+) encoders/decoders',g729_total_line)[0]

print('G729 Total')
print(g729_total)

print('G279 In Use Encoders')
print(g729_encoders)

print('G279 In Use Decoders')
print(g729_decoders)

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

print('System Uptime')
print(system_uptime)

print('Last Reload')
print(asterisk_last_reload)

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
        print(chan_data)
        if len(chan_data) > 2:
            if "IDLE" in chan_data[6] and "IDLE" in chan_data[7] :
                mfcr2_available_channels += 1
            if "ANSWER" in chan_data[6] or "ANSWER" in chan_data[7] :
                mfcr2_inuse_channels += 1
            if "BLOCK" in chan_data[6] or "BLOCK" in chan_data[7] :
                mfcr2_blocked_channels += 1

print('Total MFCR2 Channels')
print(mfcr2_total_channels)

print('MFCR2 InUse Channels')
print(mfcr2_inuse_channels)

print('MFCR2 Available Channels')
print(mfcr2_available_channels)

print('MFCR2 Blocked Channels')
print(mfcr2_blocked_channels)

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

print('SCCP Total Devices')
print(sccp_total_devices)

print('SCCP Online Devices')
print(sccp_online_devices)

print('SCCP Offile Devices')
print(sccp_offline_devices)


##### Close connection

mgr.close()