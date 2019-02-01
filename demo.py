import zerorpc
import gevent
import sys


class StateVector():
    def __init__(self):
        self.state = 'Normal'
        # coordinator of the node
        self.coordinator = 0
        # description of task
        self.desc = None
        # the node recently makes this node halt
        self.halt = -1
        # list of nodes which this node believes to be in operation
        self.Up = []


class Bully():
    def __init__(self, addr, config_file='server_config'):
        self.Statevector = StateVector()
        self.Statevector.state = 'Normal'

        self.check_servers_greenlet = None

        self.servers = []
        self.addr = addr

        f = open(config_file, 'r')
        for line in f.readlines():
            line = line.rstrip()
            self.servers.append(line)
        print('My addr: %s' % self.addr)
        print('Server list: %s' % (str(self.servers)))

        self.n = len(self.servers)

        self.connections = []

        for i, server in enumerate(self.servers):
            if server == self.addr:
                self.i = i
                self.connections.append(self)
            else:
                client = zerorpc.Client(timeout=2)
                client.connect('tcp://' + server)
                self.connections.append(client)

    def are_you_there(self):
        return True

    def are_you_normal(self):
        if self.Statevector.state == 'Normal':
            return True
        else:
            return False

    def halt(self, j):
        self.Statevector.state = 'Election'
        self.Statevector.halt = j

    def new_coordinator(self, j):
        print('call new_coordinator')
        if self.Statevector.halt == j and self.Statevector.state == 'Election':
            self.Statevector.coordinator = j
            self.Statevector.state = 'Reorganization'

    def ready(self, j, x=None):
        print('call ready')
        if self.Statevector.coordinator == j and self.Statevector.state == "Reorganization":
            self.Statevector.desc = x
            self.Statevector.state = 'Normal'

    def election(self):
        print('Check the states of higher priority nodes:')

        for i, server in enumerate(self.servers[self.i + 1:]):
            try:
                self.connections[self.i + 1 + i].are_you_there()
                if self.check_servers_greenlet is None:
                    self.Statevector.coordinator = self.i + 1 + i
                    self.Statevector.state = 'Normal'
                    self.check_servers_greenlet = self.pool.spawn(self.check())
                return
            except zerorpc.TimeoutExpired:
                print('%s Timeout!' % server)

        print('halt all lower priority nodes including this node:')
        self.halt(self.i)
        self.Statevector.state = 'Election'
        self.Statevector.halt = self.i
        self.Statevector.Up = []
        for i, server in enumerate(self.servers[self.i::-1]):
            try:
                self.connections[i].halt(self.i)
            except zerorpc.TimeoutExpired:
                print('%s Timeout!' % server)
                continue
            self.Statevector.Up.append(self.connections[i])

        # reached 'election point',inform nodes of new coordinator
        print('inform nodes of new coordinator:')
        self.Statevector.coordinator = self.i
        self.Statevector.state = 'Reorganization'
        for j in self.Statevector.Up:
            try:
                j.new_coordinator(self.i)
            except zerorpc.TimeoutExpired:
                print('Timeout! Election will be restarted.')
                self.election()
                return

        # Reorganization
        for j in self.Statevector.Up:
            try:
                j.ready(self.i, self.Statevector.desc)
            except zerorpc.TimeoutExpired:
                print('Timeout!')
                self.election()
                return

        self.Statevector.state = 'Normal'
        print('[%s] Starting ZeroRPC Server' % self.servers[self.i])
        self.check_servers_greenlet = self.pool.spawn(self.check())

    def recovery(self):
        self.Statevector.halt = -1
        self.election()

    def check(self):
        while True:
            gevent.sleep(2)
            if self.Statevector.state == 'Normal' and self.Statevector.coordinator == self.i:
                for i, server in enumerate(self.servers):
                    if i != self.i:
                        try:
                            ans = self.connections[i].are_you_normal()
                            print ('%s : are_you_normal = %s' % (server, ans))
                        except zerorpc.TimeoutExpired:
                            print('%s Timeout!' % server)
                            continue

                        if not ans:
                            self.election()
                            return
            elif self.Statevector.state == 'Normal' and self.Statevector.coordinator != self.i:
                print ('check coordinator\'s state')
                try:
                    result = self.connections[self.Statevector.coordinator].are_you_there()
                    print ('%s : are_you_there = %s' % (self.servers[self.Statevector.coordinator], result))
                except zerorpc.TimeoutExpired:
                    print ('coordinator down, start election.')
                    self.timeout()

    def timeout(self):
        if self.Statevector.state == 'Normal' or self.Statevector.state == 'Reorganization':
            try:
                self.connections[self.Statevector.coordinator].are_you_there()
            except zerorpc.TimeoutExpired:
                print('%s Timeout!' % self.servers[self.Statevector.coordinator])
                self.election()
        else:
            self.election()

    def start(self):
        self.pool = gevent.pool.Group()
        self.recovery_greenlet = self.pool.spawn(self.recovery)


def main():
    addr = sys.argv[1]
    bully = Bully(addr)
    server = zerorpc.Server(bully)
    server.bind('tcp://' + addr)
    bully.start()
    # Start server
    print ('[%s] Starting ZeroRPC Server' % addr)
    server.run()


if __name__ == '__main__':
    main()