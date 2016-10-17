#!/bin/bash

curl -H "Content-Type: application/json" \
      -X POST -d '{ "serviceCharacteristic" : [ 
      {"name":"description", "value":"JRA1T3 testing"},
      {"name":"src_domain", "value":"urn:ogf:network:pionier.net.pl:2013:topology"},
      {"name":"src_port", "value":"felix-ge-1-0-9"},
      {"name":"src_vlan", "value":1202},
      {"name":"dst_domain", "value":"urn:ogf:network:geant.net:2013:topology"},
      {"name":"dst_port", "value":"iMinds__port__to__GEANT"},
      {"name":"dst_vlan", "value":2001},
      {"name":"capacity", "value":50} ] }' \
      http://localhost:9000/api/activation/service




