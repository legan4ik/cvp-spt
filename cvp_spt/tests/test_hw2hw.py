#!/usr/bin/env python
import itertools
import re
import os
import yaml
import requests
from cvp_spt import utils
from cvp_spt.utils import helpers
from netaddr import IPNetwork, IPAddress


def test_hw2hw (local_salt_client,hw_pair):
    helpp = helpers.helpers(local_salt_client)
    config = utils.get_configuration()
    nodes = local_salt_client.cmd(expr_form='compound', tgt=str(hw_pair[0]+' or '+hw_pair[1]),
                                  fun='network.interfaces')
    nets = config.get('networks')
    local_salt_client.cmd(expr_form='compound', tgt=str(hw_pair[0]+' or '+hw_pair[1]),
                          fun='cmd.run', param=['nohup iperf -s > file 2>&1 &'])
    global_results = []
    for net in nets:
        for interf in nodes[hw_pair[0]]:
            if 'inet' not in nodes[hw_pair[0]][interf].keys():
                continue
            ip = nodes[hw_pair[0]][interf]['inet'][0]['address']
            if (IPAddress(ip) in IPNetwork(nets[net])) and (nodes[hw_pair[0]][interf]['inet'][0]['broadcast']):
                for interf2 in nodes[hw_pair[1]]:
                    if 'inet' not in nodes[hw_pair[1]][interf2].keys():
                        continue
                    ip2 = nodes[hw_pair[1]][interf2]['inet'][0]['address']
                    if (IPAddress(ip2) in IPNetwork(nets[net])) and (nodes[hw_pair[1]][interf2]['inet'][0]['broadcast']):
                        print "Will IPERF between {0} and {1}".format(ip,ip2)
                        try:
                            helpp.start_iperf_between_hosts(global_results, hw_pair[0], hw_pair[1],
                                                                      ip, ip2, net)
                            print "Measurement between {} and {} " \
                                   "has been finished".format(hw_pair[0],
                                                              hw_pair[1])
                        except Exception as e:
                                print "Failed for {0} {1}".format(
                                              hw_pair[0], hw_pair[1])
                                print e
    local_salt_client.cmd(expr_form='compound', tgt=str(hw_pair[0]+' or '+hw_pair[1]),
                          fun='cmd.run', param=['killall -9 iperf'])
    helpp.draw_table_with_results(global_results)
