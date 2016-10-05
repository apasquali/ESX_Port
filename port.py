import netmiko
import getpass
import re

usrname = raw_input("Username: ")
pswd = getpass.getpass('Password:')

FileIn = open('ip.txt', 'r')
FileOut = open('results.csv','a')

FileOut.write("Device,Port1,Port2,GB4,DRAC\n")
device = FileIn.readline().strip()

while (device != ""):
	
	cisco_ios = {
	'device_type': 'cisco_ios',
	'ip':   device,
	'username': usrname,          
	'password': pswd,
	'secret': pswd,
	}

	SSHClass = netmiko.ssh_dispatcher(cisco_ios['device_type'])
	
	#testing connectivity to device
	try:
		net_connect = SSHClass(**cisco_ios)
	except:
		print "Issues with "+device
		FileOut.write(device+",IssuesWithDevice\n")
		device = FileIn.readline().strip()
		continue
	
	#getting output from disabled command
	output = net_connect.send_command("show int status | in disabled")
	
	#testing to see if we got anything back
	if output == "":
		net_connect.disconnect()
		print device+" no ports found"
		FileOut.write(device+",NoPortsFound\n")
		device = FileIn.readline().strip()
		continue
	
	#Read output line by line, process
	count = 0
	lines = re.split('\n',output)
	for line in lines:
		port1 = line[:8]
		portTest = port1[:3]
		#Testing for Fa0 port"
		if portTest == "Fa0":
			port1 = ""
			continue
		#Checks for fiber Ports
		portTest = port1[4:5]
		if int(portTest) == 1:
			port1 == ""
			continue
					
		#Ruling out first set of ports and firewall ports
		portTest = port1[6:8]
		if int(portTest) > 14 and int(portTest) < 21:
			break
		elif int(portTest) > 24 and int(portTest) < 49:
			break

		port1 == ""
		
	#saving switch number
	switchNumber = port1[2:3]
		
	lines = re.split('\n',output)
	
	for line in lines:
		port2 = line[:8]
		portTest = port2[:3]
		#Testing for Fa0 port"
		if portTest == "Fa0":
			port2 = ""
			count += 1
			continue
		#Checks first digit to find out if on same switch
		portTest = port2[2:3]
		if int(portTest) == int(switchNumber):
			count += 1
			port2 == ""
			continue
		
		#Checks for fiber Ports with 1 in middle
		portTest = port2[4:5]
		if int(portTest) == 1:
			port2 == ""
			count += 1
			continue
		
		#Ruling out first set of ports, firewall ports, and more fiber ports
		portTest = port2[6:8]
		if int(portTest) > 14 and int(portTest) < 21:
			break
		elif int(portTest) > 24 and int(portTest) < 49:
			break
		
		port2 == ""
		count += 1
		
	#Assigning DRAC to next disabled port and testing for fiber/firewall.
	count += 1
	test = 0
	portDRAC = ""
	
	while (test == 0 and len(lines) >= count):
		
		portDRAC = lines[count]
		portDRAC = portDRAC[:8]
		portDRACtest = portDRAC[:3]
		#Testing for Fa0 port"
		if portDRACtest == "Fa0":
			portDRAC == ""
			count += 1
			continue
		portDRACtest = portDRAC[6:8]
		if int(portDRACtest) > 14 and int(portDRACtest) < 21:
			test = 1
		elif int(portDRACtest) > 24 and int(portDRACtest) < 49:
			test = 1
			
		count += 1
		
	#Assigning GB4 to next disabled port and testing for fiber/firewall.
	count += 1
	test = 0
	port4 = ""
	
	while (test == 0 and len(lines) >= count):
		
		port4 = lines[count]
		port4 = port4[:8]
		port4test = port4[:3]
		#Testing for Fa0 port"
		if port4test == "Fa0":
			port4 == ""
			count += 1
			continue
		port4test = portDRAC[6:8]
		if int(port4test) > 14 and int(port4test) < 21:
			test = 1
		elif int(port4test) > 24 and int(port4test) < 49:
			test = 1
			
		count += 1
	
	#Sending config commands if needed
	net_connect.send_command("conf t")
	
	if port1 <> "":
		net_connect.send_command("default int "+port1)
		net_connect.send_command("int "+port1)
		net_connect.send_command("desc ESX_TEMP_GB1")
		net_connect.send_command("sw m acc")
		net_connect.send_command("sw acc v 100")
		net_connect.send_command("spanning-tree portfast")
	if portDRAC <> "":
		net_connect.send_command("default int "+portDRAC)
		net_connect.send_command("int "+portDRAC)
		net_connect.send_command("desc ESX_TEMP_DRAC")
		net_connect.send_command("sw m acc")
		net_connect.send_command("sw acc v 90")
		net_connect.send_command("spanning-tree portfast")
	if port2 <> "":
		net_connect.send_command("default int "+port2)
		net_connect.send_command("int "+port2)
		net_connect.send_command("desc ESX_TEMP_GB2")
		net_connect.send_command("sw m acc")
		net_connect.send_command("sw acc v 100")
		net_connect.send_command("spanning-tree portfast")
	if port4 <> "":
		net_connect.send_command("default int "+port4)
		net_connect.send_command("int "+port4)
		net_connect.send_command("desc ESX_NEW_GB4")
		net_connect.send_command("sw m acc")
		net_connect.send_command("sw acc v 10")
		net_connect.send_command("spanning-tree portfast")
	
	net_connect.send_command("end")
		
	#Closing Connection to Current Device
	net_connect.disconnect()
	
	#print results and write to file
	#print "device "+device+"\nport 1 is "+port1+" \nport 2 is "+port2+"\nDRAC port is "+portDRAC
	FileOut.write(device+","+port1+","+port2+","+port4+","+portDRAC+"\n")
	
	device = FileIn.readline().strip()
	
FileIn.close()
FileOut.close()