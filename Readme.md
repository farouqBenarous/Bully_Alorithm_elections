# Bully Algorithm for sync peer to peer system
In distributed computing, the bully algorithm is a method for
 dynamically electing a coordinator or leader from a group
  of distributed computer processes. The process with 
  the highest process ID number from amongst the non-failed 
  processes is selected as the coordinator.

# overview


### Dependencies  
*  zerorpc : 

is a light-weight, reliable and language-agnostic library for distributed communication between server-side processes.
* gevent : 

gevent is a coroutine -based Python networking library that uses greenlet to provide a high-level synchronous API on top of the libev or libuv event loop.

* sys

This module provides access to some variables used or maintained by the interpreter and to functions that interact strongly with the interpreter. It is always available.


# usage
* set the adresses of your peers in `server_config` whather its local or distributed (this case is local)
* run the instances  `python demo.py 127.0.0.1:9000` the adress should change to correspond with every peer
 
* and to see how the election works run 5 instance of the demo and try to make test (shutdown one peer ...)

# helpful Links
#### to understand how the election works 
http://www.cs.colostate.edu/~cs551/CourseNotes/Synchronization/BullyExample.html

https://en.wikipedia.org/wiki/Bully_algorithm

http://www.cs.colostate.edu/~cs551/CourseNotes/Synchronization/BullyExample.html