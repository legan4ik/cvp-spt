from cinderclient import client as cinder_client
from glanceclient import client as glance_client
from keystoneauth1 import identity as keystone_identity
from keystoneauth1 import session as keystone_session
from keystoneclient import client as keystone_client
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as novaclient

import os
import random
import time


class OfficialClientManager(object):
    """Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    CINDERCLIENT_VERSION = 3
    GLANCECLIENT_VERSION = 2
    KEYSTONECLIENT_VERSION = 2, 0
    NEUTRONCLIENT_VERSION = 2
    NOVACLIENT_VERSION = 2
    INTERFACE = 'admin'
    if "OS_ENDPOINT_TYPE" in os.environ.keys():
        INTERFACE = os.environ["OS_ENDPOINT_TYPE"]

    def __init__(self, username=None, password=None,
                 tenant_name=None, auth_url=None, endpoint_type="internalURL",
                 cert=False, domain="Default", **kwargs):
        self.traceback = ""

        self.client_attr_names = [
            "auth",
            "compute",
            "network",
            "volume",
            "image",
        ]
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self.project_name = tenant_name
        self.auth_url = auth_url
        self.endpoint_type = endpoint_type
        self.cert = cert
        self.domain = domain
        self.kwargs = kwargs

        # Lazy clients
        self._auth = None
        self._compute = None
        self._network = None
        self._volume = None
        self._image = None

    @classmethod
    def _get_auth_session(cls, username=None, password=None,
                          tenant_name=None, auth_url=None, cert=None,
                          domain='Default'):
        if None in (username, password, tenant_name):
            print(username, password, tenant_name)
            msg = ("Missing required credentials for identity client. "
                   "username: {username}, password: {password}, "
                   "tenant_name: {tenant_name}").format(
                       username=username,
                       password=password,
                       tenant_name=tenant_name, )
            raise msg

        if cert and "https" not in auth_url:
            auth_url = auth_url.replace("http", "https")

        if cls.KEYSTONECLIENT_VERSION == (2, 0):
            #auth_url = "{}{}".format(auth_url, "v2.0/")
            auth = keystone_identity.v2.Password(
                username=username, password=password, auth_url=auth_url,
                tenant_name=tenant_name)
        else:
            auth_url = "{}{}".format(auth_url, "v3/")
            auth = keystone_identity.v3.Password(
                auth_url=auth_url, user_domain_name=domain,
                username=username, password=password,
                project_domain_name=domain, project_name=tenant_name)

        auth_session = keystone_session.Session(auth=auth, verify=cert)
        # auth_session.get_auth_headers()
        return auth_session

    @classmethod
    def get_auth_client(cls, username=None, password=None,
                        tenant_name=None, auth_url=None, cert=None,
                        domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        keystone = keystone_client.Client(
            cls.KEYSTONECLIENT_VERSION, session=session, **kwargs)
        keystone.management_url = auth_url
        return keystone

    @classmethod
    def get_compute_client(cls, username=None, password=None,
                           tenant_name=None, auth_url=None, cert=None,
                           domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'compute'
        compute_client = novaclient.Client(
            version=cls.NOVACLIENT_VERSION, session=session,
            service_type=service_type, os_cache=False, **kwargs)
        return compute_client

    @classmethod
    def get_network_client(cls, username=None, password=None,
                           tenant_name=None, auth_url=None, cert=None,
                           domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'network'
        return neutron_client.Client(
            service_type=service_type, session=session, interface=cls.INTERFACE, **kwargs)

    @classmethod
    def get_volume_client(cls, username=None, password=None,
                          tenant_name=None, auth_url=None, cert=None,
                          domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'volume'
        return cinder_client.Client(
            version=cls.CINDERCLIENT_VERSION,
            service_type=service_type,
            interface=cls.INTERFACE,
            session=session, **kwargs)

    @classmethod
    def get_image_client(cls, username=None, password=None,
                         tenant_name=None, auth_url=None, cert=None,
                         domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'image'
        return glance_client.Client(
            version=cls.GLANCECLIENT_VERSION,
            service_type=service_type,
            session=session, interface=cls.INTERFACE,
            **kwargs)

    @property
    def auth(self):
        if self._auth is None:
            self._auth = self.get_auth_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._auth

    @property
    def compute(self):
        if self._compute is None:
            self._compute = self.get_compute_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._compute

    @property
    def network(self):
        if self._network is None:
            self._network = self.get_network_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._network

    @property
    def volume(self):
        if self._volume is None:
            self._volume = self.get_volume_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._volume

    @property
    def image(self):
        if self._image is None:
            self._image = self.get_image_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain
            )
        return self._image

class OSCliActions(object):
    def __init__(self, os_clients):
        self.os_clients = os_clients

    def get_admin_tenant(self):
        return self.os_clients.auth.tenants.find(name="admin")

    # TODO: refactor
    def get_cirros_image(self):
        images_list = list(self.os_clients.image.images.list(name='TestVM'))
        if images_list:
            image = images_list[0]
        else:
            image = self.os_clients.image.images.create(
                name="TestVM",
                disk_format='qcow2',
                container_format='bare')
            with file_cache.get_file(settings.CIRROS_QCOW2_URL) as f:
                self.os_clients.image.images.upload(image.id, f)
        return image

    def get_internal_network(self):
        networks = [
            net for net in self.os_clients.network.list_networks()["networks"]
            if net["admin_state_up"] and not net["router:external"] and
            len(net["subnets"])
        ]
        if networks:
            net = networks[0]
        else:
            net = self.create_network_resources()
        return net

    def get_external_network(self):
        networks = [
            net for net in self.os_clients.network.list_networks()["networks"]
            if net["admin_state_up"] and net["router:external"] and
            len(net["subnets"])
        ]
        if networks:
            ext_net = networks[0]
        else:
            ext_net = self.create_fake_external_network()
        return ext_net

    def create_flavor(self, name, ram=256, vcpus=1, disk=2):
        return self.os_clients.compute.flavors.create(name, ram, vcpus, disk)

    def create_sec_group(self, rulesets=None):
        if rulesets is None:
            rulesets = [
                {
                    # ssh
                    'ip_protocol': 'tcp',
                    'from_port': 22,
                    'to_port': 22,
                    'cidr': '0.0.0.0/0',
                },
                {
                    # iperf
                    'ip_protocol': 'tcp',
                    'from_port':5001,
                    'to_port': 5001,
                    'cidr': '0.0.0.0/0',
                },
                {
                    # ping
                    'ip_protocol': 'icmp',
                    'from_port': -1,
                    'to_port': -1,
                    'cidr': '0.0.0.0/0',
                }
            ]
        sg_name = "spt-test-secgroup-{}".format(random.randrange(100, 999))
        sg_desc = sg_name + " SPT"
        secgroup = self.os_clients.compute.security_groups.create(
            sg_name, sg_desc)
        for ruleset in rulesets:
            self.os_clients.compute.security_group_rules.create(
                secgroup.id, **ruleset)
        return secgroup


    def wait(predicate, interval=5, timeout=60, timeout_msg="Waiting timed out"):
        start_time = time.time()
        if not timeout:
            return predicate()
        while not predicate():
            if start_time + timeout < time.time():
                raise exceptions.TimeoutError(timeout_msg)

            seconds_to_sleep = max(
                0,
                min(interval, start_time + timeout - time.time()))
            time.sleep(seconds_to_sleep)

        return timeout + start_time - time.time()

    def create_basic_server(self, image=None, flavor=None, net=None,
                            availability_zone=None, sec_groups=(),
                            keypair=None,
                            wait_timeout=3 * 60):
        os_conn = self.os_clients
        image = image or self.get_cirros_image()
        flavor = flavor or self.get_micro_flavor()
        net = net or self.get_internal_network()
        kwargs = {}
        if sec_groups:
            kwargs['security_groups'] = sec_groups
        server = os_conn.compute.servers.create(
            "spt-test-server-{}".format(random.randrange(100, 999)),
            image, flavor, nics=[{"net-id": net["id"]}],
            availability_zone=availability_zone, key_name=keypair, **kwargs)
        # TODO
        #if wait_timeout:
        #    self.wait(
        #        lambda: os_conn.compute.servers.get(server).status == "ACTIVE",
        #        timeout=wait_timeout,
        #        timeout_msg=(
        #            "Create server {!r} failed by timeout. "
        #            "Please, take a look at OpenStack logs".format(server.id)))
        return server

    def create_network(self, tenant_id):
        net_name = "spt-test-net-{}".format(random.randrange(100, 999))
        net_body = {
            'network': {
                'name': net_name,
                'tenant_id': tenant_id
            }
        }
        net = self.os_clients.network.create_network(net_body)['network']
        return net
        #yield net
        #self.os_clients.network.delete_network(net['id'])

    def create_subnet(self, net, tenant_id, cidr=None):
        subnet_name = "spt-test-subnet-{}".format(random.randrange(100, 999))
        subnet_body = {
            'subnet': {
                "name": subnet_name,
                'network_id': net['id'],
                'ip_version': 4,
                'cidr': cidr if cidr else '10.1.7.0/24',
                'tenant_id': tenant_id
            }
        }
        subnet = self.os_clients.network.create_subnet(subnet_body)['subnet']
        return subnet
        #yield subnet
        #self.os_clients.network.delete_subnet(subnet['id'])

    def create_router(self, ext_net, tenant_id):
        name = 'spt-test-router-{}'.format(random.randrange(100, 999))
        router_body = {
            'router': {
                'name': name,
                'external_gateway_info': {
                    'network_id': ext_net['id']
                },
                'tenant_id': tenant_id
            }
        }
        router = self.os_clients.network.create_router(router_body)['router']
        return router
        #yield router
        #self.os_clients.network.delete_router(router['id'])

    def create_network_resources(self):
        tenant_id = self.get_admin_tenant().id
        ext_net = self.get_external_network()
        net = self.create_network(tenant_id)
        subnet = self.create_subnet(net, tenant_id)
        #router = self.create_router(ext_net, tenant_id)
        #self.os_clients.network.add_interface_router(
        #    router['id'], {'subnet_id': subnet['id']})

        private_net_id = net['id']
        # floating_ip_pool = ext_net['id']

        return net
        #yield private_net_id, floating_ip_pool
        #yield private_net_id
        #
        #self.os_clients.network.remove_interface_router(
        #     router['id'], {'subnet_id': subnet['id']})
        #self.os_clients.network.remove_gateway_router(router['id'])
