from random import random
from copy import deepcopy
from .dnode import DNode
from .dtypes import *
from .char import Panel
from .buff import Buff
from .event import Event
from .enemy import Enemy
from data.reactinfo import reaction_info


class Nums(object):
    def __init__(self, buff_type: BuffType):
        self.type: BuffType = buff_type
        self.root: DNode = DNode()
        self.source: str = ''
        self.depend: str = ''
        self.buffed: list = []
        self.time: int = 0

    def init_tree(self):
        return

    def to_event(self, event: Event):
        return

    def to_panel(self, panel: Panel):
        return

    def to_buff(self, buff: Buff):
        return

    def to_enemy(self, enemy: Enemy):
        return

    def __repr__(self) -> str:
        return str(self.root)

    @property
    def value(self) -> float:
        return self.root.value

    def safe_insert(self, panel: Panel, attr: str, key: str, mid_key: str = ''):
        n: DNode = panel[attr]
        n.key = 'Entity '+n.key
        try:
            if mid_key:
                mid = self.root.find(mid_key)
            else:
                mid = self.root
            mid.find(key).insert(n)
        except:
            return


class Damage(Nums):
    __multipliers = ['Basic Multiplier',
                     'Bonus Multiplier',
                     'Critical Multiplier',
                     'Resistance Multiplier',
                     'Defence Multiplier']
    # 'Amplifying Multiplier',

    __amplify_scaler = {ReactType.VAPORIZE: 2,
                        ReactType.VAPORIZE_REVERSE: 1.5,
                        ReactType.MELT: 2,
                        ReactType.MELT_REVERSE: 1.5}

    __catalyze_scaler = {ReactType.AGGRAVATE: 1.15,
                         ReactType.SPREAD: 1.25}

    def __init__(self):
        super().__init__(BuffType.DMG)
        self.init_tree()
        self.damage_type: DamageType = DamageType.NONE
        self.elem_type:  ElementType = ElementType.NONE
        self.react_type:   ReactType = ReactType.NONE

    def init_tree(self) -> None:
        self.root = DNode('Total Damage', '*')
        for m in self.__multipliers:
            self.root.insert(DNode(m, '+'))
        self.root.find('Basic Multiplier').insert(
            DNode('Stat x Scaler', '*').extend([
                DNode('Ability Scaler', '+'),
            ])
        )
        self.root.find('Bonus Multiplier').extend([
            DNode('Base', '', 1),
            DNode('Damage Bonus', '+'),
        ])
        self.root.find('Critical Multiplier').extend([
            DNode('Base', '', 1),
            DNode('Expectation', 'THRESH_E').extend([
                DNode('Critical Rate', '+'),
                DNode('Critical DMG', '+')
            ])
        ])
        self.root.find('Resistance Multiplier').insert(
            DNode('Resistance', 'RES').extend([
                DNode('Resistance Base', '%', 10),
                DNode('Resistance Debuff', '+')
            ]),
        )
        self.root.find('Defence Multiplier').insert(
            DNode('Defence', 'DEF').extend([
                DNode('Character Level', '', 90),
                DNode('Enemy Level', '', 100),
                DNode('Defence Ignore', '+'),
                DNode('Defence Reduction', '+')
            ])
        )

    def to_event(self, event: Event):
        info = event.args
        self.time = event.time
        self.source = event.source
        self.depend = event.depend if event.depend else 'ATK'
        self.damage_type = info.get('damage_type', DamageType.NONE)
        self.elem_type = info.get('elem_type', ElementType.PHYSICAL)
        self.react_type = info.get('react', ReactType.NONE)

        self.root.modify('Character Level', num=event.lv)
        self.root.find('Ability Scaler').insert(
            DNode('Basic Ability Scaler', '', event.scaler))

        self.root.find('Bonus Multiplier').insert(
            DNode(f'{self.elem_type.name} Bonus', '+'))
        i = list(DamageType.__members__.values()).index(self.damage_type)
        nodes = [DNode(),
                 DNode('Normal Attack Bonus', '+'),
                 DNode('Charged Attack Bonus', '+'),
                 DNode('Plunging Attack Bonus', '+'),
                 DNode('Elemental Skill Bonus', '+'),
                 DNode('Elemental Burst Bonus', '+')]
        if nodes[i].key:
            self.root.find('Bonus Multiplier').insert(nodes[i])

        self.amplify()
        self.catalyze()

        if event.mode in [ModeType.SIM, ModeType.NOTCRIT, ModeType.CRIT]:
            n: DNode = self.root.find('Critical Rate')
            cr = max(n.value, 0)
            n.key = 'Sim Crit Result'
            n.func = ''
            n.child.clear()
            if event.mode == ModeType.CRIT or (event.mode == ModeType.SIM and random() < cr):
                n.num = 1
            else:
                n.num = 0
        elif event.mode == ModeType.MISS:
            self.root.insert(DNode('Miss'))

    def to_panel(self, panel: Panel):
        depend: DNode = getattr(panel, self.depend)
        if depend.value:
            self.safe_insert(panel, self.depend, 'Stat x Scaler')
            self.safe_insert(panel, f'{self.elem_type.name}_DMG',
                             f'{self.elem_type.name} Bonus')
            self.safe_insert(panel, 'CRIT_RATE', 'Critical Rate')
            self.safe_insert(panel, 'CRIT_DMG', 'Critical DMG')
        else:
            try:
                self.root.find('EM Bonus')
            except:
                return
            else:
                self.safe_insert(panel, 'EM', 'EM Bonus')

    def to_buff(self, buff: Buff):
        buff.work(self.root)
        self.buffed.append(buff.desc)

    def to_enemy(self, enemy: Enemy):
        enemy.work(self.root, self.elem_type)

    def amplify(self):
        if self.react_type in self.__amplify_scaler:
            scaler = self.__amplify_scaler[self.react_type]
            self.root.insert(
                DNode('Amplifying Multiplier', '*').extend([
                    DNode('ReactType Multiplier', '', scaler),
                    DNode('Reaction Multiplier', '+').extend([
                        DNode('Base', '', 1),
                        DNode('EM Bonus', 'EM_A'),
                        DNode('Reaction Bonus', '+')
                    ])
                ])
            )

    def catalyze(self):
        if self.react_type in self.__catalyze_scaler:
            lv = self.root.find('Character Level').value
            mul = reaction_info['player'][lv]
            scaler = self.__catalyze_scaler[self.react_type]
            self.root.find('Basic Multiplier').insert(
                DNode('Catalyze Bonus', '*').extend([
                    DNode('Level Multiplier', '', mul),
                    DNode('ReactType Multiplier', '', scaler),
                    DNode('Reaction Multiplier', '+').extend([
                        DNode('Base', '', 1),
                        DNode('EM Bonus', 'EM_C'),
                        DNode('Reaction Bonus', '+')
                    ])
                ])
            )

    def for_sim(self) -> tuple:
        'return [(dmg, cr, cd)]'
        node = self.root.find('Critical Multiplier')
        try:
            cr = node.find('Critical Rate').value
        except:
            cr = node.find('Actual Simulation Critical Result').value
        cr = max(0, min(1, cr))
        cd = node.find('Critical DMG').value
        e = node.value
        v = self.value
        return (v/e, cr, cd)


class TransDamage(Nums):
    __amplify_scaler = {ReactType.VAPORIZE: 2,
                        ReactType.VAPORIZE_REVERSE: 1.5,
                        ReactType.MELT: 2,
                        ReactType.MELT_REVERSE: 1.5}

    __catalyze_scaler = {ReactType.AGGRAVATE: 1.15,
                         ReactType.SPREAD: 1.25}

    def __init__(self):
        super().__init__(BuffType.ELEMENT)
        self.init_tree()
        self.damage_type: DamageType = DamageType.TRANS
        self.elem_type:  ElementType = ElementType.NONE
        self.react_type:   ReactType = ReactType.NONE
        self.sub_react:    ReactType = ReactType.NONE

    def init_tree(self):
        self.root = DNode('Total TransDamage', '*')
        self.root.extend([
            DNode('Basic Multiplier', '+').extend([
                DNode('Stat x Scaler', '*').extend([
                    DNode('Level Multiplier'),
                    DNode('ReactType Multiplier')
                ]),
            ]),
            DNode('Transformative Multiplier', '+').extend([
                DNode('Base', '', 1),
                DNode('EM Bonus', 'EM_T'),
                DNode('Reaction Bonus', '+')
            ]),
            DNode('Resistance Multiplier', 'RES').extend([
                DNode('Resistance Base', '%', 10),
                DNode('Resistance Debuff', '+')
            ]),
        ])

    def to_event(self, event: Event):
        info = event.args
        self.time = event.time
        self.source = event.source
        self.react_type = info.get('trans', ReactType.NONE)
        self.elem_type = info.get('elem', ElementType.PHYSICAL)
        if self.react_type != ReactType.NONE:
            lv = event.lv
            self.root.modify('ReactType Multiplier', num=event.scaler)
            self.root.modify('Level Multiplier',
                             num=reaction_info['player'][lv])
        else:
            self.damage_type = DamageType.NONE
            self.root.remove('Reaction Multiplier')
            self.root.modify('ReactType Multiplier', num=1)
            self.root.modify('Level Multiplier',
                             num=event.args.get('flat', 0))

        self.sub_react = info.get('react', ReactType.NONE)
        self.amplify()
        self.catalyze()

    def to_panel(self, panel: Panel):
        self.safe_insert(panel, 'EM', 'EM Bonus', 'Transformative Multiplier')
        if self.sub_react != ReactType.NONE:
            self.safe_insert(panel, 'EM', 'EM Bonus', 'Amplifying Multiplier')
            self.safe_insert(panel, 'EM', 'EM Bonus', 'Catalyze Bonus')

    def to_buff(self, buff: Buff):
        if hasattr(buff.func, 'react'):
            if any([r in self.__amplify_scaler for r in buff.func.react]):
                buff.work(self.root.find('Amplifying Multiplier'))
            elif any([r in self.__catalyze_scaler for r in buff.func.react]):
                buff.work(self.root.find('Catalyze Bonus'))
            else:
                buff.work(self.root)
        else:
            buff.work(self.root)
        self.buffed.append(buff.desc)

    def to_enemy(self, enemy: Enemy):
        enemy.work(self.root, self.elem_type)

    def amplify(self):
        if self.sub_react in self.__amplify_scaler:
            scaler = self.__amplify_scaler[self.sub_react]
            self.root.insert(
                DNode('Amplifying Multiplier', '*').extend([
                    DNode('ReactType Multiplier', '', scaler),
                    DNode('Reaction Multiplier', '+').extend([
                        DNode('Base', '', 1),
                        DNode('EM Bonus', 'EM_A'),
                        DNode('Reaction Bonus', '+')
                    ])
                ])
            )

    def catalyze(self):
        if self.sub_react in self.__catalyze_scaler:
            lv = self.root.find('Character Level').value
            mul = reaction_info['player'][lv]
            scaler = self.__catalyze_scaler[self.sub_react]
            self.root.find('Basic Multiplier').insert(
                DNode('Catalyze Bonus', '*').extend([
                    DNode('Level Multiplier', '', mul),
                    DNode('ReactType Multiplier', '', scaler),
                    DNode('Reaction Multiplier', '+').extend([
                        DNode('Base', '', 1),
                        DNode('EM Bonus', 'EM_C'),
                        DNode('Reaction Bonus', '+')
                    ])
                ])
            )

    def for_sim(self) -> tuple:
        'return [(dmg, cr, cd)]'
        return (self.value, 0, 0)


class Heal(Nums):
    def __init__(self):
        super().__init__(BuffType.HEALTH)
        self.init_tree()
        self.target: str = ''

    def init_tree(self):
        self.root = DNode('Total Heal', '*')
        self.root.extend([
            DNode('Basic Multiplier', '+').extend([
                DNode('Stat x Scaler', '*').extend([
                    DNode('Ability Scaler', '+'),
                ]),
                DNode('Ability Flat')
            ]),
            DNode('Bonus Multiplier', '+').extend([
                DNode('Base', '', 1),
                DNode('Heal Bonus', '+'),
                DNode('Heal Income', '+')
            ])
        ])

    def to_event(self, event: Event):
        info = event.args
        self.time = event.time
        self.source = event.source
        self.target = info.get('tar', event.source)
        self.depend = event.depend if event.depend else 'HP'
        self.root.find('Ability Scaler').insert(
            DNode('Basic Ability Scaler', '', event.scaler))
        self.root.modify('Ability Flat', num=info.get('flat', 0))

    def to_panel(self, panel: Panel):
        depend: DNode = getattr(panel, self.depend)
        if depend.value:
            self.safe_insert(panel, self.depend, 'Stat x Scaler')
            self.safe_insert(panel, 'HEAL_BONUS', 'Heal Bonus')
        else:
            self.safe_insert(panel, 'HEAL_INCOME', 'Heal Income')

    def to_buff(self, buff: Buff):
        buff.work(self.root)
        self.buffed.append(buff.desc)


class Shield(Nums):
    def __init__(self):
        super().__init__(BuffType.SHIELD)
        self.init_tree()

    def init_tree(self):
        self.root = DNode('Total Shield', '*')
        self.root.extend([
            DNode('Basic Multiplier', '+').extend([
                DNode('Stat x Scaler', '*').extend([
                    DNode('Ability Scaler', '+'),
                ]),
                DNode('Ability Flat')
            ]),
            DNode('Bonus Multiplier', '+').extend([
                DNode('Base', '', 1)
            ])
        ])

    def to_event(self, event: Event):
        info = event.args
        self.time = event.time
        self.source = event.source
        self.depend = event.depend if event.depend else 'HP'
        self.root.find('Ability Scaler').insert(
            DNode('Basic Ability Scaler', '', event.scaler))
        self.root.modify('Ability Flat', num=info.get('flat', 0))

    def to_panel(self, panel: Panel):
        self.safe_insert(panel, self.depend, 'Stat x Scaler')
        self.safe_insert(panel, 'SHIELD_STRENGTH', 'Bonus Multiplier')

    def to_buff(self, buff: Buff):
        buff.work(self.root)
        self.buffed.append(buff.desc)
