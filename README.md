# FutureGateway API Server (fgAPIServer)
[![Travis](http://img.shields.io/travis/FutureGateway/geAPIServer/master.png)](https://travis-ci.org/FutureGateway/fgAPIServer)
[![License](https://img.shields.io/github/license/FutureGateway/geAPIServer.svg?style?flat)](http://www.apache.org/licenses/LICENSE-2.0.txt)

This project implements the interface of a RESTful API Server, compliant with [CSGF APIs][specs] specifications. Any activity processed by this interface will be then processed and orchestrated by the [API Server Daemon][APIServerDaemon] component.

This service offers the same capabilities of the [API Server][APIServer] project with the following differences:
 - It exploits the [CSGF][CSGF]' GridEngine system to target its supported distributed ifnrastructures
 - It may support other executors services just developing the right interface classes into the [API Server Daemon][APIServerDaemon] 

The Principal advantages of this solutions are:

 - Backward compatibility with existing systems based on the CSGF
 - Fast provisioning of ready to go solutions
 - Fast prototyping when designing new features and components (including APIServer itself)
 - Ideal solution for existing development environments already using CSGF

   [specs]: <http://docs.csgfapis.apiary.io/#reference/v1.0/application/create-a-task>
   [CSGF]: <https://www.catania-science-gateways.it>
   [API Server Daemon]: <https://github.com/FutureGateway/APIServerDaemon>
   [APIServer]: <https://github.com/FutureGateway/APIServer>
