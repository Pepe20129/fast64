from .....utility import CData, indent
from ....oot_level_classes import OOTRoom
from .actor import getActorList, getActorListXML
from .room_commands import getRoomCommandList, getRoomCommandListXML, getObjectListCmdXML


def getHeaderDefines(outRoom: OOTRoom, headerIndex: int):
    """Returns a string containing defines for actor and object lists lengths"""
    headerDefines = ""

    if len(outRoom.objectIDList) > 0:
        headerDefines += f"#define {outRoom.getObjectLengthDefineName(headerIndex)} {len(outRoom.objectIDList)}\n"

    if len(outRoom.actorList) > 0:
        headerDefines += f"#define {outRoom.getActorLengthDefineName(headerIndex)} {len(outRoom.actorList)}\n"

    return headerDefines


# Object List


def getObjectList(outRoom: OOTRoom, headerIndex: int):
    objectList = CData()
    declarationBase = f"s16 {outRoom.objectListName(headerIndex)}"

    # .h
    objectList.header = f"extern {declarationBase}[];\n"

    # .c
    objectList.source = (
        (f"{declarationBase}[{outRoom.getObjectLengthDefineName(headerIndex)}]" + " = {\n")
        + ",\n".join(indent + objectID for objectID in outRoom.objectIDList)
        + ",\n};\n\n"
    )

    return objectList


# Room Header
def getRoomDataXML(outRoom: OOTRoom, logging_func):
    roomXML = "<Room>"
    logging_func({"INFO"}, "getRoomDataXML 0")

    roomHeaders = [
        (outRoom.childNightHeader, "Child Night"),
        (outRoom.adultDayHeader, "Adult Day"),
        (outRoom.adultNightHeader, "Adult Night"),
    ]

    for i, csHeader in enumerate(outRoom.cutsceneHeaders):
        logging_func({"INFO"}, "getRoomDataXML 1")
        roomHeaders.append((csHeader, f"Cutscene No. {i + 1}"))

    # TODO
    altHeaderPtrList = ""

    roomHeaders.insert(0, (outRoom, "Child Day (Default)"))
    logging_func({"INFO"}, "getRoomDataXML 2")
    for i, (curHeader, headerDesc) in enumerate(roomHeaders):
        logging_func({"INFO"}, "getRoomDataXML 3")
        if curHeader is not None:
            roomXML += indent + f"<!-- Header {headerDesc} -->\n"
            logging_func({"INFO"}, "getRoomDataXML 4")
            roomXML += getRoomCommandListXML(curHeader, i, logging_func)
            logging_func({"INFO"}, "getRoomDataXML 5")

            if i == 0 and outRoom.hasAlternateHeaders():
                roomXML += altHeaderPtrList
            logging_func({"INFO"}, "getRoomDataXML 6")

            if len(curHeader.objectIDList) > 0:
                roomXML += getObjectListCmdXML(curHeader, i)
            logging_func({"INFO"}, "getRoomDataXML 7")

            if len(curHeader.actorList) > 0:
                roomXML += getActorListXML(curHeader, i)
            logging_func({"INFO"}, "getRoomDataXML 8")

    logging_func({"INFO"}, "getRoomDataXML 9")
    roomXML += "\n</Room>"
    return roomXML


def getRoomData(outRoom: OOTRoom):
    roomC = CData()

    roomHeaders = [
        (outRoom.childNightHeader, "Child Night"),
        (outRoom.adultDayHeader, "Adult Day"),
        (outRoom.adultNightHeader, "Adult Night"),
    ]

    for i, csHeader in enumerate(outRoom.cutsceneHeaders):
        roomHeaders.append((csHeader, f"Cutscene No. {i + 1}"))

    declarationBase = f"SceneCmd* {outRoom.alternateHeadersName()}"

    # .h
    roomC.header = f"extern {declarationBase}[];\n"

    # .c
    altHeaderPtrList = (
        f"{declarationBase}[]"
        + " = {\n"
        + "\n".join(
            indent + f"{curHeader.roomName()}_header{i:02}," if curHeader is not None else indent + "NULL,"
            for i, (curHeader, headerDesc) in enumerate(roomHeaders, 1)
        )
        + "\n};\n\n"
    )

    roomHeaders.insert(0, (outRoom, "Child Day (Default)"))
    for i, (curHeader, headerDesc) in enumerate(roomHeaders):
        if curHeader is not None:
            roomC.source += "/**\n * " + f"Header {headerDesc}\n" + "*/\n"
            roomC.source += getHeaderDefines(curHeader, i)
            roomC.append(getRoomCommandList(curHeader, i))

            if i == 0 and outRoom.hasAlternateHeaders():
                roomC.source += altHeaderPtrList

            if len(curHeader.objectIDList) > 0:
                roomC.append(getObjectList(curHeader, i))

            if len(curHeader.actorList) > 0:
                roomC.append(getActorList(curHeader, i))

    return roomC
