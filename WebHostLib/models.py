from datetime import datetime
from uuid import UUID, uuid4
from pony.orm import Database, PrimaryKey, Required, Set, Optional, buffer, LongStr

from Utils import utcnow

db = Database()

STATE_QUEUED = 0
STATE_STARTED = 1
STATE_ERROR = -1

def uuid4_room_id() -> UUID:
    base_id = uuid4()
    # In k8s mode, the room ID is part of the ingress hostname; hostname segments must start with an alphanumeric character per DNS RFC.  Losing two bits of entropy from the 128-bit UUID isn't a humungous loss.
    while (base_id.bytes[0] >> 2) >= 62:
        base_id = uuid4()
    return base_id

class Slot(db.Entity):
    id = PrimaryKey(int, auto=True)
    player_id = Required(int)
    player_name = Required(str)
    data = Optional(bytes, lazy=True)
    seed = Optional('Seed')
    game = Required(str)


class Room(db.Entity):
    id = PrimaryKey(UUID, default=uuid4_room_id)
    last_activity: datetime = Required(datetime, default=lambda: utcnow(), index=True)
    creation_time: datetime = Required(datetime, default=lambda: utcnow(), index=True)  # index used by landing page
    owner = Required(UUID, index=True)
    commands = Set('Command')
    seed = Required('Seed', index=True)
    multisave = Optional(buffer, lazy=True)
    show_spoiler = Required(int, default=0)  # 0 -> never, 1 -> after completion, -> 2 always
    timeout = Required(int, default=lambda: 2 * 60 * 60)  # seconds since last activity to shutdown
    tracker = Optional(UUID, index=True)
    # Port special value -1 means the server errored out. Another attempt can be made with a page refresh
    last_port = Optional(int, default=lambda: 0)


class Seed(db.Entity):
    id = PrimaryKey(UUID, default=uuid4)
    rooms = Set(Room)
    multidata = Required(bytes, lazy=True)
    owner = Required(UUID, index=True)
    creation_time: datetime = Required(datetime, default=lambda: utcnow(), index=True)  # index used by landing page
    slots = Set(Slot)
    spoiler = Optional(LongStr, lazy=True)
    meta = Required(LongStr, default=lambda: "{\"race\": false}")  # additional meta information/tags


class Command(db.Entity):
    id = PrimaryKey(int, auto=True)
    room = Required(Room)
    commandtext = Required(str)


class Generation(db.Entity):
    id = PrimaryKey(UUID, default=uuid4)
    owner = Required(UUID)
    options = Required(buffer, lazy=True)
    meta = Required(LongStr, default=lambda: "{\"race\": false}")
    state = Required(int, default=0, index=True)


class GameDataPackage(db.Entity):
    checksum = PrimaryKey(str)
    data = Required(bytes)

