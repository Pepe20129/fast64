import bpy
import os
import mathutils

from ...exporter import OOTCollision, OOTCameraData
from ...properties import OOTCollisionExportSettings
from ..classes import OOTCameraData, OOTCameraPosData, OOTCrawlspaceData
from ..functions import exportCollisionCommon

from .....utility import (
    PluginError,
    CData,
    unhideAllAndGetHiddenState,
    restoreHiddenState,
    writeCData,
    toAlnum,
)

from ....oot_utility import (
    OOTObjectCategorizer,
    addIncludeFiles,
    ootDuplicateHierarchy,
    ootCleanupScene,
    ootGetPath,
    ootGetObjectPath,
)


def ootCollisionVertexToC(vertex):
    return "{ " + str(vertex.position[0]) + ", " + str(vertex.position[1]) + ", " + str(vertex.position[2]) + " },\n"


def ootCollisionVertexToXML(vertex):
    return (
        f'<Vertex X="{str(vertex.position[0])}" Y="{str(vertex.position[1])}" Z="{str(vertex.position[2])}"></Vertex>'
    )


def ootCollisionPolygonToC(polygon, ignoreCamera, ignoreActor, ignoreProjectile, enableConveyor, polygonTypeIndex):
    return (
        "{ "
        + ", ".join(
            (
                format(polygonTypeIndex, "#06x"),
                format(polygon.convertShort02(ignoreCamera, ignoreActor, ignoreProjectile), "#06x"),
                format(polygon.convertShort04(enableConveyor), "#06x"),
                format(polygon.convertShort06(), "#06x"),
                "COLPOLY_SNORMAL({})".format(polygon.normal[0]),
                "COLPOLY_SNORMAL({})".format(polygon.normal[1]),
                "COLPOLY_SNORMAL({})".format(polygon.normal[2]),
                format(polygon.distance, "#06x"),
            )
        )
        + " },\n"
    )


def ootCollisionPolygonToXML(polygon, ignoreCamera, ignoreActor, ignoreProjectile, enableConveyor, polygonTypeIndex):
    return '<Polygon Type="{Type}" VertexA="{VertexA}" VertexB="{VertexB}" VertexC="{VertexC}" NormalX="{NormalX}" NormalY="{NormalY}" NormalZ="{NormalZ}" Dist="{Dist}"></Polygon>'.format(
        Type=str(polygonTypeIndex),
        VertexA=str(polygon.convertShort02(ignoreCamera, ignoreActor, ignoreProjectile)),
        VertexB=str(polygon.convertShort04(enableConveyor)),
        VertexC=str(polygon.convertShort06()),
        NormalX=str(polygon.normal[0] * 32767),
        NormalY=str(polygon.normal[1] * 32767),
        NormalZ=str(polygon.normal[2] * 32767),
        Dist=str(polygon.distance),
    )


def ootPolygonTypeToC(polygonType):
    return (
        "{ " + format(polygonType.convertHigh(), "#010x") + ", " + format(polygonType.convertLow(), "#010x") + " },\n"
    )


def ootPolygonTypeToXML(polygonType):
    # might be reversed
    return f'<PolygonType Data1="{polygonType.convertHigh()}" Data2="{polygonType.convertLow()}"></PolygonType>'


def ootWaterBoxToC(waterBox):
    return (
        "{ "
        + str(waterBox.low[0])
        + ", "
        + str(waterBox.height)
        + ", "
        + str(waterBox.low[1])
        + ", "
        + str(waterBox.high[0] - waterBox.low[0])
        + ", "
        + str(waterBox.high[1] - waterBox.low[1])
        + ", "
        + format(waterBox.propertyData(), "#010x")
        + " },\n"
    )


def ootWaterBoxToXML(waterBox):
    return '<WaterBox XMin="{XMin}" Ysurface="{Ysurface}" ZMin="{ZMin}" XLength="{XLength}" ZLength="{ZLength}" Properties="{Properties}"></WaterBox>'.format(
        XMin=str(waterBox.low[0]),
        Ysurface=str(waterBox.height),
        ZMin=str(waterBox.low[1]),
        XLength=str(waterBox.high[0] - waterBox.low[0]),
        ZLength=str(waterBox.high[1] - waterBox.low[1]),
        Properties=str(waterBox.propertyData()),
    )


def ootCameraDataToC(camData):
    posC = CData()
    camC = CData()
    if len(camData.camPosDict) > 0:
        camDataName = "BgCamInfo " + camData.camDataName() + "[" + str(len(camData.camPosDict)) + "]"

        camC.source = camDataName + " = {\n"
        camC.header = "extern " + camDataName + ";\n"

        camPosIndex = 0

        for i in range(len(camData.camPosDict)):
            camItem = camData.camPosDict[i]
            if isinstance(camItem, OOTCameraPosData):
                camC.source += "\t" + ootCameraEntryToC(camItem, camData, camPosIndex) + ",\n"
                if camItem.hasPositionData:
                    posC.source += ootCameraPosToC(camItem)
                    camPosIndex += 3
            elif isinstance(camItem, OOTCrawlspaceData):
                camC.source += "\t" + ootCrawlspaceEntryToC(camItem, camData, camPosIndex) + ",\n"
                posC.source += ootCrawlspaceToC(camItem)
                camPosIndex += len(camItem.points) * 3
            else:
                raise PluginError(f"Invalid object type in camera position dict: {type(camItem)}")
        posC.source += "};\n\n"
        camC.source += "};\n\n"

        if camPosIndex > 0:
            posDataName = "Vec3s " + camData.camPositionsName() + "[" + str(camPosIndex) + "]"
            posC.header = "extern " + posDataName + ";\n"
            posC.source = posDataName + " = {\n" + posC.source
        else:
            posC = CData()

    return posC, camC


def ootCameraDataToXML(camData):
    posXML = ""
    camXML = ""
    exportPosData = False
    if len(camData.camPosDict) > 0:
        camPosIndex = 0
        for i in range(len(camData.camPosDict)):
            camItem = camData.camPosDict[i]
            if isinstance(camItem, OOTCameraPosData):
                camXML += ootCameraEntryToXML(camItem, camData, camPosIndex)
                if camItem.hasPositionData:
                    posXML += ootCameraPosToXML(camItem)
                    camPosIndex += 3
                    exportPosData = True
            elif isinstance(camItem, OOTCrawlspaceData):
                # camXML += ootCrawlspaceEntryToXML(camItem, camData, camPosIndex)
                # posXML += ootCrawlspaceToXML(camItem)
                # camPosIndex += len(camItem.points) * 3
                raise PluginError(f"TODO: OOTCrawlspaceData")
            else:
                raise PluginError(f"Invalid object type in camera position dict: {type(camItem)}")

    if not exportPosData:
        posXML = None
    return posXML, camXML


def ootCameraPosToC(camPos):
    return (
        "\t{ "
        + str(camPos.position[0])
        + ", "
        + str(camPos.position[1])
        + ", "
        + str(camPos.position[2])
        + " },\n\t{ "
        + str(camPos.rotation[0])
        + ", "
        + str(camPos.rotation[1])
        + ", "
        + str(camPos.rotation[2])
        + " },\n\t{ "
        + str(camPos.fov)
        + ", "
        + str(camPos.bgImageOverrideIndex)
        + ", "
        + str(camPos.unknown)
        + " },\n"
    )


def ootCameraPosToXML(camPos):
    return '<CameraPositionData PosX="{PosX}" PosY="{PosY}" PosZ="{PosZ}" RotX="{RotX}" RotY="{RotY}" RotZ="{RotZ}" FOV="{FOV}" JfifID="{JfifID}" Unknown="{Unknown}"></CameraPositionData>'.format(
        PosX=str(camPos.position[0]),
        PosY=str(camPos.position[1]),
        PosZ=str(camPos.position[2]),
        RotX=str(camPos.rotation[0]),
        RotY=str(camPos.rotation[1]),
        RotZ=str(camPos.rotation[2]),
        FOV=str(camPos.fov),
        JfifID=str(camPos.bgImageOverrideIndex),
        Unknown=str(camPos.unknown),
    )


def ootCameraEntryToC(camPos, camData, camPosIndex):
    return " ".join(
        (
            "{",
            camPos.camSType + ",",
            ("3" if camPos.hasPositionData else "0") + ",",
            ("&" + camData.camPositionsName() + "[" + str(camPosIndex) + "]" if camPos.hasPositionData else "NULL"),
            "}",
        )
    )


def ootCameraEntryToXML(camPos, camData, camPosIndex):
    return '<CameraData SType="{SType}" NumData="{NumData}" CameraPosDataSeg="{CameraPosDataSeg}"></CameraData>'.format(
        SType=str(camPos.camSType),
        NumData=("3" if camPos.hasPositionData else "0"),
        CameraPosDataSeg=(camPosIndex if camPos.hasPositionData else "0"),
    )


def ootCrawlspaceToC(camItem: OOTCrawlspaceData):
    data = ""
    for point in camItem.points:
        data += f"\t{{{point[0]}, {point[1]}, {point[2]}}},\n" * 3

    return data


def ootCrawlspaceEntryToC(camItem: OOTCrawlspaceData, camData: OOTCameraData, camPosIndex: int):
    return " ".join(
        (
            "{",
            camItem.camSType + ",",
            str((len(camItem.points) * 3)) + ",",
            (("&" + camData.camPositionsName() + "[" + str(camPosIndex) + "]") if len(camItem.points) > 0 else "NULL"),
            "}",
        )
    )


def ootCollisionToC(collision):
    data = CData()
    posC, camC = ootCameraDataToC(collision.cameraData)

    data.append(posC)
    data.append(camC)

    if len(collision.polygonGroups) > 0:
        data.header += "extern SurfaceType " + collision.polygonTypesName() + "[];\n"
        data.header += "extern CollisionPoly " + collision.polygonsName() + "[];\n"
        polygonTypeC = "SurfaceType " + collision.polygonTypesName() + "[] = {\n"
        polygonC = "CollisionPoly " + collision.polygonsName() + "[] = {\n"
        polygonIndex = 0
        for polygonType, polygons in collision.polygonGroups.items():
            polygonTypeC += "\t" + ootPolygonTypeToC(polygonType)
            for polygon in polygons:
                polygonC += "\t" + ootCollisionPolygonToC(
                    polygon,
                    polygonType.ignoreCameraCollision,
                    polygonType.ignoreActorCollision,
                    polygonType.ignoreProjectileCollision,
                    polygonType.enableConveyor,
                    polygonIndex,
                )
            polygonIndex += 1
        polygonTypeC += "};\n\n"
        polygonC += "};\n\n"

        data.source += polygonTypeC + polygonC
        polygonTypesName = collision.polygonTypesName()
        polygonsName = collision.polygonsName()
    else:
        polygonTypesName = "0"
        polygonsName = "0"

    if len(collision.vertices) > 0:
        data.header += "extern Vec3s " + collision.verticesName() + "[" + str(len(collision.vertices)) + "];\n"
        data.source += "Vec3s " + collision.verticesName() + "[" + str(len(collision.vertices)) + "] = {\n"
        for vertex in collision.vertices:
            data.source += "\t" + ootCollisionVertexToC(vertex)
        data.source += "};\n\n"
        collisionVerticesName = collision.verticesName()
    else:
        collisionVerticesName = "0"

    if len(collision.waterBoxes) > 0:
        data.header += "extern WaterBox " + collision.waterBoxesName() + "[];\n"
        data.source += "WaterBox " + collision.waterBoxesName() + "[] = {\n"
        for waterBox in collision.waterBoxes:
            data.source += "\t" + ootWaterBoxToC(waterBox)
        data.source += "};\n\n"
        waterBoxesName = collision.waterBoxesName()
    else:
        waterBoxesName = "0"

    if len(collision.cameraData.camPosDict) > 0:
        camDataName = collision.camDataName()
    else:
        camDataName = "0"

    data.header += "extern CollisionHeader " + collision.headerName() + ";\n"
    data.source += "CollisionHeader " + collision.headerName() + " = {\n"

    if len(collision.bounds) == 2:
        for bound in range(2):  # min, max bound
            for field in range(3):  # x, y, z
                data.source += "\t" + str(collision.bounds[bound][field]) + ",\n"
    else:
        data.source += "0, 0, 0, 0, 0, 0, "

    data.source += (
        "\t"
        + str(len(collision.vertices))
        + ",\n"
        + "\t"
        + collisionVerticesName
        + ",\n"
        + "\t"
        + str(collision.polygonCount())
        + ",\n"
        + "\t"
        + polygonsName
        + ",\n"
        + "\t"
        + polygonTypesName
        + ",\n"
        + "\t"
        + camDataName
        + ",\n"
        + "\t"
        + str(len(collision.waterBoxes))
        + ",\n"
        + "\t"
        + waterBoxesName
        + "\n"
        + "};\n\n"
    )

    return data


def ootCollisionToXML(collision):
    data = "<CollisionHeader "
    if len(collision.bounds) == 2:
        data += 'MinBoundsX="{MinBoundsX}" MinBoundsY="{MinBoundsY}" MinBoundsZ="{MinBoundsZ}" '.format(
            MinBoundsX=str(collision.bounds[0][0]),
            MinBoundsY=str(collision.bounds[0][1]),
            MinBoundsZ=str(collision.bounds[0][2]),
        )
        data += 'MaxBoundsX="{MaxBoundsX}" MaxBoundsY="{MaxBoundsY}" MaxBoundsZ="{MaxBoundsZ}"'.format(
            MaxBoundsX=str(collision.bounds[1][0]),
            MaxBoundsY=str(collision.bounds[1][1]),
            MaxBoundsZ=str(collision.bounds[1][2]),
        )
    else:
        data += 'MinBoundsX="0" MinBoundsY="0" MinBoundsZ="0" '
        data += 'MaxBoundsX="0" MaxBoundsY="0" MaxBoundsZ="0"'

    data += ">"

    for vertex in collision.vertices:
        data += ootCollisionVertexToXML(vertex)

    if len(collision.polygonGroups) > 0:
        polygonIndex = 0
        for polygonType, polygons in collision.polygonGroups.items():
            data += ootPolygonTypeToXML(polygonType)
            for polygon in polygons:
                data += ootCollisionPolygonToXML(
                    polygon,
                    polygonType.ignoreCameraCollision,
                    polygonType.ignoreActorCollision,
                    polygonType.ignoreProjectileCollision,
                    polygonType.enableConveyor,
                    polygonIndex,
                )
            polygonIndex += 1

    pos, cam = ootCameraDataToXML(collision.cameraData)

    if pos is not None:
        data += pos
    data += cam

    for waterBox in collision.waterBoxes:
        data += ootWaterBoxToXML(waterBox)

    data += "</CollisionHeader>"

    return data


def exportCollisionToC(
    originalObj: bpy.types.Object, transformMatrix: mathutils.Matrix, exportSettings: OOTCollisionExportSettings
):
    includeChildren = exportSettings.includeChildren
    name = toAlnum(originalObj.name)
    isCustomExport = exportSettings.customExport
    folderName = exportSettings.folder
    exportPath = ootGetObjectPath(isCustomExport, bpy.path.abspath(exportSettings.exportPath), folderName)

    collision = OOTCollision(name)
    collision.cameraData = OOTCameraData(name)

    if bpy.context.scene.exportHiddenGeometry:
        hiddenState = unhideAllAndGetHiddenState(bpy.context.scene)

    # Don't remove ignore_render, as we want to resuse this for collision
    obj, allObjs = ootDuplicateHierarchy(originalObj, None, True, OOTObjectCategorizer())

    if bpy.context.scene.exportHiddenGeometry:
        restoreHiddenState(hiddenState)

    try:
        exportCollisionCommon(collision, obj, transformMatrix, includeChildren, name)
        ootCleanupScene(originalObj, allObjs)
    except Exception as e:
        ootCleanupScene(originalObj, allObjs)
        raise Exception(str(e))

    collisionC = ootCollisionToC(collision)

    data = CData()
    data.source += '#include "ultra64.h"\n#include "z64.h"\n#include "macros.h"\n'
    if not isCustomExport:
        data.source += '#include "' + folderName + '.h"\n\n'
    else:
        data.source += "\n"

    data.append(collisionC)

    path = ootGetPath(exportPath, isCustomExport, "assets/objects/", folderName, False, True)
    filename = exportSettings.filename if exportSettings.isCustomFilename else f"{name}_collision"
    writeCData(data, os.path.join(path, f"{filename}.h"), os.path.join(path, f"{filename}.c"))

    if not isCustomExport:
        addIncludeFiles(folderName, path, name)


def exportCollisionToXML(originalObj, transformMatrix, includeChildren, name, isCustomExport, folderName, exportPath):
    collision = OOTCollision(name)
    collision.cameraData = OOTCameraData(name)

    if bpy.context.scene.exportHiddenGeometry:
        hiddenObjs = unhideAllAndGetHiddenList(bpy.context.scene)

    # Don't remove ignore_render, as we want to resuse this for collision
    obj, allObjs = ootDuplicateHierarchy(originalObj, None, True, OOTObjectCategorizer())

    if bpy.context.scene.exportHiddenGeometry:
        hideObjsInList(hiddenObjs)

    try:
        exportCollisionCommon(collision, obj, transformMatrix, includeChildren, name)
        ootCleanupScene(originalObj, allObjs)
    except Exception as e:
        ootCleanupScene(originalObj, allObjs)
        raise Exception(str(e))

    collisionXML = ootCollisionToXML(collision)

    data = collisionXML

    path = ootGetPath(exportPath, isCustomExport, "assets/objects/", folderName, False, False)
    writeXMLData(data, os.path.join(path, name))
