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


## Dependencies
- Docker


## Installation
In your local AAA repository, run the following:
```
docker build . -t aaa
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
