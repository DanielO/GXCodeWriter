# Copyright (c) 2022 Daniel O'Connor <darius@dons.net.au>
# GXCode is released under the terms of the BSD 2 clause license

from . import GXCodeWriter

import UM.Mesh.MeshWriter
from UM.i18n import i18nCatalog
catalog = i18nCatalog("gxcode")

def getMetaData():
    return {
        "mesh_writer": {
            "output": [{
                "extension": "gx",
                "description": catalog.i18nc("GXCode Writer File Description", "GXCode File"),
                "mime_type": "application/gx",
                "mode": UM.Mesh.MeshWriter.MeshWriter.OutputMode.BinaryMode
            }]
        }
    }

def register(app):
    return { "mesh_writer": GXCodeWriter.GXCodeWriter() }
