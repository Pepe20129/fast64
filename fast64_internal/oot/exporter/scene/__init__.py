from dataclasses import dataclass
from mathutils import Matrix
from bpy.types import Object
from typing import Optional
from ....utility import PluginError, CData, indent
from ....f3d.f3d_gbi import TextureExportSettings, ScrollMethod
from ...scene.properties import OOTSceneHeaderProperty
from ...oot_model_classes import OOTModel, OOTGfxFormatter
from ..file import SceneFile
from ..utility import Utility, altHeaderList
from ..collision import CollisionHeader
from .header import SceneAlternateHeader, SceneHeader
from .rooms import RoomEntries


@dataclass
class Scene:
    """This class defines a scene"""

    name: str
    model: OOTModel
    mainHeader: Optional[SceneHeader]
    altHeader: Optional[SceneAlternateHeader]
    rooms: Optional[RoomEntries]
    colHeader: Optional[CollisionHeader]
    hasAlternateHeaders: bool

    @staticmethod
    def new(name: str, sceneObj: Object, transform: Matrix, useMacros: bool, saveTexturesAsPNG: bool, model: OOTModel):
        i = 0
        rooms = RoomEntries.new(
            f"{name}_roomList", name.removesuffix("_scene"), model, sceneObj, transform, saveTexturesAsPNG
        )

        colHeader = CollisionHeader.new(
            f"{name}_collisionHeader",
            name,
            sceneObj,
            transform,
            useMacros,
            True,
        )

        mainHeader = SceneHeader.new(f"{name}_header{i:02}", sceneObj.ootSceneHeader, sceneObj, transform, i, useMacros)
        hasAlternateHeaders = False
        altHeader = SceneAlternateHeader(f"{name}_alternateHeaders")
        altProp = sceneObj.ootAlternateSceneHeaders

        for i, header in enumerate(altHeaderList, 1):
            altP: OOTSceneHeaderProperty = getattr(altProp, f"{header}Header")
            if not altP.usePreviousHeader:
                setattr(
                    altHeader, header, SceneHeader.new(f"{name}_header{i:02}", altP, sceneObj, transform, i, useMacros)
                )
                hasAlternateHeaders = True

        altHeader.cutscenes = [
            SceneHeader.new(f"{name}_header{i:02}", csHeader, sceneObj, transform, i, useMacros)
            for i, csHeader in enumerate(altProp.cutsceneHeaders, 4)
        ]

        hasAlternateHeaders = True if len(altHeader.cutscenes) > 0 else hasAlternateHeaders
        altHeader = altHeader if hasAlternateHeaders else None
        return Scene(name, model, mainHeader, altHeader, rooms, colHeader, hasAlternateHeaders)

    def validateRoomIndices(self):
        """Checks if there are multiple rooms with the same room index"""

        for i, room in enumerate(self.rooms.entries):
            if i != room.roomIndex:
                return False
        return True

    def validateScene(self):
        """Performs safety checks related to the scene data"""

        if not len(self.rooms.entries) > 0:
            raise PluginError("ERROR: This scene does not have any rooms!")

        if not self.validateRoomIndices():
            raise PluginError("ERROR: Room indices do not have a consecutive list of indices.")

    def getSceneHeaderFromIndex(self, headerIndex: int) -> SceneHeader | None:
        """Returns the scene header based on the header index"""

        if headerIndex == 0:
            return self.mainHeader

        for i, header in enumerate(altHeaderList, 1):
            if headerIndex == i:
                return getattr(self.altHeader, header)

        for i, csHeader in enumerate(self.altHeader.cutscenes, 4):
            if headerIndex == i:
                return csHeader

        return None

    def getCmdList(self, curHeader: SceneHeader, hasAltHeaders: bool):
        """Returns the scene's commands list"""

        cmdListData = CData()
        listName = f"SceneCmd {curHeader.name}"

        # .h
        cmdListData.header = f"extern {listName}[]" + ";\n"

        # .c
        cmdListData.source = (
            (f"{listName}[]" + " = {\n")
            + (Utility.getAltHeaderListCmd(self.altHeader.name) if hasAltHeaders else "")
            + self.colHeader.getCmd()
            + self.rooms.getCmd()
            + curHeader.infos.getCmds(curHeader.lighting)
            + curHeader.lighting.getCmd()
            + curHeader.path.getCmd()
            + (curHeader.transitionActors.getCmd() if len(curHeader.transitionActors.entries) > 0 else "")
            + curHeader.spawns.getCmd()
            + curHeader.entranceActors.getCmd()
            + (curHeader.exits.getCmd() if len(curHeader.exits.exitList) > 0 else "")
            + (curHeader.cutscene.getCmd() if len(curHeader.cutscene.entries) > 0 else "")
            + Utility.getEndCmd()
            + "};\n\n"
        )

        return cmdListData

    def getCmdListXML(self, curHeader: SceneHeader, hasAltHeaders: bool, logging_func):
        """Returns the scene's commands list"""

        #return (
        #    "<!-- " + (Utility.getAltHeaderListCmd(self.altHeader.name) if hasAltHeaders else "!hasAltHeaders") + " -->"
        #    + self.colHeader.getCmdXML()
        #    + self.rooms.getCmdXML()
        #    + curHeader.infos.getCmdsXML(curHeader.lighting)
        #    + curHeader.lighting.getCmdXML()
        #    + curHeader.path.getCmdXML()
        #    + (curHeader.transitionActors.getCmdXML() if len(curHeader.transitionActors.entries) > 0 else "")
        #    + curHeader.spawns.getCmdXML()
        #    + curHeader.entranceActors.getCmdXML()
        #    + (curHeader.exits.getCmdXML() if len(curHeader.exits.exitList) > 0 else "")
        #    + indent + "<!-- TODO: Cutscenes -->\n" # (curHeader.cutscene.getCmd() if len(curHeader.cutscene.entries) > 0 else "")
        #    + Utility.getEndCmdXML()
        #)

        logging_func({"INFO"}, "Scene.getCmdListXML 0")
        a = "<!-- " + (Utility.getAltHeaderListCmd(self.altHeader.name) if hasAltHeaders else "!hasAltHeaders") + " -->"
        logging_func({"INFO"}, "Scene.getCmdListXML 1")
        a += self.colHeader.getCmdXML()
        logging_func({"INFO"}, "Scene.getCmdListXML 2")
        a += self.rooms.getCmdXML(logging_func)
        logging_func({"INFO"}, "Scene.getCmdListXML 3")
        a += curHeader.infos.getCmdsXML(curHeader.lighting)
        logging_func({"INFO"}, "Scene.getCmdListXML 4")
        a += curHeader.lighting.getCmdXML()
        logging_func({"INFO"}, "Scene.getCmdListXML 5")
        a += curHeader.path.getCmdXML()
        logging_func({"INFO"}, "Scene.getCmdListXML 6")
        a += (curHeader.transitionActors.getCmdXML() if len(curHeader.transitionActors.entries) > 0 else "")
        logging_func({"INFO"}, "Scene.getCmdListXML 7")
        a += curHeader.spawns.getCmdXML()
        logging_func({"INFO"}, "Scene.getCmdListXML 8")
        a += curHeader.entranceActors.getCmdXML()
        logging_func({"INFO"}, "Scene.getCmdListXML 9")
        a += (curHeader.exits.getCmdXML() if len(curHeader.exits.exitList) > 0 else "")
        logging_func({"INFO"}, "Scene.getCmdListXML 10")
        a += indent + "<!-- TODO: Cutscenes -->\n" # (curHeader.cutscene.getCmd() if len(curHeader.cutscene.entries) > 0 else "")
        logging_func({"INFO"}, "Scene.getCmdListXML 11")
        a += Utility.getEndCmdXML()
        logging_func({"INFO"}, "Scene.getCmdListXML 12")

        return a

    def getSceneMainC(self):
        """Returns the main informations of the scene as ``CData``"""

        sceneC = CData()
        headers: list[tuple[SceneHeader, str]] = []
        altHeaderPtrs = None

        if self.hasAlternateHeaders:
            headers = [
                (self.altHeader.childNight, "Child Night"),
                (self.altHeader.adultDay, "Adult Day"),
                (self.altHeader.adultNight, "Adult Night"),
            ]

            for i, csHeader in enumerate(self.altHeader.cutscenes):
                headers.append((csHeader, f"Cutscene No. {i + 1}"))

            altHeaderPtrs = "\n".join(
                indent + curHeader.name + "," if curHeader is not None else indent + "NULL," if i < 4 else ""
                for i, (curHeader, _) in enumerate(headers, 1)
            )

        headers.insert(0, (self.mainHeader, "Child Day (Default)"))
        for i, (curHeader, headerDesc) in enumerate(headers):
            if curHeader is not None:
                sceneC.source += "/**\n * " + f"Header {headerDesc}\n" + "*/\n"
                sceneC.append(self.getCmdList(curHeader, i == 0 and self.hasAlternateHeaders))

                if i == 0:
                    if self.hasAlternateHeaders and altHeaderPtrs is not None:
                        altHeaderListName = f"SceneCmd* {self.altHeader.name}[]"
                        sceneC.header += f"extern {altHeaderListName};\n"
                        sceneC.source += altHeaderListName + " = {\n" + altHeaderPtrs + "\n};\n\n"

                    # Write the room segment list
                    sceneC.append(self.rooms.getC(self.mainHeader.infos.useDummyRoomList))

                sceneC.append(curHeader.getC())

        return sceneC

    def getSceneMainXML(self, logging_func):
        """Returns the main informations of the scene as ``CData``"""

        logging_func({"INFO"}, "getSceneMainXML 0")

        # Room instead of Scene due tue a SoH imitation
        sceneXML = "<Room>\n"
        headers: list[tuple[SceneHeader, str]] = []
        altHeaderPtrs = None

        logging_func({"INFO"}, "getSceneMainXML 1")

        if self.hasAlternateHeaders:
            headers = [
                (self.altHeader.childNight, "Child Night"),
                (self.altHeader.adultDay, "Adult Day"),
                (self.altHeader.adultNight, "Adult Night"),
            ]

            logging_func({"INFO"}, "getSceneMainXML 2")

            for i, csHeader in enumerate(self.altHeader.cutscenes):
                headers.append((csHeader, f"Cutscene No. {i + 1}"))

            logging_func({"INFO"}, "getSceneMainXML 3")

            altHeaderPtrs = "\n".join(
                indent + curHeader.name + "," if curHeader is not None else indent + "NULL," if i < 4 else ""
                for i, (curHeader, _) in enumerate(headers, 1)
            )

        logging_func({"INFO"}, "getSceneMainXML 4")

        headers.insert(0, (self.mainHeader, "Child Day (Default)"))
        for i, (curHeader, headerDesc) in enumerate(headers):
            logging_func({"INFO"}, "getSceneMainXML 5")
            if curHeader is not None:
                logging_func({"INFO"}, "getSceneMainXML 5.1")
                sceneXML += f"<!-- Header {headerDesc}\n -->\n"
                logging_func({"INFO"}, "getSceneMainXML 5.2")
                if i != 0:
                    sceneXML += f"<!-- This is an alternate header (i=={i}):\n"
                sceneXML += self.getCmdListXML(curHeader, i == 0 and self.hasAlternateHeaders, logging_func)
                if i != 0:
                    sceneXML += f"This is the end of an alternate header (i=={i})-->\n"
                logging_func({"INFO"}, "getSceneMainXML 5.3")

                if i == 0:
                    logging_func({"INFO"}, "getSceneMainXML 5.4")
                    if self.hasAlternateHeaders and altHeaderPtrs is not None:
                        logging_func({"INFO"}, "getSceneMainXML 5.5")
                        sceneXML += indent + f"<!-- self.altHeader.name={self.altHeader.name} altHeaderPtrs={altHeaderPtrs} -->"
                        logging_func({"INFO"}, "getSceneMainXML 5.6")

                logging_func({"INFO"}, "getSceneMainXML 5.7")
                sceneXML += curHeader.getXML(logging_func)
                logging_func({"INFO"}, "getSceneMainXML 5.8")
            logging_func({"INFO"}, "getSceneMainXML 5.9")

        logging_func({"INFO"}, "getSceneMainXML 6")

        sceneXML += "</Room>"

        return sceneXML

    def getSceneCutscenesC(self):
        """Returns the cutscene informations of the scene as ``CData``"""

        csDataList: list[CData] = []
        headers: list[SceneHeader] = [
            self.mainHeader,
        ]

        if self.altHeader is not None:
            headers.extend(
                [
                    self.altHeader.childNight,
                    self.altHeader.adultDay,
                    self.altHeader.adultNight,
                ]
            )
            headers.extend(self.altHeader.cutscenes)

        for curHeader in headers:
            if curHeader is not None:
                for csEntry in curHeader.cutscene.entries:
                    csDataList.append(csEntry.getC())

        return csDataList

    def getSceneCutscenesXML(self):
        """Returns the cutscene informations of the scene as ``CData``"""

        csDataList: list[str] = []
        headers: list[SceneHeader] = [
            self.mainHeader,
        ]

        if self.altHeader is not None:
            headers.extend(
                [
                    self.altHeader.childNight,
                    self.altHeader.adultDay,
                    self.altHeader.adultNight,
                ]
            )
            headers.extend(self.altHeader.cutscenes)

        for curHeader in headers:
            if curHeader is not None:
                for csEntry in curHeader.cutscene.entries:
                    csDataList.append(csEntry.getXML())

        return csDataList

    def getSceneTexturesC(self, textureExportSettings: TextureExportSettings):
        """
        Writes the textures and material setup displaylists that are shared between multiple rooms
        (is written to the scene)
        """

        return self.model.to_c(textureExportSettings, OOTGfxFormatter(ScrollMethod.Vertex)).all()

    def getSceneTexturesXML(self, textureExportSettings: TextureExportSettings):
        """
        Writes the textures and material setup displaylists that are shared between multiple rooms
        (is written to the scene)
        """

        return "<!-- TODO getSceneTexturesXML -->"#self.model.to_xml(textureExportSettings, OOTGfxFormatter(ScrollMethod.Vertex)).all()

    def getNewSceneFile(self, path: str, isSingleFile: bool, textureExportSettings: TextureExportSettings):
        """Returns a new scene file containing the C data"""

        sceneMainData = self.getSceneMainC()
        sceneCollisionData = self.colHeader.getC()
        sceneCutsceneData = self.getSceneCutscenesC()
        sceneTexturesData = self.getSceneTexturesC(textureExportSettings)

        includes = (
            "\n".join(
                [
                    '#include "ultra64.h"',
                    '#include "macros.h"',
                    '#include "z64.h"',
                ]
            )
            + "\n\n\n"
        )

        return SceneFile(
            self.name,
            sceneMainData.source,
            sceneCollisionData.source,
            [cs.source for cs in sceneCutsceneData],
            sceneTexturesData.source,
            {
                room.roomIndex: room.getNewRoomFile(path, isSingleFile, textureExportSettings)
                for room in self.rooms.entries
            },
            isSingleFile,
            path,
            (
                f"#ifndef {self.name.upper()}_H\n"
                + f"#define {self.name.upper()}_H\n\n"
                + includes
                + sceneMainData.header
                + "".join(cs.header for cs in sceneCutsceneData)
                + sceneCollisionData.header
                + sceneTexturesData.header
            ),
        )

    def getNewSceneFileXML(self, path: str, isSingleFile: bool, textureExportSettings: TextureExportSettings, resourceBasePath: str, logging_func):
        """Returns a new scene file containing the C data"""

        logging_func({"INFO"}, "getNewSceneFileXML 0")

        sceneMainData = self.getSceneMainXML(logging_func)

        logging_func({"INFO"}, "getNewSceneFileXML 1")

        sceneCollisionData = self.colHeader.getXML(logging_func)

        logging_func({"INFO"}, "getNewSceneFileXML 2")

        sceneCutsceneData = self.getSceneCutscenesXML()

        logging_func({"INFO"}, "getNewSceneFileXML 3")

        sceneTexturesData = self.getSceneTexturesXML(textureExportSettings)

        logging_func({"INFO"}, "getNewSceneFileXML 4")

        return SceneFile(
            self.name,
            sceneMainData,
            sceneCollisionData,
            sceneCutsceneData,
            sceneTexturesData,
            {
                room.roomIndex: room.getNewRoomFileXML(path, isSingleFile, textureExportSettings, resourceBasePath, logging_func)
                for room in self.rooms.entries
            },
            isSingleFile,
            path,
            "",
        )
