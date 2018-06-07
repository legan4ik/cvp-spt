import pytest
import cvp_spt.utils as utils
import random
import time
from cvp_spt.utils import os_client

@pytest.fixture(scope='session')
def local_salt_client():
    return utils.init_salt_client()

nodes = utils.get_pairs()

@pytest.fixture(scope='session', params=nodes.values(), ids=nodes.keys())
def pair(request):
    return request.param

@pytest.fixture(scope='session')
def openstack_clients(local_salt_client):
    nodes_info = local_salt_client.cmd(
        'keystone:server', 'pillar.get',
        ['keystone:server'],
        expr_form='pillar')
    keystone = nodes_info[nodes_info.keys()[0]]
    url = 'http://{0}:{1}/v2.0'.format(keystone['bind']['private_address'],
                                       keystone['bind']['private_port'])
    return os_client.OfficialClientManager(
            username=keystone['admin_name'],
            password=keystone['admin_password'],
            tenant_name=keystone['admin_tenant'],
            auth_url=url,
            cert=False,
            domain='Default',
        )

@pytest.fixture(scope='session')
def os_resources(openstack_clients):
    os_actions = os_client.OSCliActions(openstack_clients)
    zone = 'nova'
    #import pdb;pdb.set_trace()
    #hosts = [service.host for service in openstack_clients.compute.services.list() if service.zone != 'internal']
    
    #host1 = hosts[0]
    #host2 = hosts[1]
    os_resource = {}
    os_resource['zone'] = zone 
    os_resource['image_id'] = str([image.id for image in openstack_clients.image.images.list(name='Ubuntu')][0])
    
    if not os_resource['image_id']:
        print "No image ID. Exiting"
        exit()
    
    os_resource['flavor_id'] = [flavor.id for flavor in openstack_clients.compute.flavors.list() if flavor.name == 'spt-test']
    if not os_resource['flavor_id']:
        os_resource['flavor_id'] = openstack_clients.compute.flavors.create('spt-test',1536,1,3,0).id
    else:
        os_resource['flavor_id'] = str(os_resource['flavor_id'][0])

    os_resource['sec_group'] = os_actions.create_sec_group()
    os_resource['keypair'] = openstack_clients.compute.keypairs.create('test-{}'.format(random.randrange(100, 999)))
    os_resource['net1'] = os_actions.create_network_resources()
    os_resource['ext_net'] = os_actions.get_external_network()
    adm_tenant = os_actions.get_admin_tenant()
    os_resource['router'] = os_actions.create_router(os_resource['ext_net'],adm_tenant.id)
    os_resource['net2'] = os_actions.create_network(adm_tenant)
    os_resource['subnet2'] = os_actions.create_subnet(os_resource['net2'],adm_tenant,'10.2.7.0/24')
    for subnet in openstack_clients.network.list_subnets()['subnets']:
        if subnet['network_id'] == os_resource['net1']['id']:
            os_resource['subnet1'] = subnet['id']
    
    openstack_clients.network.add_interface_router(os_resource['router']['id'],{'subnet_id': os_resource['subnet1']})
    openstack_clients.network.add_interface_router(os_resource['router']['id'],{'subnet_id': os_resource['subnet2']['id']})
    #return os_resource
    yield os_resource
    time.sleep(5)
    openstack_clients.network.remove_interface_router(os_resource['router']['id'], {'subnet_id': os_resource['subnet1']})
    openstack_clients.network.remove_interface_router(os_resource['router']['id'], {'subnet_id': os_resource['subnet2']['id']})
    openstack_clients.network.remove_gateway_router(os_resource['router']['id'])
    time.sleep(5)
    openstack_clients.network.delete_router(os_resource['router']['id'])
    
    time.sleep(10)
    
    #openstack_clients.network.delete_subnet(subnet1['id'])
    openstack_clients.network.delete_network(os_resource['net1']['id'])
    openstack_clients.network.delete_network(os_resource['net2']['id'])
    
    openstack_clients.compute.security_groups.delete(os_resource['sec_group'].id)
    openstack_clients.compute.keypairs.delete(os_resource['keypair'].name)
    
    openstack_clients.compute.flavors.delete(os_resource['flavor_id'])
