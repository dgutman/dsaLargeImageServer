### These are bits I have extracted from the wsi-deid plugin to remove some of the dependencies
## on the entire DSA stack

## The functions are largely taken from this library
#! pip install git+https://github.com/DigitalSlideArchive/DSA-WSI-DeID.git
# I reluctantly decided to strip them out, as the DSA-WSI-DeID package has a huge number
# of dependencies making it easier to just strip out what I need and refactor the functions
# Otherwise everything needs to be on a DSA server and can't be used independently

import large_image
from girder_large_image.models import image_item
import tempfile, os, math, io
from girder import logger
import PIL.Image, PIL.ImageDraw, PIL.ImageFont, PIL.ImageOps
import tifftools
from lxml import etree as lxmlElementTree
import large_image
import config
import shutil

## NOTE: FLAG IS SET TO ALWAYS REMOVE CELL LABEL... THIS IS ON CONFIG.py


valid_formats = ["aperio"]
# import large_image_source_tiff.girder_source
# from large_image_source_tiff import TiffFileTileSource

# import xml.etree.ElementTree
# from girder_large_image.models.image_item import ImageItem  <<< MAY ADD THIS AS A NULL CLASS?
# from large_image.tilesource import dictToEtree

## TO Think about:  Generate a class that inherits from ImageItem but doesn't do anything
## This would avoid having to edit as many functions going forward

from deidFunctions_wsideid import (
    metadata_field_count,
    get_redact_list,
    get_standard_redactions_format_aperio,
    redact_topleft_square,
    get_deid_field_dict,
    determine_format,
    redact_format_aperio_add_image,
    redact_tiff_tags,
    add_deid_metadata,
    model_information,
    generate_system_redaction_list_entry,
    redact_image_area,
    get_generated_title,
    redact_format_aperio_philips_redact_wsi,
)

__version__ = "0.0.1"
debug = True
available_formats = ["aperio"]


## This is monkey patching the full DSA ImageItem() object so I can use as much
## upsteam code and functions without modification
class ImageItem:
    def __init__(self, item):
        self._tileSource = item.tileSource

    @property
    def tileSource(self):
        return self._tileSource


## Have both name, and filename.. likely can remove one of these
class DeIdImageItem:
    def __init__(self, filePath=None, metadata=None):
        # print(filePath,"is the file path")
        self.metadata = metadata if metadata else {}
        self.filePath = filePath
        self.filename = os.path.basename(filePath) if self.filePath else None
        self.name = os.path.basename(filePath) if self.filePath else None
        #  self.largeImage = self.tileSource.getMetadata() if self.tileSource else None
        self.meta = {"largeImage": True}
        self._largeImagePath = self.filePath

        ## TO DO ADD AN ERROR IF TILESOURCE IS NOT ACCESSIBLE / CAN BE OPENED
        self.tileSource = large_image.open(filePath)

    def update_metadata(self, new_metadata):
        self.metadata.update(new_metadata)

    def get_metadata(self):
        return self.metadata

    def get_meta(self):
        return self.metadata

    def get_tile_source(self, *args, **kwargs):
        # Your implementation here
        print("Crap nuggets")
        pass

    def __iter__(self):
        for key, value in self.meta.items():
            yield (key, value)

    def getMetadata(self, item, **kwargs):

        return self.tileSource().getMetadata()

    def get(self, key, default=None):
        return self.meta.get(key, default)

    def _largeImagePath(self, item, **kwargs):
        return self.filePath

    def __getitem__(self, key):
        if key == "name":
            return self.name
        else:
            return self.meta.get(key, None)


## TO DO:  Move these class definitions to a separate file
image_item.ImageItem = DeIdImageItem


## NOT SURE IF I HAVE TO HAVE THE HLEPER FUNCTIONS DECLARED ABOVE?
## This is based on the function redact_item from process.py
def deid_workflow():
    sampleSlide = (
        "data/CMU-2-backup.svs"
    )
    print('Sample slide', sampleSlide)
    # return

    with tempfile.TemporaryDirectory(prefix="wsi_deid") as tempdir:
        print('In tempdir')

        ts = large_image.open(sampleSlide)
        print('ts created')
        
        curItem = DeIdImageItem(sampleSlide)
        print('Here')

        redactList = get_standard_redactions(curItem, "Iamacoolslidename.svs")
        print('Redact list', redactList)
        
        newTitle = get_generated_title(
            curItem
        )  # The newtitle is the filename without the extension
        tileSource = curItem.tileSource
        labelImage = None
        label_geojson = redactList.get("images", {}).get("label", {}).get("geojson")

        ## TO IMPLEMENT...
        if (
            "label" not in redactList["images"]
            and not config.getConfig("always_redact_label")
        ) or label_geojson is not None:
            try:
                labelImage = PIL.Image.open(
                    io.BytesIO(tileSource.getAssociatedImage("label")[0])
                )
                # ImageItem().removeThumbnailFiles(item) Verify if this is needed.. I think it is not
            except Exception:
                pass
        if label_geojson is not None and labelImage is not None:
            labelImage = redact_image_area(labelImage, label_geojson)
        if config.getConfig("add_title_to_label"):
            labelImage = add_title_to_image(labelImage, newTitle, False, item=curItem)
        macroImage = None
        macro_geojson = redactList.get("images", {}).get("macro", {}).get("geojson")
        redact_square_default = "macro" not in redactList[
            "images"
        ] and config.getConfig("redact_macro_square")
        redact_square_manual = "macro" in redactList["images"] and redactList["images"][
            "macro"
        ].get("square")
        redact_square = redact_square_default or redact_square_manual
        if redact_square or macro_geojson:
            try:
                macroImage = PIL.Image.open(
                    io.BytesIO(tileSource.getAssociatedImage("macro")[0])
                )
                # ImageItem().removeThumbnailFiles(item)
            except Exception:
                pass
        if macroImage is not None:
            if redact_square:
                macroImage = redact_topleft_square(macroImage)
            elif macro_geojson:
                macroImage = redact_image_area(macroImage, macro_geojson)
        format = determine_format(tileSource)

        if format not in ["aperio"]:
            return f"FORMAT NOT AVAILABLE FOR DEID YET: {format}"

        func = None
        if format is not None:
            # fadvise_willneed(curItem)  ## DETERMINE WHAT THIS FUNCTION DOSE..
            func = globals().get("redact_format_" + format)
        if func is None:
            raise Exception("Cannot redact this format.")
        file, mimetype = func(
            curItem, tempdir, redactList, newTitle, labelImage, macroImage
        )
        info = {
            "format": format,
            "model": model_information(tileSource, format),
            "mimetype": mimetype,
            "redactionCount": {
                key: len([k for k, v in redactList[key].items() if v["value"] is None])
                for key in redactList
                if key != "area"
            },
            "fieldCount": {
                "metadata": metadata_field_count(tileSource, format, redactList),
                "images": len(tileSource.getAssociatedImagesList()),
            },
        }
        print(tileSource)
        print(newTitle, "is the new title..")
        print(redactList, "was generated...")
        print(file)
        print(info)
        print(os.listdir(tempdir))

        for f in os.listdir(tempdir):
            fp = os.path.join(tempdir, f)
            print(f"Copying file from {fp} to ./output/{f}")
            shutil.copy(fp, f"./output/{f}")

        return file, info


## MODIFIED FROM UPSTREAM
def get_standard_redactions(item, title):
    """
    Produce a standardize redaction list based on format.

    :param item: a Girder item.
    :param title: the new title of the image.
    :returns: a redactList.
    """

    tileSource = item.tileSource  ## MOD was ImageItem()
    sourcePath = tileSource._getLargeImagePath()
    func = None
    format = determine_format(tileSource)
    if debug:
        print("Detected format was", format)  ## MOD added for debug

    if format is not None:
        func = globals().get("get_standard_redactions_format_" + format)
    try:
        tiffinfo = tifftools.read_tiff(sourcePath)
        ifds = tiffinfo["ifds"]
    except Exception:
        tiffinfo = None
    if func:
        redactList = func(item, tileSource, tiffinfo, title)
    else:
        redactList = {
            "images": {},
            "metadata": {},
        }
    if tiffinfo:
        for key in {"DateTime"}:
            tag = tifftools.Tag[key].value
            if tag in ifds[0]["tags"]:
                value = ifds[0]["tags"][tag]["data"]
                if len(value) >= 10:
                    value = value[:5] + "01:01" + value[10:]
                else:
                    value = None
                redactList["metadata"]["internal;openslide;tiff.%s" % key] = (
                    generate_system_redaction_list_entry(value)
                )
        # Make, Model, Software?
        for key in {"Copyright", "HostComputer"}:
            tag = tifftools.Tag[key].value
            if tag in ifds[0]["tags"]:
                redactList["metadata"]["internal;openslide;tiff.%s" % key] = {
                    "value": None,
                    "automatic": True,
                }
    return redactList


## MODIFIED
def fadvise_willneed(item):
    """
    Tell the os we will need to read the entire file.

    :param item: the girder item.
    """
    try:
        tileSource = item.tileSource
        path = tileSource._getLargeImagePath()
        fptr = open(path, "rb")
        os.posix_fadvise(
            fptr.fileno(), 0, os.path.getsize(path), os.POSIX_FADV_WILLNEED
        )
    except Exception:
        pass


## MODIFIED
def redact_format_aperio(item, tempdir, redactList, title, labelImage, macroImage):
    """
    Redact aperio files.

    :param item: the item to redact.
    :param tempdir: a directory for work files and the final result.
    :param redactList: the list of redactions (see get_redact_list).
    :param title: the new title for the item.
    :param labelImage: a PIL image with a new label image.
    :param macroImage: a PIL image with a new macro image.  None to keep or
        redact the current macro image.
    :returns: (filepath, mimetype) The redacted filepath in the tempdir and
        its mimetype.
    """
    # import large_image_source_tiff.girder_source

    tileSource = item.tileSource  ##MODDED
    sourcePath = tileSource._getLargeImagePath()
    logger.info("Redacting aperio file %s", sourcePath)
    tiffinfo = tifftools.read_tiff(sourcePath)
    ifds = tiffinfo["ifds"]
    if redactList.get("area", {}).get("_wsi", {}).get("geojson"):
        ifds = redact_format_aperio_philips_redact_wsi(
            tileSource, ifds, redactList["area"]["_wsi"]["geojson"], tempdir
        )
        ## ImageItem().removeThumbnailFiles(item) TBD
    aperioValues = aperio_value_list(item, redactList, title)
    imageDescription = "|".join(aperioValues)
    # We expect aperio to have the full resolution image in directory 0, the
    # thumbnail in directory 1, lower resolutions starting in 2, and label and
    # macro images in other directories.  Confirm this -- our tiff reader will
    # report the directories used for the full resolution.
    tiffSource = TiffFileTileSource(item._largeImagePath)
    mainImageDir = [
        dir._directoryNum for dir in tiffSource._tiffDirectories[::-1] if dir
    ]
    associatedImages = tileSource.getAssociatedImagesList()
    if mainImageDir != [
        d + (1 if d and "thumbnail" in associatedImages else 0)
        for d in range(len(mainImageDir))
    ]:
        raise Exception("Aperio TIFF directories are not in the expected order.")
    firstAssociatedIdx = max(mainImageDir) + 1
    # Set new image description
    ifds[0]["tags"][tifftools.Tag.ImageDescription.value] = {
        "datatype": tifftools.Datatype.ASCII,
        "data": imageDescription,
    }
    # redact or adjust thumbnail
    if "thumbnail" in associatedImages:
        if "thumbnail" in redactList["images"]:
            ifds.pop(1)
            firstAssociatedIdx -= 1
        else:
            thumbnailComment = ifds[1]["tags"][tifftools.Tag.ImageDescription.value][
                "data"
            ]
            thumbnailDescription = "|".join(
                thumbnailComment.split("|", 1)[0:1] + aperioValues[1:]
            )
            ifds[1]["tags"][tifftools.Tag.ImageDescription.value][
                "data"
            ] = thumbnailDescription
    # redact other images
    for idx in range(len(ifds) - 1, 0, -1):
        ifd = ifds[idx]
        key = None
        keyparts = (
            ifd["tags"]
            .get(tifftools.Tag.ImageDescription.value, {})
            .get("data", "")
            .split("\n", 1)[-1]
            .strip()
            .split()
        )
        if len(keyparts) and keyparts[0].lower() and not keyparts[0][0].isdigit():
            key = keyparts[0].lower()
        if (
            key is None
            and ifd["tags"].get(tifftools.Tag.NewSubfileType.value)
            and ifd["tags"][tifftools.Tag.NewSubfileType.value]["data"][0]
            & tifftools.Tag.NewSubfileType.bitfield.ReducedImage.value
        ):
            key = (
                "label"
                if ifd["tags"][tifftools.Tag.NewSubfileType.value]["data"][0] == 1
                else "macro"
            )
        if (
            key in redactList["images"]
            or key == "label"
            or (key == "macro" and macroImage)
        ):
            ifds.pop(idx)
    # Add back label and macro image
    if macroImage:
        redact_format_aperio_add_image(
            "macro", macroImage, ifds, firstAssociatedIdx, tempdir, aperioValues
        )
    if labelImage:
        redact_format_aperio_add_image(
            "label", labelImage, ifds, firstAssociatedIdx, tempdir, aperioValues
        )
    # redact general tiff tags
    redact_tiff_tags(ifds, redactList, title)
    add_deid_metadata(item, ifds)
    outputPath = os.path.join(tempdir, "aperio.svs")
    tifftools.write_tiff(ifds, outputPath)
    logger.info("Redacted aperio file %s as %s", sourcePath, outputPath)
    return outputPath, "image/tiff"


def orig_aperio_value_list(item, redactList, title):
    """
    Get a list of aperio values that can be joined with | to form the aperio
    comment.

    :param item: the item to redact.
    :param redactList: the list of redactions (see get_redact_list).
    :param title: the new title for the item.
    """
    tileSource = ImageItem().tileSource(item)
    metadata = tileSource.getInternalMetadata() or {}
    comment = metadata["openslide"]["openslide.comment"]
    aperioHeader = comment.split("|", 1)[0]
    # Add defaults for required aperio fields to this dictionary
    aperioDict = {}
    for fullkey, value in metadata["openslide"].items():
        if fullkey.startswith("aperio."):
            redactKey = "internal;openslide;" + fullkey.replace("\\", "\\\\").replace(
                ";", "\\;"
            )
            value = redactList["metadata"].get(redactKey, {}).get("value", value)
            if value is not None and "|" not in value:
                key = fullkey.split(".", 1)[1]
                if key.startswith("CustomField."):
                    continue
                aperioDict[key] = value
    # From DeID Upload information
    aperioDict.update(get_deid_field_dict(item))
    # Required values
    aperioDict.update(
        {
            "Filename": title,
            "Title": title,
        }
    )
    aperioValues = [aperioHeader] + [
        "%s = %s" % (k, v) for k, v in sorted(aperioDict.items())
    ]
    return aperioValues


## MODIFIED
def aperio_value_list(item, redactList, title):
    """
    Get a list of aperio values that can be joined with | to form the aperio
    comment.

    :param item: the item to redact.
    :param redactList: the list of redactions (see get_redact_list).
    :param title: the new title for the item.
    """
    tileSource = item.tileSource  # MODIFIED
    metadata = tileSource.getInternalMetadata() or {}
    comment = metadata["openslide"]["openslide.comment"]
    aperioHeader = comment.split("|", 1)[0]
    # Add defaults for required aperio fields to this dictionary
    aperioDict = {}
    for fullkey, value in metadata["openslide"].items():
        if fullkey.startswith("aperio."):
            redactKey = "internal;openslide;" + fullkey.replace("\\", "\\\\").replace(
                ";", "\\;"
            )
            value = redactList["metadata"].get(redactKey, {}).get("value", value)
            if value is not None and "|" not in value:
                key = fullkey.split(".", 1)[1]
                if key.startswith("CustomField."):
                    continue
                aperioDict[key] = value
    # From DeID Upload information
    aperioDict.update(get_deid_field_dict(item))
    # Required values
    aperioDict.update(
        {
            "Filename": title,
            "Title": title,
        }
    )
    aperioValues = [aperioHeader] + [
        "%s = %s" % (k, v) for k, v in sorted(aperioDict.items())
    ]
    return aperioValues


""" TO DO:  VALIDATE THAT THE IMAGE FONT FILE IS LOCATED AND COPIED INTO THE
CONTAINER IMAGE"""


def add_title_to_image(
    image,
    title,
    previouslyAdded=False,
    minWidth=384,
    background="#000000",
    textColor="#ffffff",
    square=True,
    item=None,
):
    """
    Add a title to an image.  If the image doesn't exist, a new image is made
    the minimum width and appropriate height.  If the image does exist, a bar
    is added at its top to hold the title.  If an existing image is smaller
    than minWidth, it is pillarboxed to the minWidth.

    :param image: a PIL image or None.
    :param title: a text string.
    :param previouslyAdded: if true and modifying an image, don't allocate more
        space for the title; overwrite the top of the image instead.
    :param minWidth: the minimum width for the new image.
    :param background: the background color of the title and any necessary
        pillarbox.
    :param textColor: the color of the title text.
    :param square: if True, output a square image.
    :param item: the original item record.
    :returns: a PIL image.
    """
    title = title or ""
    mode = "RGB"
    if image is None:
        image = PIL.Image.new(mode, (0, 0))
    image = image.convert(mode)
    w, h = image.size
    background = PIL.ImageColor.getcolor(background, mode)
    textColor = PIL.ImageColor.getcolor(textColor, mode)
    targetW = max(minWidth, w)
    fontSize = 0.15
    imageDraw = PIL.ImageDraw.Draw(image)
    for iter in range(3, 0, -1):
        try:
            imageDrawFont = PIL.ImageFont.truetype(
                font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                size=int(fontSize * targetW),
            )
        except IOError:
            try:
                imageDrawFont = PIL.ImageFont.truetype(size=int(fontSize * targetW))
            except IOError:
                imageDrawFont = PIL.ImageFont.load_default()
        textL, textT, textR, textB = imageDrawFont.getbbox(title)
        textW = textR - textL
        textH = textB  # from old imageDraw.textsize(title, imageDrawFont)
        if iter != 1 and (textW > targetW * 0.95 or textW < targetW * 0.85):
            fontSize = fontSize * targetW * 0.9 / textW
    titleH = int(math.ceil(textH * 1.25))
    if square and (w != h or (not previouslyAdded or w != targetW or h < titleH)):
        if targetW < h + titleH:
            targetW = h + titleH
        else:
            titleH = targetW - h
    if previouslyAdded and w == targetW and h >= titleH:
        newImage = image.copy()
    else:
        newImage = PIL.Image.new(
            mode=mode, size=(targetW, h + titleH), color=background
        )
        newImage.paste(image, (int((targetW - w) / 2), titleH))
    imageDraw = PIL.ImageDraw.Draw(newImage)
    imageDraw.rectangle((0, 0, targetW, titleH), fill=background, outline=None, width=0)
    imageDraw.text(
        xy=(int((targetW - textW) / 2), int((titleH - textH) / 2)),
        text=title,
        fill=textColor,
        font=imageDrawFont,
    )
    return newImage
