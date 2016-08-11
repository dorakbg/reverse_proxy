from proxy import slave, event_reactor as er

if __name__ == '__main__':

    reactor = er.EventReactor()
    reactor.setDaemon(True)
    reactor.start()

    proxy = slave.Proxy()
    proxy.start(reactor, 3, 5555)

    try:
        while (True):
            reactor.join(2)
            if not reactor.isAlive():
                break

    except KeyboardInterrupt:
        print('\nstopped by keyboard')
        exit(-1)
