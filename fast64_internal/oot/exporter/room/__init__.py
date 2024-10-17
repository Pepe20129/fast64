from dataclasses import dataclass
from typing import Optional
from mathutils import Matrix
from bpy.types import Object
from ....utility import PluginError, CData, indent
from ....f3d.f3d_gbi import ScrollMethod, TextureExportSettings
from ...room.properties import OOTRoomHeaderProperty
from ...oot_object import addMissingObjectsToAllRoomHeaders
from ...oot_model_classes import OOTModel, OOTGfxFormatter
from ..file import RoomFile
from ..utility import Utility, altHeaderList
from .header import RoomAlternateHeader, RoomHeader
from .shape import RoomShapeUtility, RoomShape, RoomShapeImageMulti, RoomShapeImageBase
import os


@dataclass
class Room:
    """This class defines a room"""

    name: str
    roomIndex: int
    mainHeader: Optional[RoomHeader]
    altHeader: Optional[RoomAlternateHeader]
    roomShape: Optional[RoomShape]
    hasAlternateHeaders: bool

    @staticmethod
    def new(
        name: str,
        transform: Matrix,
        sceneObj: Object,
        roomObj: Object,
        roomShapeType: str,
        model: OOTModel,
        roomIndex: int,
        sceneName: str,
        saveTexturesAsPNG: bool,
    ):
        i = 0
        mainHeaderProps = roomObj.ootRoomHeader
        altHeader = RoomAlternateHeader(f"{name}_alternateHeaders")
        altProp = roomObj.ootAlternateRoomHeaders

        if mainHeaderProps.roomShape == "ROOM_SHAPE_TYPE_IMAGE" and len(mainHeaderProps.bgImageList) == 0:
            raise PluginError(f'Room {roomObj.name} uses room shape "Image" but doesn\'t have any BG images.')

        if mainHeaderProps.roomShape == "ROOM_SHAPE_TYPE_IMAGE" and roomIndex >= 1:
            raise PluginError(f'Room shape "Image" can only have one room in the scene.')

        mainHeader = RoomHeader.new(
            f"{name}_header{i:02}",
            mainHeaderProps,
            sceneObj,
            roomObj,
            transform,
            i,
        )
        hasAlternateHeaders = False

        for i, header in enumerate(altHeaderList, 1):
            altP: OOTRoomHeaderProperty = getattr(altProp, f"{header}Header")
            if not altP.usePreviousHeader:
                hasAlternateHeaders = True
                newRoomHeader = RoomHeader.new(
                    f"{name}_header{i:02}",
                    altP,
                    sceneObj,
                    roomObj,
                    transform,
                    i,
                )
                setattr(altHeader, header, newRoomHeader)

        altHeader.cutscenes = [
            RoomHeader.new(
                f"{name}_header{i:02}",
                csHeader,
                sceneObj,
                roomObj,
                transform,
                i,
            )
            for i, csHeader in enumerate(altProp.cutsceneHeaders, 4)
        ]

        hasAlternateHeaders = True if len(altHeader.cutscenes) > 0 else hasAlternateHeaders
        altHeader = altHeader if hasAlternateHeaders else None
        headers: list[RoomHeader] = [mainHeader]
        if altHeader is not None:
            headers.extend([altHeader.childNight, altHeader.adultDay, altHeader.adultNight])
            if len(altHeader.cutscenes) > 0:
                headers.extend(altHeader.cutscenes)
        addMissingObjectsToAllRoomHeaders(roomObj, headers)

        roomShape = RoomShapeUtility.create_shape(
            sceneName, name, roomShapeType, model, transform, sceneObj, roomObj, saveTexturesAsPNG, mainHeaderProps
        )
        return Room(name, roomIndex, mainHeader, altHeader, roomShape, hasAlternateHeaders)

    def getRoomHeaderFromIndex(self, headerIndex: int) -> RoomHeader | None:
        """Returns the current room header based on the header index"""

        if headerIndex == 0:
            return self.mainHeader

        for i, header in enumerate(altHeaderList, 1):
            if headerIndex == i:
                return getattr(self.altHeader, header)

        for i, csHeader in enumerate(self.altHeader.cutscenes, 4):
            if headerIndex == i:
                return csHeader

        return None

    def getCmdList(self, curHeader: RoomHeader, hasAltHeaders: bool):
        """Returns the room commands list"""

        cmdListData = CData()
        listName = f"SceneCmd {curHeader.name}"

        # .h
        cmdListData.header = f"extern {listName}[];\n"

        # .c
        cmdListData.source = (
            (f"{listName}[]" + " = {\n")
            + (Utility.getAltHeaderListCmd(self.altHeader.name) if hasAltHeaders else "")
            + self.roomShape.get_cmds()
            + curHeader.infos.getCmds()
            + (curHeader.objects.getCmd() if len(curHeader.objects.objectList) > 0 else "")
            + (curHeader.actors.getCmd() if len(curHeader.actors.actorList) > 0 else "")
            + Utility.getEndCmd()
            + "};\n\n"
        )

        return cmdListData

    def getCmdListXML(self, curHeader: RoomHeader, hasAltHeaders: bool, logging_func):
        """Returns the room commands list"""
        logging_func({"INFO"}, "Room.getCmdListXML 0")

        #return (
        #    "<!--" +
        #    f"hasAltHeaders={hasAltHeaders} Utility.getAltHeaderListCmd(self.altHeader.name)={(Utility.getAltHeaderListCmd(self.altHeader.name) if hasAltHeaders else '')}" +
        #    "-->" +
        #    self.roomShape.get_cmds_xml() +
        #    curHeader.infos.getCmdsXML() +
        #    (curHeader.objects.getCmdXML() if len(curHeader.objects.objectList) > 0 else "") +
        #    (curHeader.actors.getCmdXML() if len(curHeader.actors.actorList) > 0 else "") +
        #    Utility.getEndCmdXML()
        #)

        logging_func({"INFO"}, "Room.getCmdListXML 1")
        a = (
            "<!-- " +
            f"hasAltHeaders={hasAltHeaders} Utility.getAltHeaderListCmd(self.altHeader.name)={(Utility.getAltHeaderListCmd(self.altHeader.name) if hasAltHeaders else '')}" +
            "-->"
        )

        logging_func({"INFO"}, "Room.getCmdListXML 2")
        a += Utility.getEndCmdXML()
        logging_func({"INFO"}, "Room.getCmdListXML 3")
        a += self.roomShape.get_cmds_xml()
        logging_func({"INFO"}, "Room.getCmdListXML 4")
        a += curHeader.infos.getCmdsXML()
        logging_func({"INFO"}, "Room.getCmdListXML 5")
        a += (curHeader.objects.getCmdXML() if len(curHeader.objects.objectList) > 0 else "")
        logging_func({"INFO"}, "Room.getCmdListXML 6")
        a += (curHeader.actors.getCmdXML() if len(curHeader.actors.actorList) > 0 else "")
        logging_func({"INFO"}, "Room.getCmdListXML 7")
        a += Utility.getEndCmdXML()
        logging_func({"INFO"}, "Room.getCmdListXML 8")

        return a

    def getRoomMainC(self):
        """Returns the C data of the main informations of a room"""

        roomC = CData()
        roomHeaders: list[tuple[RoomHeader, str]] = []
        altHeaderPtrList = None

        if self.hasAlternateHeaders:
            roomHeaders: list[tuple[RoomHeader, str]] = [
                (self.altHeader.childNight, "Child Night"),
                (self.altHeader.adultDay, "Adult Day"),
                (self.altHeader.adultNight, "Adult Night"),
            ]

            for i, csHeader in enumerate(self.altHeader.cutscenes):
                roomHeaders.append((csHeader, f"Cutscene No. {i + 1}"))

            altHeaderPtrListName = f"SceneCmd* {self.altHeader.name}"

            # .h
            roomC.header = f"extern {altHeaderPtrListName}[];\n"

            # .c
            altHeaderPtrList = (
                f"{altHeaderPtrListName}[]"
                + " = {\n"
                + "\n".join(
                    indent + f"{curHeader.name}," if curHeader is not None else indent + "NULL,"
                    for (curHeader, _) in roomHeaders
                )
                + "\n};\n\n"
            )

        roomHeaders.insert(0, (self.mainHeader, "Child Day (Default)"))
        for i, (curHeader, headerDesc) in enumerate(roomHeaders):
            if curHeader is not None:
                roomC.source += "/**\n * " + f"Header {headerDesc}\n" + "*/\n"
                roomC.source += curHeader.getHeaderDefines()
                roomC.append(self.getCmdList(curHeader, i == 0 and self.hasAlternateHeaders))

                if i == 0 and self.hasAlternateHeaders and altHeaderPtrList is not None:
                    roomC.source += altHeaderPtrList

                if len(curHeader.objects.objectList) > 0:
                    roomC.append(curHeader.objects.getC())

                if len(curHeader.actors.actorList) > 0:
                    roomC.append(curHeader.actors.getC())

        return roomC

    def getRoomMainXML(self, logging_func):
        """Returns the XML data of the main informations of a room"""

        logging_func({"INFO"}, "getRoomMainXML 0")
        roomHeaders: list[tuple[RoomHeader, str]] = []
        altHeaderPtrList = None
        logging_func({"INFO"}, "getRoomMainXML 1")

        if self.hasAlternateHeaders:
            roomHeaders: list[tuple[RoomHeader, str]] = [
                (self.altHeader.childNight, "Child Night"),
                (self.altHeader.adultDay, "Adult Day"),
                (self.altHeader.adultNight, "Adult Night"),
            ]
            logging_func({"INFO"}, "getRoomMainXML 2")

            for i, csHeader in enumerate(self.altHeader.cutscenes):
                roomHeaders.append((csHeader, f"Cutscene No. {i + 1}"))

            logging_func({"INFO"}, "getRoomMainXML 3")
            altHeaderPtrList = (
                "<!-- altHeaderPtrList start -->" +
                "\n".join(
                    (
                        indent +
                        "<!-- " +
                        (f"{curHeader.name} \"{headerDesc}\"" if curHeader is not None else "NULL") +
                        " -->"
                    )
                    for (curHeader, headerDesc) in roomHeaders
                ) +
                "<!-- altHeaderPtrList end -->"
            )
            logging_func({"INFO"}, "getRoomMainXML 4")

        logging_func({"INFO"}, "getRoomMainXML 5")
        roomHeaders.insert(0, (self.mainHeader, "Child Day (Default)"))
        roomXML = ""
        logging_func({"INFO"}, "getRoomMainXML 6")
        for i, (curHeader, headerDesc) in enumerate(roomHeaders):
            if curHeader is not None:
                logging_func({"INFO"}, "getRoomMainXML 7")
                roomXML += f"<!-- Header {i}: \"{headerDesc}\" start -->\n"
                logging_func({"INFO"}, "getRoomMainXML 8")

                roomXML += self.getCmdListXML(curHeader, i == 0 and self.hasAlternateHeaders, logging_func)
                logging_func({"INFO"}, "getRoomMainXML 9")

                if i == 0 and self.hasAlternateHeaders and altHeaderPtrList is not None:
                    roomXML += altHeaderPtrList
                logging_func({"INFO"}, "getRoomMainXML 10")

                if len(curHeader.objects.objectList) > 0:
                    roomXML += curHeader.objects.getXML()
                logging_func({"INFO"}, "getRoomMainXML 11")

                if len(curHeader.actors.actorList) > 0:
                    roomXML += curHeader.actors.getXML()
                logging_func({"INFO"}, "getRoomMainXML 12")

                roomXML += f"<!-- Header {i}: \"{headerDesc}\" end -->\n"

        return roomXML

    def getRoomShapeModelC(self, textureSettings: TextureExportSettings):
        """Returns the C data of the room model"""
        roomModel = CData()

        for i, entry in enumerate(self.roomShape.dl_entries):
            if entry.opaque is not None:
                roomModel.append(entry.opaque.to_c(self.roomShape.model.f3d))

            if entry.transparent is not None:
                roomModel.append(entry.transparent.to_c(self.roomShape.model.f3d))

            # type ``ROOM_SHAPE_TYPE_IMAGE`` only allows 1 room
            if i == 0 and isinstance(self.roomShape, RoomShapeImageBase):
                break

        roomModel.append(self.roomShape.model.to_c(textureSettings, OOTGfxFormatter(ScrollMethod.Vertex)).all())

        if isinstance(self.roomShape, RoomShapeImageMulti):
            # roomModel.append(self.roomShape.multiImg.getC()) # Error? double call in getRoomShapeC()?
            roomModel.append(self.roomShape.to_c_img(textureSettings.includeDir))

        return roomModel

    def getRoomShapeModelXML(self, textureSettings: TextureExportSettings, resourceBasePath: str, logging_func):
        """Returns the XML data of the room model"""
        roomModel = ""
        logging_func({"INFO"}, "getRoomShapeModelXML 0")

        for i, entry in enumerate(self.roomShape.dl_entries):
            if entry.opaque is not None:
                logging_func({"INFO"}, f"getRoomShapeModelXML 1")
                roomModel += "<!-- getRoomShapeModelXML entry.opaque start "
                roomModel += entry.opaque.to_xml(resourceBasePath[:-1], resourceBasePath[:-1])
                roomModel += " getRoomShapeModelXML entry.opaque end -->"

            if entry.transparent is not None:
                logging_func({"INFO"}, "getRoomShapeModelXML 2")
                roomModel += "<!-- getRoomShapeModelXML entry.transparent start "
                roomModel += entry.transparent.to_xml(resourceBasePath[:-1], resourceBasePath[:-1])
                roomModel += " getRoomShapeModelXML entry.transparent end -->"

            logging_func({"INFO"}, f"getRoomShapeModelXML 2.5 self.roomShape={self.roomShape}")

            # type ``ROOM_SHAPE_TYPE_IMAGE`` only allows 1 room
            if i == 0 and isinstance(self.roomShape, RoomShapeImageBase):
                break

        logging_func(
            {"INFO"},
            "getRoomShapeModelXML 3 textureExportSettings.exportPath=" +
            (textureSettings.exportPath if textureSettings.exportPath is not None else "None"),
        )
        logging_func(
            {"INFO"}, "getRoomShapeModelXML 4 resourceBasePath=" +
            (resourceBasePath if resourceBasePath is not None else "None")
        )
        roomModel += "<!-- getRoomShapeModelXML self.roomShape.to_xml start -->"
        roomModel += self.roomShape.model.to_xml(
            os.path.join(textureSettings.exportPath, ""), resourceBasePath[:-1], logging_func
        )
        roomModel += "<!-- getRoomShapeModelXML self.roomShape.to_xml end -->"


        if isinstance(self.roomShape, RoomShapeImageMulti):
            # roomModel.append(self.roomShape.multiImg.getC()) # Error? double call in getRoomShapeC()?
            roomModel += f"<!-- self.roomShape.to_c_img(textureSettings.includeDir)={self.roomShape.to_c_img(textureSettings.includeDir)} -->"

    def getNewRoomFile(self, path: str, isSingleFile: bool, textureExportSettings: TextureExportSettings):
        """Returns a new ``RoomFile`` element"""

        roomMainData = self.getRoomMainC()
        roomModelData = self.getRoomShapeModelC(textureExportSettings)
        roomModelInfoData = self.roomShape.to_c()

        return RoomFile(
            self.name,
            roomMainData.source,
            roomModelData.source,
            roomModelInfoData.source,
            isSingleFile,
            path,
            roomMainData.header + roomModelData.header + roomModelInfoData.header,
        )

    def getNewRoomFileXML(self, path: str, isSingleFile: bool, textureExportSettings: TextureExportSettings, resourceBasePath: str, logging_func):
        """Returns a new ``RoomFile`` element"""

        logging_func({"INFO"}, "getNewRoomFileXML 0")
        roomMainData = self.getRoomMainXML(logging_func)
        logging_func({"INFO"}, "getNewRoomFileXML 1")
        roomModelData = self.getRoomShapeModelXML(textureExportSettings, resourceBasePath, logging_func)
        logging_func({"INFO"}, "getNewRoomFileXML 2")
        roomModelInfoData = self.roomShape.to_xml()
        logging_func({"INFO"}, "getNewRoomFileXML 3")

        return RoomFile(
            self.name,
            roomMainData,
            roomModelData,
            roomModelInfoData,
            isSingleFile,
            path,
            ""
        )
