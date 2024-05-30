from .....utility import CData, indent
from ....oot_level_classes import OOTScene
from .actor import getActorEntryXML


def getSoundSettingsCmd(outScene: OOTScene):
    return indent + f"SCENE_CMD_SOUND_SETTINGS({outScene.audioSessionPreset}, {outScene.nightSeq}, {outScene.musicSeq})"


def getSoundSettingsCmdXML(outScene: OOTScene):
    return (
        indent
        + f'<SetSoundSettings Reverb="{outScene.audioSessionPreset}" NatureAmbienceId="{int(outScene.nightSeq, 16)}" SeqId="{outScene.musicSeq}"/>'
    )


def getRoomListCmd(outScene: OOTScene):
    return indent + f"SCENE_CMD_ROOM_LIST({len(outScene.rooms)}, {outScene.roomListName()})"


def getRoomListCmdXML(outScene: OOTScene):
    data = indent + "<SetRoomList>\n"
    # TODO: path
    for room in outScene.rooms:
        data += indent + "    " + f'<RoomEntry Path=""/><!-- getRoomListCmdXML TODO: path -->\n'
    data += indent + "</SetRoomList>"

    return data


def getTransActorListCmd(outScene: OOTScene, headerIndex: int):
    return (
        indent + "SCENE_CMD_TRANSITION_ACTOR_LIST("
    ) + f"{len(outScene.transitionActorList)}, {outScene.transitionActorListName(headerIndex)})"


def getTransActorListCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetTransitionActorList>\n"
    for transActor in outScene.transitionActorList:
        data += (
            indent
            + "    "
            + f'<TransitionActorEntry FrontSideRoom="{transActor.frontRoom}" FrontSideEffects="{transActor.frontCam}" BackSideRoom="{transActor.backRoom}" BackSideEffects="{transActor.backCam}" Id="{transActor.actorID}" PosX="{transActor.position[0]}" PosY="{transActor.position[1]}" PosZ="{transActor.position[2]}" RotY="{transActor.rotationY}" Params="{int(transActor.actorParam, 16)}"/>\n'
        )
    data += indent + "</SetTransitionActorList>"

    return data


def getMiscSettingsCmd(outScene: OOTScene):
    return indent + f"SCENE_CMD_MISC_SETTINGS({outScene.cameraMode}, {outScene.mapLocation})"


def getMiscSettingsCmdXML(outScene: OOTScene):
    return (
        indent
        + f'<SetCameraSettings CameraMovement="{int(outScene.cameraMode, 16)}" WorldMapArea="{int(outScene.mapLocation, 16)}"/>'
    )


def getColHeaderCmd(outScene: OOTScene):
    return indent + f"SCENE_CMD_COL_HEADER(&{outScene.collision.headerName()})"


def getColHeaderCmdXML(outScene: OOTScene):
    # TODO: path
    return indent + f'<SetCollisionHeader Path="{outScene.sceneName()}_collision.xml"/><!-- TODO: absolute path -->'


def getSpawnListCmd(outScene: OOTScene, headerIndex: int):
    return (
        indent + "SCENE_CMD_ENTRANCE_LIST("
    ) + f"{outScene.entranceListName(headerIndex) if len(outScene.entranceList) > 0 else 'NULL'})"


def getSpawnListCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetEntranceList>\n"
    for entrance in outScene.entranceList:
        data += (
            indent + "    " + f'<EntranceEntry Spawn="{entrance.startPositionIndex}" Room="{entrance.roomIndex}"/>\n'
        )
    data += indent + "</SetEntranceList>"
    return data


def getSpecialFilesCmd(outScene: OOTScene):
    return indent + f"SCENE_CMD_SPECIAL_FILES({outScene.naviCup}, {outScene.globalObject})"


def getSpecialFilesCmdXML(outScene: OOTScene):
    return indent + f'<SetSpecialObjects ElfMessage="{outScene.naviCup}" GlobalObject="{outScene.globalObject}"/>'


def getPathListCmd(outScene: OOTScene, headerIndex: int):
    return indent + f"SCENE_CMD_PATH_LIST({outScene.pathListName(headerIndex)})"


def getPathListCmdXML(outScene: OOTScene, headerIndex: int):
    # TODO
    return indent + f"<SetPathways/>"


def getSpawnActorListCmd(outScene: OOTScene, headerIndex: int):
    return (
        (indent + "SCENE_CMD_SPAWN_LIST(")
        + f"{len(outScene.startPositions)}, "
        + f"{outScene.startPositionsName(headerIndex) if len(outScene.startPositions) > 0 else 'NULL'})"
    )


def getSpawnActorListCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetStartPositionList>\n"
    for spawnActor in outScene.startPositions.values():
        data += getActorEntryXML(spawnActor).replace("ActorEntry", "StartPositionEntry") + "\n"
    data += indent + "</SetStartPositionList>"

    return data


def getSkyboxSettingsCmd(outScene: OOTScene):
    return (
        indent
        + f"SCENE_CMD_SKYBOX_SETTINGS({outScene.skyboxID}, {outScene.skyboxCloudiness}, {outScene.skyboxLighting})"
    )


def getSkyboxSettingsCmdXML(outScene: OOTScene):
    return (
        indent
        + f'<SetSkyboxSettings Unknown="0" SkyboxId="{int(outScene.skyboxID, 16)}" Weather="{int(outScene.skyboxCloudiness, 16)}" Indoors="{outScene.skyboxLighting}"/>'
    )


def getExitListCmd(outScene: OOTScene, headerIndex: int):
    return indent + f"SCENE_CMD_EXIT_LIST({outScene.exitListName(headerIndex)})"


def getExitListCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetExitList>\n"
    for exit in outScene.exitList:
        data += indent + "    " + f'<ExitEntry Id="{exit.index}"/>\n'
    data += indent + "</SetExitList>"

    return data


def getLightSettingsCmd(outScene: OOTScene, headerIndex: int):
    return (
        indent + "SCENE_CMD_ENV_LIGHT_SETTINGS("
    ) + f"{len(outScene.lights)}, {outScene.lightListName(headerIndex) if len(outScene.lights) > 0 else 'NULL'})"


def getLightSettingsCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetLightingSettings>\n"
    for light in outScene.lights:
        # TODO: ???
        data += indent + "    " + "<LightingSetting /><!-- TODO: ??? -->\n"
    data += indent + "</SetLightingSettings>"

    return data


def getCutsceneDataCmd(outScene: OOTScene, headerIndex: int):
    match outScene.csWriteType:
        case "Object":
            csDataName = outScene.csName
        case _:
            csDataName = outScene.csWriteCustom

    return indent + f"SCENE_CMD_CUTSCENE_DATA({csDataName})"


def getCutsceneDataCmdXML(outScene: OOTScene, headerIndex: int):
    # TODO:
    return ""


def getSceneCommandList(outScene: OOTScene, headerIndex: int):
    cmdListData = CData()
    declarationBase = f"SceneCmd {outScene.sceneName()}_header{headerIndex:02}"

    getCmdFunc1ArgList = [
        getSoundSettingsCmd,
        getRoomListCmd,
        getMiscSettingsCmd,
        getColHeaderCmd,
        getSpecialFilesCmd,
        getSkyboxSettingsCmd,
    ]

    getCmdFunc2ArgList = [getSpawnListCmd, getSpawnActorListCmd, getLightSettingsCmd]

    if len(outScene.transitionActorList) > 0:
        getCmdFunc2ArgList.append(getTransActorListCmd)

    if len(outScene.pathList) > 0:
        getCmdFunc2ArgList.append(getPathListCmd)

    if len(outScene.exitList) > 0:
        getCmdFunc2ArgList.append(getExitListCmd)

    if outScene.writeCutscene:
        getCmdFunc2ArgList.append(getCutsceneDataCmd)

    sceneCmdData = (
        (outScene.getAltHeaderListCmd(outScene.alternateHeadersName()) if outScene.hasAlternateHeaders() else "")
        + (",\n".join(getCmd(outScene) for getCmd in getCmdFunc1ArgList) + ",\n")
        + (",\n".join(getCmd(outScene, headerIndex) for getCmd in getCmdFunc2ArgList) + ",\n")
        + outScene.getEndCmd()
    )

    # .h
    cmdListData.header = f"extern {declarationBase}[]" + ";\n"

    # .c
    cmdListData.source = f"{declarationBase}[]" + " = {\n" + sceneCmdData + "};\n\n"

    return cmdListData


def getSceneCommandListXML(outScene: OOTScene, headerIndex: int):
    cmdListData = ""

    getCmdFunc1ArgList = [
        getSoundSettingsCmdXML,
        getRoomListCmdXML,
        getMiscSettingsCmdXML,
        getColHeaderCmdXML,
        getSpecialFilesCmdXML,
        getSkyboxSettingsCmdXML,
    ]

    getCmdFunc2ArgList = [getSpawnListCmdXML, getSpawnActorListCmdXML, getLightSettingsCmdXML]

    if len(outScene.transitionActorList) > 0:
        getCmdFunc2ArgList.append(getTransActorListCmdXML)

    if len(outScene.pathList) > 0:
        getCmdFunc2ArgList.append(getPathListCmdXML)

    if len(outScene.exitList) > 0:
        getCmdFunc2ArgList.append(getExitListCmdXML)

    if outScene.writeCutscene:
        getCmdFunc2ArgList.append(getCutsceneDataCmdXML)

    cmdListData += (
        (outScene.getAltHeaderListCmdXML(outScene.alternateHeadersName()) if outScene.hasAlternateHeaders() else "")
        + ("\n".join(getCmd(outScene) for getCmd in getCmdFunc1ArgList) + "\n")
        + ("\n".join(getCmd(outScene, headerIndex) for getCmd in getCmdFunc2ArgList) + "\n")
        + outScene.getEndCmdXML()
    )

    return cmdListData
