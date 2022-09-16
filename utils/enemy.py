from typing import Dict
from .dtypes import ElementType


class Enemy(object):
    def __init__(self, lv: int = 90, name: str = '', hp: int = 1e5, res: Dict = {}):
        self.lv: int = lv
        self.name: str = name
        self.HP: float = hp
        self.RES: Dict[ElementType: int] = dict.fromkeys(
            ElementType.__members__.values(), 10) if not res else res

    def work(self, node, elem: ElementType):
        try:
            node.modify('Enemy Level', num=self.lv)
        except:
            pass
        try:
            node.modify('Resistance Base', num=self.RES[elem])
        except:
            pass
