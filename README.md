Asterisk PBX Integration for Datadog
===================

Datadog Agent plugin for the Open Source Asterisk PBX based on the work of jwestbrook (https://github.com/jwestbrook/datadog-asteriskpbx).

Prerequisites
-----------
- Datadog Agent v5 (1.5) or v6 (6.3.1)
- pyst Library
- PyYaml (for test)

Installation (Datadog Agent v6)
-----------
For Installation on Datadog Agent v5 [read this document](https://github.com/mafairnet/Asterisk-PBX-Integration-for-Datadog/blob/master/README_v5.md)

Install the Asterisk Manager Python library for datadog.

```
/opt/datadog-agent/embedded/bin/pip install pyst2
```

Get the module files for the datadog agent.

```
cd /usr/src/
wget https://github.com/mafairnet/datadog-asteriskpbx/archive/master.zip
unzip master.zip
cd Asterisk-PBX-Integration-for-Datadog-master/
```

Copy the module files to the datadog directories.

```
cp -R checks.d/asteriskpbx.py /etc/datadog-agent/checks.d/
cp -R conf.d/asteriskpbx.yaml /etc/datadog-agent/conf.d/
```

Edit the configuration file for the module.

```
nano /etc/datadog-agent/conf.d/asteriskpbx.yaml
```

Insert the AMI User and Password for the PBX.

```
init_config:
	instances:
		- host: localhost #defaults to localhost
		  port: 5038 #defaults to 5038
		  manager_user: user #required
		  manager_secret: secret #required
		  extension_length: 5 #Length of your internal extensions at the PBX
		  #this user needs to have the command write privilege
```

Restart  the Datadog service.

```
/etc/init.d/datadog-agent restart
```

Check the Datadog service status.

```
/etc/init.d/datadog-agent info
```

The output should be like the next text.

```
    asteriskpbx
    -----------
      - instance #0 [OK]
      - Collected 17 metrics, 0 events & 1 service check
```

Important notes
-----------
**SIP Trunks Metrics**

It is highly recommended that you use '-trunk' string as posfix into your SIP trunk name to detect it as a Trunk so the script can detect the SIP Trunks. You can verify this when executing the next command in the console:

```
[user@yourpbx]# asterisk -rx 'sip show peers' | grep "\-trunk"
SIP1-trunk          192.168.1.10                                  Yes        Yes            5060     OK (1 ms)
SIP2-trunk/SIP2     192.168.1.11                                  Yes        Yes            5060     OK (1 ms)
```

But in the lastest changes SIP Trunks monitoring was improved:
-You dont need to put "-trunk" posfix to detect SIP Trunks. Just add them in the YAML config file. 
-SIP Trunks Channels Usage added, just add the total capacity of your SIP Trunk for channels.