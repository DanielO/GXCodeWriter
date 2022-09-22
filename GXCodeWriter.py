# Copyright (c) 2022 Daniel O'Connor <darius@dons.net.au>
# GXCode is released under the terms of the BSD 2 clause license

import io
import struct
import traceback

from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread
from PyQt6.QtCore import QBuffer, QByteArray
import UM.Mesh.MeshWriter
from UM.Logger import Logger
import UM.PluginRegistry

gxcode_header_fmt = '<16sIIIIIIIHHHHHHH'

class GXCodeWriter(UM.Mesh.MeshWriter.MeshWriter):
    @call_on_qt_thread
    def write(self, stream, node, mode):
        try:
            self.dowrite(stream)
            Logger.log('w', 'Wrote OK')
            return True
        except Exception as e:
            Logger.log('e', 'Unable to write file: %s' % (e))
            Logger.log('e', traceback.format_exc())
            return False

    def dowrite(self, stream):
        # Generate GCode
        stringio = io.StringIO()
        UM.PluginRegistry.PluginRegistry.getInstance().getPluginObject('GCodeWriter').write(stringio, None)
        stringio.seek(0)
        gcode_data = stringio.read()

        # Generate preview images
        bmpsnap = self.getsnap(80, 60, 'BMP')
        bmpsize = len(bmpsnap)
        pngsnap =  self.getsnap(320,  320, 'PNG')
        pngsize = len(pngsnap)
        bmpofs = struct.calcsize(gxcode_header_fmt)
        pngofs = bmpofs + bmpsize
        gcodeofs = pngofs + pngsize
        unk2 = 0
        ptime = 500
        filusage = 500
        unk3 = 0
        unk4 = 0
        nshells = 2
        pspeed = 10
        ptemp = 55
        extemp = 210
        ex2temp = 210
        unk5 = 0
        hdr = struct.pack(gxcode_header_fmt, b'xgcode 1.0\n\x00\x00\x00\x00\x00',
                          bmpofs, pngofs, gcodeofs, unk2, ptime, filusage, unk3,
                          unk4, nshells, pspeed, ptemp, extemp, ex2temp, unk5)
        stream.write(hdr)
        stream.write(bmpsnap)
        stream.write(pngsnap)
        stream.write(bytes(gcode_data, 'ascii'))

    def getsnap(self, width, height, fmt):
        snap = Snapshot.snapshot(width = width, height = height)
        if snap is None:
            return b''

        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QBuffer.OpenModeFlag.ReadWrite)
        snap.save(buf, fmt)
        dat = buf.data()
        buf.close()
        return dat
