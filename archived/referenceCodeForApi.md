ref   return Response(content=result, media_type="text/xml")

# @app.get("/dzi/{item_id}")
# async def get_dzi_info(
#     item_id: str,
#     encoding: Optional[str] = None,
#     tilesize: Optional[int] = 256,
#     overlap: Optional[int] = 0,
# ):

# def _getDZITile(self, item, level, xandy, params):
#     pass

#     # _adjustParams(params)
#     tilesize = int(params.get("tilesize", 256))
#     if tilesize & (tilesize - 1):
#         raise HTTPException(status_code=400, detail="Invalid tilesize")

#     overlap = int(params.get("overlap", 0))
#     if overlap < 0:
#         raise HTTPException(status_code=400, detail="Invalid overlap")
#     x, y = (int(xy) for xy in xandy.split(".")[0].split("_"))
#     # _handleETag('getDZITile', item, level, xandy, params)  # TO EVAL
#     metadata = self._get_slideMetadata()
#     level = int(level)
#     maxlevel = int(
#         math.ceil(math.log(max(metadata["sizeX"], metadata["sizeY"])) / math.log(2))
#     )
#     if level < 1 or level > maxlevel:
#         raise HTTPException(
#             status_code=400, detail="level must be between 1 and the image scale"
#         )

#     lfactor = 2 ** (maxlevel - level)
#     region = {
#         "left": (x * tilesize - overlap) * lfactor,
#         "top": (y * tilesize - overlap) * lfactor,
#         "right": ((x + 1) * tilesize + overlap) * lfactor,
#         "bottom": ((y + 1) * tilesize + overlap) * lfactor,
#     }
#     width = height = tilesize + overlap * 2
#     if region["left"] < 0:
#         width += int(region["left"] / lfactor)
#         region["left"] = 0
#     if region["top"] < 0:
#         height += int(region["top"] / lfactor)
#         region["top"] = 0
#     if region["left"] >= metadata["sizeX"]:
#         raise HTTPException("x is outside layer", code=400)
#     if region["top"] >= metadata["sizeY"]:
#         raise HTTPException("y is outside layer", code=400)
#     if region["left"] < metadata["sizeX"] and region["right"] > metadata["sizeX"]:
#         region["right"] = metadata["sizeX"]
#         width = int(math.ceil(float(region["right"] - region["left"]) / lfactor))
#     if region["top"] < metadata["sizeY"] and region["bottom"] > metadata["sizeY"]:
#         region["bottom"] = metadata["sizeY"]
#         height = int(math.ceil(float(region["bottom"] - region["top"]) / lfactor))

#     regionData, regionMime = self.ts.getRegion(
#         region=region, format=large_image.tilesource.TILE_FORMAT_NUMPY
#     )
#     print(region)

# regionData, regionMime = self.imageItemModel.getRegion(
#     item,
#     region=region,
#     output=dict(maxWidth=width, maxHeight=height),
#     **params)
# setResponseHeader('Content-Type', regionMime)

#       image_data = b"your image data"

# return Response(content=image_data, media_type="image/jpeg")

# return regionData

#         @tile_source.setter
#         def tile_source(self, source: IPyLeafletMixin) -> None:
#             self._tile_source_ = weakref.ref(source)


#         def get(self) -> None:
#             x = int(self.get_argument("x"))
#             y = int(self.get_argument("y"))
#             z = int(self.get_argument("z"))
#             encoding = self.get_argument("encoding", "PNG")
#             try:
#                 tile_binary = manager.tile_source.getTile(  # type: ignore[attr-defined]
#                     x, y, z, encoding=encoding
#                 )
#             except TileSourceXYZRangeError as e:
#                 self.clear()
#                 self.set_status(404)
#                 self.finish(f"<html><body>{e}</body></html>")
#             else:
#                 self.write(tile_binary)
#                 self.set_header("Content-Type", "image/png")

# if encoding and encoding not in ("JPEG", "PNG"):
#         raise HTTPException(
#             status_code=400, detail="Only JPEG and PNG encodings are supported"
#         )
#     if tilesize & (tilesize - 1):
#         raise HTTPException(status_code=400, detail="Invalid tilesize")
#     if overlap < 0:
#         raise HTTPException(status_code=400, detail="Invalid overlap")

#     info = get_tiles_info(
#         item_id, {"encoding": encoding, "tilesize": tilesize, "overlap": overlap}
#     )



# @describeRoute(
#         Description('Get DeepZoom compatible metadata.')
#         .param('itemId', 'The ID of the item.', paramType='path')
#         .param('overlap', 'Pixel overlap (default 0), must be non-negative.',
#                required=False, dataType='int')
#         .param('tilesize', 'Tile size (default 256), must be a power of 2',
#                required=False, dataType='int')
#         .errorResponse('ID was invalid.')
#         .errorResponse('Read access was denied for the item.', 403),
#     )


#      def _getTile(self, item, z, x, y, imageArgs, mayRedirect=False):
#         """
#         Get an large image tile.

#         :param item: the item to get a tile from.
#         :param z: tile layer number (0 is the most zoomed-out).
#         .param x: the X coordinate of the tile (0 is the left side).
#         .param y: the Y coordinate of the tile (0 is the top).
#         :param imageArgs: additional arguments to use when fetching image data.
#         :param mayRedirect: if True or one of 'any', 'encoding', or 'exact',
#             allow return a response which may be a redirect.
#         :return: a function that returns the raw image data.
#         """


#     @describeRoute(
#         Description('Get a large image tile.')
#         .param('itemId', 'The ID of the item.', paramType='path')
#         .param('z', 'The layer number of the tile (0 is the most zoomed-out '
#                'layer).', paramType='path')
#         .param('x', 'The X coordinate of the tile (0 is the left side).',
#                paramType='path')
#         .param('y', 'The Y coordinate of the tile (0 is the top).',
#                paramType='path')
#         .produces(ImageMimeTypes)
#         .errorResponse('ID was invalid.')
#         .errorResponse('Read access was denied for the item.', 403),
#     )
#     # Without caching, this checks for permissions every time.  By using the
#     # LoadModelCache, three database lookups are avoided, which saves around
#     # 6 ms in tests. We also avoid the @access.public decorator and directly
#     # set the accessLevel attribute on the method.

#     #   def getTile(self, item, z, x, y, params):
#     #       return self._getTile(item, z, x, y, params, True)
#     def getTile(self, itemId, z, x, y, params):
#         _adjustParams(params)
#         item = loadmodelcache.loadModel(
#             self, 'item', id=itemId, allowCookie=True, level=AccessType.READ)
#         _handleETag('getTile', item, z, x, y, params)
#         redirect = params.get('redirect', False)
#         if redirect not in ('any', 'exact', 'encoding'):
#             redirect = False
#         return self._getTile(item, z, x, y, params, mayRedirect=redirect)

#     @describeRoute(
#         Description('Get a large image tile with a frame number.')
#         .param('itemId', 'The ID of the item.', paramType='path')
#         .param('frame', 'The frame number of the tile.', paramType='path')
#         .param('z', 'The layer number of the tile (0 is the most zoomed-out '
#                'layer).', paramType='path')
#         .param('x', 'The X coordinate of the tile (0 is the left side).',
#                paramType='path')
#         .param('y', 'The Y coordinate of the tile (0 is the top).',
#                paramType='path')
#         .param('redirect', 'If the tile exists as a complete file, allow an '
#                'HTTP redirect instead of returning the data directly.  The '
#                'redirect might not have the correct mime type.  "exact" must '
#                'match the image encoding and quality parameters, "encoding" '
#                'must match the image encoding but disregards quality, and '
#                '"any" will redirect to any image if possible.', required=False,
#                enum=['false', 'exact', 'encoding', 'any'], default='false')
#         .produces(ImageMimeTypes)
#         .errorResponse('ID was invalid.')
#         .errorResponse('Read access was denied for the item.', 403),
#     )
#     # See getTile for caching rationale
#     def getTileWithFrame(self, itemId, frame, z, x, y, params):
#         _adjustParams(params)
#         item = loadmodelcache.loadModel(
#             self, 'item', id=itemId, allowCookie=True, level=AccessType.READ)
#         _handleETag('getTileWithFrame', item, frame, z, x, y, params)
#         redirect = params.get('redirect', False)
#         if redirect not in ('any', 'exact', 'encoding'):
#             redirect = False
#         params['frame'] = frame
#         return self._getTile(item, z, x, y, params, mayRedirect=redirect)
#     getTileWithFrame.accessLevel = 'public'

#     @describeRoute(
#         Description('Get a test large image tile.')
#         .param('z', 'The layer number of the tile (0 is the most zoomed-out '
#                'layer).', paramType='path')
#         .param('x', 'The X coordinate of the tile (0 is the left side).',
#                paramType='path')
#         .param('y', 'The Y coordinate of the tile (0 is the top).',
#                paramType='path')
#         .produces(ImageMimeTypes),
#     )

#     @describeRoute(
#         Description('Get a DeepZoom image tile.')
#         .param('itemId', 'The ID of the item.', paramType='path')
#         .param('level', 'The deepzoom layer number of the tile (8 is the '
#                'most zoomed-out layer).', paramType='path')
#         .param('xandy', 'The X and Y coordinate of the tile in the form '
#                '(x)_(y).(extension) where (0_0 is the left top).',
#                paramType='path')
#         .produces(ImageMimeTypes)
#         .errorResponse('ID was invalid.')
#         .errorResponse('Read access was denied for the item.', 403),
#     )


# # Use repr in URL params to prevent caching across sources/styles
# endpoint = f'tile?z={{z}}&x={{x}}&y={{y}}&encoding=png&repr={self.__repr__()}'


# class MyObject:
#     def __init__(self):
#         self.callback = None

#     def register_callback(self, callback):
#         self.callback = weakref.ref(callback)

#     def __del__(self):
#         if self.callback is not None:
#             self.callback()

# def callback():
#     print("The object has been garbage collected.")

# obj = MyObject()
# obj.register_callback(callback)

# The object will be garbage collected when it is no longer needed.


#  