from .....utility import CData, indent
from ....oot_level_classes import OOTScene, OOTLight
from .actor import getActorEntryXML
from ....oot_ids import ootActorIds, ootEntranceIds


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
    for room in outScene.rooms:
        data += indent + "    " + f'<RoomEntry Path="{{resource_base_path}}/{outScene.name}_room_{str(room)}.xml"/>\n'
    data += indent + "</SetRoomList>"

    return data


def getTransActorListCmd(outScene: OOTScene, headerIndex: int):
    return (
        indent + "SCENE_CMD_TRANSITION_ACTOR_LIST("
    ) + f"{len(outScene.transitionActorList)}, {outScene.transitionActorListName(headerIndex)})"


def getTransActorListCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetTransitionActorList>\n"
    for transActor in outScene.transitionActorList:
        actorID = transActor.actorID
        for i, actorElement in enumerate(ootActorIds):
            if actorElement == actorID:
                actorID = i

        data += (
            indent
            + "    "
            + f'<TransitionActorEntry FrontSideRoom="{transActor.frontRoom}" FrontSideEffects="{transActor.frontCam}" BackSideRoom="{transActor.backRoom}" BackSideEffects="{transActor.backCam}" Id="{actorID}" PosX="{transActor.position[0]}" PosY="{transActor.position[1]}" PosZ="{transActor.position[2]}" RotY="{transActor.rotationY}" Params="{int(transActor.actorParam, 16)}"/>\n'
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
    return indent + f'<SetCollisionHeader FileName="{{resource_base_path}}/{outScene.sceneName()}_collision.xml"/>'


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
    data = indent + f"<SetPathways>\n"
    for i in range(len(outScene.pathList)):
        data += (
            indent + f'    <Pathway FilePath="{{resource_base_path}}/{outScene.sceneName()}_pathway_{str(i)}.xml"/>\n'
        )
    data += indent + f"</SetPathways>"

    return data


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
        + f'<SetSkyboxSettings Unknown="0" SkyboxId="{int(outScene.skyboxID, 16)}" Weather="{int(outScene.skyboxCloudiness, 16)}" Indoors="{int(outScene.skyboxLighting == "true")}"/>'
    )


def getExitListCmd(outScene: OOTScene, headerIndex: int):
    return indent + f"SCENE_CMD_EXIT_LIST({outScene.exitListName(headerIndex)})"


def getExitListCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetExitList>\n"
    for exit in outScene.exitList:
        entranceID = exit.index
        for i, entranceElement in enumerate(ootEntranceIds):
            if entranceElement == entranceID:
                entranceID = i

        data += indent + "    " + f'<ExitEntry Id="{entranceID}"/>\n'
    data += indent + "</SetExitList>"

    return data


def getLightSettingsCmd(outScene: OOTScene, headerIndex: int):
    return (
        indent + "SCENE_CMD_ENV_LIGHT_SETTINGS("
    ) + f"{len(outScene.lights)}, {outScene.lightListName(headerIndex) if len(outScene.lights) > 0 else 'NULL'})"


def getLightSettingsEntryXML(light: OOTLight, lightMode: str, isLightingCustom: bool, index: int):
    lightDescs = ["Dawn", "Day", "Dusk", "Night"]

    if not isLightingCustom and lightMode == "LIGHT_MODE_TIME":
        # @TODO: Improve the lighting system.
        # Currently Fast64 assumes there's only 4 possible settings for "Time of Day" lighting.
        # This is not accurate and more complicated,
        # for now we are doing ``index % 4`` to avoid having an OoB read in the list
        # but this will need to be changed the day the lighting system is updated.
        lightDesc = f"<!-- {lightDescs[index % 4]} Lighting -->\n"
    else:
        isIndoor = not isLightingCustom and lightMode == "LIGHT_MODE_SETTINGS"
        lightDesc = f"<!-- {'Indoor' if isIndoor else 'Custom'} No. {index + 1} Lighting -->\n"

    lightData = (
        f"<LightingSetting"
        + f' AmbientColorR="{light.ambient[0]}" AmbientColorG="{light.ambient[1]}" AmbientColorB="{light.ambient[2]}"'
        + f' Light1DirX="{str(light.diffuseDir0[0] - 0x100 if light.diffuseDir0[0] > 0x7F else f"{light.diffuseDir0[0]:5}").strip()}" Light1DirY="{str(light.diffuseDir0[1] - 0x100 if light.diffuseDir0[1] > 0x7F else f"{light.diffuseDir0[1]:5}").strip()}" Light1DirZ="{str(light.diffuseDir0[2] - 0x100 if light.diffuseDir0[2] > 0x7F else f"{light.diffuseDir0[2]:5}").strip()}"'
        + f' Light1ColorR="{light.diffuse0[0]}" Light1ColorG="{light.diffuse0[1]}" Light1ColorB="{light.diffuse0[2]}"'
        + f' Light2DirX="{str(light.diffuseDir1[0] - 0x100 if light.diffuseDir1[0] > 0x7F else f"{light.diffuseDir1[0]:5}").strip()}" Light2DirY="{str(light.diffuseDir1[1] - 0x100 if light.diffuseDir1[1] > 0x7F else f"{light.diffuseDir1[1]:5}").strip()}" Light2DirZ="{str(light.diffuseDir1[2] - 0x100 if light.diffuseDir1[2] > 0x7F else f"{light.diffuseDir1[2]:5}").strip()}"'
        + f' Light2ColorR="{light.diffuse1[0]}" Light2ColorG="{light.diffuse1[1]}" Light2ColorB="{light.diffuse1[2]}"'
        + f' FogColorR="{light.fogColor[0]}" FogColorG="{light.fogColor[1]}" FogColorB="{light.fogColor[2]}"'
        + f' FogNear="{((light.transitionSpeed << 10) | light.fogNear)}" FogFar="{light.fogFar}"'
        + f"/>"
        + lightDesc
    )

    return lightData


def getLightSettingsCmdXML(outScene: OOTScene, headerIndex: int):
    data = indent + "<SetLightingSettings>\n"
    for i, light in enumerate(outScene.lights):
        data += (
            indent
            + "    "
            + getLightSettingsEntryXML(light, outScene.skyboxLighting, outScene.isSkyboxLightingCustom, i)
        )
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
