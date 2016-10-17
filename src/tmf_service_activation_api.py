
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