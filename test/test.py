import httplib
import json

HOSTNAME = 'localhost:9000'

properties = { 'src_domain':'urn:ogf:network:pionier.net.pl:2013:topology',
                    'src_port':'felix-ge-1-0-9',
                    'src_vlan': 1202,
                    'dst_domain':'urn:ogf:network:geant.net:2013:topology',
                    'dst_port':'iMinds__port__to__GEANT',
                    'dst_vlan': 2001,
                    'capacity': 50,
                    'description': 'JRA1T3 testing'}

def test_create_connection():        
    conn = httplib.HTTPConnection(HOSTNAME)
    conn.request(method  = 'POST',
                      url         = "/nsi/connections", 
                      headers  = {"Content-Type": "application/json"},
                      body      = json.dumps(properties)
    )
                      
    response = conn.getresponse()
    print "Response received %s, %s" % (response.status, response.reason)
    conn.close()
    


def test_terminate_connection():
    conn = httplib.HTTPConnection(HOSTNAME)
    conn.request(method  = 'DELETE',
                      url         = "/nsi/connections", 
                      headers  = {},
                      body      = ""
    )
                      
    response = conn.getresponse()
    print "Response received %s, %s" % (response.status, response.reason)
    conn.close()

test_create_connection()
test_terminate_connection()
