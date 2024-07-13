import bpy, os, mathutils
from bpy.types import Operator, Mesh
from bpy.ops import object
from bpy.path import abspath
from bpy.utils import register_class, unregister_class
from mathutils import Matrix
from ...utility import CData, PluginError, raisePluginError, writeCData, writeXMLData, toAlnum
from ...f3d.f3d_parser import importMeshC, getImportData
from ...f3d.f3d_gbi import DLFormat, F3D, TextureExportSettings, ScrollMethod, get_F3D_GBI
from ...f3d.f3d_writer import TriangleConverterInfo, removeDL, saveStaticModel, getInfoDict
from ..oot_utility import ootGetObjectPath, getOOTScale
from ..oot_model_classes import OOTF3DContext, ootGetIncludedAssetData
from ..oot_texture_array import ootReadTextureArrays
from ..oot_model_classes import OOTModel, OOTGfxFormatter
from ..oot_f3d_writer import (
    ootReadActorScale,
    writeTextureArraysNew,
    writeTextureArraysNewXML,
    writeTextureArraysExisting,
)
from .properties import OOTDLImportSettings, OOTDLExportSettings

from ..oot_utility import (
    OOTObjectCategorizer,
    ootDuplicateHierarchy,
    ootCleanupScene,
    ootGetPath,
    addIncludeFiles,
    getOOTScale,
)


def ootConvertMeshToC(
    originalObj: bpy.types.Object,
    finalTransform: mathutils.Matrix,
    DLFormat: DLFormat,
    saveTextures: bool,
    settings: OOTDLExportSettings,
):
    folderName = settings.folder
    exportPath = bpy.path.abspath(settings.customPath)
    isCustomExport = settings.isCustom
    drawLayer = settings.drawLayer
    removeVanillaData = settings.removeVanillaData
    name = toAlnum(originalObj.name)
    overlayName = settings.actorOverlayName
    flipbookUses2DArray = settings.flipbookUses2DArray
    flipbookArrayIndex2D = settings.flipbookArrayIndex2D if flipbookUses2DArray else None

    try:
        obj, allObjs = ootDuplicateHierarchy(originalObj, None, False, OOTObjectCategorizer())

        fModel = OOTModel(name, DLFormat, drawLayer)
        triConverterInfo = TriangleConverterInfo(obj, None, fModel.f3d, finalTransform, getInfoDict(obj))
        fMeshes = saveStaticModel(
            triConverterInfo, fModel, obj, finalTransform, fModel.name, not saveTextures, False, "oot"
        )

        # Since we provide a draw layer override, there should only be one fMesh.
        for drawLayer, fMesh in fMeshes.items():
            fMesh.draw.name = name

        ootCleanupScene(originalObj, allObjs)

    except Exception as e:
        ootCleanupScene(originalObj, allObjs)
        raise Exception(str(e))

    data = CData()
    data.source += '#include "ultra64.h"\n#include "global.h"\n'
    if not isCustomExport:
        data.source += '#include "' + folderName + '.h"\n\n'
    else:
        data.source += "\n"

    path = ootGetPath(exportPath, isCustomExport, "assets/objects/", folderName, False, True)
    includeDir = settings.customAssetIncludeDir if settings.isCustom else f"assets/objects/{folderName}"
    exportData = fModel.to_c(
        TextureExportSettings(False, saveTextures, includeDir, path), OOTGfxFormatter(ScrollMethod.Vertex)
    )

    data.append(exportData.all())

    if isCustomExport:
        textureArrayData = writeTextureArraysNew(fModel, flipbookArrayIndex2D)
        data.append(textureArrayData)

    filename = settings.filename if settings.isCustomFilename else name
    writeCData(data, os.path.join(path, filename + ".h"), os.path.join(path, filename + ".c"))

    if not isCustomExport:
        writeTextureArraysExisting(bpy.context.scene.ootDecompPath, overlayName, False, flipbookArrayIndex2D, fModel)
        addIncludeFiles(folderName, path, name)
        if removeVanillaData:
            headerPath = os.path.join(path, folderName + ".h")
            sourcePath = os.path.join(path, folderName + ".c")
            removeDL(sourcePath, headerPath, name)


def ootConvertMeshToXML(
    originalObj: bpy.types.Object,
    finalTransform: mathutils.Matrix,
    DLFormat: DLFormat,
    saveTextures: bool,
    settings: OOTDLExportSettings,
    logging_func,
):
    logging_func({"INFO"}, "ootConvertMeshToXML 1")

    folderName = settings.folder
    exportPath = bpy.path.abspath(settings.customPath)
    isCustomExport = settings.isCustom
    drawLayer = settings.drawLayer
    removeVanillaData = settings.removeVanillaData
    name = toAlnum(originalObj.name)
    overlayName = settings.actorOverlayName
    flipbookUses2DArray = settings.flipbookUses2DArray
    flipbookArrayIndex2D = settings.flipbookArrayIndex2D if flipbookUses2DArray else None

    logging_func({"INFO"}, "ootConvertMeshToXML 2")

    try:
        obj, allObjs = ootDuplicateHierarchy(originalObj, None, False, OOTObjectCategorizer())

        logging_func({"INFO"}, "ootConvertMeshToXML 3")

        fModel = OOTModel(name, DLFormat, drawLayer)

        logging_func({"INFO"}, "ootConvertMeshToXML 4")

        triConverterInfo = TriangleConverterInfo(obj, None, fModel.f3d, finalTransform, getInfoDict(obj))

        logging_func({"INFO"}, "ootConvertMeshToXML 5")

        fMeshes = saveStaticModel(
            triConverterInfo,
            fModel,
            obj,
            finalTransform,
            fModel.name,
            not saveTextures,
            False,
            "oot",
            logging_func=logging_func,
        )

        logging_func({"INFO"}, "ootConvertMeshToXML 6")

        # Since we provide a draw layer override, there should only be one fMesh.
        for drawLayer, fMesh in fMeshes.items():
            fMesh.draw.name = name

        logging_func({"INFO"}, "ootConvertMeshToXML 7")

        ootCleanupScene(originalObj, allObjs)

        logging_func({"INFO"}, "ootConvertMeshToXML 8")

    except Exception as e:
        ootCleanupScene(originalObj, allObjs)
        raise Exception(str(e))

    logging_func(
        {"INFO"}, "ootConvertMeshToXML 9.1 exportPath=" + (str(exportPath) if exportPath is not None else "None")
    )
    logging_func(
        {"INFO"},
        "ootConvertMeshToXML 9.2 settings.customAssetIncludeDir="
        + (str(settings.customAssetIncludeDir) if settings.customAssetIncludeDir is not None else "None"),
    )

    path = ootGetPath(exportPath, isCustomExport, "assets/objects/", folderName, False, True)

    logging_func({"INFO"}, "ootConvertMeshToXML 10.1 path=" + (str(path) if path is not None else "None"))
    logging_func(
        {"INFO"}, "ootConvertMeshToXML 10.2 folderName=" + (str(folderName) if folderName is not None else "None")
    )

    data = fModel.to_soh_xml(exportPath, folderName, logging_func)

    logging_func({"INFO"}, "ootConvertMeshToXML 11")

    data += writeTextureArraysNewXML(fModel, flipbookArrayIndex2D)

    logging_func({"INFO"}, "ootConvertMeshToXML 12")


class OOT_ImportDL(Operator):
    # set bl_ properties
    bl_idname = "object.oot_import_dl"
    bl_label = "Import DL"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Called on demand (i.e. button press, menu item)
    # Can also be called from operator search menu (Spacebar)
    def execute(self, context):
        obj = None
        if context.mode != "OBJECT":
            object.mode_set(mode="OBJECT")

        try:
            settings: OOTDLImportSettings = context.scene.fast64.oot.DLImportSettings
            name = settings.name
            folderName = settings.folder
            importPath = abspath(settings.customPath)
            isCustomImport = settings.isCustom
            basePath = abspath(context.scene.ootDecompPath) if not isCustomImport else importPath
            removeDoubles = settings.removeDoubles
            importNormals = settings.importNormals
            drawLayer = settings.drawLayer
            overlayName = settings.actorOverlayName
            flipbookUses2DArray = settings.flipbookUses2DArray
            flipbookArrayIndex2D = settings.flipbookArrayIndex2D if flipbookUses2DArray else None

            paths = [ootGetObjectPath(isCustomImport, importPath, folderName)]
            data = getImportData(paths)
            f3dContext = OOTF3DContext(get_F3D_GBI(), [name], basePath)

            scale = getOOTScale(settings.actorScale)
            if not isCustomImport:
                data = ootGetIncludedAssetData(basePath, paths, data) + data

                if overlayName is not None:
                    ootReadTextureArrays(basePath, overlayName, name, f3dContext, False, flipbookArrayIndex2D)
                if settings.autoDetectActorScale:
                    scale = ootReadActorScale(basePath, overlayName, False)

            obj = importMeshC(
                data,
                name,
                scale,
                removeDoubles,
                importNormals,
                drawLayer,
                f3dContext,
            )
            obj.ootActorScale = scale / context.scene.ootBlenderScale

            self.report({"INFO"}, "Success!")
            return {"FINISHED"}

        except Exception as e:
            if context.mode != "OBJECT":
                object.mode_set(mode="OBJECT")
            raisePluginError(self, e)
            return {"CANCELLED"}  # must return a set


class OOT_ExportDL(Operator):
    # set bl_ properties
    bl_idname = "object.oot_export_dl"
    bl_label = "Export DL"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Called on demand (i.e. button press, menu item)
    # Can also be called from operator search menu (Spacebar)
    def execute(self, context):
        self.report({"INFO"}, "OOT_ExportDL execute 0")
        obj = None
        if context.mode != "OBJECT":
            object.mode_set(mode="OBJECT")
        self.report({"INFO"}, "OOT_ExportDL execute 1")
        if len(context.selected_objects) == 0:
            raise PluginError("Mesh not selected.")
        self.report({"INFO"}, "OOT_ExportDL execute 2")
        obj = context.active_object
        if obj.type != "MESH":
            raise PluginError("Mesh not selected.")

        self.report({"INFO"}, "OOT_ExportDL execute 3")

        finalTransform = Matrix.Scale(getOOTScale(obj.ootActorScale), 4)

        try:
            # exportPath, levelName = getPathAndLevel(context.scene.geoCustomExport,
            # 	context.scene.geoExportPath, context.scene.geoLevelName,
            # 	context.scene.geoLevelOption)

            saveTextures = context.scene.saveTextures
            exportSettings = context.scene.fast64.oot.DLExportSettings

            self.report({"INFO"}, "OOT_ExportDL execute 4")

            if context.scene.fast64.oot.featureSet == "SoH":
                ootConvertMeshToXML(obj, finalTransform, DLFormat.Static, saveTextures, exportSettings, self.report)
            else:
                ootConvertMeshToC(
                    obj,
                    finalTransform,
                    DLFormat.Static,
                    saveTextures,
                    exportSettings,
                )

            self.report({"INFO"}, "Success!")
            return {"FINISHED"}

        except Exception as e:
            if context.mode != "OBJECT":
                object.mode_set(mode="OBJECT")
            raisePluginError(self, e)
            return {"CANCELLED"}  # must return a set


oot_dl_writer_classes = (
    OOT_ImportDL,
    OOT_ExportDL,
)


def f3d_ops_register():
    for cls in oot_dl_writer_classes:
        register_class(cls)


def f3d_ops_unregister():
    for cls in reversed(oot_dl_writer_classes):
        unregister_class(cls)
