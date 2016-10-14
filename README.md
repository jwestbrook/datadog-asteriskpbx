Asterisk PBX Integration for Datadog
===================

DataDog Agent plugin for the Open Source Asterisk PBX based on the work of jwestbrook (https://github.com/jwestbrook/datadog-asteriskpbx).

Prerequisites
-----------
- Datadog
- pyst Library

Installation
-----------
Install the Asterisk Manager Python library for datadog.

```
/opt/datadog-agent/embedded/bin/pip install pyst2
```

Get the module files for the datadog agent.

```
cd /usr/src/
wget https://github.com/mafairnet/datadog-asteriskpbx/archive/master.zip
unzip master.zip
cd datadog-asteriskpbx-master/
```

Copy the module files to the datadog directories.

```
cp -R checks.d/asteriskpbx.py /opt/datadog-agent/agent/checks.d/
cp -R conf.d/asteriskpbx.yaml /etc/dd-agent/conf.d/
```

Edit the configuration file for the module.

```
nano /etc/dd-agent/conf.d/asteriskpbx.yaml
```

Insert the AMI User and Password for the PBX.

```
init_config:
	instances:
		- host: localhost #defaults to localhost
		  port: 5038 #defaults to 5038
		  manager_user: user #required
		  manager_secret: secret #required
		  #this user needs to have the command write privilege
```

Restart  the datadog service.

```
/etc/init.d/datadog-agent restart
```

Check the datadog service status.

```
/etc/init.d/datadog-agent info
```

The output should be like the next text.

```
    asteriskpbx
    -----------
      - instance #0 [OK]
      - Collected 11 metrics, 0 events & 1 service check
```