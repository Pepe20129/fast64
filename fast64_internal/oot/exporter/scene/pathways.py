from dataclasses import dataclass, field
from mathutils import Matrix
from bpy.types import Object
from ....utility import PluginError, CData, indent
from ...oot_utility import getObjectList
from ..utility import Utility


@dataclass
class Path:
    """This class defines a pathway"""

    name: str
    points: list[tuple[int, int, int]] = field(default_factory=list)

    def getC(self):
        """Returns the pathway position array"""

        pathData = CData()
        pathName = f"Vec3s {self.name}"

        # .h
        pathData.header = f"extern {pathName}[];\n"

        # .c
        pathData.source = (
            f"{pathName}[]"
            + " = {\n"
            + "\n".join(
                indent + "{ " + ", ".join(f"{round(curPoint):5}" for curPoint in point) + " }," for point in self.points
            )
            + "\n};\n\n"
        )

        return pathData

    def getXML(self):
        """Returns the pathway position array"""

        return (
            indent
            + "<PathData>\n"
            + "".join(
                indent * 2 + f'<PathPoint X="{f"{round(point[0])}"}" Y="{f"{round(point[1])}"}" Z="{f"{round(point[2])}"}"/>\n' for point in self.points
            )
            + indent
            + "</PathData>\n"
        )


@dataclass
class ScenePathways:
    """This class hosts pathways array data"""

    name: str
    pathList: list[Path]

    @staticmethod
    def new(name: str, sceneObj: Object, transform: Matrix, headerIndex: int):
        pathFromIndex: dict[int, Path] = {}
        pathObjList = getObjectList(sceneObj.children_recursive, "CURVE", splineType="Path")

        for obj in pathObjList:
            relativeTransform = transform @ sceneObj.matrix_world.inverted() @ obj.matrix_world
            pathProps = obj.ootSplineProperty
            isHeaderValid = Utility.isCurrentHeaderValid(pathProps.headerSettings, headerIndex)
            if isHeaderValid and Utility.validateCurveData(obj):
                if pathProps.index not in pathFromIndex:
                    pathFromIndex[pathProps.index] = Path(
                        f"{name}List{pathProps.index:02}",
                        [relativeTransform @ point.co.xyz for point in obj.data.splines[0].points],
                    )
                else:
                    raise PluginError(f"ERROR: Path index already used ({obj.name})")

        pathFromIndex = dict(sorted(pathFromIndex.items()))
        if list(pathFromIndex.keys()) != list(range(len(pathFromIndex))):
            raise PluginError("ERROR: Path indices are not consecutive!")

        return ScenePathways(name, list(pathFromIndex.values()))

    def getCmd(self):
        """Returns the path list scene command"""

        return indent + f"SCENE_CMD_PATH_LIST({self.name}),\n" if len(self.pathList) > 0 else ""

    def getCmdXML(self):
        """Returns the path list scene command"""

        return indent + f"<!-- SCENE_CMD_PATH_LIST({self.name}) -->\n" if len(self.pathList) > 0 else ""

        if len(self.pathList) < 0:
            return ""

        data = indent + f"<SetPathways>\n"
        for i in range(len(outScene.pathList)):
            data += (
                indent * 2 + f'<Pathway FilePath="{{resource_base_path}}/{self.name}_{str(i)}.xml"/>\n'
            )
        data += indent + f"</SetPathways>"

        return data

    def getC(self):
        """Returns a ``CData`` containing the C data of the pathway array"""

        pathData = CData()
        pathListData = CData()
        listName = f"Path {self.name}[{len(self.pathList)}]"

        # .h
        pathListData.header = f"extern {listName};\n"

        # .c
        pathListData.source = listName + " = {\n"

        for path in self.pathList:
            pathListData.source += indent + "{ " + f"ARRAY_COUNTU({path.name}), {path.name}" + " },\n"
            pathData.append(path.getC())

        pathListData.source += "};\n\n"
        pathData.append(pathListData)

        return pathData

    def getXML(self):
        """Returns a string containing the XML data of the pathway array"""

        return (
            indent +
            "<Path>\n" +
            "".join(path.getXML() for path in self.pathList) +
            "</Path>"
        )
