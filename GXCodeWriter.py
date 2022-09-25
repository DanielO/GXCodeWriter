# Copyright (c) 2022 Daniel O'Connor <darius@dons.net.au>
# GXCode is released under the terms of the BSD 2 clause license

import io
import pdb
import struct
import traceback

from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread
from PyQt6.QtCore import QBuffer, QByteArray
import UM.Mesh.MeshWriter
from UM.Logger import Logger
from UM.Qt.Duration import DurationFormat
import UM.PluginRegistry
import UM.Application

gxcode_header_fmt = '<16sIIIIIIIHHHHHHH'

dev = False

class GXCodeWriter(UM.Mesh.MeshWriter.MeshWriter):
    # Need to run on the Qt thread otherwise grabbing snapshots won't work
    @call_on_qt_thread
    def write(self, stream, node, mode):
        try:
            self.dowrite(stream)
            return True
        except Exception as e:
            Logger.log('e', 'Unable to write file: %s' % (e))
            Logger.log('e', traceback.format_exc())
            if dev:
                pdb.set_trace()
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

        app = UM.Application.Application.getInstance()
        exts = app.getExtruderManager().getActiveExtruderStacks()
        extemp = int(exts[0].getProperty('material_print_temperature', 'value'))
        if len(exts) > 1:
            ex2temp = int(exts[1].getProperty('material_print_temperature', 'value'))
        else:
            ex2temp = extemp
        nshells = exts[0].getProperty('wall_line_count', 'value')
        ptemp = int(exts[0].getProperty('material_bed_temperature', 'value'))
        pspeed = int(exts[0].getProperty('speed_print', 'value'))

        pinf = app.getPrintInformation()
        filusage = int(sum(pinf.materialLengths) * 1000) # metres to millimetres

        ptime = int(pinf.currentPrintTime.getDisplayString(DurationFormat.Format.Seconds))

        # Dummy up other header parameters
        unk2 = 0
        unk3 = 0
        unk4 = 0
        unk5 = 0

        # Break to debugger
        if dev:
            pdb.set_trace()

        # Assemble header blob
        hdr = struct.pack(gxcode_header_fmt, b'xgcode 1.0\n\x00\x00\x00\x00\x00',
                          bmpofs, pngofs, gcodeofs, ptime, filusage, unk2, unk3,
                          unk4, nshells, pspeed, ptemp, extemp, ex2temp, unk5)

        # Write everything out
        stream.write(hdr)
        stream.write(bmpsnap)
        stream.write(pngsnap)
        stream.write(bytes(gcode_data, 'ascii'))

    def getsnap(self, width, height, fmt):
        '''Helper function to create a snapshot image in the requested format and return it as a binary string'''
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
