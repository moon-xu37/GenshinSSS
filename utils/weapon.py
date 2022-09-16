from typing import List
from .dtypes import WeaponType, StatType
from data.curves import weapon_lv_curve
from data.weaponinfo import weapon_info


class Weapon(object):
    __asc_info = {
        3: [19.5, 38.9, 58.4, 77.8, 97.3, 116.7],
        4: [25.9, 51.9, 77.8, 103.7, 129.7, 155.6],
        5: [31.1, 62.2, 93.4, 124.5, 155.6, 186.7]
    }

    def __init__(self, name: str, refine: int, lv: int, asc: bool):
        self.name: str = ''
        self.rarity: int = 5
        self.weapon_type: WeaponType = WeaponType(1)
        self.lv: int = 0
        self.asc: int = 0
        self.ATK_BASE: float = 0
        self.ATK: float = 0
        self.atk_curve: str = ''
        self.sub_stat: StatType = StatType(1)
        self.stat_base: float = 0
        self.stat_value: float = 0
        self.stat_curve: str = ''

        self.refine: int = 1
        self.bonus_stat: str = ''
        self.bonus_stat_value: float = 0.0
        self.scaler: List[float] = []
        self.skill: object = None
        self.skillname: str = ''
        self.choose(name, refine, lv, asc)

    def choose(self, name: str, refine: int, lv: int, asc: bool):
        self.refine = refine
        self.name = name
        for w in weapon_info:
            if w['name'] == name:
                self.skillname = w['skill']['skill_name']
                self.bonus_stat = w['skill']['bonus_stat']
                if self.bonus_stat:
                    self.bonus_stat_value = w['skill']['bonus_stat_value'][refine-1]
                self.scaler = w['skill']['param_list'][refine-1]
                self.rarity = w['rarity']
                self.weapon_type = WeaponType(w['weapon_type'])
                self.sub_stat = StatType[w['sub_stat']]
                self.stat_base = w['stat_base']
                self.stat_curve = w['stat_curve']
                self.ATK_BASE = w['ATK_BASE']
                self.atk_curve = w['atk_curve']
                break
        self.lv = lv
        self.asc = self.set_asc(lv, asc)
        atk_curve = weapon_lv_curve[self.atk_curve]
        stat_curve = weapon_lv_curve[self.stat_curve]
        self.ATK = self.ATK_BASE * atk_curve[self.lv]
        self.stat_value = self.stat_base * stat_curve[self.lv]
        if self.asc:
            self.ATK += self.__asc_info[self.rarity][self.asc-1]

    @staticmethod
    def set_asc(lv: int, asc: bool) -> int:
        if lv <= 20:
            return (lv + int(asc))//21
        elif (20 < lv < 40):
            return lv // 20
        elif (lv % 10 != 0):
            return lv // 10 - 2
        else:
            return min(lv // 10 - 3 + int(asc), 6)
