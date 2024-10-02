from dataclasses import dataclass
from ....utility import CData, indent


@dataclass(unsafe_hash=True)
class SurfaceType:
    """This class defines a single surface type"""

    # surface type 0
    bgCamIndex: int
    exitIndex: int
    floorType: int
    unk18: int  # unused?
    wallType: int
    floorProperty: int
    isSoft: bool
    isHorseBlocked: bool

    # surface type 1
    material: int
    floorEffect: int
    lightSetting: int
    echo: int
    canHookshot: bool
    conveyorSpeed: int
    conveyorDirection: int
    isWallDamage: bool  # unk27

    useMacros: bool

    def getIsSoftC(self):
        return "1" if self.isSoft else "0"

    def getIsHorseBlockedC(self):
        return "1" if self.isHorseBlocked else "0"

    def getCanHookshotC(self):
        return "1" if self.canHookshot else "0"

    def getIsWallDamageC(self):
        return "1" if self.isWallDamage else "0"

    def getSurfaceType0(self):
        """Returns surface type properties for the first element of the data array"""

        if self.useMacros:
            return (
                ("SURFACETYPE0(")
                + f"{self.bgCamIndex}, {self.exitIndex}, {self.floorType}, {self.unk18}, "
                + f"{self.wallType}, {self.floorProperty}, {self.getIsSoftC()}, {self.getIsHorseBlockedC()}"
                + ")"
            )
        else:
            return (
                (indent * 2 + "(")
                + " | ".join(
                    prop
                    for prop in [
                        f"(({self.getIsHorseBlockedC()} & 1) << 31)",
                        f"(({self.getIsSoftC()} & 1) << 30)",
                        f"(({self.floorProperty} & 0x0F) << 26)",
                        f"(({self.wallType} & 0x1F) << 21)",
                        f"(({self.unk18} & 0x07) << 18)",
                        f"(({self.floorType} & 0x1F) << 13)",
                        f"(({self.exitIndex} & 0x1F) << 8)",
                        f"({self.bgCamIndex} & 0xFF)",
                    ]
                )
                + ")"
            )

    def getSurfaceType1(self):
        """Returns surface type properties for the second element of the data array"""

        if self.useMacros:
            return (
                ("SURFACETYPE1(")
                + f"{self.material}, {self.floorEffect}, {self.lightSetting}, {self.echo}, "
                + f"{self.getCanHookshotC()}, {self.conveyorSpeed}, {self.conveyorDirection}, {self.getIsWallDamageC()}"
                + ")"
            )
        else:
            return (
                (indent * 2 + "(")
                + " | ".join(
                    prop
                    for prop in [
                        f"(({self.getIsWallDamageC()} & 1) << 27)",
                        f"(({self.conveyorDirection} & 0x3F) << 21)",
                        f"(({self.conveyorSpeed} & 0x07) << 18)",
                        f"(({self.getCanHookshotC()} & 1) << 17)",
                        f"(({self.echo} & 0x3F) << 11)",
                        f"(({self.lightSetting} & 0x1F) << 6)",
                        f"(({self.floorEffect} & 0x03) << 4)",
                        f"({self.material} & 0x0F)",
                    ]
                )
                + ")"
            )

    def getEntryC(self):
        """Returns an entry for the surface type array"""

        if self.useMacros:
            return indent + "{ " + self.getSurfaceType0() + ", " + self.getSurfaceType1() + " },"
        else:
            return (indent + "{\n") + self.getSurfaceType0() + ",\n" + self.getSurfaceType1() + ("\n" + indent + "},")

    def getEntryXML(self):
        surfaceType0 = (
            ((int(self.getIsHorseBlockedC()) & 1) << 31) |
            ((int(self.getIsSoftC()) & 1) << 30) |
            ((int(self.floorProperty) & 0x0F) << 26) |
            ((int(self.wallType) & 0x1F) << 21) |
            ((int(self.unk18) & 0x07) << 18) |
            ((int(self.floorType) & 0x1F) << 13) |
            ((int(self.exitIndex) & 0x1F) << 8) |
            (int(self.bgCamIndex) & 0xFF)
        )

        surfaceType1 = (
            ((int(self.getIsWallDamageC()) & 1) << 27) |
            ((int(self.conveyorDirection) & 0x3F) << 21) |
            ((int(self.conveyorSpeed) & 0x07) << 18) |
            ((int(self.getCanHookshotC()) & 1) << 17) |
            ((int(self.echo) & 0x3F) << 11) |
            ((int(self.lightSetting) & 0x1F) << 6) |
            ((int(self.floorEffect) & 0x03) << 4) |
            (int(self.material) & 0x0F)
        )

        return (
            indent +
            f'<PolygonType Data1="{self.surfaceType0}" Data2="{self.surfaceType1}"/>'
        )


@dataclass
class SurfaceTypes:
    """This class defines the array of surface types"""

    name: str
    surfaceTypeList: list[SurfaceType]

    def getC(self):
        surfaceData = CData()
        listName = f"SurfaceType {self.name}[{len(self.surfaceTypeList)}]"

        # .h
        surfaceData.header = f"extern {listName};\n"

        # .c
        surfaceData.source = (
            (listName + " = {\n") + "\n".join(poly.getEntryC() for poly in self.surfaceTypeList) + "\n};\n\n"
        )

        return surfaceData

    def getXML(self):
        return "\n".join(poly.getEntryXML() for poly in self.surfaceTypeList)
