from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import Response
import os, json, weakref
import large_image
import hashlib
from typing import Any, Dict, List, Optional
import math
from large_image.exceptions import TileSourceXYZRangeError
from large_image.tilesource.utilities import JSONDict
import io
import deidCode.deidHelpers as deid

"""A simple FASTAPI Rest Interface to serve tiles from a slide image
Currently returns metadata about the tile, and can also return a tile
Will be adding a macro and thumbnail endpoint soon
"""

app = FastAPI()  ## Initialize fastAPI Map

""" This should accept a filepath, but this must be made relative
To the locations that the docker container can actually read
Need to determine how to make this clear to the end user
who is starting the containaer.
Probably add some supports that allow me to check if a file can be opened
"""

## CREATE A TILE OBJECT using WEAK REF that stores the tile Object
## Seems like this will help with garbage collection

## TO ASK:  If I want to set the encoding or overlap, do I just pass those as params?

## TO DO: ADD CODE THAT WILL DETECT IF MACRO or LABEL IS ALREADY NULLED


class SlideImage:
    def __init__(self, path, encoding="PNG"):
        self.path = path  # Path to the file, note this must be accessible within the docker container
        self.ts = None
        self.get_tileSource()
        if encoding.upper() not in ["PNG", "JPG"]:
            raise ValueError("Encoding must be either 'PNG' or 'JPG'")
        self.encoding = encoding.lower()

    def get_tileSource(self):
        try:
            self.ts = large_image.getTileSource(self.path)
        except Exception as e:
            print(f"Failed to create tile source: {e}")
            self.ts = None

    ## This returns the tile metadata in terms of tileWidth, sizeX, sizeY, and # of pyramid layers
    def get_slideMetadata(self):
        if not self.ts:
            return None
        return self.ts.getMetadata()

    def get_dziInfo(self, encoding="PNG"):
        """
        Retrieves the Deep Zoom Image (DZI) information.

        Parameters:
        - encoding (str): The encoding format of the image. Default is "PNG".

        Returns:
        - str: The DZI information in XML format.
        """
        ## Need to get the tile info paramaters from the image metadata..
        slideMeta = self.get_slideMetadata()
        encoding = self.encoding
        result = "".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<Image",
                ' TileSize="%d"' % slideMeta["tileWidth"],
                ' Overlap="0"',  ## Should I submit this as a parameter?
                ' Format="%s"' % encoding,
                ' xmlns="http://schemas.microsoft.com/deepzoom/2008">',
                "<Size",
                ' Width="%d"' % slideMeta["sizeX"],
                ' Height="%d"' % slideMeta["sizeY"],
                "/>" "</Image>",
            ]
        )
        return result

    def get_macroImage(self, encoding="PNG"):
        """
        Retrieves the macro image associated with the image.

        Returns:
            The macro image associated with the tile as a PNG image.
        """
        macroImage, mime_type = self.ts.getAssociatedImage("macro", encoding=encoding)
        return Response(content=macroImage, media_type=f"image/{encoding.lower()}")

    def get_labelImage(self, encoding="PNG"):
        """
        Retrieves the label image from the associated image

        Parameters:
        - encoding (str): The encoding format of the image. Default is "PNG".

        Returns:
        - Response: The HTTP response containing the label image.
        """
        labelImage, mime_type = self.ts.getAssociatedImage("label", encoding="PNG")
        return Response(content=labelImage, media_type=f"image/{encoding.lower()}")


slideCache = (
    {}
)  ## This will store the hash information of loaded slides and their tile sources

sampleFile = "sampleSlide.svs"

### This will create a slideCache object called "sample" and load the tileSource

slideCache["sample"] = SlideImage(sampleFile)


""" I am going to use a fileHash based on the inputted filename 
 and use this as the local ID for the cache instead of the entire filename
to simplify the API calls, other wise the url's will either be very long
or have weird encoded issues
 """


## This is for debugging purposes, to see if the tile source is being loaded
## and if the debug parts load.. will split this into a separate function later
@app.get("/testDeidWorkflow")
async def testDeidWorkflow():
    deid.deid_workflow()
    return {"status": "success"}


@app.get("item/{fileHashId}/tile/{z}/{x}/{y}")
async def get_tile(
    z: int = Path(..., description="The Z coordinate of the tile."),
    x: int = Path(..., description="The X coordinate of the tile."),
    y: int = Path(..., description="The Y coordinate of the tile."),
):
    sampleFile = "sampleSlide.svs"
    encoding = "PNG"  ### Get this from the slideobject
    if sampleFile not in slideCache:
        try:
            slideCache[sampleFile] = large_image.getTileSource(sampleFile)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot open slide: {e}")

    slide = SlideImage(sampleFile)

    try:
        tile_data = slide.ts.getTile(
            x, y, z, format=large_image.tilesource.TILE_FORMAT_IMAGE
        )
        encoding = "PNG"
        img_byte_arr = io.BytesIO()

        img_byte_arr = img_byte_arr.getvalue()

        return Response(content=tile_data, media_type=f"image/{encoding.lower()}")
    except TileSourceXYZRangeError:
        raise HTTPException(status_code=404, detail="Tile not found")


## maybe rename to getSlideObj(fileHashId ) ??


def lookup_fileHashId(fileHashId):
    if fileHashId not in slideCache:
        raise HTTPException(
            status_code=400,
            detail=f"FileHash Not found, trying passing full filename first to get hashID {fileHashId}",
        )
    return slideCache[fileHashId]


## TO DO: Insert the hash ID functionality..
@app.get("/get/slideInfo")
async def getSlideInfo():
    slide = SlideImage(sampleFile)
    return slide._get_slideMetadata()


@app.get("/get/item/{fileHashId}/macroImage")
def get_macroImage(fileHashId: str):
    slide = lookup_fileHashId(fileHashId)
    return slide.get_macroImage()


@app.get("/get/item/{fileHashId}/labelImage")
def get_labelImage(fileHashId: str):
    slide = lookup_fileHashId(fileHashId)
    return slide.get_labelImage()


## Once you have the fileHashID, this will return a DZI XML document that can be used
@app.get("/get/{fileHashId}/dzi.dzi", tags=["Get DeepZoom compatible metadata"])
async def get_dziInfo(
    fileHashId: str = Path(..., description="The hash ID of the file.")
):
    slide = lookup_fileHashId(fileHashId)
    slide = slideCache[fileHashId]["slideObj"]
    return Response(content=slide._getDZIInfo(), media_type="text/xml")


@app.get("/getFileHashId/{filepath}")
async def get_fileHashId(filepath: str):
    ## First check if the file exists based on its hash, if so generate a hash
    ## Will use the first 8 digits of the hash as the ID, can also check for hash collisions
    ## But this is unlikely

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    else:
        hash_object = hashlib.sha256(filepath.encode())
        hex_dig = hash_object.hexdigest()[:8]
        slideCache[hex_dig] = {"slideObj": SlideImage(filepath), "filepath": filepath}
        ## Storing the filepath in the cache as well, to check for collisions if I ever need to
        return {"fileHashId": hex_dig}
