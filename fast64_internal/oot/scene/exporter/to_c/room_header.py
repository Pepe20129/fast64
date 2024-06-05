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
def getRoomAlternateHeadersXMLs(outRoom: OOTRoom, logging_func):
    alternateHeadersXML = []
    logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 0")

    roomHeaders = [
        (outRoom.childNightHeader, "Child Night"),
        (outRoom.adultDayHeader, "Adult Day"),
        (outRoom.adultNightHeader, "Adult Night"),
    ]

    for i, csHeader in enumerate(outRoom.cutsceneHeaders):
        logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 1")
        roomHeaders.append((csHeader, f"Cutscene No. {i + 1}"))

    logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 2")
    for i, (curHeader, headerDesc) in enumerate(roomHeaders):
        logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 3")
        if curHeader is not None:
            alternateHeaderXML = "<Room>\n"
            alternateHeaderXML += indent + f"<!-- Header {headerDesc} -->\n"
            logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 4")
            alternateHeaderXML += getRoomCommandListXML(curHeader, i, logging_func)
            logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 5")

            if len(curHeader.objectIDList) > 0:
                alternateHeaderXML += getObjectListCmdXML(curHeader, i)
            logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 6")

            if len(curHeader.actorList) > 0:
                alternateHeaderXML += getActorListXML(curHeader, i)
            logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 7")
            alternateHeaderXML += "</Room>"
            alternateHeadersXML.append(alternateHeaderXML)

    logging_func({"INFO"}, "getRoomAlternateHeadersXMLs 8")
    return alternateHeadersXML

def getRoomDataXML(outRoom: OOTRoom, logging_func):
    roomXML = "<Room>\n"
    logging_func({"INFO"}, "getRoomDataXML 0")
    if outRoom is not None:
        roomXML += indent + f"<!-- Header Child Day (Default) -->\n"
        logging_func({"INFO"}, "getRoomDataXML 1")
        roomXML += getRoomCommandListXML(outRoom, 0, logging_func)
        logging_func({"INFO"}, "getRoomDataXML 2")

        if outRoom.hasAlternateHeaders():
            roomXML += ""
            roomXML += indent + "<SetAlternateHeaders>\n"
            numAlternateHeaders = (1 if outRoom.childNightHeader != None else 0) + (1 if outRoom.adultDayHeader != None else 0) + (1 if outRoom.adultNightHeader != None else 0) + len(outRoom.cutsceneHeaders)
            for i in range(numAlternateHeaders):
                roomXML += indent + f'    <Header Path="{outRoom.roomName()}_alternate_headers_{i}.xml"/><!-- getRoomDataXML TODO: absolute path -->\n'
            roomXML += indent + "</SetAlternateHeaders>\n"
        logging_func({"INFO"}, "getRoomDataXML 3")

        # if len(outRoom.objectIDList) > 0:
        #     roomXML += getObjectListCmdXML(outRoom, 0)
        # logging_func({"INFO"}, "getRoomDataXML 4")

        # if len(outRoom.actorList) > 0:
        #     roomXML += getActorListXML(outRoom, 0)
        # logging_func({"INFO"}, "getRoomDataXML 5")

    logging_func({"INFO"}, "getRoomDataXML 6")
    roomXML += "</Room>"
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
