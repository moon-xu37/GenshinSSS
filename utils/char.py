from copy import deepcopy
from typing import Dict, List
from .dtypes import *
from .dnode import *
from .weapon import Weapon
from .artifact import Artifact
from .buff import Buff
from data.charinfo import char_info
from data.curves import lv_curve


class Char(object):
    def __init__(self, name, lv, asc, cx, a_, e_, q_):
        self.base: CharBase = CharBase(name, lv, asc)
        self.attr: CharAttr = CharAttr(cx, a_, e_, q_)
        self.attr.update_base(self.base)

    def connect(self, *args):
        for arg in args:
            if isinstance(arg, Weapon):
                self.attr.update_weapon(arg)
            elif isinstance(arg, Artifact):
                self.attr.update_artifact(arg)
            elif isinstance(arg, Buff):
                self.attr.connect(arg)

    def disconnect(self, buff):
        self.attr.disconnect(buff)

    def __getitem__(self, key: str) -> DNode:
        if hasattr(self.attr, key):
            return deepcopy(getattr(self.attr, key))
        else:
            return DNode()


class CharBase(object):
    def __init__(self, name: str, lv: int, asc: bool):
        self.name: str = ''
        self.nick_names: List[str] = []
        self.rarity: str = ''
        self.weapon: int = 0
        self.element: int = 0
        self.region: int = 0
        self.energy: int = 0
        self.lv:  int = 0
        self.asc: int = 0
        self.asc_info: Dict[str, List[float]] = {}
        self.HP_BASE:  float = 0
        self.ATK_BASE: float = 0
        self.DEF_BASE: float = 0
        self.HP:  float = 0
        self.ATK: float = 0
        self.DEF: float = 0
        self.EXTRA: List[str, float] = ['', 0]

        self.choose(name, lv, asc)

    def choose(self, name: str, lv: int, asc: bool):
        self.name = name
        c = char_info.get(name)
        self.rarity = str(c['rarity'])
        self.weapon = c['weapon']
        self.element = c['element']
        self.region = c['region']
        self.energy = c['energy']
        self.HP_BASE = c['HP_BASE']
        self.ATK_BASE = c['ATK_BASE']
        self.DEF_BASE = c['DEF_BASE']
        self.asc_info = c['asc']

        self.lv = lv
        self.asc = self.set_asc(lv, asc)
        lv_list = lv_curve[self.rarity]
        self.HP = self.HP_BASE * lv_list[self.lv]
        self.ATK = self.ATK_BASE * lv_list[self.lv]
        self.DEF = self.DEF_BASE * lv_list[self.lv]
        if self.asc:
            self.HP += self.asc_info['HP_BASE'][self.asc-1]
            self.ATK += self.asc_info['ATK_BASE'][self.asc-1]
            self.DEF += self.asc_info['DEF_BASE'][self.asc-1]
            for k in self.asc_info.keys():
                if 'BASE' not in k:
                    self.EXTRA[0] = k
                    self.EXTRA[1] = self.asc_info[k][self.asc-1]
                    break
        else:
            self.EXTRA[0] = [
                k for k in self.asc_info.keys() if 'BASE' not in k][0]
            self.EXTRA[1] = 0

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


class CharAttr(object):
    def __init__(self, cx: int, a_: int, e_: int, q_: int):
        '''
        ### 包含面板属性\n
        - ATK | DEF | HP | EM | ER | CRIT_RATE | CRIT_DMG\n
        - HEAL_BONUS | HEAL_INCOME | SHIELD_STRENGTH | CD_REDUCTION\n
        - ELEM_DMG... | ELEM_RES...\n
        ### 和其他属性\n
        - ATK_SPD | MOVE_SPD | INTERRUPT_RES | DMG_REDUCTION\n
        '''
        # panel attributes
        self.ATK: DNode = self.tree_expr('ATK')
        self.DEF: DNode = self.tree_expr('DEF')
        self.HP:  DNode = self.tree_expr('HP')
        self.EM: DNode = DNode('Total EM', '+')
        self.ER: DNode = DNode('Total ER', '+')
        self.CRIT_RATE:       DNode = DNode('Total CRIT_RATE',       '+')
        self.CRIT_DMG:        DNode = DNode('Total CRIT_DMG',        '+')
        self.HEAL_BONUS:      DNode = DNode('Total HEAL_BONUS',      '+')
        self.HEAL_INCOME:     DNode = DNode('Total HEAL_INCOME',     '+')
        self.SHIELD_STRENGTH: DNode = DNode('Total SHIELD_STRENGTH', '+')
        self.CD_REDUCTION:    DNode = DNode('Total CD_REDUCTION',    '+')
        self.ANEMO_DMG:       DNode = DNode('Total ANEMO_DMG',       '+')
        self.GEO_DMG:         DNode = DNode('Total GEO_DMG',         '+')
        self.ELECTRO_DMG:     DNode = DNode('Total ELECTRO_DMG',     '+')
        self.HYDRO_DMG:       DNode = DNode('Total HYDRO_DMG',       '+')
        self.PYRO_DMG:        DNode = DNode('Total PYRO_DMG',        '+')
        self.CRYO_DMG:        DNode = DNode('Total CRYO_DMG',        '+')
        self.DENDRO_DMG:      DNode = DNode('Total DENDRO_DMG',      '+')
        self.PHYSICAL_DMG:    DNode = DNode('Total PHYSICAL_DMG',    '+')
        # other attributes
        self.ATK_SPD:  float = 0
        self.MOVE_SPD: float = 0
        self.INTERRUPT_RES: float = 0
        self.DMG_REDUCTION: float = 0
        # talent attributes
        self.cx_lv: int = cx
        self.normatk_lv:   int = a_
        self.elemskill_lv: int = e_
        self.elemburst_lv: int = q_
        self.name: str = ''

    def tree_expr(self, stat: str) -> DNode:
        root = DNode(f'Total {stat}', '+')
        root.extend([
            DNode(f'Scaled {stat}', '*').extend([
                DNode(f'{stat} Base', '+').extend([
                    DNode(f'Character {stat} Base'),
                    DNode(f'Weapon {stat} Base')
                ]),
                DNode(f'{stat} Scalers', '+').extend([
                    DNode('Base', '', 1),
                    DNode('Artifact Scalers', '+'),
                    DNode('Bonus Scalers', '+'),
                    DNode('Weapon Scaler'),
                    DNode('Ascension Scaler')
                ])
            ]),
            DNode(f'Flat {stat}', '+').extend([
                DNode('Artifact Flat', '+'),
                DNode('Bonus Flat', '+')
            ]),
            # DNode(f'Bonus {stat}', '+').extend([
            #     DNode(f'Skill Transform {stat}', '*').extend([
            #         DNode('Skill Transform Stat'),
            #         DNode('Skill Transform Scaler')
            #     ]),
            #     DNode(f'Weapon Transform {stat}', '*').extend([
            #         DNode('Weapon Transform Stat'),
            #         DNode('Weapon Transform Scaler')
            #     ])
            # ])
        ])
        return root

    def update_base(self, base: CharBase):
        self.name = base.name
        for k in ['ATK', 'DEF', 'HP']:
            self.__dict__[k].modify(
                f'Character {k} Base',
                num=base.__dict__[k]
            )
        for k, n in zip(['ER', 'CRIT_RATE', 'CRIT_DMG'], [100, 5, 50]):
            try:
                self.__dict__[k].modify(f'Character {k} Base', num=n)
            except:
                self.__dict__[k].insert(DNode(f'Character {k} Base', '%', n))

        if base.EXTRA[0] in ['ATK_PER', 'DEF_PER', 'HP_PER']:
            k = base.EXTRA[0].split('_')[0]
            self.__dict__[k].modify('Ascension Scaler', num=base.EXTRA[1])
        elif base.EXTRA[0]:
            k, n = base.EXTRA[0], base.EXTRA[1]
            try:
                self.__dict__[k].modify(f'Character {k} Ascension', num=n)
            except:
                self.__dict__[k].insert(
                    DNode(f'Character {k} Ascension', num=n))

    def update_weapon(self, weapon: Weapon):
        self.ATK.modify('Weapon ATK Base', num=weapon.ATK)
        sub_stat, stat_value = weapon.sub_stat.name, weapon.stat_value
        if sub_stat in ['ATK_PER', 'DEF_PER', 'HP_PER']:
            self.__dict__[sub_stat.split('_')[0]].modify(
                'Weapon Scaler', num=stat_value)
        else:
            try:
                self.__dict__[sub_stat].modify('Weapon Scaler', num=stat_value)
            except:
                self.__dict__[sub_stat].insert(
                    DNode('Weapon Scaler', '', stat_value))
        bonus_stat, bonus_value = weapon.bonus_stat, weapon.bonus_stat_value
        if not bonus_stat:
            return
        elif bonus_stat in ['ATK_PER', 'DEF_PER', 'HP_PER']:
            try:
                self.__dict__[bonus_stat.split('_')[0]].modify(
                    'Weapon Bonus Scaler', num=bonus_value)
            except:
                self.__dict__[bonus_stat.split('_')[0]].find('Bonus Scalers').insert(
                    DNode('Weapon Bonus Scaler', '', bonus_value))
        elif bonus_stat != 'ELEM_DMG':
            try:
                self.__dict__[bonus_stat].modify(
                    'Weapon Bonus Scaler', num=bonus_value)
            except:
                self.__dict__[bonus_stat].insert(
                    DNode('Weapon Bonus Scaler', '', bonus_value))

    def update_artifact(self, artifact: Artifact) -> None:
        for stat, val in artifact.sub_value:
            if 'CONST' in stat:
                front = stat.split('_')[0]
                self.__dict__[front].find('Artifact Flat').insert(
                    DNode(f'SubStat {stat} {self.name}', '', val).argument())
            elif 'PER' in stat:
                front = stat.split('_')[0]
                self.__dict__[front].find('Artifact Scalers').insert(
                    DNode(f'SubStat {stat} {self.name}', '%', val).argument())
            elif stat == 'EM':
                self.__dict__[stat].insert(
                    DNode(f'SubStat {stat} {self.name}', '', val).argument())
            else:
                self.__dict__[stat].insert(
                    DNode(f'SubStat {stat} {self.name}', '%', val).argument())

        for pos, stat, val in artifact.main_value:
            if 'CONST' in stat:
                front = stat.split('_')[0]
                self.__dict__[front].find('Artifact Flat').insert(
                    DNode(f'MainStat {stat} {pos}', '', val))
            elif 'PER' in stat:
                front = stat.split('_')[0]
                self.__dict__[front].find('Artifact Scalers').insert(
                    DNode(f'MainStat {stat} {pos}', '%', val))
            elif stat == 'EM':
                self.__dict__[stat].insert(
                    DNode(f'MainStat {stat} {pos}', '', val))
            else:
                self.__dict__[stat].insert(
                    DNode(f'MainStat {stat} {pos}', '%', val))

        for stat, func, val, name in artifact.piece_effect:
            if 'PER' in stat:
                front = stat.split('_')[0]
                self.__dict__[front].find('Bonus Scalers').insert(
                    DNode(f'{name} Piece2', func, val))
            else:
                self.__dict__[stat].insert(
                    DNode(f'{name} Piece2', func, val))

    def connect(self, buff: Buff):
        tar_list = [buff.attr_val] if buff.attr_val != 'ELEM_DMG' else \
            ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
             'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']
        for tar in tar_list:
            tar_node: DNode = getattr(self, tar)
            buff.work(tar_node)

    def disconnect(self, buff: Buff):
        tar_list = [buff.attr_val] if buff.attr_val != 'ELEM_DMG' else \
            ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
             'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']
        for tar in tar_list:
            tar_node: DNode = getattr(self, tar)
            for a in buff.adds:
                tar_node.remove(a[1].key)


class Panel(object):
    def __init__(self, character: Char, target: str = ''):
        '''记录面板树\n使用`target`则只记录部分面板树'''
        self.ATK = DNode('ATK')
        self.DEF = DNode('DEF')
        self.HP = DNode('HP')
        self.EM = DNode('EM')
        self.ER = DNode('ER')
        self.CRIT_RATE = DNode('CRIT_RATE')
        self.CRIT_DMG = DNode('CRIT_DMG')
        self.HEAL_BONUS = DNode('HEAL_BONUS')
        self.HEAL_INCOME = DNode('HEAL_INCOME')
        self.SHIELD_STRENGTH = DNode('SHIELD_STRENGTH')
        self.CD_REDUCTION = DNode('CD_REDUCTION')
        self.ANEMO_DMG = DNode('ANEMO_DMG')
        self.GEO_DMG = DNode('GEO_DMG')
        self.ELECTRO_DMG = DNode('ELECTRO_DMG')
        self.HYDRO_DMG = DNode('HYDRO_DMG')
        self.PYRO_DMG = DNode('PYRO_DMG')
        self.CRYO_DMG = DNode('CRYO_DMG')
        self.DENDRO_DMG = DNode('DENDRO_DMG')
        self.PHYSICAL_DMG = DNode('PHYSICAL_DMG')

        for k in self.__dict__.keys():
            if target and k != target:
                continue
            self.__dict__[k] = character[k]
            self.__dict__[k].key = k

    def __getitem__(self, key: str) -> DNode:
        if hasattr(self, key):
            return deepcopy(getattr(self, key))
        else:
            return DNode()
