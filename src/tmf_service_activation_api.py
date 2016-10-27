
from pprint import pformat
from flask import Blueprint, request, jsonify, abort
from flask import current_app as app


from attribute_utils import characterstics2attributes, prepare_nsi_attributes, status2characterstics

activation_api = Blueprint('activation_api', __name__)
LAST_RESERVATION = None

LOGGER_INTRO = '\n'*3+'*'*80

from nsi_connections import nsi
                                

#----------------------------------------------

@activation_api.route("/api/activation/service", methods=['POST'])
def create_service():
    """
    Create a new data plane connection
    ---
    tags:
        -   NSI connections
    parameters:
        -   in: body
            name: body
            description: NSI service request attributes
            schema:
                id: ConnProperties
                properties:
                    serviceCharacteristic:
                        id: ConnAttributes
                        desciption: requested connection attributes
                            description:  
                                type: string
                                description: description of a new connection
                                required: true
                            src_domain:
                                type: string
                                description: URN identifier of source domain, example urn:ogf:network:pionier.net.pl:2013:topology
                                required: true
                            src_port:
                                type: string
                                description: identifier of the interface of source domain where connection must be terminated
                                required: true
                            src_vlan:
                                type: integer
                                description: VLAN tag to be used on source port
                                required: true
                            dst_domain:
                                type: string
                                description: URN identifier of destination domain, example urn:ogf:network:geant.net:2013:topology
                                required: true
                            dst_port:
                                type: string
                                description: identifier of the interface of destination domain where connection must be terminated
                                required: true
                            dst_vlan: 
                                type: integer
                                description: VLAN tag to be used on destination port
                                required: true   
                            capacity:
                                type: integer
                                description: bandwidth which must be reserved for a new connection
                                required: true 
                            start_time:
                                type: string
                                description: date and time in any when connection should be provisioned, if missing then starts immediatelly, example 2016-09-1T8:32:10+02:00
                                required: false                     
                            end_time:
                                type: string
                                description: date and time in any when connection should be terminated, if missing then no termination planned, example 2016-09-1T8:32:10+02:00
                                required: false 
                            explicit_routes:
                                type: array
                                description: list of port taking part of the connection route
                                items:
                                    type: string
                                    description: URN identifier of ports
                                    required: false 
    responses:
        201:
            description: NSI connection succesfully reserved
            schema:
                id: ConnCreationResp
                properties:
                    service_id: 
                        type: string
                        description: URN identifier of the reserved connection, example urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266
                    serviceCharacteristic:
                        $ref: '#/definitions/ConnAttributes'
        400:
            description: incorrect connection attributes provided
        500:
            description: connection couldn't be reserved in the BoD system or other problem occured
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
        if type(connAttributes) == list:
            connAttributes = characterstics2attributes(connAttributes)
        params = prepare_nsi_attributes(connAttributes)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        app.logger.error("Bad connection attributes. Responging HTTP code: 400")
        abort(400)
        
    try:      
        reservation_id = 'urn:uuid:5f3d47d2-b201-4943-8606-7893d2dc246b' #nsi.reserve(params)
        app.logger.debug("reservation ID=" + reservation_id)
        
        if not reservation_id:
            app.logger.error("Couldn't reserve the connection. Responging HTTP code: 500")
            abort(500)

        #nsi.provision(reservation_id)
        
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
def delete_service(service_id):
    """
    Delete the connection or its reservation
    ---
    tags:
        -   NSI connections
    parameters:
        -   name: service_id
            type: string
            description: URN identifier of the reserved connection, example urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266
    responses:
        200:
            description: deletion was performed
    """
    app.logger.debug(LOGGER_INTRO)
    reservation_id = service_id
    app.logger.info("Deleting connection %s", reservation_id)
    
    try:
        pass
        #~ nsi.release(reservation_id)
        #~ nsi.terminate(reservation_id)
    except:
        import traceback
        app.logger.error(traceback.format_exc())
        
    app.logger.debug("Connection %s delated", reservation_id)
    return "Connection %s has been deleted\n" % reservation_id, 202
 
#----------------------------------------------    
    
@activation_api.route("/api/activation/service/<service_id>", methods=['GET'])
def get_service(service_id):
    """
    Query status of the connection or its reservation
    ---
    tags:
        -   NSI connections
    parameters:
        -   name: service_id
            type: string
            description: URN identifier of the reserved connection, example urn:uuid:7ebc5196-9293-4346-b847-d2fa123b5266
    responses:
        200:
            description: NSI service found
            schema:
                properties:
                    serviceCharacteristic:
                        id: ConnStatus
                        properties:
                            active:
                                type: string
                                description: true if data plane for the connection provisioned and can traffic be send
                                default: [false', 'true'] 
                                required: true
                            connectionId:
                                type: string
                                description: URN identifier of the reserved connection
                                required: true
                            description:
                                type: string
                                description: description of the connection 
                                required: true
                            globalReservationId:
                                type: string
                                description: URN identifier used to correlate individually created connections 
                                required: true
                            lifecycleState:
                                type: string
                                description: state values for the reservation lifecycle
                                default: ['CREATED', 'FAILED', 'PASSED_END_TIME', 'TERMINATING', 'TERMINATED'] 
                                required: true
                            notificationId:
                                type: integer
                                description: identifier of the last notification send for given connection
                                required: true
                            provisionState:
                                type: string
                                description: state values for the data plane resources provisioning
                                default: ['RELEASED', 'PROVISIONING', 'PROVISIONED', 'RELEASING']
                                required: true
                            requesterNSA:
                                type: string
                                description: URN identifier of requester NSA 
                                required: true
                            reservationState:
                                type: string
                                description: transitions of the reservation lifecycle
                                default: ['RESERVE_START', 'RESERVE CHECKING', 'RESERVE_FAILED', 'RESERVE_ABORTING', 'RESERVE_HELD', 'RESERVE_COMMITTING', 'RESERVE_TIMEOUT']
                                required: true
                            version:
                                type: integer
                                description:  version of the reservation instantiated in the data plan
                                required: true
                            versionConsistent:
                                type: string
                                description: consistency of reservation versions for NSI AG
                                default: ['false', 'true']
                                required: true
        404: 
            description: connection was not found 
        500:
            description: query request could not be sent to NSI API
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