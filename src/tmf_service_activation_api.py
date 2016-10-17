
from pprint import pformat
from flask import Blueprint, request, jsonify, abort
from flask import current_app as app


from attribute_utils import characterstics2attributes, prepare_nsi_attributes, status2characterstics

activation_api = Blueprint('activation_api', __name__)
LAST_RESERVATION = None

LOGGER_INTRO = '\n'*3+'*'*80

from nsi_connections import nsi, auto
                                

#----------------------------------------------

@activation_api.route("/api/activation/service", methods=['POST'])
@auto.doc()
def create_service():
    """Create a new data plane connection following TMF service activation API.
    
    Data:  service request in JSON format containing attributes in 'serviceCharacteristic' field:
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
        1. HTTP code 201 and JSON object being a copy of service request plus a new attribute:
            - service_id: [string] URN identifier of the reserved connection (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
        2. HTTP code 400 when incorrect connection attributes provided
        3. HTTP code 500 when a connection couldn't be reserved in the BoD system or other problem occured
    """
    app.logger.debug(LOGGER_INTRO)
    
    # service is not suporting immediate asynchronous responses (see TMF Activation REST API spec) 
    if request.headers.get('Expect') == '202-accepted':
        abort(417)  
    
    connAttributes = request.get_json() 
    if connAttributes:
        connAttributes = connAttributes.get('serviceCharacteristic')
        app.logger.info("Creating connection with attributes \n%s", pformat(connAttributes))
    if not connAttributes:
        app.logger.error("Responging HTTP code: 400")
        abort(400)
    
    try:
        connAttributes = characterstics2attributes(connAttributes)
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
        
        connAttributes = request.get_json() 
        connAttributes['id'] = reservation_id
        
        return jsonify(connAttributes, 201, {'location': '/api/activation/service/%s' % reservation_id})
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        app.logger.error("Responging HTTP code: 500")
        abort(500)

#----------------------------------------------    
    
@activation_api.route("/api/activation/service/<service_id>", methods=['DELETE'])
@auto.doc()
def delete_service(service_id):
    """Delete the connection or its reservation
    
    Arguments:
        - service_id: [string] URN identifier of the reserved connection (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
        
    Returns:
        1. HTTP code 200 for all conditions
    """
    app.logger.debug(LOGGER_INTRO)
    reservation_id = service_id
    app.logger.info("Deleting connection %s", reservation_id)
    
    try:
        nsi.release(reservation_id)
        nsi.terminate(reservation_id)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        
    app.logger.debug("Connection %s delated", reservation_id)
    return "Connection %s has been deleted\n" % reservation_id, 202
 
#----------------------------------------------    
    
@activation_api.route("/api/activation/service/<service_id>", methods=['GET'])
@auto.doc()
def get_service(service_id):
    """Query status of the connection or its reservation
    
    Arguments:
        - service_id: [string] URN identifier of the reserved connection (eg.: 'urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266')
        
    Returns:
        1. HTTP code 200 and JSON object containing service information stored in 'serviceCharacteristic' field:
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
    reservation_id = service_id
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
    serviceDesc = {}
    serviceDesc['serviceCharacteristic'] = status2characterstics(status)
    serviceDesc['id'] = reservation_id
    
    return jsonify(serviceDesc)