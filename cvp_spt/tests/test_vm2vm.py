import os
import random
import time
import pytest
from cvp_spt.utils import os_client
from cvp_spt.utils import ssh


def test_vm2vm (openstack_clients, pair, os_resources):
    os_actions = os_client.OSCliActions(openstack_clients)
    try:
        zone1 = [service.zone for service in openstack_clients.compute.services.list() if service.host == pair[0]]
        zone2 = [service.zone for service in openstack_clients.compute.services.list() if service.host == pair[1]]
        vm1 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(zone1[0],pair[0]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm2 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(zone1[0],pair[0]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm3 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(zone2[0],pair[1]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm4 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net2'],
                                             '{0}:{1}'.format(zone2[0],pair[1]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)
        
        time.sleep(30)
        vm_info = []
        vms = []
        vms.extend([vm1,vm2,vm3,vm4])
        fips = []
        for i in range(4):
            fip = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
            fips.append(fip.id)
            vms[i].add_floating_ip(fip)
            private_address = vms[i].addresses[vms[i].addresses.keys()[0]][0]['addr']
            time.sleep(45)
            ssh.prepare_iperf(fip.ip,private_key=os_resources['keypair'].private_key)
            vm_info.append({'vm': vms[i], 'fip': fip.ip, 'private_address': private_address})   
        
        transport1 = ssh.SSHTransport(vm_info[0]['fip'], 'ubuntu', password='dd', private_key=os_resources['keypair'].private_key)
        
        result1 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm_info[1]['private_address']))
        print ' '.join(result1.split()[-2::])
        result2 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm_info[2]['private_address']))
        print ' '.join(result2.split()[-2::])
        result3 = transport1.exec_command('iperf -c {} -P 10 | tail -n 1'.format(vm_info[2]['private_address']))
        print ' '.join(result3.split()[-2::])
        result4 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm_info[2]['fip']))
        print ' '.join(result4.split()[-2::])
        result5 = transport1.exec_command('iperf -c {} | tail -n 1'.format(vm_info[3]['private_address']))
        print ' '.join(result5.split()[-2::])

        for vm in vms:
            openstack_clients.compute.servers.delete(vm)
        for fip in fips:
            openstack_clients.compute.floating_ips.delete(fip)
        
    except:
        print "Something went wrong"
        for vm in vms:
            openstack_clients.compute.servers.delete(vm)
        for fip in fips:
            openstack_clients.compute.floating_ips.delete(fip)
