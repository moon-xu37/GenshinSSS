from typing import Dict
from .dtypes import EventType, ModeType, ElementType


class Event(object):
    def __init__(self, **config):
        '''Attributes:\n
        `type`, `name`, `family`, `source`\\
        `time`, `endtime`\\
        `depend`, `actiontime`, `cooltime`, `scaler`, `snapshot`, `lv`\\
        `desc`, `visible`\\
        `mode`
        ---
        - in Damage
        args: `damage_type`, `elem_type`, `react_type`
        - in TransDamage
        args: `trans`, `elem_type`, `react_type`
        - in Heal: args: `flat`
        - in Shield: args: `flat`\\
        (all need `depend`, `scaler`, `lv`)
        ---
        (`elem`, `react`, `view`, `manual`)
        '''
        self.type: EventType = EventType.NONE
        self.name: str = ''
        self.family: str = ''
        self.source: str = ''
        self.time: int = 0  # use frame not second
        self.endtime: int = 0
        self.depend: str = ''
        self.cooltime: int = 0
        self.actiontime: int = 0
        self.scaler: float = 0.0
        self.mode: ModeType = ModeType.EXPECT
        self.snapshot: str = ''
        self.lv: int = 0
        self.visible: bool = False
        self.desc: str = ''
        self.args: Dict = {}

        self.initialize(**config)

    def initialize(self, **config):
        all_key = [k for k in self.__dict__.keys() if k != 'args']
        for k, v in config.items():
            if k in all_key:
                setattr(self, k, v)
            else:
                self.args[k] = v

    @property
    def dur(self) -> int:
        return self.endtime-self.time

    def __lt__(self, other: 'Event'):
        if self.time < other.time:
            return True
        elif self.time > other.time:
            return False
        else:
            return self.type.value < other.type.value

    def __repr__(self) -> str:
        return 'EVENT:[{:<8}][{:^10}][{:^10}]< {:<4}F> :{:<20}'.format(
            self.type.name, self.name, self.source, self.time, self.desc)
