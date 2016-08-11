from proxy import master, event_reactor as er

if __name__ == '__main__':

    reactor = er.EventReactor()
    reactor.setDaemon(True)
    reactor.start()

    tunnel_master = master.TunnelMaster(reactor, 5555)

    for port in [8080]:
        master.Proxy.add(reactor, port)

    try:
        while (True):
            reactor.join(2)
            if not reactor.isAlive():
                break

    except KeyboardInterrupt:
        print('\nstopped by keyboard')
        exit(-1)
