# Copyright 2016 Poznan Supercomputing and Networking Center (PSNC)
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

import logging, os, time
from logging.handlers import RotatingFileHandler
from pprint import pformat

from flask import Flask, request, jsonify, abort
from flasgger import Swagger

import nsi2interface
from attribute_utils import prepare_nsi_attributes

#----------------------------------------------------------

app = Flask(__name__)
Swagger(app)                               

app.config.from_envvar('NSI_CONNECTIONS_SETTINGS')  # config file name declared in environment variable (see start script)

handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=200000000, backupCount=5)
handler.setFormatter(logging.Formatter("%(levelname)s - %(asctime)s - %(name)s - %(message)s"))
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

werkzeug_loggger = logging.getLogger('werkzeug')
werkzeug_loggger.addHandler(handler)

utils_loggger = logging.getLogger('time_utils')
utils_loggger.addHandler(handler)


nsi = nsi2interface.NSI(app.config['PROVIDER_NSA'], app.config['PROVIDER_URI'], 
                                app.config['REQUESTER_NSA'], app.config['REQUESTER_URI'])

LOGGER_INTRO = '\n'*3+'*'*80

from tmf_service_activation_api import activation_api
app.register_blueprint(activation_api)



#----------------------------------------------
@app.route("/nsi/connections", methods=['POST'])
def create_connection():
    """Create a new data plane connection
    
    Data:  connection attributes in JSON format:
        - description:  [string] description of a new connection (eg.: 'required by Microsoft Azure service 3232-4345')
        - src_domain: [string] URN identifier of source domain (eg.: 'urn:ogf:network:pionier.net.pl:2013:topology')
        - src_port: [string] identifier of the interface of source domain where connection must be terminated (eg.: 'felix-ge-1-0-9')
        - src_vlan: [int] VLAN tag to be used on source port (eg.: 1202)
        - dst_domain: [string] URN identifier of destination domain (eg.: urn:ogf:network:geant.net:2013:topology')
        - dst_port: [string] identifier of the interface of destination domain where connection must be terminated (eg.: 'iMinds__port__to__GEANT')
        - dst_vlan: [int] VLAN tag to be used on destination port (eg.: 2001)
        - capacity: [int] bandwidth which must be reserved for a new connection
        - start_time: (optional) [string] date and time in any when connection should be provisioned, if missing then starts immediatelly (eg.: '2016-09-1T8:32:10+02:00') [See #1]
        - end_time: (optional) [string] date and time in any when connection should be terminated, if missing then no termination planned (eg.: '2017-09-1T13:00:00+02:00') [See #1]
        - explicit_routes: (optional) [list of strings] URN identifiers of STP ports taking part of the connection route 
        
        #1 Date and time format must be formated in ISO 8601 date/time format. Examples: 
            - 'yyyy-mm-ddThh:mm:ssZ'
            - 'yyyy-mm-ddThh:mm:ss+hh:mm'  
            - 'yyyy-mm-ddThh:mm:ss-hh:mm'
            During processing of date/time after calling this REST function is always translated from localtime zone to UTC timezone. 
            
    Returns: 
        1. HTTP code 201 and JSON object containing one attribute
            - reservation_id: [string] URN identifier of the reserved connection (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
        2. HTTP code 400 when incorrect connection attributes provided
        3. HTTP code 500 when a connection couldn't be reserved in the BoD system or other problem occured
    """
    app.logger.debug(LOGGER_INTRO)
    
    connAttributes = request.get_json() 
    app.logger.info("Creating connection with attributes \n%s", pformat(connAttributes))
    if not connAttributes:
        app.logger.error("Responging HTTP code: 400")
        abort(400)
    
    try:
        params = prepare_nsi_attributes(connAttributes)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        app.logger.error("Bad connection attributes. Responging HTTP code: 400")
        abort(400)
        
    try:      
        reservation_id = nsi.reserve(params)
        app.logger.debug("reservation ID=" + reservation_id)
        
        if not reservation_id:
            app.logger.error("Couldn't reserve the connection. Responging HTTP code: 500")
            abort(500)

        nsi.provision(reservation_id)
        
        app.logger.debug("Connection %s created" % reservation_id)
        
        global LAST_RESERVATION
        LAST_RESERVATION = reservation_id
        
        return jsonify({'reservation_id': reservation_id}), 201, {'location': '/nsi/connection/%s' % reservation_id}
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        app.logger.error("Responging HTTP code: 500")
        abort(500)


#----------------------------------------------
    
@app.route("/nsi/connections/<reservation_id>", methods=['DELETE'])
def delete_connection(reservation_id):
    """Delete the connection or its reservation
    
    Arguments:
        - reservation_id: [string] URN identifier of the reserved connection (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
        
    Returns:
        1. HTTP code 200 for all conditions
    """
    app.logger.debug(LOGGER_INTRO)
    app.logger.info("Deleting connection %s", reservation_id)
    
    try:
        nsi.release(reservation_id)
        nsi.terminate(reservation_id)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        
    app.logger.debug("Connection %s delated", reservation_id)
    return "Connection %s has been deleted\n" % reservation_id, 200
    
    
#----------------------------------------------

@app.route("/nsi/connections", methods=['DELETE'])
def delete_last_connection():
    """Delete lastly created connection or its reservation (for testing purposes only)"""
    app.logger.debug(LOGGER_INTRO)
    app.logger.info("Deleting last connection")
    
    try:
        nsi.release(LAST_RESERVATION)
        nsi.terminate(LAST_RESERVATION)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        
    app.logger.debug("Connection %s deleted", LAST_RESERVATION)
    return "Connection %s deleted\n" % LAST_RESERVATION, 200
    
    
#----------------------------------------------

@app.route("/nsi/connections/<reservation_id>", methods=['GET'])
def query_connection(reservation_id):
    """Query status of the connection or its reservation
    
    Arguments:
        - reservation_id: [string] URN identifier of the reserved connection (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
        
    Returns:
        1. HTTP code 200 and JSON object containing status information about the connection:
            - active: ["false", "true"] is data plane for the connection provisioned (can traffic be send)
            - connectionId: [string] URN identifier of the reserved connection
            - description:  [string] description of the connection 
            - globalReservationId: [string] URN identifier used to correlate individually created connections
            - lifecycleState: ["CREATED", "FAILED", "PASSED_END_TIME", "TERMINATING", "TERMINATED"] state values for the reservation lifecycle
            - notificationId: [int] identifier of the last notification send for given connection
            - provisionState: ["RELEASED", "PROVISIONING", "PROVISIONED", "RELEASING"] state values for the data plane resources provisioning
            - requesterNSA: [string] URN identifier of requester NSA
            - reservationState: ["RESERVE_START", "RESERVE CHECKING", "RESERVE_FAILED", "RESERVE_ABORTING", "RESERVE_HELD", "RESERVE_COMMITTING", "RESERVE_TIMEOUT"] transitions of the reservation lifecycle
            - version: [int] version of the reservation instantiated in the data plan
            - versionConsistent:  ["true", "false"] consistency of reservation versions for NSI AG
        2. HTTP code 404 when connection was not found 
        3. HTTP code 500 when query request could not be sent to NSI API
    """
    app.logger.debug(LOGGER_INTRO)
    app.logger.debug("Query connection %s", reservation_id)
    status = {}
    
    try:
        status = nsi.query(reservation_id)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        abort(500)
        
    if not status:
        app.logger.debug("Connection not found")
        abort(404)
        
    app.logger.debug("Connection status is \n%s", pformat(status))
    return jsonify(status)
   
    
 #############################################################   

if __name__ == "__main__":
    app.logger.info("Running HTTP REST API on port %i", app.config['REST_PORT'])
    app.run(host="0.0.0.0", port=app.config['REST_PORT'])

    

    
