#import client
import os
import random
import time
import pytest
from cvp_spt.utils import os_client
from cvp_spt.utils import ssh


def test_vm2vm ():
    openstack_clients = os_client.OfficialClientManager(
            username=os.environ['OS_USERNAME'],
            password=os.environ['OS_PASSWORD'],
            tenant_name=os.environ['OS_TENANT_NAME'],
            auth_url=os.environ['OS_AUTH_URL'],
            cert=False,
            domain='Default',
        )
    
    os_actions = os_client.OSCliActions(openstack_clients)
    
    zone = 'nova'
    
    hosts = [service.host for service in openstack_clients.compute.services.list() if service.zone != 'internal']
    
    host1 = hosts[0]
    host2 = hosts[1]
    
    image_id = str([image.id for image in openstack_clients.image.images.list(name='Ubuntu')][0])
    
    if not image_id:
        print "No image ID. Exiting"
        exit()
    
    flavor_id = str([flavor.id for flavor in openstack_clients.compute.flavors.list() if flavor.name == 'spt-test'][0])
    
    if not flavor_id:
        openstack_clients.compute.flavors.create('spt-test',1536,1,3,0)
    import pdb;pdb.set_trace()
    sec_group = os_actions.create_sec_group()
    keypair = openstack_clients.compute.keypairs.create('test-{}'.format(random.randrange(100, 999)))
    net1 = os_actions.create_network_resources()
    ext_net = os_actions.get_external_network()
    adm_tenant = os_actions.get_admin_tenant()
    router = os_actions.create_router(ext_net,adm_tenant.id)
    net2 = os_actions.create_network(adm_tenant)
    subnet2 = os_actions.create_subnet(net2,adm_tenant,'10.2.7.0/24')
    for subnet in openstack_clients.network.list_subnets()['subnets']:
        if subnet['network_id'] == net1['id']:
            subnet1 = subnet['id']
    
    openstack_clients.network.add_interface_router(router['id'],{'subnet_id': subnet1})
    openstack_clients.network.add_interface_router(router['id'],{'subnet_id': subnet2['id']})
    
    vm1 = os_actions.create_basic_server(image_id,flavor_id,net1,'{0}:{1}'.format(zone,host1),[sec_group.name], keypair.name)
    vm2 = os_actions.create_basic_server(image_id,flavor_id,net1,'{0}:{1}'.format(zone,host1),[sec_group.name], keypair.name)
    vm3 = os_actions.create_basic_server(image_id,flavor_id,net1,'{0}:{1}'.format(zone,host2),[sec_group.name], keypair.name)
    vm4 = os_actions.create_basic_server(image_id,flavor_id,net2,'{0}:{1}'.format(zone,host2),[sec_group.name], keypair.name)
    
    time.sleep(30)
    
    floating_ip1 = openstack_clients.compute.floating_ips.create(ext_net['name'])
    floating_ip2 = openstack_clients.compute.floating_ips.create(ext_net['name'])
    floating_ip3 = openstack_clients.compute.floating_ips.create(ext_net['name'])
    floating_ip4 = openstack_clients.compute.floating_ips.create(ext_net['name'])
    
    time.sleep(30)
    
    
    vm1.add_floating_ip(floating_ip1)
    vm2.add_floating_ip(floating_ip2)
    vm3.add_floating_ip(floating_ip3)
    vm4.add_floating_ip(floating_ip4)
    
    time.sleep(5)
    transport1 = ssh.SSHTransport(floating_ip1.ip, 'ubuntu', password='dd',
                                              private_key=keypair.private_key)
    
    transport1.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
    transport1.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
    transport1.exec_command('nohup iperf -s > file 2>&1 &')
    
    transport2 = ssh.SSHTransport(floating_ip2.ip, 'ubuntu', password='dd',
                                              private_key=keypair.private_key)
    
    transport2.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
    transport2.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
    transport2.exec_command('nohup iperf -s > file 2>&1 &')
    
    transport3 = ssh.SSHTransport(floating_ip3.ip, 'ubuntu', password='dd',
                                              private_key=keypair.private_key)
    
    transport3.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
    transport3.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
    transport3.exec_command('nohup iperf -s > file 2>&1 &')
    
    transport4 = ssh.SSHTransport(floating_ip4.ip, 'ubuntu', password='dd',
                                              private_key=keypair.private_key)
    
    transport4.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
    transport4.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
    transport4.exec_command('nohup iperf -s > file 2>&1 &')
    
    vm1_private = vm1.addresses[vm1.addresses.keys()[0]][0]['addr']
    vm2_private = vm2.addresses[vm2.addresses.keys()[0]][0]['addr']
    vm3_private = vm3.addresses[vm3.addresses.keys()[0]][0]['addr']
    vm4_private = vm4.addresses[vm4.addresses.keys()[0]][0]['addr']
    
    result1 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm2_private))
    print ' '.join(result1.split()[-2::])
    result2 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm3_private))
    print ' '.join(result2.split()[-2::])
    result3 = transport1.exec_command('iperf -c {} -P 10 | tail -n 1'.format(vm3_private))
    print ' '.join(result3.split()[-2::])
    result4 = transport1.exec_command('iperf -c {} | tail -n 1'.format(floating_ip3.ip))
    print ' '.join(result4.split()[-2::])
    result5 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm4_private))
    print ' '.join(result5.split()[-2::])
    
    openstack_clients.compute.servers.delete(vm1)
    openstack_clients.compute.servers.delete(vm2)
    openstack_clients.compute.servers.delete(vm3)
    openstack_clients.compute.servers.delete(vm4)
    
    openstack_clients.compute.floating_ips.delete(floating_ip1.ip)
    openstack_clients.compute.floating_ips.delete(floating_ip2.ip)
    openstack_clients.compute.floating_ips.delete(floating_ip3.ip)
    openstack_clients.compute.floating_ips.delete(floating_ip4.ip)
    
    
    openstack_clients.network.remove_interface_router(router['id'], {'subnet_id': subnet1})
    openstack_clients.network.remove_gateway_router(router['id'])
    openstack_clients.network.delete_router(router['id'])
    
    time.sleep(10)
    
    #openstack_clients.network.delete_subnet(subnet1['id'])
    openstack_clients.network.delete_network(net1['id'])
    
    openstack_clients.compute.security_groups.delete(sec_group.id)
    openstack_clients.compute.keypairs.delete(keypair.name)
    
    openstack_clients.compute.flavors.delete('spt-test')
