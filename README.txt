# Copyright 2016 Poznan Supercomputing and Networking Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

nsi_connections
----------------

1. Overview

'nsi_connections' exposes HTTP/REST API for creating, quering and deleting Bandwidth-on-Demand connection using OGF NSI Connection Service v2.0 protocol:
    - https://www.ogf.org/documents/GFD.212.pdf
    
This REST API can be more easily used by any applications or other services than NSIv2 protocol itself.  

'nsi_connections' implements TMF Activation and Configuration API v1.0:
https://projects.tmforum.org/wiki/display/API/Open+API+Table


1.1 REST API specification

    1. POST /api/activation/service
    
        Create a new data plane connection
        
        Data:  service request in JSON format containing attributes in 'serviceCharacteristic' field:
            - description: [string] description of a new connection 
                        (eg.: 'required by Microsoft Azure service 3232-4345')
            - src_domain: [string] URN identifier of source domain 
                        (eg.: 'urn:ogf:network:pionier.net.pl:2013:topology')
            - src_port: [string] identifier of the interface of source domain where connection 
                        must be terminated (eg.: 'felix-ge-1-0-9')
            - src_vlan: [int] VLAN tag to be used on source port 
                        (eg.: 1202)
            - dst_domain: [string] URN identifier of destination domain 
                        (eg.: urn:ogf:network:geant.net:2013:topology')
            - dst_port: [string] identifier of the interface of destination domain where connection must be 
                        terminated  (eg.: 'iMinds__port__to__GEANT')
            - dst_vlan: [int] VLAN tag to be used on destination port 
                        (eg.: 2001)
            - capacity: [int] bandwidth which must be reserved for a new connection
            - start_time: (optional) [string] date and time in any when connection should be provisioned, 
                        if missing then starts immediatelly (eg.: '2016-09-1T8:32:10+02:00') [See #1]
            - end_time: (optional) [string] date and time in any when connection should be terminated, 
                        if missing then no termination planned (eg.: '2017-09-1T13:00:00+02:00') [See #1]
            - explicit_routes: (optional) [list of strings] URN identifiers of STP ports taking part 
                        of the connection route

        #1) Date and time format must be formated in ISO 8601 date/time format. Examples:
            - 'yyyy-mm-ddThh:mm:ssZ'
            - 'yyyy-mm-ddThh:mm:ss+hh:mm'
            - 'yyyy-mm-ddThh:mm:ss-hh:mm'
        During processing of date/time after calling this REST function is always translated 
        from localtime zone to UTC timezone.
        
        Returns:
            1. HTTP code 201 and JSON object being a copy of service request plus a new attribute:
                - service_id: [string] URN identifier of the reserved connection 
                        (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
            2. HTTP code 400 when incorrect connection attributes provided
            3. HTTP code 500 when a connection couldn't be reserved in the BoD system or other problem occured
    
    2. DELETE /api/activation/service/<service_id>
    
        Delete the connection or its reservation
        
        Parameters:
            - service_id: [string] URN identifier of the reserved connection 
                        (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
            
        Returns:
            1. HTTP code 200 for all conditions

    3. GET /api/activation/service/<service_id> 
    
        Query status of the connection or its reservation
        
        Parameters:
            - service_id: [string] URN identifier of the reserved connection 
                        (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
            
        Returns:
            1. HTTP code 200 and JSON object containing service information stored in 'serviceCharacteristic' field:
                - active: ["false", "true"] is data plane for the connection provisioned (can traffic be send)
                - connectionId: [string] URN identifier of the reserved connection
                - description: [string] description of the connection
                - globalReservationId: [string] URN identifier used to correlate individually created connections
                - lifecycleState: ["CREATED", "FAILED", "PASSED_END_TIME", "TERMINATING", "TERMINATED"] 
                            state values for the reservation lifecycle
                - notificationId: [int] identifier of the last notification send for given connection
                - provisionState: ["RELEASED", "PROVISIONING", "PROVISIONED", "RELEASING"] 
                            state values for the data plane resources provisioning
                - requesterNSA: [string] URN identifier of requester NSA
                - reservationState: ["RESERVE_START", "RESERVE CHECKING", "RESERVE_FAILED", "RESERVE_ABORTING",
                            "RESERVE_HELD", "RESERVE_COMMITTING", "RESERVE_TIMEOUT"] 
                            transitions of the reservation lifecycle
                - version: [int] version of the reservation instantiated in the data plan
                - versionConsistent: ["true", "false"] consistency of reservation versions for NSI AG
            2. HTTP code 404 when connection was not found
            3. HTTP code 500 when query request could not be sent to NSI API

    4. GET /doc 
    
        Generates HTML documentation of exposed REST API
        
        
        
        

2. Installation

2.1 Requirements

Needs Jython, Apache CXF 2.7.10, Flask and NSIv2 API implementation by AIST.
Jython, CXF are installed from the respective website.

2.1.1 Java requirements
    - Java SDK 8 (http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html)
    - Apache Ant 1.9.6 (http://ant.apache.org/)
    - Apache CXF 2.7.10 (http://cxf.apache.org)
    
    1. Java SDK requires to set JAVA_HOME:
        update-alternatives --config java 
        (to check where installed if done automaticly; shows <jdk-install-dir>/bin/java)
        
        root@debian:~# update-alternatives --config java
        There are 2 choices for the alternative java (providing /usr/bin/java).

          Selection    Path                                            Priority   Status
        ------------------------------------------------------------
            0            /usr/lib/jvm/java-6-openjdk-amd64/jre/bin/java   1061      auto mode
        *  1            /opt/java/jdk1.8.0_71/bin/java                          100       manual mode
            2            /usr/lib/jvm/java-6-openjdk-amd64/jre/bin/java   1061      manual mode


        export JAVA_HOME=<jdk-install-dir>  
                    (eg.: /opt/java/jdk1.8.0_71)
        export PATH=$JAVA_HOME/bin:$PATH

    2. Apache CXF requires to set CXF_HOME:
        cd /opt
        wget http://archive.apache.org/dist/cxf/2.7.10/apache-cxf-2.7.10.tar.gz
        tar zxvf apache-cxf-2.7.10.tar.gz
        ln -s apache-cxf-2.7.10 cxf
        export CXF_HOME=/opt/cxf
        export PATH=$CXF_HOME/bin:$PATH
        
2.1.2 Python requirements
    - Jython 2.7.0 (http://www.jython.org)
    - Flask 1.10.1 (http://flask.pocoo.org)
    - Flask-Autodoc 0.1.2 (https://github.com/acoomans/flask-autodoc)
    - isodate 0.5.4 (https://pypi.python.org/pypi/isodate)
    - pytz 2016.6.1 (http://pytz.sourceforge.net/)
    
    1. Install python libraries by pip:
        pip install Flask Flask-Autodoc isodate pytz
    

2.2 Install NSIv2 client library

    1. extract NSIv2 code
        tar zxvf ./lib/aist-nsi2-20150910.tar.gz /opt/
    2. setting nsi2
        cd /opt
        ln -s aist-nsi2-20150910 nsi2
    3. compile nsi2/java/common
        cd /opt/nsi2/java/common
        ant clean; ant
    4. compile nsi2/java/clientapi
        cd /opt/nsi2/java/clientapi/
        ant clean; ant
    5. check existance of jar files:
        ls /opt/nsi2/java/common/build/jar/nsi2_common.jar
        ls /opt/nsi2/java/common/lib/commons-io-2.4.jar
        ls /opt/nsi2/java/common/lib/commons-logging-1.1.1.jar
        ls /opt/nsi2/java/common/lib/jax-ws-catalog.xml
        ls /opt/nsi2/java/common/lib/log4j-1.2.13.jar
        ls /opt/nsi2/java/clientapi/build/jar/nsi2_client.jar
    
    
2.3 Make your self-signed certificates for NSIv2 library:
    
If you use SSL for NSI communication between your requester and NSI Provider Agent (PA) or NSI Aggragate (AG), 
you must prepare a SSL key for the provider server to get replies from PA or AG. 
You must truest the cert of NSI PA/GA. Please read java/clientapi/README for more details.
    
    1. set your CA_DN_JKS, HOST_DN_JKS etc
        nano /opt/nsi2/java/clientapi/certs/Makefile
        
        CN of CA_DN_JKS can be any text you want, but CN of HOST_DN_JKS
        must be the correct (global) IP address or hostname of your host.
        
    2. get CA certificate from NSI AG administrator and put that certificate as ag-ca.cert
        cp <reseived-ca-cert> /opt/nsi2/java/client/certs/ag-ca.cert
        
        That certificate will be added to trust.jks by following command:
        keytool -importcert -noprompt -trustcacerts -file <name of received CA cert> -alias <choose a name> -keystore trust.jks -storepass changeit 
        You can use it to add more certs if required.

    2. make the certificate of your dummy CA
        cd /opt/nsi2/java/clientapi/certs
        make ca
        
    3. make your host certificate (if your IP address is a.b.c.d.)
        make ADDRESS=a.b.c.d certs

        ca.cert : X.509 certificate of your dummy CA
        ca.jks: JKS (Java Key Store) format of ca.cert (including private key)
        host.cert : X.509 certificate of your host signed by your dummy CA
        host.jks : JKS format of host.cert
        host.certreq: certification request file (can be removed)
        trust.jks : trusted certificates
        ag-ca.cert : PA or AG CA certificate 
 
    4. check and fix absolute paths and passwords in config files /opt/nsi2/java/clientapi/etc
        nano /opt/nsi2/java/clientapi/etc/nsi2.properties 
        nano /opt/nsi2/java/clientapi/etc/ServerConfig.xml
    
    5. check and fix <httpj:engine port="29081"> in ServerConfig.xml.
        This port number must be your NSI Requester's port number for HTTPS communications.
        If you want to use several ports for requester, copy-and-paste 
        <httpj:engine-factory> block for each port numbers.
        
        You must open your firewall to pass this port from the Internet.
     
    6. after changing these files, update nsi_client.jar as follows:
        cd /opt/nsi2/java/clientapi
        jar uvf /opt/nsi2/java/clientapi/build/jar/nsi2_client.jar ./etc/nsi2.properties ./etc/ServerConfig.xml 

    7. To connect to someone's NSI provider, you must send your /opt/nsi2/java/clientapi/certs/ca.cert 
        to the admin of the provider to append it in his/her trusted certificates.

    8. If you couldn't connect to a NSI provider because of certification errors
        (i.e. using a self-signed certificate etc.), you must add the certificate of 
        the provider (HTTPS server) like follows (HOSTNAME, PORT are configurable):

        cd /opt/nsi2/java/clientapi/certs
        echo -n | openssl s_client -connect <HOSTNAME>:<PORT> \
                    | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > HOSTNAME.pem
        keytool -import -alias <HOSTNAME> -storepass changeit -noprompt -file HOSTNAME.pem -keystore trust.jks
        
        
        
        
3. Setup

    1. create configuration file from an example
        From root of the project do
        cd ./etc
        cp nsi_connections.conf.example nsi_connections.conf
        
    2. edit nsi_connections.conf

        REST_PORT=9000
        LOG_FILE="../log/nsi_connections.log"

        PROVIDER_NSA = "urn:ogf:network:pionier.net.pl:2013:nsa"
        PROVIDER_URI = "https://banana.man.poznan.pl:8091/nsi/ConnectionProvider"

        REQUESTER_NSA = "urn:ogf:network:pionier.net.pl:2013:nsa"
        REQUESTER_URI = "https://150.254.160.153:29081/nsi2_requester/services/ConnectionRequester"
            
            
            
            
            
4. Start up

Compilation and launching must be done always from ./bin

    1. compile java code
        cd ./bin
        ./compile.sh
        
    2. run HTTP/REST service
        ./start.sh
        
    3. check logging entries
        tail -f ../log/nsi_connections.log
        
    4. check REST API documentation in web browser:
        http://localhost:9000/nsi/connections/doc
        
    5. make testing connections using REST API
        cd ./test
        ./create_conn.sh
        ./delete_last_conn.sh
        
    6. Enable default TCP ports in the firewall:
        - 9000: HTTP REST/API service
        - 29081: NSIv2 SOAP ConnectionRequester service