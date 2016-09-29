#! /bin/bash

# Copyright 2016 Poznan Supercomputing and Networking Center
# Copyright 2014-2015 National Institute of Advanced Industrial Science and Technology
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

rm ../log/nsi_connections.log

NSI_HOME=/opt/nsi2/java
LIBS=../src
LIBS=$LIBS:../etc/
LIBS=$LIBS:${NSI_HOME}/clientapi/build/jar/nsi2_client.jar
LIBS=$LIBS:${NSI_HOME}/common/build/jar/aist_upa.jar
LIBS=$LIBS:${NSI_HOME}/common/lib/commons-logging-1.1.1.jar
LIBS=$LIBS:${NSI_HOME}/common/lib/log4j-1.2.13.jar
LIBS=$LIBS:${NSI_HOME}/common/lib/commons-io-2.4.jar
for i in ${CXF_HOME}/lib/*.jar
do
   LIBS=$LIBS:"$i"
done

export NSI_CONNECTIONS_SETTINGS=`pwd`/../etc/nsi_connections.conf

echo "Loading libraries..."
JOPT='-Dpython.cachedir=tmp/cache'
env CLASSPATH=$LIBS jython $JOPT ../src/nsi_connections.py 2>&1
