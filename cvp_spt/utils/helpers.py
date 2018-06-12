import texttable as tt

class helpers(object):
    def __init__ (self, local_salt_client):
        self.local_salt_client = local_salt_client

    def start_iperf_between_hosts(self, global_results, node_i, node_j, ip_i, ip_j, net_name):
        result = []
        direct_raw_results = self.start_iperf_client(node_i, ip_j)
        result.append(direct_raw_results)
        print "1 forward"
        forward = "1 thread:\n"
        forward += direct_raw_results + " Gbits/sec"

        direct_raw_results = self.start_iperf_client(node_i, ip_j, 10)
        result.append(direct_raw_results)
        print "10 forward"
        forward += "\n\n10 thread:\n"
        forward += direct_raw_results + " Gbits/sec"

        reverse_raw_results = self.start_iperf_client(node_j, ip_i)
        result.append(reverse_raw_results)
        print "1 backward"
        backward = "1 thread:\n"
        backward += reverse_raw_results + " Gbits/sec"

        reverse_raw_results = self.start_iperf_client(node_j, ip_i, 10)
        result.append(reverse_raw_results)
        print "10 backward"
        backward += "\n\n10 thread:\n"
        backward += reverse_raw_results + " Gbits/sec"
        global_results.append([node_i, node_j,
                               net_name, forward, backward])
        return result

    def draw_table_with_results(self, global_results):
        tab = tt.Texttable()
        header = [
            'node name 1',
            'node name 2',
            'network',
            'bandwidth >',
            'bandwidth <',
        ]
        tab.set_cols_align(['l', 'l', 'l', 'l', 'l'])
        tab.set_cols_width([27, 27, 15, 20, '20'])
        tab.header(header)
        for row in global_results:
            tab.add_row(row)
        s = tab.draw()
        print s
     
    def start_iperf_client(self, minion_name, target_ip, thread_count=None):
        iperf_command = 'iperf -c {0}'.format(target_ip)
        if thread_count:
            iperf_command += ' -P {0}'.format(thread_count)
        output = self.local_salt_client.cmd(tgt=minion_name,
                                            fun='cmd.run',
                                            param=[iperf_command])
        result = output.values()[0].split('\n')[-1].split(' ')[-2:]
        #import pdb;pdb.set_trace()
        if result[1] == 'Mbits/sec':
            return result[0]*0.001
        if result[1] != 'Gbits/sec':
            return "0"
        return result[0]
