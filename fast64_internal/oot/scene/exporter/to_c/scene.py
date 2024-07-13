from .....utility import CData, PluginError
from .....f3d.f3d_gbi import TextureExportSettings
from ....oot_level_classes import OOTScene
from .scene_header import getSceneData, getSceneDataXML, getSceneModel, getSceneModelXML, getSceneAlternateHeadersXMLs
from .scene_collision import getSceneCollision, getSceneCollisionXML
from .scene_cutscene import getSceneCutscenes, getSceneCutscenesXML
from .room_header import getRoomData, getRoomDataXML, getRoomAlternateHeadersXMLs
from .room_shape import getRoomModel, getRoomModelXML, getRoomShape, getRoomShapeXML
from .scene_pathways import getScenePathDataXML


class OOTSceneXML:
    def sceneTexturesIsUsed(self):
        return len(self.sceneTexturesXML) > 0

    def sceneCutscenesIsUsed(self):
        return len(self.sceneCutscenesXML) > 0

    def __init__(self):
        # Files for the scene segment
        self.sceneMainXML = ""
        self.sceneAlternateHeadersXML = []
        self.sceneTexturesXML = ""
        self.sceneCollisionXML = ""
        self.sceneCutscenesXML = []
        self.scenePathDataXML = []

        # Files for room segments
        self.roomMainXML = {}
        self.roomAlternateHeadersXML = {}
        self.roomShapeInfoXML = {}
        self.roomModelXML = {}


class OOTSceneC:
    def sceneTexturesIsUsed(self):
        return len(self.sceneTexturesC.source) > 0

    def sceneCutscenesIsUsed(self):
        return len(self.sceneCutscenesC) > 0

    def __init__(self):
        # Main header file for both the scene and room(s)
        self.header = CData()

        # Files for the scene segment
        self.sceneMainC = CData()
        self.sceneTexturesC = CData()
        self.sceneCollisionC = CData()
        self.sceneCutscenesC = []

        # Files for room segments
        self.roomMainC = {}
        self.roomShapeInfoC = {}
        self.roomModelC = {}


def getSceneXML(outScene: OOTScene, textureExportSettings: TextureExportSettings, resourceBasePath, logging_func):
    """Generates XML for each scene element and returns the data"""
    logging_func({"INFO"}, "getSceneXML 0")
    sceneXML = OOTSceneXML()
    logging_func({"INFO"}, "getSceneXML 1")

    sceneXML.sceneMainXML = getSceneDataXML(outScene)
    logging_func({"INFO"}, "getSceneXML 2")
    sceneXML.sceneAlternateHeadersXML = getSceneAlternateHeadersXMLs(outScene)
    logging_func({"INFO"}, "getSceneXML 3")
    sceneXML.sceneTexturesXML = getSceneModelXML(outScene, textureExportSettings, logging_func)
    logging_func({"INFO"}, "getSceneXML 4")
    sceneXML.sceneCollisionXML = getSceneCollisionXML(outScene)
    logging_func({"INFO"}, "getSceneXML 5")
    sceneXML.sceneCutscenesXML = getSceneCutscenesXML(outScene)
    logging_func({"INFO"}, "getSceneXML 6")
    sceneXML.scenePathDataXML = getScenePathDataXML(outScene)

    for outRoom in outScene.rooms.values():
        outRoomName = outRoom.roomName()
        logging_func({"INFO"}, "getSceneXML 7")

        if len(outRoom.mesh.meshEntries) <= 0:
            raise PluginError(f"Error: Room {outRoom.index} has no mesh children.")

        logging_func({"INFO"}, "getSceneXML 8")
        sceneXML.roomMainXML[outRoomName] = getRoomDataXML(outRoom, logging_func)
        logging_func({"INFO"}, "getSceneXML 9")
        sceneXML.roomAlternateHeadersXML[outRoomName] = getRoomAlternateHeadersXMLs(outRoom, logging_func)
        logging_func({"INFO"}, "getSceneXML 10")
        sceneXML.roomShapeInfoXML[outRoomName] = getRoomShapeXML(outRoom)
        sceneXML.roomModelXML[outRoomName] = getRoomModelXML(
            outRoom, textureExportSettings, resourceBasePath, logging_func
        )

    logging_func({"INFO"}, "getSceneXML 11")
    return sceneXML


def getSceneC(outScene: OOTScene, textureExportSettings: TextureExportSettings):
    """Generates C code for each scene element and returns the data"""
    sceneC = OOTSceneC()

    sceneC.sceneMainC = getSceneData(outScene)
    sceneC.sceneTexturesC = getSceneModel(outScene, textureExportSettings)
    sceneC.sceneCollisionC = getSceneCollision(outScene)
    sceneC.sceneCutscenesC = getSceneCutscenes(outScene)

    for outRoom in outScene.rooms.values():
        outRoomName = outRoom.roomName()

        if len(outRoom.mesh.meshEntries) > 0:
            roomShapeInfo = getRoomShape(outRoom)
            roomModel = getRoomModel(outRoom, textureExportSettings)
        else:
            raise PluginError(f"Error: Room {outRoom.index} has no mesh children.")

        sceneC.roomMainC[outRoomName] = getRoomData(outRoom)
        sceneC.roomShapeInfoC[outRoomName] = roomShapeInfo
        sceneC.roomModelC[outRoomName] = roomModel

    return sceneC


def getIncludes(outScene: OOTScene):
    """Returns the files to include"""
    # @TODO: avoid including files where it's not needed
    includeData = CData()

    fileNames = [
        "ultra64",
        "z64",
        "macros",
        outScene.sceneName(),
        "segment_symbols",
        "command_macros_base",
        "z64cutscene_commands",
        "variables",
    ]

    includeData.source = "\n".join(f'#include "{fileName}.h"' for fileName in fileNames) + "\n\n"

    return includeData
