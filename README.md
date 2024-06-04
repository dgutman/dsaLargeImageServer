Based on the code from
http://localhost:8080/api/v1/item/6595906d482cd2c47d4d615e/tiles/dzi.dzi

https://github.com/girder/large_image/blob/master/large_image/tilesource/jupyter.py


This is trying to generate a FASTAPI light weight dockerized tile server
as well as also integrate deID components and functions


## Getting started

  docker compose build
  docker compose up 


This starts a FASTAPI server, which exposes the functions I have been developed.  Note this is still in alpha, and I am refactoring.

To access the fastAPI page, go to http://localhost:80/docs

The most relevant function now is the testDeidWorkflow function, which is contained in the fastApiTileServer.py file.  This calls the various functions needed to point to an SVS file, and remove the label and deidentify it. 


 To test the other functions, you can use the slideID == "sample", which will reference a sampleSlide.svs file I have in the container.  In the long term, I will clarify the path that needs to be bind-mounted within the docker container... it will probably wind up binding the path from where your files are living outside the dockerhost to /localData within the docker container, and then everything will be relative to the base path.  Will need to provide some examples so this is more intuitive.
 

