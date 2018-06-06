import os
import yaml
import requests
import re
import sys, traceback
import itertools


class salt_remote:
    def cmd(self, tgt, fun, param=None, expr_form=None, tgt_type=None):
        config = get_configuration()
        headers = {'Accept': 'application/json'}
        login_payload = {'username': config['SALT_USERNAME'],
                         'password': config['SALT_PASSWORD'], 'eauth': 'pam'}
        accept_key_payload = {'fun': fun, 'tgt': tgt, 'client': 'local',
                              'expr_form': expr_form, 'tgt_type': tgt_type,
                              'timeout': config['salt_timeout']}
        if param:
            accept_key_payload['arg'] = param

        try:
            login_request = requests.post(os.path.join(config['SALT_URL'],
                                                       'login'),
                                          headers=headers, data=login_payload)
            if login_request.ok:
                request = requests.post(config['SALT_URL'], headers=headers,
                                        data=accept_key_payload,
                                        cookies=login_request.cookies)
                return request.json()['return'][0]
        except Exception:
            print "\033[91m\nConnection to SaltMaster " \
                  "was not established.\n" \
                  "Please make sure that you " \
                  "provided correct credentials.\033[0m\n"
            traceback.print_exc(file=sys.stdout)
            sys.exit()


def init_salt_client():
    local = salt_remote()
    return local


def get_active_nodes(test=None):
    config = get_configuration()
    local_salt_client = init_salt_client()

    skipped_nodes = config.get('skipped_nodes') or []
    if test:
        testname = test.split('.')[0]
        if 'skipped_nodes' in config.get(testname).keys():
            skipped_nodes += config.get(testname)['skipped_nodes'] or []
    if skipped_nodes != ['']:
        print "\nNotice: {0} nodes will be skipped".format(skipped_nodes)
        nodes = local_salt_client.cmd(
            '* and not ' + list_to_target_string(skipped_nodes, 'and not'),
            'test.ping',
            expr_form='compound')
    else:
        nodes = local_salt_client.cmd('*', 'test.ping')
    return nodes


def get_pairs():
    result = {}
    #import pdb;pdb.set_trace()
    if os.environ['NODES']:
        nodes = os.environ['NODES'].split(',')
        if len(nodes) %2 != 0:
            nodes.pop(1)
        pairs = zip(*[iter(nodes)]*2)

    for pair in pairs:
        result[pair[0]+'<>'+pair[1]] = pair
    return result


def get_configuration():
    """function returns configuration for environment
    and for test if it's specified"""
    global_config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../global_config.yaml")
    with open(global_config_file, 'r') as file:
        global_config = yaml.load(file)
    for param in global_config.keys():
        if param in os.environ.keys():
            if ',' in os.environ[param]:
                global_config[param] = []
                for item in os.environ[param].split(','):
                    global_config[param].append(item)
            else:
                global_config[param] = os.environ[param]

    return global_config
