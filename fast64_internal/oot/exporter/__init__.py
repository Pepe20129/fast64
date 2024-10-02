import bpy
import os

from mathutils import Matrix
from bpy.types import Object
from ...f3d.f3d_gbi import DLFormat, TextureExportSettings
from ..oot_model_classes import OOTModel
from ..oot_f3d_writer import writeTextureArraysNew, writeTextureArraysExisting1D
from .scene import Scene
from .decomp_edit import Files

from ...utility import (
    PluginError,
    checkObjectReference,
    unhideAllAndGetHiddenState,
    restoreHiddenState,
    toAlnum,
    readFile,
    writeFile,
)

from ..oot_utility import (
    ExportInfo,
    OOTObjectCategorizer,
    ootDuplicateHierarchy,
    ootCleanupScene,
    getSceneDirFromLevelName,
    ootGetPath,
)


def writeTextureArraysExistingScene(fModel: OOTModel, exportPath: str, sceneInclude: str):
    drawConfigPath = os.path.join(exportPath, "src/code/z_scene_table.c")
    drawConfigData = readFile(drawConfigPath)
    newData = drawConfigData

    if f'#include "{sceneInclude}"' not in newData:
        additionalIncludes = f'#include "{sceneInclude}"\n'
    else:
        additionalIncludes = ""

    for flipbook in fModel.flipbooks:
        if flipbook.exportMode == "Array":
            newData = writeTextureArraysExisting1D(newData, flipbook, additionalIncludes)
        else:
            raise PluginError("Scenes can only use array flipbooks.")

    if newData != drawConfigData:
        writeFile(drawConfigPath, newData)


class SceneExport:
    """This class is the main exporter class, it handles generating the C data and writing the files"""

    @staticmethod
    def create_scene(originalSceneObj: Object, transform: Matrix, exportInfo: ExportInfo) -> Scene:
        """Returns and creates scene data"""
        # init
        if originalSceneObj.type != "EMPTY" or originalSceneObj.ootEmptyType != "Scene":
            raise PluginError(f'{originalSceneObj.name} is not an empty with the "Scene" empty type.')

        if bpy.context.scene.exportHiddenGeometry:
            hiddenState = unhideAllAndGetHiddenState(bpy.context.scene)

        # Don't remove ignore_render, as we want to reuse this for collision
        sceneObj, allObjs = ootDuplicateHierarchy(originalSceneObj, None, True, OOTObjectCategorizer())

        if bpy.context.scene.exportHiddenGeometry:
            restoreHiddenState(hiddenState)

        try:
            sceneName = f"{toAlnum(exportInfo.name)}_scene"
            newScene = Scene.new(
                sceneName,
                sceneObj,
                transform,
                exportInfo.useMacros,
                exportInfo.saveTexturesAsPNG,
                OOTModel(f"{sceneName}_dl", DLFormat.Static, False),
            )
            newScene.validateScene()

        except Exception as e:
            raise Exception(str(e))
        finally:
            ootCleanupScene(originalSceneObj, allObjs)

        return newScene

    @staticmethod
    def export(originalSceneObj: Object, transform: Matrix, exportInfo: ExportInfo):
        """Main function"""
        # circular import fixes
        from .decomp_edit.config import Config

        checkObjectReference(originalSceneObj, "Scene object")
        scene = SceneExport.create_scene(originalSceneObj, transform, exportInfo)

        isCustomExport = exportInfo.isCustomExportPath
        exportPath = exportInfo.exportPath
        sceneName = exportInfo.name

        exportSubdir = ""
        if exportInfo.customSubPath is not None:
            exportSubdir = exportInfo.customSubPath
        if not isCustomExport and exportInfo.customSubPath is None:
            exportSubdir = os.path.dirname(getSceneDirFromLevelName(sceneName))

        sceneInclude = exportSubdir + "/" + sceneName + "/"
        path = ootGetPath(exportPath, isCustomExport, exportSubdir, sceneName, True, True)
        textureExportSettings = TextureExportSettings(False, exportInfo.saveTexturesAsPNG, sceneInclude, path)

        sceneFile = scene.getNewSceneFile(path, exportInfo.isSingleFile, textureExportSettings)

        if not isCustomExport:
            writeTextureArraysExistingScene(scene.model, exportPath, sceneInclude + sceneName + "_scene.h")
        else:
            textureArrayData = writeTextureArraysNew(scene.model, None)
            sceneFile.sceneTextures += textureArrayData.source
            sceneFile.header += textureArrayData.header

        sceneFile.write()
        for room in scene.rooms.entries:
            room.roomShape.copy_bg_images(path)

        if not isCustomExport:
            Files.add_scene_edits(exportInfo, scene, sceneFile)

        hackerootBootOption = exportInfo.hackerootBootOption
        if hackerootBootOption is not None and hackerootBootOption.bootToScene:
            Config.setBootupScene(
                os.path.join(exportPath, "include/config/config_debug.h")
                if not isCustomExport
                else os.path.join(path, "config_bootup.h"),
                f"ENTR_{sceneName.upper()}_{hackerootBootOption.spawnIndex}",
                hackerootBootOption,
            )

    def export_xml(originalSceneObj: Object, transform: Matrix, exportInfo: ExportInfo, logging_func):
        checkObjectReference(originalSceneObj, "Scene object")
        scene = SceneExport.create_scene(originalSceneObj, transform, exportInfo)

        exportSubdir = ""
        if exportInfo.customSubPath is not None:
            exportSubdir = exportInfo.customSubPath

        logging_func({"INFO"}, "ootExportSceneToXML 3")

        resourceBasePath = ""

        if bpy.context.scene.ootSceneExportSettings.option == "Custom":
            resourceBasePath = bpy.context.scene.ootSceneExportSettings.sohCustomResourcePath
        elif bpy.context.scene.ootSceneExportSettings.sohResourcePath == "Shared":
            resourceBasePath = f"scenes/shared/{scene.name}/"
        elif bpy.context.scene.ootSceneExportSettings.sohResourcePath == "Vanilla":
            resourceBasePath = f"scenes/nonmq/{scene.name}/"
        elif bpy.context.scene.ootSceneExportSettings.sohResourcePath == "MQ":
            resourceBasePath = f"scenes/mq/{scene.name}/"
        else:
            logging_func({"ERROR"}, f"Unknown sohResourcePath")
            return

        logging_func(
            {"INFO"},
            "ootExportSceneToXML 4.1 resourceBasePath=" + (resourceBasePath if resourceBasePath is not None else "None"),
        )
        logging_func(
            {"INFO"}, "ootExportSceneToXML 4.2 exportSubdir=" + (exportSubdir if exportSubdir is not None else "None")
        )
        logging_func({"INFO"}, "ootExportSceneToXML 4.3 scene.name=" + (scene.name if scene.name is not None else "None"))
        logging_func(
            {"INFO"},
            "ootExportSceneToXML 4.4 exportInfo.exportPath="
            + (exportInfo.exportPath if exportInfo.exportPath is not None else "None"),
        )
        sceneInclude = exportSubdir + "/" + scene.name + "/"
        exportPath = exportInfo.exportPath
        for section in resourceBasePath.split("/"):
            exportPath = os.path.join(exportPath, section)
        path = ootGetPath(exportPath, True, exportSubdir, scene.name, True, True)

        levelXML = getSceneXML(
            scene, TextureExportSettings(False, savePNG, sceneInclude, path), resourceBasePath, logging_func
        )
        logging_func({"INFO"}, "ootExportSceneToXML 5")

        textureArrayData = writeTextureArraysNewXML(scene.model, None)
        logging_func(
            {"INFO"},
            "ootExportSceneToXML 6 levelXML.sceneTexturesXML="
            + (levelXML.sceneTexturesXML if levelXML.sceneTexturesXML is not None else "None"),
        )
        logging_func(
            {"INFO"},
            "ootExportSceneToXML 7 textureArrayData=" + (textureArrayData if textureArrayData is not None else "None"),
        )
        # levelXML.sceneTexturesXML.append(textureArrayData)
        logging_func({"INFO"}, "ootExportSceneToXML 8")

        logging_func({"INFO"}, f"ootExportSceneToXML 9 path={(path if path is not None else 'None')}")
        # TODO: uses Room instead of Scene due to a SoH limitation
        writeXMLData(
            '{\n    "path": "'
            + resourceBasePath
            + scene.name
            + '.xml",\n    "type": "Room",\n    "format": "XML",\n    "version": 0\n}',
            os.path.join(path, scene.name + ".meta"),
        )
        writeXMLData(
            ootCombineSceneFilesXML(levelXML).replace("{resource_base_path}", resourceBasePath[:-1]),
            os.path.join(path, scene.name + ".xml"),
        )
        for i in range(len(levelXML.sceneAlternateHeadersXML)):
            writeXMLData(
                levelXML.sceneAlternateHeadersXML[i].replace("{resource_base_path}", resourceBasePath[:-1]),
                os.path.join(path, scene.name + "_alternate_headers_" + str(i) + ".xml"),
            )
        for i in range(len(levelXML.scenePathDataXML)):
            writeXMLData(
                levelXML.scenePathDataXML[i].replace("{resource_base_path}", resourceBasePath[:-1]),
                os.path.join(path, scene.name + "_pathway_" + str(i) + ".xml"),
            )
        writeXMLData(
            levelXML.sceneCollisionXML.replace("{resource_base_path}", resourceBasePath[:-1]),
            os.path.join(path, scene.name + "_collision.xml"),
        )
        logging_func({"INFO"}, "ootExportSceneToXML 10")
        for i in range(len(scene.rooms.entries)):
            logging_func({"INFO"}, "ootExportSceneToXML 11")
            roomXML = levelXML.roomMainXML[scene.rooms.entries[i].roomName()]
            writeXMLData(
                roomXML.replace("{resource_base_path}", resourceBasePath[:-1]),
                os.path.join(path, scene.rooms.entries[i].roomName() + ".xml"),
            )

            for j in range(len(levelXML.roomAlternateHeadersXML[scene.rooms.entries[i].roomName()])):
                writeXMLData(
                    levelXML.roomAlternateHeadersXML[scene.rooms.entries[i].roomName()][j].replace(
                        "{resource_base_path}", resourceBasePath[:-1]
                    ),
                    os.path.join(path, scene.rooms.entries[i].roomName() + "_alternate_headers_" + str(j) + ".xml"),
                )

            for meshEntry in scene.rooms.entries[i].mesh.meshEntries:
                opaqueName = meshEntry.DLGroup.opaque.name if meshEntry.DLGroup.opaque is not None else ""
                transparentName = meshEntry.DLGroup.transparent.name if meshEntry.DLGroup.transparent is not None else ""
                if meshEntry.DLGroup.opaque is not None:
                    writeXMLData(
                        meshEntry.DLGroup.opaque.to_soh_xml(None, "{resource_base_path}").replace(
                            "{resource_base_path}", resourceBasePath[:-1]
                        ),
                        os.path.join(path, opaqueName + ".xml"),
                    )
                if meshEntry.DLGroup.transparent is not None:
                    writeXMLData(
                        meshEntry.DLGroup.transparent.to_soh_xml(None, "{resource_base_path}").replace(
                            "{resource_base_path}", resourceBasePath[:-1]
                        ),
                        os.path.join(path, transparentName + ".xml"),
                    )

            logging_func({"INFO"}, "ootExportSceneToXML 12")

        # Copy bg images
        for room in scene.rooms.entries:
            room.roomShape.copy_bg_images(path)

        logging_func({"INFO"}, "ootExportSceneToXML 13")