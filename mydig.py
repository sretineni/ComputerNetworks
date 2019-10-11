# -*- coding: utf-8 -*-
import dns.name
import dns.message
import dns.query
import dns.flags
import sys
from datetime import datetime
from time import perf_counter
# function to print result section.
def printResult(recordText, execTime, domain, mode, responseSize):
    print("QUESTION SECTION:")
    print(domain,"\tIN",mode)
    print("\nANSWER SECTION:")
    print(recordText,"\n")
    print('Query time: ',execTime,"msec")
    currTime = datetime.now().strftime("%b %d %Y %H:%M:%S")

    print('WHEN: ',currTime)
    print('\nMSG SIZE rcvd: ',responseSize)
    
"""function to recursively resolve host name into an IP address.We recursively 
call the resolveHost function until the answer section returns an IP Address."""
def resolveHost(currServer, domain, mode):
    global currRootServer
    request = dns.message.make_query(domain, mode)
    response = dns.query.udp(request, currServer, timeout=10)
    responseCode = response.rcode()
    if responseCode !=0:
        return False
    for record in response.answer:
        hostName = (record.to_text()).split()[0]
        modeReturned = (record.to_text()).split()[3]

        if hostName == domain+"." or hostName == domain:
            if modeReturned == "A" or modeReturned == "MX" or modeReturned == "NS" or mode == "MX" or mode == "NS":
                return record,True
            #If cname record is returned, we resolve the cname recursively again.
            elif modeReturned == "CNAME" and mode:
                cnameHost = (record.to_text()).split()[4]
                finalRecord, status = resolveHost(currRootServer,cnameHost,mode)
                return finalRecord,True               
          
    """Call the resolveHost function from the additional section, with the 
    IP address of the top level domain name server."""    
    for record in response.additional:
        ipAddress = (record.to_text()).split()[4]
        modeReturned = (record.to_text()).split()[3]
        if modeReturned=="A":
            try:
                recordReturned,status = resolveHost(ipAddress, domain, mode)
            except dns.exception.Timeout:
                continue
            if status:
                return recordReturned,status
        
    """When the A record is queried and NS is returned in authority section, we resolve it's
IP address first and then use that IP to resolve the IP of our domain name."""    
    for record in response.authority:
        hostName = (record.to_text()).split()[0]
        modeReturned = (record.to_text()).split()[3]
        if hostName == domain+".":
            if modeReturned=="A" or modeReturned=="SOA":
                return record,True
            if modeReturned=="NS":
                NSHost = (record.to_text()).split()[4]
                try:
                    record, status = resolveHost(currRootServer, NSHost, "A")
                    currIpAddress = (record.to_text()).split()[4]
                except dns.exception.Timeout:
                    continue
                finalRecord, status = resolveHost(currIpAddress,domain,mode)
                return finalRecord,status

        
       
    
rootServerList = [line.rstrip('\n') for line in open('rootservers.txt')]
domain = sys.argv[1]
mode = sys.argv[2]
t1_start = perf_counter()
"""Loop through rootservers and break as soon as an address is resolved, 
if not, we move on to the next root server."""
try:  
    for rootServer in rootServerList:
        currRootServer = rootServer
        record,status = resolveHost(currRootServer, domain, mode)
        if status:
            break
    t1_stop = perf_counter()
    exec_time=int((t1_stop-t1_start)*1000)
    resSize = record.__sizeof__()
    printResult(record.to_text(), exec_time, domain, mode, resSize)
    
except:
    print("The DNS operation failed...") 

    
