from .....utility import CData, indent
from ....oot_spline import OOTPath
from ....oot_level_classes import OOTScene


def getPathPointData(path: OOTPath, headerIndex: int, pathIndex: int):
    pathData = CData()
    declarationBase = f"Vec3s {path.pathName(headerIndex, pathIndex)}"

    # .h
    pathData.header = f"extern {declarationBase}[];\n"

    # .c
    pathData.source = (
        f"{declarationBase}[]"
        + " = {\n"
        + "\n".join(
            indent + "{ " + ", ".join(f"{round(curPoint):5}" for curPoint in point) + " }," for point in path.points
        )
        + "\n};\n\n"
    )

    return pathData


def getPathPointDataXML(path: OOTPath, headerIndex: int, pathIndex: int):
    return "\n".join(
        indent
        + f'    <PathPoint X="{f"{round(point[0]):5}"}" Y="{f"{round(point[1]):5}"}" Z="{f"{round(point[2]):5}"}"/>'
        for point in path.points
    )


def getPathData(outScene: OOTScene, headerIndex: int):
    pathData = CData()
    pathListData = CData()
    declarationBase = f"Path {outScene.pathListName(headerIndex)}[{len(outScene.pathList)}]"

    # .h
    pathListData.header = f"extern {declarationBase};\n"

    # .c
    pathListData.source = declarationBase + " = {\n"

    # Parse in alphabetical order of names
    sortedPathList = sorted(outScene.pathList, key=lambda x: x.objName.lower())
    for i, curPath in enumerate(sortedPathList):
        pathName = curPath.pathName(headerIndex, i)
        pathListData.source += indent + "{ " + f"ARRAY_COUNTU({pathName}), {pathName}" + " },\n"
        pathData.append(getPathPointData(curPath, headerIndex, i))

    pathListData.source += "};\n\n"
    pathData.append(pathListData)

    return pathData


def getPathDataXML(outScene: OOTScene, headerIndex: int):
    pathData = "<Path>\n"

    # Parse in alphabetical order of names
    sortedPathList = sorted(outScene.pathList, key=lambda x: x.objName.lower())
    for i, curPath in enumerate(sortedPathList):
        pathData += (
            indent + "<PathData>\n" + getPathPointDataXML(curPath, headerIndex, i) + "\n" + indent + "</PathData>\n"
        )

    pathData += "</Path>"

    return pathData


def getScenePathDataXML(outScene: OOTScene):
    sceneHeaders = [
        (outScene.childNightHeader, "Child Night"),
        (outScene.adultDayHeader, "Adult Day"),
        (outScene.adultNightHeader, "Adult Night"),
    ]

    for i, csHeader in enumerate(outScene.cutsceneHeaders):
        logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 1")
        sceneHeaders.append((csHeader, f"Cutscene No. {i + 1}"))

    pathDatas = []
    for i, (curHeader, headerDesc) in enumerate(sceneHeaders):
        pathDatas.append(getPathDataXML(outScene, i))

    return pathDatas
