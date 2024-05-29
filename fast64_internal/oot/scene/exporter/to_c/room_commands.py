from .actor import getActorListXML
from .....utility import CData, indent
from ....oot_level_classes import OOTRoom


def getEchoSettingsCmd(outRoom: OOTRoom):
    return indent + f"SCENE_CMD_ECHO_SETTINGS({outRoom.echo})"


def getEchoSettingsCmdXML(outRoom: OOTRoom):
    return indent + f'<SetEchoSettings Echo="{outRoom.echo}"/>'


def getRoomBehaviourCmd(outRoom: OOTRoom):
    showInvisibleActors = "true" if outRoom.showInvisibleActors else "false"
    disableWarpSongs = "true" if outRoom.disableWarpSongs else "false"

    return (
        (indent + "SCENE_CMD_ROOM_BEHAVIOR(")
        + ", ".join([outRoom.roomBehaviour, outRoom.linkIdleMode, showInvisibleActors, disableWarpSongs])
        + ")"
    )


def getRoomBehaviourCmdXML(outRoom: OOTRoom):
    showInvisibleActors = 1 if outRoom.showInvisibleActors else 0
    disableWarpSongs = 1 if outRoom.disableWarpSongs else 0

    return (
        indent
        + f'<SetRoomBehavior GameplayFlags1="{int(outRoom.roomBehaviour, 16)}" GameplayFlags2="{int(outRoom.linkIdleMode, 16) | (showInvisibleActors << 8) | (disableWarpSongs << 10)}"/>'
    )


def getSkyboxDisablesCmd(outRoom: OOTRoom):
    disableSkybox = "true" if outRoom.disableSkybox else "false"
    disableSunMoon = "true" if outRoom.disableSunMoon else "false"

    return indent + f"SCENE_CMD_SKYBOX_DISABLES({disableSkybox}, {disableSunMoon})"


def getSkyboxDisablesCmdXML(outRoom: OOTRoom):
    disableSkybox = "1" if outRoom.disableSkybox else "0"
    disableSunMoon = "1" if outRoom.disableSunMoon else "0"

    return indent + f'<SetSkyboxModifier SkyboxDisabled="{disableSkybox}" SunMoonDisabled="{disableSunMoon}"/>'


def getTimeSettingsCmd(outRoom: OOTRoom):
    return indent + f"SCENE_CMD_TIME_SETTINGS({outRoom.timeHours}, {outRoom.timeMinutes}, {outRoom.timeSpeed})"


def getTimeSettingsCmdXML(outRoom: OOTRoom):
    return (
        indent
        + f'<SetTimeSettings Hour="{int(outRoom.timeHours, 16)}" Minute="{int(outRoom.timeMinutes, 16)}" TimeIncrement="{outRoom.timeSpeed}"/>'
    )


def getWindSettingsCmd(outRoom: OOTRoom):
    return (
        indent
        + f"SCENE_CMD_WIND_SETTINGS({', '.join(f'{dir}' for dir in outRoom.windVector)}, {outRoom.windStrength}),\n"
    )


def getWindSettingsCmdXML(outRoom: OOTRoom):
    # TODO
    return indent + f"<!-- TODO: getWindSettingsCmdXML -->\n"


def getRoomShapeCmd(outRoom: OOTRoom):
    return indent + f"SCENE_CMD_ROOM_SHAPE(&{outRoom.mesh.headerName()})"


def getRoomShapeCmdXML(outRoom: OOTRoom):
    # TODO
    return indent + f"<!-- TODO: getRoomShapeCmdXML -->"


def getObjectListCmd(outRoom: OOTRoom, headerIndex: int):
    return (
        indent + "SCENE_CMD_OBJECT_LIST("
    ) + f"{outRoom.getObjectLengthDefineName(headerIndex)}, {outRoom.objectListName(headerIndex)}),\n"


def getObjectListCmdXML(outRoom: OOTRoom, headerIndex: int):
    # the data is inline
    data = indent + f"<SetObjectList>\n"
    for entry in outRoom.objectIDList:
        data += indent + "    " + f'<ObjectEntry Id="{entry}"/>\n'
    data += indent + f"</SetObjectList>\n"

    return data


def getActorListCmd(outRoom: OOTRoom, headerIndex: int):
    return (
        indent + "SCENE_CMD_ACTOR_LIST("
    ) + f"{outRoom.getActorLengthDefineName(headerIndex)}, {outRoom.actorListName(headerIndex)}),\n"


def getActorListCmdXML(outRoom: OOTRoom, headerIndex: int):
    # the data is inline
    return getActorListXML(outRoom, headerIndex)


def getRoomCommandList(outRoom: OOTRoom, headerIndex: int):
    cmdListData = CData()
    declarationBase = f"SceneCmd {outRoom.roomName()}_header{headerIndex:02}"

    getCmdFuncList = [
        getEchoSettingsCmd,
        getRoomBehaviourCmd,
        getSkyboxDisablesCmd,
        getTimeSettingsCmd,
        getRoomShapeCmd,
    ]

    roomCmdData = (
        (outRoom.getAltHeaderListCmd(outRoom.alternateHeadersName()) if outRoom.hasAlternateHeaders() else "")
        + (",\n".join(getCmd(outRoom) for getCmd in getCmdFuncList) + ",\n")
        + (getWindSettingsCmd(outRoom) if outRoom.setWind else "")
        + (getObjectListCmd(outRoom, headerIndex) if len(outRoom.objectIDList) > 0 else "")
        + (getActorListCmd(outRoom, headerIndex) if len(outRoom.actorList) > 0 else "")
        + outRoom.getEndCmd()
    )

    # .h
    cmdListData.header = f"extern {declarationBase}[];\n"

    # .c
    cmdListData.source = f"{declarationBase}[]" + " = {\n" + roomCmdData + "};\n\n"

    return cmdListData


def getRoomCommandListXML(outRoom: OOTRoom, headerIndex: int, logging_func):
    logging_func({"INFO"}, "getRoomCommandListXML 0")
    getCmdFuncList = [
        getEchoSettingsCmdXML,
        getRoomBehaviourCmdXML,
        getSkyboxDisablesCmdXML,
        getTimeSettingsCmdXML,
        getRoomShapeCmdXML,
    ]

    roomCmdData = (
        outRoom.getAltHeaderListCmdXML(outRoom.alternateHeadersName()) if outRoom.hasAlternateHeaders() else ""
    )
    logging_func({"INFO"}, "getRoomCommandListXML 1")

    roomCmdData += "\n".join(getCmd(outRoom) for getCmd in getCmdFuncList) + "\n"
    logging_func({"INFO"}, "getRoomCommandListXML 2")

    roomCmdData += getWindSettingsCmdXML(outRoom) if outRoom.setWind else ""
    logging_func({"INFO"}, "getRoomCommandListXML 3")

    roomCmdData += getObjectListCmdXML(outRoom, headerIndex) if len(outRoom.objectIDList) > 0 else ""
    logging_func({"INFO"}, "getRoomCommandListXML 4")

    roomCmdData += getActorListCmdXML(outRoom, headerIndex) if len(outRoom.actorList) > 0 else ""
    logging_func({"INFO"}, "getRoomCommandListXML 5")

    roomCmdData += outRoom.getEndCmdXML()
    logging_func({"INFO"}, "getRoomCommandListXML 6")

    return roomCmdData
