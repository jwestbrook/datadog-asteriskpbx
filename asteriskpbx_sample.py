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

host    = "localhost"
port    = 5038
user    = "user"
secret  = "secret"


mgr = asterisk.manager.Manager()
mgr.connect(host,port)
mgr.login(user,secret)

#Call volume

call_volume = mgr.command('core show calls')

current_call_vol = call_volume.data.split('\n')

current_call_vol = current_call_vol[0].replace('active call','')
current_call_vol = current_call_vol.replace('s','')
current_call_vol = current_call_vol.replace(' ','')

print('Current Call Volume')
print(current_call_vol)

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

mgr.close()