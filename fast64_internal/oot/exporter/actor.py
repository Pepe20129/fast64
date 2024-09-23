from ...utility import indent
from ..oot_ids import ootActorIds

# this file is not inside the room folder since the scene data can have actors too


class Actor:
    """Defines an Actor"""

    def __init__(self):
        self.name = str()
        self.id = str()
        self.pos: list[int] = []
        self.rot = str()
        self.params = str()

    def getActorEntry(self):
        """Returns a single actor entry"""

        posData = "{ " + ", ".join(f"{round(p)}" for p in self.pos) + " }"
        rotData = "{ " + self.rot + " }"

        actorInfos = [self.id, posData, rotData, self.params]
        infoDescs = ["Actor ID", "Position", "Rotation", "Parameters"]

        return (
            indent
            + (f"// {self.name}\n" + indent if self.name != "" else "")
            + "{\n"
            + ",\n".join((indent * 2) + f"/* {desc:10} */ {info}" for desc, info in zip(infoDescs, actorInfos))
            + ("\n" + indent + "},\n")
        )

    def getActorEntryXML(actor: OOTActor):
        """Returns a single actor entry"""
        split_rotation = actor.rotation.split(", ")
        split_processed_rotation = []
        for split_rotation_value in split_rotation:
            split_processed_rotation.append(
                str(int(split_rotation_value, 16))
                if split_rotation_value.startswith("0x")
                else int(float(re.search(r"DEG_TO_BINANG\(([^()]*?)\)", split_rotation_value).group(1)) * 0x8000 / 180)
            )

        actorID = actor.actorID
        for i, actorElement in enumerate(ootActorIds):
            if actorElement == actorID:
                actorID = i

        return (
            indent * 2
            + f'<ActorEntry Id="{actorID}" PosX="{actor.position[0]}" PosY="{actor.position[1]}" PosZ="{actor.position[2]}" '
            + f'RotX="{split_processed_rotation[0]}" RotY="{split_processed_rotation[1]}" RotZ="{split_processed_rotation[2]}" Params="{int(actor.actorParam, 16)}"/>'
        )
