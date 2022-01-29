# AAA
`AAA` is our active aircraft avoidance system which gets the telemetry of other aircraft from interop and flies accordingly so that all obstacles are avoided.


## Connections
```
  [AAA]
    |
 <http/s>
    |
 [GCOM-X]
```

## Required Object Values
- Latitude
- Longitude
- Radius
- Height


## Tickets
- Fetch other aircraft positions from GCOM-X taken from interop
- Get GCOM-X to fetch AAA obstacles
- Get GCOM-X to repeatedly reroute the drones path if the position of other aircraft has changed and may affect our path (base on heading, position, and speed of other aircraft)


## Future Modifications
- Make avoidance 3D using the altitude of other aircraft


## Dependencies
- Docker


## Installation
In your local AAA repository, run the following:
```
docker build -t aaa .
```

[Once aaa has been added to DockerHub]

In your local AAA repository, run the following to pull from DockerHub:
```
docker pull ubcuas/aaa:latest
```

The images can also be built locally:
```
docker build --tag ubcuas/aaa:latest .
```


## Usage
Standard usage:
```
docker run aaa
```
To run with built-in testing:
```
```