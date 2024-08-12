docker build -t localdeid --platform=linux/amd64 .
docker run -it -p80:80 --platform=linux/amd64 -v ${PWD}:/app localdeid /bin/bash
