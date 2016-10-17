from time_utils import time_constrains


def prepare_nsi_attributes(connAttributes):
    params = {}
    params['gid'] = "NSI-REST service"
    params['desc'] = connAttributes['description']
    params['src'] = "%(src_domain)s:%(src_port)s" %  connAttributes
    params['dst'] = "%(dst_domain)s:%(dst_port)s" %  connAttributes
    params['srcvlan'] = int(connAttributes['src_vlan'])
    params['dstvlan'] = int(connAttributes['dst_vlan'])
    params['capacity'] = int(connAttributes['capacity'])
    params['explicit_routes'] = connAttributes.get('explicit_routes')
    
    start_time = connAttributes.get('start_time')
    end_time = connAttributes.get('end_time')
    params['start_sec'], params['end_sec'] = time_constrains(start_time, end_time)
    
    return params
    
    
def characterstics2attributes(characterstics):
    attributes = {}
    for characterstic in characterstics:
        name = characterstic['name']
        value = characterstic['value']
        attributes[name] = value
    return attributes
    
def status2characterstics(status):
    characterstics = []
    for name, value in status.items():
        characterstics.append({'name':name, 'value':value})
    return characterstics