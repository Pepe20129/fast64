from dataclasses import dataclass
from bpy.types import Object
from ....utility import PluginError, CData, exportColor, ootGetBaseOrCustomLight, indent
from ...scene.properties import OOTSceneHeaderProperty, OOTLightProperty
from ..utility import Utility
from ...oot_ids import ootEntranceIds


@dataclass
class EnvLightSettings:
    """This class defines the information of one environment light setting"""

    envLightMode: str
    ambientColor: tuple[int, int, int]
    light1Color: tuple[int, int, int]
    light1Dir: tuple[int, int, int]
    light2Color: tuple[int, int, int]
    light2Dir: tuple[int, int, int]
    fogColor: tuple[int, int, int]
    fogNear: int
    zFar: int
    blendRate: int

    def getBlendFogNear(self):
        """Returns the packed blend rate and fog near values"""

        return f"(({self.blendRate} << 10) | {self.fogNear})"

    def getBlendFogNearXML(self):
        """Returns the packed blend rate and fog near values"""

        return ((self.blendRate << 10) | self.fogNear)

    def getColorValues(self, vector: tuple[int, int, int]):
        """Returns and formats color values"""

        return ", ".join(f"{v:5}" for v in vector)

    def getDirectionValues(self, vector: tuple[int, int, int]):
        """Returns and formats direction values"""

        return ", ".join(f"{v - 0x100 if v > 0x7F else v:5}" for v in vector)

    def getEntryC(self, index: int):
        """Returns an environment light entry"""

        isLightingCustom = self.envLightMode == "Custom"

        vectors = [
            (self.ambientColor, "Ambient Color", self.getColorValues),
            (self.light1Dir, "Diffuse0 Direction", self.getDirectionValues),
            (self.light1Color, "Diffuse0 Color", self.getColorValues),
            (self.light2Dir, "Diffuse1 Direction", self.getDirectionValues),
            (self.light2Color, "Diffuse1 Color", self.getColorValues),
            (self.fogColor, "Fog Color", self.getColorValues),
        ]

        fogData = [
            (self.getBlendFogNear(), "Blend Rate & Fog Near"),
            (f"{self.zFar}", "Fog Far"),
        ]

        lightDescs = ["Dawn", "Day", "Dusk", "Night"]

        if not isLightingCustom and self.envLightMode == "LIGHT_MODE_TIME":
            # TODO: Improve the lighting system.
            # Currently Fast64 assumes there's only 4 possible settings for "Time of Day" lighting.
            # This is not accurate and more complicated,
            # for now we are doing ``index % 4`` to avoid having an OoB read in the list
            # but this will need to be changed the day the lighting system is updated.
            lightDesc = f"// {lightDescs[index % 4]} Lighting\n"
        else:
            isIndoor = not isLightingCustom and self.envLightMode == "LIGHT_MODE_SETTINGS"
            lightDesc = f"// {'Indoor' if isIndoor else 'Custom'} No. {index + 1} Lighting\n"

        lightData = (
            (indent + lightDesc)
            + (indent + "{\n")
            + "".join(
                indent * 2 + f"{'{ ' + vecToC(vector) + ' },':26} // {desc}\n" for (vector, desc, vecToC) in vectors
            )
            + "".join(indent * 2 + f"{fogValue + ',':26} // {fogDesc}\n" for fogValue, fogDesc in fogData)
            + (indent + "},\n")
        )

        return lightData

    def getEntryXML(self, index: int):
        """Returns an environment light entry"""

        isLightingCustom = self.envLightMode == "Custom"

        lightDescs = ["Dawn", "Day", "Dusk", "Night"]

        if not isLightingCustom and self.envLightMode == "LIGHT_MODE_TIME":
            # TODO: Improve the lighting system.
            # Currently Fast64 assumes there's only 4 possible settings for "Time of Day" lighting.
            # This is not accurate and more complicated,
            # for now we are doing ``index % 4`` to avoid having an OoB read in the list
            # but this will need to be changed the day the lighting system is updated.
            lightDesc = f"<!-- {lightDescs[index % 4]} Lighting -->\n"
        else:
            isIndoor = not isLightingCustom and self.envLightMode == "LIGHT_MODE_SETTINGS"
            lightDesc = f"<!-- {'Indoor' if isIndoor else 'Custom'} No. {index + 1} Lighting -->\n"

        return (
            indent * 2 +
            f"<LightingSetting"
            + f' AmbientColorR="{self.ambientColor[0]}" AmbientColorG="{self.ambientColor[1]}" AmbientColorB="{self.ambientColor[2]}"'

            + f' Light1DirX="{str(self.light1Dir[0] - 0x100 if self.light1Dir[0] > 0x7F else f"{self.light1Dir[0]:5}").strip()}"'
            + f' Light1DirY="{str(self.light1Dir[1] - 0x100 if self.light1Dir[1] > 0x7F else f"{self.light1Dir[1]:5}").strip()}"'
            + f' Light1DirZ="{str(self.light1Dir[2] - 0x100 if self.light1Dir[2] > 0x7F else f"{self.light1Dir[2]:5}").strip()}"'
            + f' Light1ColorR="{self.light1Color[0]}" Light1ColorG="{self.light1Color[1]}" Light1ColorB="{self.light1Color[2]}"'

            + f' Light2DirX="{str(self.light2Dir[0] - 0x100 if self.light2Dir[0] > 0x7F else f"{self.light2Dir[0]:5}").strip()}"'
            + f' Light2DirY="{str(self.light2Dir[1] - 0x100 if self.light2Dir[1] > 0x7F else f"{self.light2Dir[1]:5}").strip()}"'
            + f' Light2DirZ="{str(self.light2Dir[2] - 0x100 if self.light2Dir[2] > 0x7F else f"{self.light2Dir[2]:5}").strip()}"'
            + f' Light2ColorR="{self.light2Color[0]}" Light2ColorG="{self.light2Color[1]}" Light2ColorB="{self.light2Color[2]}"'

            + f' FogColorR="{self.fogColor[0]}" FogColorG="{self.fogColor[1]}" FogColorB="{self.fogColor[2]}"'
            + f' FogNear="{self.getBlendFogNearXML()}" FogFar="{self.zFar}"'
            + f"/>"
            + lightDesc
        )


@dataclass
class SceneLighting:
    """This class hosts lighting data"""

    name: str
    envLightMode: str
    settings: list[EnvLightSettings]

    @staticmethod
    def new(name: str, props: OOTSceneHeaderProperty):
        envLightMode = Utility.getPropValue(props, "skyboxLighting")
        lightList: list[OOTLightProperty] = []
        settings: list[EnvLightSettings] = []

        if envLightMode == "LIGHT_MODE_TIME":
            todLights = props.timeOfDayLights
            lightList = [todLights.dawn, todLights.day, todLights.dusk, todLights.night]
        else:
            lightList = props.lightList

        for lightProp in lightList:
            light1 = ootGetBaseOrCustomLight(lightProp, 0, True, True)
            light2 = ootGetBaseOrCustomLight(lightProp, 1, True, True)
            settings.append(
                EnvLightSettings(
                    envLightMode,
                    exportColor(lightProp.ambient),
                    light1[0],
                    light1[1],
                    light2[0],
                    light2[1],
                    exportColor(lightProp.fogColor),
                    lightProp.fogNear,
                    lightProp.z_far,
                    lightProp.transitionSpeed,
                )
            )
        return SceneLighting(name, envLightMode, settings)

    def getCmd(self):
        """Returns the env light settings scene command"""

        return (
            indent + "SCENE_CMD_ENV_LIGHT_SETTINGS("
        ) + f"{len(self.settings)}, {self.name if len(self.settings) > 0 else 'NULL'}),\n"

    def getCmdXML(self):
        """Returns the env light settings scene command"""

        #the data is inline
        return self.getXML()

    def getC(self):
        """Returns a ``CData`` containing the C data of env. light settings"""

        lightSettingsC = CData()
        lightName = f"EnvLightSettings {self.name}[{len(self.settings)}]"

        # .h
        lightSettingsC.header = f"extern {lightName};\n"

        # .c
        lightSettingsC.source = (
            (lightName + " = {\n") + "".join(light.getEntryC(i) for i, light in enumerate(self.settings)) + "};\n\n"
        )

        return lightSettingsC

    def getXML(self):
        """Returns a string containing the XML data of env. light settings"""

        return (
            indent + "<SetLightingSettings>\n" +
            "".join(light.getEntryXML(i) for i, light in enumerate(self.settings)) +
            indent + "</SetLightingSettings>\n"
        )


@dataclass
class SceneInfos:
    """This class stores various scene header informations"""

    ### General ###

    keepObjectID: str
    naviHintType: str
    drawConfig: str
    appendNullEntrance: bool
    useDummyRoomList: bool

    ### Skybox And Sound ###

    # Skybox
    skyboxID: str
    skyboxConfig: str

    # Sound
    sequenceID: str
    ambienceID: str
    specID: str

    ### Camera And World Map ###

    # World Map
    worldMapLocation: str

    # Camera
    sceneCamType: str

    @staticmethod
    def new(props: OOTSceneHeaderProperty, sceneObj: Object):
        return SceneInfos(
            Utility.getPropValue(props, "globalObject"),
            Utility.getPropValue(props, "naviCup"),
            Utility.getPropValue(props.sceneTableEntry, "drawConfig"),
            props.appendNullEntrance,
            sceneObj.fast64.oot.scene.write_dummy_room_list,
            Utility.getPropValue(props, "skyboxID"),
            Utility.getPropValue(props, "skyboxCloudiness"),
            Utility.getPropValue(props, "musicSeq"),
            Utility.getPropValue(props, "nightSeq"),
            Utility.getPropValue(props, "audioSessionPreset"),
            Utility.getPropValue(props, "mapLocation"),
            Utility.getPropValue(props, "cameraMode"),
        )

    def getCmds(self, lights: SceneLighting):
        """Returns the sound settings, misc settings, special files and skybox settings scene commands"""

        return (
            indent
            + f",\n{indent}".join(
                [
                    f"SCENE_CMD_SOUND_SETTINGS({self.specID}, {self.ambienceID}, {self.sequenceID})",
                    f"SCENE_CMD_MISC_SETTINGS({self.sceneCamType}, {self.worldMapLocation})",
                    f"SCENE_CMD_SPECIAL_FILES({self.naviHintType}, {self.keepObjectID})",
                    f"SCENE_CMD_SKYBOX_SETTINGS({self.skyboxID}, {self.skyboxConfig}, {lights.envLightMode})",
                ]
            )
            + ",\n"
        )


    def getCmdsXML(self, lights: SceneLighting):
        """Returns the sound settings, misc settings, special files and skybox settings scene commands"""

        return (
            f"\n{indent}".join(
                [
                    f'<SetSoundSettings Reverb="{self.specID}" NatureAmbienceId="{int(self.ambienceID, 16)}" SeqId="{self.sequenceID}"/>',
                    f'<SetCameraSettings CameraMovement="{int(self.sceneCamType, 16)}" WorldMapArea="{int(self.worldMapLocation, 16)}"/>',
                    f'<SetSpecialObjects ElfMessage="{self.naviHintType}" GlobalObject="{self.keepObjectID}"/>',
                    f'<SetSkyboxSettings Unknown="0" SkyboxId="{int(self.skyboxID, 16)}" Weather="{int(self.skyboxConfig, 16)}" Indoors="{int(lights.envLightMode == "true")}"/>',
                ]
            )
            + "\n"
        )


@dataclass
class SceneExits(Utility):
    """This class hosts exit data"""

    name: str
    exitList: list[tuple[int, str]]

    @staticmethod
    def new(name: str, props: OOTSceneHeaderProperty):
        # TODO: proper implementation of exits

        exitList: list[tuple[int, str]] = []
        for i, exitProp in enumerate(props.exitList):
            if exitProp.exitIndex != "Custom":
                raise PluginError("ERROR: Exits are unfinished, please use 'Custom'.")
            exitList.append((i, exitProp.exitIndexCustom))
        return SceneExits(name, exitList)

    def getCmd(self):
        """Returns the exit list scene command"""

        return indent + f"SCENE_CMD_EXIT_LIST({self.name}),\n"

    def getCmdXML(self):
        """Returns the exit list scene command"""

        #the data is inline
        return self.getXML()

    def getC(self):
        """Returns a ``CData`` containing the C data of the exit array"""

        exitListC = CData()
        listName = f"u16 {self.name}[{len(self.exitList)}]"

        # .h
        exitListC.header = f"extern {listName};\n"

        # .c
        exitListC.source = (
            (listName + " = {\n")
            # @TODO: use the enum name instead of the raw index
            + "\n".join(indent + f"{value}," for (_, value) in self.exitList)
            + "\n};\n\n"
        )

        return exitListC

    def getXML(self):
        """Returns a XML string containing the C data of the exit array"""

        #return (
        #    indent + "<SetExitList>\n" +
        #    "\n".join(indent * 2 + f"<ExitEntry Id="{value}"/>" for (_, value) in self.exitList) +
        #    indent + "</SetExitList>"
        #)

        data = indent + "<SetExitList>\n"
        for _, value in self.exitList:
            entranceID = value
            for i, entranceElement in enumerate(ootEntranceIds):
                if entranceElement == entranceID:
                    entranceID = i

            data += indent * 2 + f'<ExitEntry Id="{entranceID}"/>\n'
        data += indent + "</SetExitList>\n"

        return data
