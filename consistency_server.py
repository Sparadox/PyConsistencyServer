#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Here's the consistency server module. It's a server app making it possible for clients (WebApps
mostly but Smartphone app support is also planned. If you can't wait, you can easily implement
something) to be notified when an element being displayed (a list of messages, an article, a
comment...) is updated on the server.
This server is the last element to bring a generalistic Observer/Observed pattern between a
web page and a server and therefore a view (HTML) that is consistent with a model (your backend,
on a remote servrer) in real-time or not far from it !

This module can (and must) be run as a standalone programe. Call it with the -h flag for a
description of the possible parameter. The connection with the client side is held in a WebSocket
while the connection with the backend uses a standard socket connection. Soon, it will be
possible to use a SSL paradigm for the latter. Indeed, standard sockets are fine as long as
consitency and your backend are running on the same machines or at least on the same local
network. But one day, you may need to have Consistency on a remote server and then, SSL will be
essential (even though the data sent between your backend and the remote server is probably not
critical).
"""

import sys
import json
import time
import signal
import asyncio
import argparse

from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

CONSISTENCY_SERVER = None

class Resource:
    """
    A very simple entity representing a resource that will be watched by clients and regularly
    updated by the backend.
    """

    def __init__(self, uri, consistency_server):
        self._uri = uri
        self._clients = list()
        self._last_update_date = time.time()
        self._consistency_server = consistency_server

    def update(self):
        """
        Called when the resource identified by the current instance is modified in the backend.
        It notifies all the clients watching it that it changed (and therefore, make them refresh).
        """
        self._last_update_date = time.time()
        for client in self._clients:
            client.protocol.invalidate(self)

    def add_client(self, client):
        """
        Add a client to the list of those watching the current resource instance
        """
        self._clients.append(client)

    def remove_client(self, client):
        """
        Removes a listener. In case there's no listener on the current resource, we ask consistency
        server to remove the current resource from its list of resources.
        """
        self._clients.remove(client)

        if len(self._clients) == 0:
            self._consistency_server.remove_resource(self)

    def _get_uri(self):
        """
        The resource Uniform Resource Identifier
        """
        return self._uri
    uri = property(_get_uri, doc="The resource URI on the client and server side.")


class Client:
    """
    A wrapper for a client websocket. Its main purpose is to encapsulate the application level
    protocol to communicate with the client (JSON by default). It can be extended and the
    extension can be injected into ConsistencyServer's constructor if you require a different
    protocol to encode your data at the application level
    """

    def __init__(self, protocol):
        self._protocol = protocol
        self._resources = list()

    def __del__(self):
        self.stop_watching()

    def stop_watching(self):
        """
        Unregisters the Client from all the resources it was watching
        """
        for resource in self._resources:
            resource.remove_client(self)

    def _get_protocol(self):
        """
        Returns a reference to the Protocol instance holding the connexion with the client (yes
        the name is badly choosen :( )
        """
        return self._protocol
    protocol = property(_get_protocol, doc="Handle on the Websocket connection with the client")


class BackendProtocol(asyncio.Protocol):
    """
    A protocol for communication between the backend side of the application and consistency
    """

    def __init__(self, consistency_server):
        self._consistency_server = consistency_server

    def data_received(self, msg):
        """
        Handles messages sent by the backend to consistency when a resource has been modified.
        These messages respect the following pattern :
        {"message": "update", "data":{"uri": "my_uri"}}
        """
        data = json.loads(msg.decode('utf8'))
        if data["message"] == "update":
            uri = data["data"]["uri"]
            self._consistency_server.update(uri)


class ClientProtocol(WebSocketServerProtocol):
    """
    A protocol to bind with the client and notify him when a change on a resource he's watching
    has been made
    """
    def __init__(self):
        self._client_representation = None

    def invalidate(self, resource):
        """
        Notifies the client the the resource identified by resource.uri on the client side is not
        consistent with the server anymore and has therefore to be refreshed.
        """
        data = {"message": "invalidate", "data":{"uri": resource.uri}}

        msg = json.dumps(data).encode('utf8')

        self.sendMessage(msg)

    def onConnect(self, request):
        """
        Called everytime a WebSocket client is bound to Consistency
        """
        self._client_representation = Client(self)

    def onMessage(self, msg, is_binary):
        """
        The messages of the client are there only to register him as a listener for some resource,
        everytime a message is sent, we start listening to the specified resource through an
        asynchronous process. When the resources yields "hey I have been modified", we dispatch
        the information to the client and that's basically all there is to it.
        The message sent by the client should respect the following standard :
        {"message": "watch", "data":{"uri": "my_uri"}}
        """
        if not is_binary:
            data = json.loads(msg.decode('utf8'))
            if data["message"] == "watch":
                uri = data["data"]["uri"]
                CONSISTENCY_SERVER.watch(self._client_representation, uri)

    def onClose(self, wasClean, code, reason):
        """
        Called when the WebSocket connection is closed (intentionnaly or not). It unregisters the
        current client from all the resources it was watching.
        """
        if self._client_representation:
            del self._client_representation


class ConsistencyServer:
    """
    The main consistency server class. It can be constructed with the following arguments :

    addr_public : the address of the current server for the clients to connect to (or localhost ?)
    addr_backend : same but for the backend connection, probably the same as above
    port_public : port for the clients to connect
    port_backend : same for the backend
    PublicProt : (defaut ClientProtocol) protocol to talk with the clients
    BackendProt : (default BackendProtocol) protocol to talk with the backend
    """

    def __init__(self, addr_public, addr_backend, port_public, port_backend,
                 PublicProt=ClientProtocol, BackendProt=BackendProtocol):
        self._resources = dict()

        public_factory = WebSocketServerFactory("ws://" + addr_public + ":" + str(port_public))

        public_factory.protocol = PublicProt

        self._event_loop = asyncio.get_event_loop()

        asyncio.Task(self._event_loop.create_server(public_factory, addr_public, port_public))
        asyncio.Task(self._event_loop.create_server(lambda: BackendProt(self), addr_backend,
                                                    port_backend))

    def run_forvever(self):
        """ Runs the server until close() is called """
        self._event_loop.run_forever()

    def close(self):
        """ Terminates the server """
        self._event_loop.close()

    def update(self, uri):
        """ Updates the resource matching the passed URI """
        if uri in self._resources:
            self._resources[uri].update()

    def watch(self, client, uri):
        """ Creates the Observer/Observed relation between client and the resource represented by
        uri. """
        if not uri in self._resources:
            self._resources[uri] = Resource(uri, self)

        self._resources[uri].add_client(client)

    def remove_resource(self, resource):
        """
        Removes a resource from the consistency server (usually called when no client is listening
        to that resource anymore).
        """
        if resource.uri in self._resources:
            del self._resources[resource.uri]


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='A simple program to keep your webapp\'s backend \
consistent with your frontend in a lightweight, fast and fashionable way (using websockets). It \
will be paired with the consistency JavaScript client (unless you want to write your own client) \
and if you are using Django, you can use consistency-django for an almost seamless integration in \
your backend. Modules for other framework will come later. If you write your own for your favorite \
framework, please let me know (etienne.lafarge@gmail.com) so that I can advertise it on \
Consistency\'s website and documentation.', epilog='In case you\'re wondering, you can exit the \
program with CTRL-C or sending it a SIGINT signal.')

    PARSER.add_argument('-h', '--public-hostname', type=str, help='The hostname for the clients \
access. The default localhost should work anyway.', default="localhost")
    PARSER.add_argument('-p', '--public-port', type=int, help='The port number for the clients \
access. Default is 4691.', default=4691)
    PARSER.add_argument('-s', '--backend-hostname', type=str, help='The hostname for the backend \
access. The default localhost should work anyway.', default="localhost")
    PARSER.add_argument('-c', '--backend-port', type=int, help='The port number for the backend \
access. Default is 1991.', default=1991)

    ARGS = PARSER.parse_args()

    PUBLIC_HOSTNAME = ARGS.public_hostname
    PUBLIC_PORT = ARGS.public_port
    BACKEND_HOSTNAME = ARGS.backend_hostname
    BACKEND_PORT = ARGS.backend_port

    CONSISTENCY_SERVER = ConsistencyServer(PUBLIC_HOSTNAME, BACKEND_HOSTNAME,
                                           PUBLIC_PORT, BACKEND_PORT)

    def _on_close_request():
        """
        Called when an interrupt signal is received (for instance on a CTRL-C exit)
        """
        CONSISTENCY_SERVER.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_close_request)

    CONSISTENCY_SERVER.run_forvever()
