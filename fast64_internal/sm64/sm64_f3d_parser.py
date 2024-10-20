import bpy
from ..panels import SM64_Panel, sm64GoalImport
from ..utility import *
from ..f3d.f3d_parser import *
from bpy.utils import register_class, unregister_class
from .sm64_constants import level_enums, level_pointers
from .sm64_level_parser import parseLevelAtPointer


class SM64_ImportDL(bpy.types.Operator):
    # set bl_ properties
    bl_idname = "object.sm64_import_dl"
    bl_label = "Import Display List"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Called on demand (i.e. button press, menu item)
    # Can also be called from operator search menu (Spacebar)
    def execute(self, context):
        romfileSrc = None
        try:
            if context.mode != "OBJECT":
                raise PluginError("Operator can only be used in object mode.")
        except Exception as e:
            raisePluginError(self, e)
            return {"CANCELLED"}
        try:
            checkExpanded(bpy.path.abspath(context.scene.importRom))
            romfileSrc = open(bpy.path.abspath(context.scene.importRom), "rb")
            levelParsed = parseLevelAtPointer(romfileSrc, level_pointers[context.scene.levelDLImport])
            segmentData = levelParsed.segmentData
            start = (
                decodeSegmentedAddr(int(context.scene.DLImportStart, 16).to_bytes(4, "big"), segmentData)
                if context.scene.isSegmentedAddrDLImport
                else int(context.scene.DLImportStart, 16)
            )
            readObj = F3DtoBlenderObject(
                romfileSrc, start, context.scene, "sm64_mesh", Matrix.Identity(4), segmentData, True
            )

            applyRotation([readObj], math.radians(-90), "X")
            romfileSrc.close()

            self.report({"INFO"}, "Generic import succeeded.")
            return {"FINISHED"}  # must return a set

        except Exception as e:
            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            if romfileSrc is not None:
                romfileSrc.close()
            raisePluginError(self, e)
            return {"CANCELLED"}


class SM64_ImportDLPanel(SM64_Panel):
    bl_idname = "SM64_PT_import_dl"
    bl_label = "SM64 DL Importer"
    goal = sm64GoalImport

    # called every frame
    def draw(self, context):
        col = self.layout.column()
        propsDLI = col.operator(SM64_ImportDL.bl_idname)

        prop_split(col, context.scene, "DLImportStart", "Start Address")
        col.prop(context.scene, "levelDLImport")
        col.prop(context.scene, "isSegmentedAddrDLImport")
        col.box().label(text="Only Fast3D mesh importing allowed.")


sm64_dl_parser_classes = (SM64_ImportDL,)

sm64_dl_parser_panel_classes = (SM64_ImportDLPanel,)


def sm64_dl_parser_panel_register():
    for cls in sm64_dl_parser_panel_classes:
        register_class(cls)


def sm64_dl_parser_panel_unregister():
    for cls in sm64_dl_parser_panel_classes:
        unregister_class(cls)


def sm64_dl_parser_register():
    for cls in sm64_dl_parser_classes:
        register_class(cls)

    bpy.types.Scene.DLImportStart = bpy.props.StringProperty(name="Start Address", default="A3BE1C")
    bpy.types.Scene.levelDLImport = bpy.props.EnumProperty(items=level_enums, name="Level", default="CG")
    bpy.types.Scene.isSegmentedAddrDLImport = bpy.props.BoolProperty(name="Is Segmented Address", default=False)


def sm64_dl_parser_unregister():
    for cls in reversed(sm64_dl_parser_classes):
        unregister_class(cls)

    del bpy.types.Scene.levelDLImport
    del bpy.types.Scene.DLImportStart
    del bpy.types.Scene.isSegmentedAddrDLImport
