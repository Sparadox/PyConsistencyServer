Consistency server application
==============================

This is a Python implementation for the consistency server.

The consistency server talks with your backend (\*) and all the connected clients (basicall HTML pages that talk with consistency over Websocket using the Javascript consistency toolkit). It makes it possible to implement an Observer pattern between the views on your webpage and the data in your backend. This ways, it ensures that the web pages keeps up to date with the server at any moment. Since it's not using regular AJAX reloads but bidirectionnal websockets, it's as fast as fast on the web could mean.

All the interest of Consistency is this bidirectionnal link. Indeed, when the Web has been built a very long time ago, it's been design for static content. A client requests this content from a server through the HTTP protocol and the latter replies with the content and the connection is close. There is therefore no way for the server to notify the client if anything is changed on it, at least not in the HTTP protocol. What a sad and lonely world for our servers... 

... But WebSockets came and put an end to it by enabling the client to start a nearly standard TCP socket connection with the server and have a bidirectionnal chit-chat, and that's what Consistency is made of : a very lightweight and simplistic use of these Websocket.


(\*) There's a django app containing all the utilities, context processors and middlewares to help you make a responsive web app with Django. It makes it easy to implement consistency over your pre-existing Django application or even better, to use consistency from scratch. It doesn't require anything in particular about your data model or the way you pass it to your client. Wether you pass the data to your app as JSON, XML, plain HTML or even if you refresh the page when there is something to update on it, consistency works (nearly) out of the box.

This being said, Consistency is particulary well suited if your backend provides it's data through a RESTful API of yours.

How does it work ?
------------------

Basically, when a page is loaded, it creates this websocket connection and registers all the components it wants to watch on the consistency server. These components are likely to be rows and list of rows in your database, or documents if you're using a document-based data storage approach. We call them **resources**. Each resource on the server is identified in a unique way by a **URI** (**U**niform **R**esource **I**dentifier). Actually, this URI may match the URL you use to retrieve this resource, especially if you're trying to comply with the RESTful practices but it doesn't have to be. You can just choose what you like for it. (\*\*)

(\*\*)If you use Django it provides a default naming convention for your entities and template context processors to print it automatically in your templates. In one word, you don't have to think about your URI's by default :D

Dependencies
------------

* You need Python 3.4 or 3.3 with the asyncio module, sorry :D A Node.js implementation relying on socket.io is planned : on the frontend it will also bring support for IE 8 and below (down to 5.5... yes, yes :D) using WebSocket alternative such as Adobe Flash Sockets or... AJAX call (so don't expect crazy performances). 
* autobahn : contains a WebSocket implementations. Will be removed in a very near future.

TODO List
=========

* Make it possible to pass the new value for a resource (in a format of your choice, probably JSON) to the consistency server so that it directly sends it to the client along with the invalidate notice. This way the client doesn't even have to make a server call to get the refreshed data, everything can be passed through a websocket.
* Performance benchmarking : determine if Python garbage collection can cause performance issue. If so, maybe we can handle memory management ourselves even though Python is not the best suited language for it. (Then maybe rewriting consistency server in C++ could do the job).
* Make it possible, a least for the backend <-> consistency binding, to use SSL or any secure communication method. As long as both are on a single machine and provided that this one is the same it's ok like it is now but if you whish to run consistency on a separate machine, this will become essential. 
* Check if it already works on the client side, if not implementing it would be a plus.
* Get rid of autobahn. It sucks ! (it forces use to use a global variable because it deals badly with the pythonic server factories, it makes us import a big library while we only need to do very basic stuff with websockets and async, python coding standards aren't respected...)
