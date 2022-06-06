# ergopad-api
[Ergopad.io](https://ergopad.io) frontend collaborates with this repo.  All repositories that support Ergopad are open source.  The architecture of the API is a RESTful API, built with FastAPI in Python 3.10.  
- Infrastructure depends on: PostgreSql, Redis, [an implementation of] Ergo Explorer, and Ergo Node.  
- The ASGI server currently used to power the FastAPI API service is NGINX Unit.
- Asynchronous calls are used for the database and explorer/node REST APIs.
- Docker is used to coordinate and simplify the orchestration of services although this is not strictly necessary, however this repo does not explore the configuration otherwise.
<br>

![ergopad-200x200-transparent](https://user-images.githubusercontent.com/42897033/148552822-d4ab78a5-79b0-4078-a8cb-34908ce88cee.png)

![Build Test](https://github.com/ergo-pad/ergopad-api/actions/workflows/build_test.yml/badge.svg?branch=dev)

## Quick Start
### Dependencies
These need to be running prior to starting the API, and the configs updated
- [ergopad-data](https://github.com/ergo-pad/ergopad-data)
- [ergopad-explorer](https://github.com/ergo-pad/ergopad-explorer)
- [ergopad-quicknode](https://github.com/ergo-pad/ergopad-quicknode)
<br>

### Optional
- [ergopad-tasks](https://github.com/ergo-pad/ergopad-tasks)
- [ergopad-monitor](https://github.com/ergo-pad/ergopad-monitor)
<br>

### Setup
```
> git clone https://github.com/ergo-pad/ergopad-api.git
> cd ergopad-api
> docker network create ergopad-net
> docker compose up
```

### Unit Testing
```
$ cd ergopad-api/app
$ python3 -m pytest
```

## Support
Join the ergopad discord [#development](https://discord.gg/CBmCDsME) channel.

## Developer Team
- Luivatra
- Noob77777
- Trappert
- LGD
- Esot321c
- Leif
