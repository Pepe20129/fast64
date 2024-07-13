from .....utility import CData, indent
from .....f3d.f3d_gbi import ScrollMethod, TextureExportSettings
from ....oot_model_classes import OOTGfxFormatter
from ....oot_constants import ootEnumRoomShapeType
from ....oot_level_classes import OOTRoom, OOTRoomMeshGroup, OOTRoomMesh
import os

ootRoomShapeStructs = [
    "RoomShapeNormal",
    "RoomShapeImage",
    "RoomShapeCullable",
]

ootRoomShapeEntryStructs = [
    "RoomShapeDListsEntry",
    "RoomShapeDListsEntry",
    "RoomShapeCullableEntry",
]


def getRoomShapeDLEntry(meshEntry: OOTRoomMeshGroup, roomShape: str):
    opaqueName = meshEntry.DLGroup.opaque.name if meshEntry.DLGroup.opaque is not None else "NULL"
    transparentName = meshEntry.DLGroup.transparent.name if meshEntry.DLGroup.transparent is not None else "NULL"

    roomShapeDListsEntries = "{ "
    if roomShape == "ROOM_SHAPE_TYPE_CULLABLE":
        roomShapeDListsEntries += (
            "{ " + ", ".join(f"{pos}" for pos in meshEntry.cullGroup.position) + " }, "
        ) + f"{meshEntry.cullGroup.cullDepth}, "
    roomShapeDListsEntries += f"{opaqueName}, {transparentName}" + " },\n"

    return roomShapeDListsEntries


# Texture files must be saved separately.
def getRoomShapeImageData(roomMesh: OOTRoomMesh, textureSettings: TextureExportSettings):
    code = CData()

    if len(roomMesh.bgImages) > 1:
        declarationBase = f"RoomShapeImageMultiBgEntry {roomMesh.getMultiBgStructName()}"

        # .h
        code.header += f"extern {declarationBase}[{len(roomMesh.bgImages)}];\n"

        # .c
        code.source += f"{declarationBase}[{len(roomMesh.bgImages)}] = {{\n"
        for i in range(len(roomMesh.bgImages)):
            bgImage = roomMesh.bgImages[i]
            code.source += indent + "{\n" + bgImage.multiPropertiesC(2, i) + indent + "},\n"
        code.source += f"}};\n\n"

    bitsPerValue = 64
    for bgImage in roomMesh.bgImages:
        # .h
        code.header += f"extern u{bitsPerValue} {bgImage.name}[];\n"

        # .c
        code.source += (
            # This is to force 8 byte alignment
            (f"Gfx {bgImage.name}_aligner[] = " + "{ gsSPEndDisplayList() };\n" if bitsPerValue != 64 else "")
            + (f"u{bitsPerValue} {bgImage.name}[SCREEN_WIDTH * SCREEN_HEIGHT / 4]" + " = {\n")
            + f'#include "{textureSettings.includeDir + bgImage.getFilename()}.inc.c"'
            + "\n};\n\n"
        )

    return code


def getRoomShape(outRoom: OOTRoom):
    roomShapeInfo = CData()
    roomShapeDLArray = CData()
    mesh = outRoom.mesh

    shapeTypeIdx = [value[0] for value in ootEnumRoomShapeType].index(mesh.roomShape)
    dlEntryType = ootRoomShapeEntryStructs[shapeTypeIdx]
    structName = ootRoomShapeStructs[shapeTypeIdx]
    roomShapeImageFormat = "Multi" if len(mesh.bgImages) > 1 else "Single"

    if mesh.roomShape == "ROOM_SHAPE_TYPE_IMAGE":
        structName += roomShapeImageFormat

    roomShapeInfo.header = f"extern {structName} {mesh.headerName()};\n"

    if mesh.roomShape != "ROOM_SHAPE_TYPE_IMAGE":
        entryName = mesh.entriesName()
        dlEntryDeclarationBase = f"{dlEntryType} {mesh.entriesName()}[{len(mesh.meshEntries)}]"

        roomShapeInfo.source = (
            "\n".join(
                (
                    f"{structName} {mesh.headerName()} = {{",
                    indent + f"{mesh.roomShape},",
                    indent + f"ARRAY_COUNT({entryName}),",
                    indent + f"{entryName},",
                    indent + f"{entryName} + ARRAY_COUNT({entryName})",
                    f"}};",
                )
            )
            + "\n\n"
        )

        roomShapeDLArray.header = f"extern {dlEntryDeclarationBase};\n"
        roomShapeDLArray.source = dlEntryDeclarationBase + " = {\n"

        for entry in mesh.meshEntries:
            roomShapeDLArray.source += indent + getRoomShapeDLEntry(entry, mesh.roomShape)

        roomShapeDLArray.source += "};\n\n"
    else:
        # type 1 only allows 1 room
        entry = mesh.meshEntries[0]

        roomShapeImageFormatValue = (
            "ROOM_SHAPE_IMAGE_AMOUNT_SINGLE" if roomShapeImageFormat == "Single" else "ROOM_SHAPE_IMAGE_AMOUNT_MULTI"
        )

        roomShapeInfo.source += (
            (f"{structName} {mesh.headerName()}" + " = {\n")
            + (indent + f"{{ ROOM_SHAPE_TYPE_IMAGE, {roomShapeImageFormatValue}, &{mesh.entriesName()} }},\n")
            + (
                mesh.bgImages[0].singlePropertiesC(1)
                if roomShapeImageFormat == "Single"
                else indent + f"ARRAY_COUNTU({mesh.getMultiBgStructName()}), {mesh.getMultiBgStructName()},"
            )
            + "\n};\n\n"
        )

        roomShapeDLArray.header = f"extern {dlEntryType} {mesh.entriesName()};\n"
        roomShapeDLArray.source = (
            f"{dlEntryType} {mesh.entriesName()} = {getRoomShapeDLEntry(entry, mesh.roomShape)[:-2]};\n\n"
        )

    roomShapeInfo.append(roomShapeDLArray)
    return roomShapeInfo


def getRoomShapeXML(outRoom: OOTRoom):
    roomShapeXML = (
        indent
        + f'<SetMesh Data="0" MeshHeaderType="{outRoom.mesh.roomShape}" PolyNum="{len(outRoom.mesh.meshEntries)}">\n'
    )
    for meshEntry in outRoom.mesh.meshEntries:
        opaqueName = meshEntry.DLGroup.opaque.name if meshEntry.DLGroup.opaque is not None else ""
        transparentName = meshEntry.DLGroup.transparent.name if meshEntry.DLGroup.transparent is not None else ""
        roomShapeXML += (
            indent
            + f'    <Polygon PolyType="0" PosX="{meshEntry.cullGroup.position[0]}" PosY="{meshEntry.cullGroup.position[1]}" PosZ="{meshEntry.cullGroup.position[2]}" Unknown="{meshEntry.cullGroup.cullDepth}" MeshOpa="{(f"{{resource_base_path}}/{opaqueName}.xml" if opaqueName != "" else "")}" MeshXlu="{(f"{{resource_base_path}}/{transparentName}.xml" if transparentName != "" else "")}"/>\n'
        )
    roomShapeXML += indent + f"</SetMesh>"

    return roomShapeXML


def getRoomModel(outRoom: OOTRoom, textureExportSettings: TextureExportSettings):
    roomModel = CData()
    mesh = outRoom.mesh

    for i, entry in enumerate(mesh.meshEntries):
        if entry.DLGroup.opaque is not None:
            roomModel.append(entry.DLGroup.opaque.to_c(mesh.model.f3d))

        if entry.DLGroup.transparent is not None:
            roomModel.append(entry.DLGroup.transparent.to_c(mesh.model.f3d))

        # type ``ROOM_SHAPE_TYPE_IMAGE`` only allows 1 room
        if i == 0 and mesh.roomShape == "ROOM_SHAPE_TYPE_IMAGE":
            break

    roomModel.append(mesh.model.to_c(textureExportSettings, OOTGfxFormatter(ScrollMethod.Vertex)).all())
    roomModel.append(getRoomShapeImageData(outRoom.mesh, textureExportSettings))

    return roomModel


def getRoomModelXML(outRoom: OOTRoom, textureExportSettings: TextureExportSettings, resourceBasePath, logging_func):
    roomModel = ""
    mesh = outRoom.mesh
    logging_func({"INFO"}, "getRoomModelXML 0")

    for i, entry in enumerate(mesh.meshEntries):
        if entry.DLGroup.opaque is not None:
            logging_func({"INFO"}, "getRoomModelXML 1")
            roomModel += "<!-- getRoomModelXML entry.DLGroup.opaque start "
            roomModel += entry.DLGroup.opaque.to_soh_xml(resourceBasePath[:-1], resourceBasePath[:-1])
            roomModel += " getRoomModelXML entry.DLGroup.opaque end -->"

        if entry.DLGroup.transparent is not None:
            logging_func({"INFO"}, "getRoomModelXML 2")
            roomModel += "<!-- getRoomModelXML entry.DLGroup.transparent start "
            roomModel += entry.DLGroup.transparent.to_soh_xml(resourceBasePath[:-1], resourceBasePath[:-1])
            roomModel += " getRoomModelXML entry.DLGroup.transparent end -->"

        # type ``ROOM_SHAPE_TYPE_IMAGE`` only allows 1 room
        if i == 0 and mesh.roomShape == "ROOM_SHAPE_TYPE_IMAGE":
            break

    logging_func(
        {"INFO"},
        "getRoomModelXML 3 textureExportSettings.exportPath="
        + (textureExportSettings.exportPath if textureExportSettings.exportPath is not None else "None"),
    )
    logging_func(
        {"INFO"}, "getRoomModelXML 4 resourceBasePath=" + (resourceBasePath if resourceBasePath is not None else "None")
    )
    roomModel += "<!-- getRoomModelXML mesh.model.to_soh_xml start -->"
    roomModel += mesh.model.to_soh_xml(
        os.path.join(textureExportSettings.exportPath, ""), resourceBasePath[:-1], logging_func
    )
    roomModel += "<!-- getRoomModelXML mesh.model.to_soh_xml end -->"

    logging_func({"INFO"}, "getRoomModelXML 5")
    roomModel += "<!-- getRoomModelXML getRoomShapeImageData start -->"
    roomModel += str(getRoomShapeImageData(outRoom.mesh, textureExportSettings))
    roomModel += "<!-- getRoomModelXML getRoomShapeImageData end -->"
    logging_func({"INFO"}, "getRoomModelXML 6")

    return roomModel
