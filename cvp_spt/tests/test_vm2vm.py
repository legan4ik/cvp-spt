#import client
import os
import random
import time
import pytest
from cvp_spt.utils import os_client
from cvp_spt.utils import ssh


def test_vm2vm (openstack_clients, pair, os_resources):
    os_actions = os_client.OSCliActions(openstack_clients)
    try:
        vm1 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(os_resources['zone'],pair[0]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm2 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(os_resources['zone'],pair[0]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm3 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(os_resources['zone'],pair[1]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm4 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net2'],
                                             '{0}:{1}'.format(os_resources['zone'],pair[1]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)
        
        time.sleep(30)
        
        floating_ip1 = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
        floating_ip2 = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
        floating_ip3 = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
        floating_ip4 = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
        
        time.sleep(30)
        
        
        vm1.add_floating_ip(floating_ip1)
        vm2.add_floating_ip(floating_ip2)
        vm3.add_floating_ip(floating_ip3)
        vm4.add_floating_ip(floating_ip4)
        
        time.sleep(5)
        transport1 = ssh.SSHTransport(floating_ip1.ip, 'ubuntu', password='dd',
                                                  private_key=os_resources['keypair'].private_key)
        
        transport1.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
        transport1.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
        transport1.exec_command('nohup iperf -s > file 2>&1 &')
        
        transport2 = ssh.SSHTransport(floating_ip2.ip, 'ubuntu', password='dd',
                                                  private_key=os_resources['keypair'].private_key)
        
        transport2.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
        transport2.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
        transport2.exec_command('nohup iperf -s > file 2>&1 &')
        
        transport3 = ssh.SSHTransport(floating_ip3.ip, 'ubuntu', password='dd',
                                                  private_key=os_resources['keypair'].private_key)
        
        transport3.exec_command('sudo /bin/bash -c "echo \'91.189.88.161        archive.ubuntu.com\' >> /etc/hosts"')
        transport3.exec_command('sudo apt-get update; sudo apt-get install -y iperf')
        transport3.exec_command('nohup iperf -s > file 2>&1 &')
        
        transport4 = ssh.SSHTransport(floating_ip4.ip, 'ubuntu', password='dd',
                                                  private_key=os_resources['keypair'].private_key)
        
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
        
        #openstack_clients.compute.floating_ips.delete(floating_ip1.id)
        #openstack_clients.compute.floating_ips.delete(floating_ip2.id)
        #openstack_clients.compute.floating_ips.delete(floating_ip3.id)
        #openstack_clients.compute.floating_ips.delete(floating_ip4.id)
        
        
        #openstack_clients.network.remove_interface_router(os_resources['router']['id'], {'subnet_id': os_resources['subnet1']})
        #openstack_clients.network.remove_gateway_router(os_resources['router']['id'])
        #openstack_clients.network.delete_router(os_resources['router']['id'])
        
        time.sleep(10)
        
        #openstack_clients.network.delete_subnet(subnet1['id'])
        #openstack_clients.network.delete_network(os_resources['net1']['id'])
        
        #openstack_clients.compute.security_groups.delete(os_resources['sec_group'].id)
        #openstack_clients.compute.keypairs.delete(os_resources['keypair'].name)
        
        #openstack_clients.compute.flavors.delete('spt-test')
    except:
        print "Something went wrong"
