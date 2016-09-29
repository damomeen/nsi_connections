#!/bin/bash

curl -H "Content-Type: application/json" \
      -X POST -d '{"description":"JRA1T3 testing","src_domain":"urn:ogf:network:pionier.net.pl:2013:topology","src_port":"felix-ge-1-0-9","src_vlan":1202,"dst_domain":"urn:ogf:network:geant.net:2013:topology","dst_port":"iMinds__port__to__GEANT","dst_vlan":2001,"capacity":50}' \
      http://localhost:9000/nsi/connections




