from copy import deepcopy
from typing import Dict, Callable, List
from utils.dtypes import *
from utils.dnode import DNode
from utils.buff import Buff
from utils.nums import Nums, Damage, TransDamage, Heal, Shield
from data.translation import chinese_translation as c_trans

# ---trigger functions---


class _DamageTypeChecker(object):
    def __init__(self, *types):
        self.types = list(types)

    def __call__(self, damage: Nums) -> bool:
        return isinstance(damage, Damage) and (not self.types or damage.damage_type in self.types)


class _DamageElemChecker(object):
    def __init__(self, *elem: ElementType):
        self.elem = list(elem)

    def __call__(self, damage: Nums) -> bool:
        return (isinstance(damage, Damage) or isinstance(damage, TransDamage)) \
            and (not self.elem or damage.elem_type in self.elem)


class _DamageCounter(object):
    def __init__(self, num: int, elem: ElementType, *types):
        self.elem = elem
        self.num = num
        self.types = list(types)

    def __call__(self, damage: Nums) -> bool:
        if self.num > 0 \
                and (isinstance(damage, Damage) or isinstance(damage, TransDamage)) \
                and (self.elem == ElementType.NONE or damage.elem_type == self.elem) \
                and (not self.types or damage.damage_type in self.types):
            self.num -= 1
            return True
        else:
            return False


class _ResistanceChecker(object):
    def __init__(self, elem: ElementType):
        self.elem = elem

    def __call__(self, damage: Nums) -> bool:
        return (isinstance(damage, Damage) or isinstance(damage, TransDamage)) and damage.elem_type == self.elem


class _ReactTypeChecker(object):
    def __init__(self, *react):
        self.react = list(react)

    def __call__(self, damage: Nums) -> bool:
        return (isinstance(damage, Damage) and damage.react_type in self.react) \
            or (isinstance(damage, TransDamage) and (damage.react_type in self.react or
                                                     damage.sub_react in self.react))

# ---formatter---


__buff_keys = ['name', 'type', 'dur', 'tar', 'func', 'adds', 'desc']


def _auto_generate_buff(proto: Buff, mappings: List[Dict],
                        time_bias: int = 0, view: bool = True) -> List[Buff]:
    '''
    arguments are default\n
    mappings keys = `name`, `type`, `dur`, `tar`, `func`, `adds`, `desc`,
    \t(`view`)
    '''
    buffs: List[Buff] = []
    name, family, source = proto.name, proto.family, proto.source
    for map in mappings:
        if name != map['name']:
            continue
        buff = Buff(type=map['type'],
                    name=name, family=family, source=source, **proto.args)
        buff.begin = proto.begin+time_bias
        if map['dur'] != 0:
            buff.end = buff.begin+map['dur'] if not proto.end else proto.end
        else:
            buff.begin, buff.end = 0, 1_000_000
        if buff.type == BuffType.DMG:
            buff.num_tar = map['tar']
            buff.func = map['func']
        elif buff.type == BuffType.ATTR:
            buff.attr_tar = map['tar']
            buff.attr_val = map['func']
        buff.adds = map['adds']
        if map['dur'] != 0:
            flag = map.get('view') if 'view' in map else view
        else:
            flag = map.get('view') if 'view' in map else False
        if 'delay' in proto.args:
            buff.args['delay'] = proto.args['delay']
        buff.visible = proto.args.get('view', flag)
        buff.desc = map['desc']
        buffs.append(buff)
    return buffs


# ---passive and cx---


def Ayaka_PS(buff: Buff, inter) -> List[Buff]:
    func1 = _DamageTypeChecker(DamageType.NORMAL_ATK,
                               DamageType.CHARGED_ATK)
    func2 = 'CRYO_DMG'
    adds = [[('Normal Attack Bonus',  DNode('Ayaka Passive1', '%', 30)),
             ('Charged Attack Bonus', DNode('Ayaka Passive1', '%', 30))],
            [('Total CRYO_DMG',       DNode('Ayaka Passive2', '%', 18))]]
    config = [['PS1',   BuffType.DMG,   6*60,   buff.source,
               func1,   adds[0],    '神里绫华:天赋一:天罪国罪镇词'],
              ['PS2',   BuffType.ATTR,  10*60,  buff.source,
               func2,   adds[1],    '神里绫华:天赋二:寒天宣命祝词']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Ayaka_CX(buff: Buff, inter) -> List[Buff]:
    func1 = _DamageTypeChecker()
    func2 = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [[('Defence Reduction',    DNode('Ayaka Constellation4', '%', 30))],
            [('Charged Attack Bonus', DNode('Ayaka Constellation6', '%', 298))]]
    config = [['CX4',    BuffType.DMG,   6*60,  'all',
               func1, adds[0], '神里绫华:四命:盈缺流返'],
              ['CX6',   BuffType.DMG,    30,    buff.source,
               func2, adds[1], '神里绫华:六命:间水月']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Jean_CX(buff: Buff, inter) -> List[Buff]:
    func = _ResistanceChecker(ElementType.ANEMO)
    adds = [[('Resistance Debuff', DNode('Jean Constellation4', '%', -40))]]
    config = [['CX4', BuffType.DMG, 10*60, 'all',
               func, adds[0], '琴:四命:蒲公英的国土']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Diluc_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Total PYRO_DMG', DNode('Diluc Passive2', '%', 20))]]
    config = [['PS2', BuffType.ATTR, 12*60, buff.source,
               'PYRO_DMG', adds[0], '迪卢克:天赋二:熔毁之翼']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Diluc_CX(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '1'))
    func1 = _DamageTypeChecker()
    func2 = _DamageTypeChecker(DamageType.ELEM_SKILL)
    func3 = _DamageCounter(2, ElementType.NONE, DamageType.NORMAL_ATK)
    adds = [[('Damage Bonus',   DNode('Diluc Constellation1', '%', 15))],
            [('Bonus Scalers',  DNode('Diluc Constellation2', '%', 10*stack))],
            [('Damage Bonus',   DNode('Diluc Constellation4', '%', 40))],
            [('Damage Bonus',   DNode('Diluc Constellation6', '%', 30))]]
    config = [['CX1',   BuffType.DMG,    5*60,  buff.source,
               func1, adds[0], '迪卢克:一命:罪罚裁断'],
              ['CX2',   BuffType.ATTR,   10*60, buff.source,
               'ATK', adds[1], '迪卢克:二命:炙热余烬'],
              ['CX4',   BuffType.DMG,    2*60,  buff.source,
               func2, adds[2], '迪卢克:四命:流火焦灼'],
              ['CX6',   BuffType.DMG,    6*60,  buff.source,
               func3, adds[3], '迪卢克:六命:清算黑暗的炎之剑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Xiangling_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Bonus Scalers', DNode('Xiangling Passive2', '%', 10))]]
    config = [['PS2', BuffType.ATTR, 10*60, inter.stage,
               'ATK', adds[0], '香菱:天赋二:绝云朝天椒']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Xiangling_CX(buff: Buff, inter) -> List[Buff]:
    func = _ResistanceChecker(ElementType.PYRO)
    adds = [[('Resistance Debuff', DNode('Xiangling Constellation1', '%', -15))],
            [('Total PYRO_DMG', DNode('Xiangling Constellation6', '%', 15))]]
    config = [['CX1', BuffType.DMG, 6*60, 'all',
               func, adds[0],  '香菱:一命:外酥里嫩'],
              ['CX6', BuffType.ATTR, 14*60, 'all',
               'PYRO_DMG', adds[1], '香菱:六命:大龙卷旋火轮']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Xingqiu_PS(buff: Buff, inter) -> List[Buff]:
    asc = inter.characters[buff.source].base.asc >= 4
    adds = [[('Total HYDRO_DMG', DNode('Xingqiu Passive2', '%', 20))]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'HYDRO_DMG', adds[0], '行秋:天赋二:虚实工笔']]
    if not asc:
        config.pop(0)
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Xingqiu_CX(buff: Buff, inter) -> List[Buff]:
    func = _ResistanceChecker(ElementType.HYDRO)
    adds = [[('Resistance Debuff', DNode('Xingqiu Constellation2', '%', -15))]]
    config = [['CX2', BuffType.DMG, 4*60, 'all',
               func, adds[0], '行秋:二命:天青现虹']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Klee_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageCounter(1, ElementType.NONE, DamageType.CHARGED_ATK)
    adds = [[('Damage Bonus', DNode('Klee Passive1', '%', 50))]]
    config = [['PS1', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '可莉:天赋一:砰砰礼物']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings, view=False)


def Klee_CX(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker()
    adds = [[('Defence Reduction',  DNode('Klee Constellation4', '%', 23))],
            [('Total PYRO_DMG',     DNode('Klee Constellation6', '%', 10))]]
    config = [['CX2', BuffType.DMG,  10*60, 'all',
               func,        adds[0], '可莉:二命:破破弹片'],
              ['CX6', BuffType.ATTR, 25*60, 'all',
               'PYRO_DMG',  adds[1], '可莉:六命:火力全开']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Zhongli_PS(buff: Buff, inter) -> List[Buff]:
    func1 = _DamageTypeChecker(DamageType.NORMAL_ATK)
    func2 = _DamageTypeChecker(DamageType.ELEM_SKILL)
    func3 = _DamageTypeChecker(DamageType.ELEM_BURST)
    adds = [
        [('Basic Multiplier', DNode('Zhongli Passive2', '*')),
         ('Zhongli Passive2',
          DNode('Zhongli Passive2 NORMAL_ATK Scaler', '%', 1.39)),
         ('Zhongli Passive2', inter.characters[buff.source].attr.HP)],

        [('Basic Multiplier', DNode('Zhongli Passive2', '*')),
         ('Zhongli Passive2',
          DNode('Zhongli Passive2 ELEM_SKILL Scaler', '%', 1.9)),
         ('Zhongli Passive2', inter.characters[buff.source].attr.HP)],

        [('Basic Multiplier', DNode('Zhongli Passive2', '*')),
         ('Zhongli Passive2',
          DNode('Zhongli Passive2 ELEM_BURST Scaler', '%', 33)),
         ('Zhongli Passive2', inter.characters[buff.source].attr.HP)]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func1, adds[0], '钟离:天赋二:炊金馔玉:普攻'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func2, adds[1], '钟离:天赋二:炊金馔玉:元素战技'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func3, adds[2], '钟离:天赋二:炊金馔玉:元素爆发']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Zhongli_SK(buff: Buff, inter) -> List[Buff]:
    func = _DamageElemChecker()
    adds = [[('Resistance Debuff', DNode('Zhongli ELEM_SKILL buff', '%', -20))]]
    config = [['E', BuffType.DMG, 20*60, 'all',
               func, adds[0], '钟离:元素战技:减抗']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Bennett_SK(buff: Buff, inter) -> List[Buff]:
    info = [0.56, 0.602, 0.644, 0.7, 0.742, 0.784, 0.84,
            0.896, 0.952, 1.008, 1.064, 1.12, 1.19, 1.26, 1.33]
    lv = inter.characters[buff.source].attr.elemburst_lv
    cx1 = inter.characters[buff.source].attr.cx_lv >= 1
    cx6 = inter.characters[buff.source].attr.cx_lv >= 6
    buff.args['delay'] = 30
    atk = inter.characters[buff.source].attr.ATK.find('ATK Base').value
    s = info[lv-1] if not cx1 else info[lv-1]+0.2
    adds = [[('Bonus Flat',
              DNode('Bennett ELEM_BURST buff', '', atk*s))],
            [('Total PYRO_DMG',
              DNode('Bennett ELEM_BURST buff', '%', 15))]]
    keys = __buff_keys+['view']
    config = [['Q', BuffType.ATTR, 12*60, 'stage',
               'ATK', adds[0], '班尼特:元素爆发:鼓舞领域', True]]
    if cx6:
        config.append(['Q', BuffType.ATTR, 12*60, 'stage',
                       'PYRO_DMG', adds[1], '班尼特:六命:烈火与勇气', False])
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Hutao_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Total CRIT_RATE', DNode('Hutao Passive1', '%', 12))],
            [('Total PYRO_DMG', DNode('Hutao Passive2', '%', 33))]]
    config = [['PS2', BuffType.ATTR, 5*60, buff.source,
               'PYRO_DMG', adds[1], '胡桃:天赋二:血之灶火']]
    for char in inter.characters:
        if char == buff.source:
            continue
        config.append(['PS1', BuffType.ATTR, 8*60, char,
                       'CRIT_RATE', adds[0], '胡桃:天赋一:蝶隐之时'])
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Hutao_CX(buff: Buff, inter) -> List[Buff]:
    cx2 = inter.characters[buff.source].attr.cx_lv >= 2
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [[('Basic Multiplier', DNode('Hutao Constellation2', '*')),
             ('Hutao Constellation2', DNode('Hutao Constellation4 Scaler', '%', 10)),
             ('Hutao Constellation2', inter.characters[buff.source].attr.HP)],
            [('Total CRIT_RATE', DNode('Hutao Constellation4', '%', 12))],
            [('Total CRIT_RATE', DNode('Hutao Constellation6', '', 1))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func,  adds[0], '胡桃:二命:最不安神晴又复雨'],
              ['CX6', BuffType.ATTR, 10*60, buff.source,
               'CRIT_RATE',  adds[2], '胡桃:六命:幽蝶能留一缕芳']]
    for char in inter.characters:
        if char == buff.source:
            continue
        config.append(['CX4', BuffType.ATTR, 15*60, char,
                       'CRIT_RATE',  adds[1], '胡桃:四命:伴君眠花房'])
    if not cx2:
        config.pop(0)
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Hutao_SK(buff: Buff, inter) -> List[Buff]:
    info = [0.03841, 0.04071, 0.04301, 0.046, 0.0483, 0.0506, 0.05359,
            0.05658, 0.05957, 0.06256, 0.06555, 0.06854, 0.07153, 0.07452, 0.07751]
    lv = inter.characters[buff.source].attr.elemskill_lv
    base_atk = inter.characters[buff.source].attr.ATK.find('ATK Base').value
    adds = [[('Bonus Flat',
              DNode('Hutao ELEM_BURST buff', 'THRESH')),
             ('Hutao ELEM_BURST buff',
              DNode('Hutao ELEM_BURST buff Threshold', '', base_atk*4)),
             ('Hutao ELEM_BURST buff',
              DNode('Hutao ELEM_BURST Bonus', '*')),
             ('Hutao ELEM_BURST Bonus',
              DNode('Hutao ELEM_BURST Scaler', '', info[lv-1])),
             ('Hutao ELEM_BURST Bonus', deepcopy(inter.characters[buff.source].attr.HP))]]
    config = [['E', BuffType.ATTR, 9*60, buff.source,
               'ATK', adds[0], '胡桃:元素战技:彼岸蝶舞']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kazuha_PS(buff: Buff, inter) -> List[Buff]:
    elem = buff.args.get('elem', ElementType.NONE)
    buff.name += f'_{elem.name}'
    adds = [[(f'Total {elem.name}_DMG', DNode('Kazuha Passive2', '*')),
             ('Kazuha Passive2', DNode('Kazuha Passive2 Scaler', '%', 0.04)),
             ('Kazuha Passive2', deepcopy(inter.characters[buff.source].attr.EM))]]
    config = [[f'PS2_{elem.name}', BuffType.ATTR, 8*60, 'all',
               f'{elem.name}_DMG', adds[0], f'枫原万叶:天赋二:风物之诗咏:{c_trans[elem.name]}']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kazuha_CX(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK,
                              DamageType.PLUNGING_ATK)
    adds = [[('Total EM',              DNode('Kazuha Constellation2', '', 200))],
            [('Normal Attack Bonus',   DNode('Kazuha Constellation6', '*')),
             ('Charged Attack Bonus',  DNode('Kazuha Constellation6', '*')),
             ('Plunging Attack Bonus', DNode('Kazuha Constellation6', '*')),
             ('Kazuha Constellation6', DNode(
                 'Kazuha Constellation6 Scaler', '%', 0.2)),
             ('Kazuha Constellation6', inter.characters[buff.source].attr.EM)]]
    config = [['CX2', BuffType.ATTR, 8*60, buff.source,
               'EM',  adds[0], '枫原万叶:二命:山岚残芯'],
              ['CX2', BuffType.ATTR, 8*60, 'stage',
               'EM',  adds[0], '枫原万叶:二命:山岚残芯'],
              ['CX6', BuffType.DMG,  5*60, buff.source,
               func,  adds[1], '枫原万叶:六命:血赤叶红']]
    if stack == 1:
        config.pop(1)
    if stack == 2:
        config.pop(0)
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Shogun_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Total ELECTRO_DMG', DNode('Shogun Passive2', '*')),
             ('Shogun Passive2', DNode('Shogun Passive2 Scaler', '', 0.4)),
             ('Shogun Passive2', DNode('Shogun Passive2 Stat', '+')),
             ('Shogun Passive2 Stat', DNode('Shogun Passive2 Bias', '', -1)),
             ('Shogun Passive2 Stat', inter.characters[buff.source].attr.ER)]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ELECTRO_DMG', adds[0], '雷电将军:天赋二:殊胜之御体'], ]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Shogun_CX(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker()
    adds = [[('Defence Ignore', DNode('Shogun Constellation2', '%', 60))],
            [('Bonus Scalers',  DNode('Shogun Constellation4', '%', 30))]]
    config = [['CX2', BuffType.DMG, 7*60, buff.source,
               func, adds[0], '雷电将军:二命:斩铁断金']]
    for char in inter.characters.keys():
        if char == buff.source:
            continue
        config.append(['CX4', BuffType.ATTR, 10*60, char,
                       'ATK', adds[1], '雷电将军:四命:誓奉常道'])
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Shogun_SK(buff: Buff, inter) -> List[Buff]:
    info = [0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28,
            0.29, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
    lv = int(inter.characters[buff.source].attr.elemskill_lv)-1
    result = []
    for char, c in inter.characters.items():
        flag = (char == buff.source)
        energy = c.base.energy
        func = _DamageTypeChecker(DamageType.ELEM_BURST)
        adds = [[('Elemental Burst Bonus',
                  DNode('Shogun ELEM_SKILL buff', '%', info[lv]*energy))]]
        config = [['E',  BuffType.DMG, 25*60, char,
                   func, adds[0], '雷电将军:雷罚恶曜之眼']]
        mappings = [dict(zip(__buff_keys, c)) for c in config]
        result.extend(_auto_generate_buff(buff, mappings, view=flag))
    return result


def Kokomi_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Total HEAL_BONUS', DNode('Kokomi Flawless Strategy', '%', 25))],
            [('Total CRIT_RATE',  DNode('Kokomi Flawless Strategy', '', -1))]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'HEAL_BONUS', adds[0], '珊瑚宫心海:庙算无遗'],
              ['AUTO', BuffType.ATTR, 0, buff.source,
               'CRIT_RATE',  adds[1], '珊瑚宫心海:庙算无遗']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kokomi_CX(buff: Buff, inter) -> List[Buff]:
    adds = [[('Total HYDRO_DMG', DNode('Kokomi Constellation6', '%', 40))]]
    config = [['CX6', BuffType.ATTR, 4*60, buff.source,
               'HYDRO_DMG', adds[0], '珊瑚宫心海:六命:珊瑚一心']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kokomi_SK(buff: Buff, inter) -> List[Buff]:
    info = {'1': [0.10416, 0.00808, 77.03738, 0.0484, 0.06776, 10, 18, 70, 0.070963],
            '2': [0.111972, 0.008686, 84.74218, 0.05203, 0.072842, 10, 18, 70, 0.076285],
            '3': [0.119784, 0.009292, 93.08906, 0.05566, 0.077924, 10, 18, 70, 0.081608],
            '4': [0.1302, 0.0101, 102.078, 0.0605, 0.0847, 10, 18, 70, 0.088704],
            '5': [0.138012, 0.010706, 111.70901, 0.06413, 0.089782, 10, 18, 70, 0.094026],
            '6': [0.145824, 0.011312, 121.982086, 0.06776, 0.094864, 10, 18, 70, 0.099348],
            '7': [0.15624, 0.01212, 132.89723, 0.0726, 0.10164, 10, 18, 70, 0.106445],
            '8': [0.166656, 0.012928, 144.45445, 0.07744, 0.108416, 10, 18, 70, 0.113541],
            '9': [0.177072, 0.013736, 156.65373, 0.08228, 0.115192, 10, 18, 70, 0.120637],
            '10': [0.187488, 0.014544, 169.49507, 0.08712, 0.121968, 10, 18, 70, 0.127734],
            '11': [0.197904, 0.015352, 182.97849, 0.09196, 0.128744, 10, 18, 70, 0.13483],
            '12': [0.20832, 0.01616, 197.10397, 0.0968, 0.13552, 10, 18, 70, 0.141926],
            '13': [0.22134, 0.01717, 211.87152, 0.10285, 0.14399, 10, 18, 70, 0.150797],
            '14': [0.23436, 0.01818, 227.28113, 0.1089, 0.15246, 10, 18, 70, 0.159667],
            '15': [0.24738, 0.01919, 243.33281, 0.11495, 0.16093, 10, 18, 70, 0.168538]}
    # q, h, hf, na, ca, dur, cd, energy, e
    heal_bonus = inter.characters[buff.source].attr.HEAL_BONUS.value
    lv = str(inter.characters[buff.source].attr.elemburst_lv)
    func1 = _DamageTypeChecker(DamageType.NORMAL_ATK)
    func2 = _DamageTypeChecker(DamageType.CHARGED_ATK)
    func3 = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [
        [('Basic Multiplier', DNode('Kokomi ELEM_BURST buff', '*')),
         ('Kokomi ELEM_BURST buff',
          DNode('Kokomi ELEM_BURST buff Scalers', '+')),
         ('Kokomi ELEM_BURST buff', inter.characters[buff.source].attr.HP),
         ('Kokomi ELEM_BURST buff Scalers',
          DNode('Kokomi ELEM_BURST Scaler', '', info[lv][3])),
         ('Kokomi ELEM_BURST buff Scalers',
          DNode('Kokomi Passive Scaler', '', heal_bonus*0.15))],

        [('Basic Multiplier', DNode('Kokomi ELEM_BURST buff', '*')),
         ('Kokomi ELEM_BURST buff',
          DNode('Kokomi ELEM_BURST buff Scalers', '+')),
         ('Kokomi ELEM_BURST buff', inter.characters[buff.source].attr.HP),
         ('Kokomi ELEM_BURST buff Scalers',
          DNode('Kokomi ELEM_BURST Scaler', '', info[lv][4])),
         ('Kokomi ELEM_BURST buff Scalers',
          DNode('Kokomi Passive Scaler', '', heal_bonus*0.15))],

        [('Basic Multiplier', DNode('Kokomi ELEM_BURST buff', '*')),
         ('Kokomi ELEM_BURST buff',
          DNode('Kokomi ELEM_BURST Scaler', '', info[lv][-1])),
         ('Kokomi ELEM_BURST buff', inter.characters[buff.source].attr.HP)]]
    config = [['Q', BuffType.DMG, 10*60, buff.source,
               func1, adds[0], '珊瑚宫心海:元素爆发:仪来羽衣'],
              ['Q', BuffType.DMG, 10*60, buff.source,
               func2, adds[1], '珊瑚宫心海:元素爆发:仪来羽衣'],
              ['Q', BuffType.DMG, 10*60, buff.source,
               func3, adds[2], '珊瑚宫心海:元素爆发:仪来羽衣']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Sara_SK(buff: Buff, inter) -> List[Buff]:
    info = [0.4296, 0.46182, 0.49404, 0.537, 0.56922, 0.60144, 0.6444,
            0.68736, 0.73032, 0.77328, 0.81624, 0.8592, 0.9129, 0.9666, 1.0203]
    lv = inter.characters[buff.source].attr.elemskill_lv
    cx6 = buff.args.get(
        'cx', inter.characters[buff.source].attr.cx_lv >= 6)
    atk = inter.characters[buff.source].attr.ATK.find('ATK Base').value
    s = info[lv-1]
    func = _DamageElemChecker(ElementType.ELECTRO)
    adds = [[('Bonus Flat',
              DNode('Sara ELEM_SKILL buff', '', atk*s))],
            [('Critical DMG',
              DNode('Sara ELEM_SKILL buff', '%', 60))]]
    keys = __buff_keys+['view']
    config = [['E', BuffType.ATTR, 6*60, inter.stage,
               'ATK', adds[0], '九条裟罗:元素战技:天狗咒雷', True]]
    if cx6:
        config.append(['E', BuffType.DMG, 6*60, inter.stage,
                       func, adds[1], '九条裟罗:六命:我界', False])
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Yelan_PS(buff: Buff, inter) -> List[Buff]:
    info = [6, 12, 18, 30]
    stack = int(buff.args.get('stack', '0'))
    cnt = len(set([c.base.element for c in inter.characters.values()]))
    func = _DamageTypeChecker()
    adds = [
        [('Bonus Scalers', DNode('Yelan Passive1', '%', info[cnt-1]))],
        [('Damage Bonus', DNode('Yelan Passive2', '%', 1+3.5*stack))]]
    keys = __buff_keys+['view']
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'HP', adds[0], f'夜兰:天赋一:猜先有方:{cnt}层', True],
              ['PS2', BuffType.DMG, 60, 'stage',
               func, adds[1], f'夜兰:天赋二:{stack}层', True]]
    mappings = [dict(zip(keys, c)) for c in config]
    if not buff.args.get('seq', False):
        return _auto_generate_buff(buff, mappings)
    else:
        buffs = []
        for i in range(15):
            adds2 = [[('Damage Bonus', DNode('Yelan Passive2', '%', 1+3.5*i))]]
            config2 = [['PS2', BuffType.DMG, 60, 'stage',
                        func, adds2[0], f'夜兰:天赋二:{i}层']]
            mappings2 = [dict(zip(__buff_keys, c)) for c in config2]
            buffs.extend(_auto_generate_buff(buff, mappings2, time_bias=i*60))
        return buffs


def Yelan_CX(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '1'))
    adds = [[('Bonus Scalers', DNode('Yelan Constellation4', '%', 10*stack))]]
    config = [['CX4', BuffType.ATTR, 25*60, 'all',
               'HP', adds[0], '夜兰:四命:接树移花']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Shenhe_CX(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '0'))
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [
        [('Elemental Skill Bonus', DNode('Shenhe Constellation4', '%', 5*stack))]]
    config = [['CX4', BuffType.DMG, 30, buff.source,
               func, adds[0], '申鹤:四命:洞观']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings, view=False)


def Shenhe_SK(buff: Buff, inter) -> List[Buff]:
    if buff.name == 'E' or buff.name == 'EE':
        info = [0.45656, 0.490802, 0.525044, 0.5707, 0.604942, 0.639184, 0.68484,
                0.730496, 0.776152, 0.821808, 0.867464, 0.91312, 0.97019, 1.02726, 1.08433]
        lv = inter.characters[buff.source].attr.elemskill_lv
        cx6 = buff.args.get(
            'cx', inter.characters[buff.source].attr.cx_lv >= 6)
        result = []
        for char in inter.characters.keys():
            flag = (char == buff.source)
            cnt = 5 if buff.name == 'E' else 7
            if not cx6:
                func = _DamageCounter(cnt,
                                      ElementType.CRYO,
                                      DamageType.NORMAL_ATK,
                                      DamageType.CHARGED_ATK,
                                      DamageType.PLUNGING_ATK,
                                      DamageType.ELEM_SKILL,
                                      DamageType.ELEM_BURST)
            else:
                func = _DamageCounter(cnt,
                                      ElementType.CRYO,
                                      DamageType.PLUNGING_ATK,
                                      DamageType.ELEM_SKILL,
                                      DamageType.ELEM_BURST)
            adds = [
                [('Basic Multiplier', DNode('Shenhe ELEM_SKILL buff', '*')),
                 ('Shenhe ELEM_SKILL buff',
                  DNode('Shenhe ELEM_SKILL buff Scaler', '', info[lv-1])),
                 ('Shenhe ELEM_SKILL buff', inter.characters[buff.source].attr.ATK)]]
            config = [['E',  BuffType.DMG, 10*60, char,
                       func, adds[0], '申鹤:元素战技:冰翎'],
                      ['EE', BuffType.DMG, 15*60, char,
                       func, adds[0], '申鹤:元素战技:冰翎']]
            mappings = [dict(zip(__buff_keys, c)) for c in config]
            result.extend(_auto_generate_buff(buff, mappings, view=flag))

        if cx6:
            func = _DamageCounter(10000,
                                  ElementType.CRYO,
                                  DamageType.NORMAL_ATK,
                                  DamageType.CHARGED_ATK)
            adds = [
                [('Basic Multiplier', DNode('Shenhe ELEM_SKILL buff cx6', '*')),
                 ('Shenhe ELEM_SKILL buff cx6',
                  DNode('Shenhe ELEM_SKILL buff Scaler', '', info[lv-1])),
                 ('Shenhe ELEM_SKILL buff cx6', inter.characters[buff.source].attr.ATK)]]
            config = [['E',  BuffType.DMG, 10*60, 'all',
                       func, adds[0], '申鹤:元素战技:冰翎六命'],
                      ['EE', BuffType.DMG, 15*60, 'all',
                       func, adds[0], '申鹤:元素战技:冰翎六命']]
            mappings = [dict(zip(__buff_keys, c)) for c in config]
            result.extend(_auto_generate_buff(buff, mappings, view=False))

        func1 = _DamageTypeChecker(DamageType.ELEM_SKILL,
                                   DamageType.ELEM_BURST)
        func2 = _DamageTypeChecker(DamageType.NORMAL_ATK,
                                   DamageType.CHARGED_ATK,
                                   DamageType.PLUNGING_ATK)
        adds = [
            [('Elemental Skill Bonus', DNode('Shenhe Passive2', '%', 15)),
             ('Elemental Burst Bonus', DNode('Shenhe Passive2', '%', 15))],
            [('Normal Attack Bonus',   DNode('Shenhe Passive2', '%', 15)),
             ('Charged Attack Bonus',  DNode('Shenhe Passive2', '%', 15)),
             ('Plunging Attack Bonus', DNode('Shenhe Passive2', '%', 15))]]
        config = [['E',  BuffType.DMG, 10*60, 'all',
                   func1, adds[0], '申鹤:天赋二:缚灵通真法印'],
                  ['EE', BuffType.DMG, 15*60, 'all',
                   func2, adds[1], '申鹤:天赋二:缚灵通真法印']]
        mappings = [dict(zip(__buff_keys, c)) for c in config]
        result.extend(_auto_generate_buff(buff, mappings, view=False))
        return result
    elif buff.name == 'Q':
        info = [0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12,
                0.13, 0.14, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15]
        lv = inter.characters[buff.source].attr.elemburst_lv
        cx2 = buff.args.get(
            'cx', inter.characters[buff.source].attr.cx_lv >= 2)
        dur = 12*60 if not cx2 else 18*60
        buff.args['delay'] = 0
        func = _DamageElemChecker(ElementType.CRYO,
                                  ElementType.PHYSICAL)
        adds = [[('Resistance Debuff', DNode('Shnehe ELEM_BURST buff', '', -info[lv-1]))],
                [('Total CRYO_DMG',    DNode('Shenhe Passive1', '%', 15))]]
        keys = __buff_keys+['view']
        config = [['Q', BuffType.DMG, dur, 'all',
                   func, adds[0], '申鹤:元素爆发:减抗', True],
                  ['Q', BuffType.ATTR, dur, 'stage',
                   'CRYO_DMG', adds[1], '申鹤:天赋一:大洞弥罗尊法', False]]
        mappings = [dict(zip(keys, c)) for c in config]
        return _auto_generate_buff(buff, mappings)


# ---shared weapon skill---


def Press_The_Advantage(buff: Buff, inter, chinese: str, english: str) -> List[Buff]:
    '''
    乘胜追击:\\
    击败敌人后,攻击力提升12%/15%/18%/21%/24%,持续30秒.\\
    该效果至多叠加三层,每层持续时间独立.
    '''
    info = [12, 15, 18, 21, 24]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [[
        ('Bonus Scalers', DNode(f'{english} Passive', '%', info[refine]*stack))]]
    config = [['PS', BuffType.DMG, 30*60, buff.source,
               'ATK', adds[0], f'{chinese}:乘胜追击:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Watatsumi_Wavewalker(buff: Buff, inter, chinese: str, english: str) -> List[Buff]:
    '''
    驭浪的海祇民:\\
    队伍中所有角色的元素能量上限的总和,\\
    每1点能使装备此武器的角色的元素爆发造成的伤害提高0.12%/0.15%/0.18%/0.21%/0.24%,\\
    通过这种方式,元素爆发造成的伤害至多提高40%/50%/60%/70%/80%
    '''
    info = [[0.12, 40], [0.15, 50], [0.18, 60], [0.21, 70], [0.24, 80]]
    refine: int = inter.weapons[buff.source].refine-1
    energy = sum([c.base.energy for c in inter.characters.values()])
    increase = min(energy*info[refine][0], info[refine][1])
    func = _DamageTypeChecker(DamageType.ELEM_BURST)
    adds = [[
        ('Elemental Burst Bonus', DNode(f'{english} Passive', '%', increase))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], f'{chinese}:驭浪的海祇民']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings, view=False)


def Golden_Majesty(buff: Buff, inter, chinese: str, english: str) -> List[Buff]:
    '''
    金璋皇极:\\
    护盾强效提升20%/25%/30%/35%/40%。攻击命中后的8秒内,攻击力提升4%/5%/6%/7%/8%。\\
    该效果至多可叠加5层,每0.3秒只能触发一次。此外,处于护盾庇护下时,该效果的攻击力提升效果提高100%。\\
    （注：需要角色在场触发，角色离场效果不提前结束，有护盾时的加成数值在后台不会退化为无护盾时的。）
    '''
    info = [4, 5, 6, 7, 8]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [[
        ('Bonus Scalers', DNode(f'{english} Passive {stack=}', '%', info[refine]*stack))]]
    config = [['PS', BuffType.ATTR, 8*60, buff.source,
               'ATK', adds[0], f'{chinese}:金璋皇极:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)

# ---weapon--


def Cool_Steel_PS(buff: Buff, inter) -> List[Buff]:
    info = [12, 15, 18, 21, 24]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [[
        ('Damage Bonus', DNode('Cool_Steel Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '冷刃']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Harbinger_of_Dawn_PS(buff: Buff, inter) -> List[Buff]:
    info = [14, 17.5, 21, 24.5, 28]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[
        ('Total CRIT_RATE', DNode('Harbinger_of_Dawn Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 5*60, buff.source,
               'CRIT_RATE', adds[0], '黎明神剑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Lions_Roar_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 24, 28, 32, 36]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [[
        ('Damage Bonus', DNode('Lions_Roar Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '匣里龙吟']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Prototype_Rancour_PS(buff: Buff, inter) -> List[Buff]:
    info = [4, 5, 6, 7, 8]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [
        [('Bonus Scalers', DNode('Prototype_Rancour Passive', '%', info[refine]*stack))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[0], f'试做斩岩:{stack}层', True],
              ['PS', BuffType.ATTR, 6*60, buff.source,
               'DEF', adds[0], f'试做斩岩:{stack}层', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Iron_Sting_PS(buff: Buff, inter) -> List[Buff]:
    info = [6, 7.5, 9, 10.5, 12]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker()
    adds = [[
        ('Damage Bonus', DNode('Iron_Sting Passive', '%', info[refine]*stack))]]
    config = [['PS', BuffType.DMG, 6*60, buff.source,
               func, adds[0], f'铁蜂刺:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Blackcliff_Longsword_PS(buff: Buff, inter) -> List[Buff]:
    return Press_The_Advantage(buff, inter, '黑岩长剑', 'Blackcliff_Longsword')


def The_Black_Sword_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK)
    adds = [[('Normal Attack Bonus',
              DNode('The_Black_Sword Passive', '%', info[refine])),
             ('Charged Attack Bonus',
              DNode('The_Black_Sword Passive', '%', info[refine]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '黑剑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def The_Alley_Flash_PS(buff: Buff, inter) -> List[Buff]:
    info = [12, 15, 18, 21, 24]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [[
        ('Damage Bonus', DNode('The_Alley_Flash Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '暗巷闪光']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Festering_Desire_PS(buff: Buff, inter) -> List[Buff]:
    info = [[16, 6], [20, 7.5], [24, 9], [28, 10.5], [32, 12]]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [[('Elemental Skill Bonus',
              DNode('Festering_Desire Passive', '%', info[refine][0]))],
            [('Critical Rate',
              DNode('Festering_Desire Passive', '%', info[refine][1]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '腐殖之剑'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[1], '腐殖之剑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Cinnabar_Spindle_PS(buff: Buff, inter) -> List[Buff]:
    info = [40, 50, 60, 70, 80]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [[
        ('Basic Multiplier', DNode('Cinnabar_Spindle Passive', '*')),
        ('Cinnabar_Spindle Passive',
         DNode('Cinnabar_Spindle Scaler', '%', info[refine])),
        ('Cinnabar_Spindle Passive', inter.characters[buff.source].attr.DEF)]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '辰砂之纺锤']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kagotsurube_Isshin_PS(buff: Buff, inter) -> List[Buff]:
    info = [15]
    # refine: int = inter.weapons[buff.source].refine-1
    adds = [[
        ('Bonus Scalers', DNode('Kagotsurube_Isshin Passive', '%', info[0]))]]
    config = [['PS', BuffType.ATTR, 8*60, buff.source,
               'ATK', adds[0], '笼钓瓶一心']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Sapwood_Blade_PS(buff: Buff, inter) -> List[Buff]:
    info = [60, 75, 90, 105, 120]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [('Total EM', DNode('Sapwood_Blade Passive', '', info[refine]))]]
    config = [['PS', BuffType.ATTR, 12*60, inter.stage,
               'EM', adds[0], '原木刀:森林的瑞佑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def FreedomSworn_PS(buff: Buff, inter) -> List[Buff]:
    info = [[10,    16, 20],
            [12.5,  20, 25],
            [15,    24, 30],
            [17.5,  28, 35],
            [20,    32, 40]]
    refine: int = inter.weapons[buff.source].refine-1
    func1 = _DamageTypeChecker()
    func2 = _DamageTypeChecker(DamageType.NORMAL_ATK,
                               DamageType.CHARGED_ATK,
                               DamageType.PLUNGING_ATK)
    adds = [[('Damage Bonus', DNode('FreedomSworn Passive', '%', info[refine][0]))],
            [('Bonus Scalers', DNode('FreedomSworn Passive1', '%', info[refine][2]))],
            [('Normal Attack Bonus',
              DNode('FreedomSworn Passive2', '%', info[refine][1])),
             ('Charged Attack Bonus',
              DNode('FreedomSworn Passive2', '%', info[refine][1])),
             ('Plunging Attack Bonus',
              DNode('FreedomSworn Passive2', '%', info[refine][1]))]]
    keys = __buff_keys+['view']
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func1, adds[0], '苍古自由之誓:固定被动', False],
              ['PS', BuffType.ATTR, 12*60, 'all',
               'ATK', adds[1], '苍古自由之誓:千年的大乐章', True],
              ['PS', BuffType.DMG, 12*60, 'all',
               func2, adds[2], '苍古自由之誓:千年的大乐章', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Summit_Shaper_PS(buff: Buff, inter) -> List[Buff]:
    return Golden_Majesty(buff, inter, '斫峰之刃', 'Summit_Shaper')


def Primordial_Jade_Cutter_PS(buff: Buff, inter) -> List[Buff]:
    info = [1.2, 1.5, 1.8, 2.1, 2.4]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[
        ('Total ATK', DNode('Primordial_Jade_Cutter Passive', '*')),
        ('Primordial_Jade_Cutter Passive',
         DNode('Primordial_Jade_Cutter Scaler', '%', info[refine])),
        ('Primordial_Jade_Cutter Passive', inter.characters[buff.source].attr.HP)]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ATK', adds[0], '磐岩结绿']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Mistsplitter_Reforged_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 8,  16, 28],
            [15, 10, 20, 35],
            [18, 12, 24, 42],
            [21, 14, 28, 49],
            [24, 16, 32, 56]]
    refine: int = inter.weapons[buff.source].refine-1
    elem = ElementType(inter.characters[buff.source].base.element)
    stack = int(buff.args.get('stack', '1'))
    adds = [
        [(f'Total {k}',
          DNode('Mistsplitter_Reforged Passive1', '%', info[refine][0]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']],
        [(f'Total {elem.name}_DMG',
          DNode(f'Mistsplitter_Reforged Passive2 {stack=}', '%', info[refine][stack]))]
    ]
    config = [['AUTO',  BuffType.ATTR, 0, buff.source,
               'ELEM_DMG',          adds[0], '雾切之回光:固定被动'],
              ['PS',    BuffType.ATTR, 5*60, buff.source,
               f'{elem.name}_DMG',  adds[1], f'雾切之回光:雾切之巴印:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Haran_Geppaku_Futsu_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 20], [15, 25], [18, 30], [21, 35], [24, 40]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [
        [(f'Total {k}',
          DNode('Haran_Geppaku_Futsu Passive1', '%', info[refine][0]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']],
        [('Normal Attack Bonus',
          DNode(f'Haran_Geppaku_Futsu Passive2 {stack=}', '%', info[refine][1]*stack))]
    ]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ELEM_DMG',  adds[0], '波乱月白经津:固定被动'],
              ['PS', BuffType.DMG, 8*60, buff.source,
               func,        adds[1], f'波乱月白经津:波穗:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Rainslasher_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 24, 28, 32, 36]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [[
        ('Damage Bonus', DNode('Rainslasher Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '雨裁']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Whiteblind_PS(buff: Buff, inter) -> List[Buff]:
    info = [6, 7.5, 9, 10.5, 12]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [
        [('Bonus Scalers', DNode('Whiteblind Passive', '%', info[refine]*stack))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[0], f'白影剑:{stack}层', True],
              ['PS', BuffType.ATTR, 6*60, buff.source,
               'DEF', adds[0], f'白影剑:{stack}层', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Blackcliff_Slasher_PS(buff: Buff, inter) -> List[Buff]:
    return Press_The_Advantage(buff, inter, '黑岩斩刀', 'Blackcliff_Slasher')


def Serpent_Spine_PS(buff: Buff, inter) -> List[Buff]:
    info = [6, 7, 8, 9, 10]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker()
    adds = [
        [('Damage Bonus', DNode('Serpent_Spine Passive', '%', info[refine]*stack))]]
    config = [['PS', BuffType.DMG, 4*60, buff.source,
               func, adds[0], f'螭骨剑:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Lithic_Blade_PS(buff: Buff, inter) -> List[Buff]:
    info = [[7, 3], [8, 4], [9, 5], [10, 6], [11, 7]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = sum([c.base.region == 2 for c in inter.characters.items()])
    adds = [[('Bonus Scalers', DNode('Lithic_Blade Passive', '%', info[refine][0]*stack))],
            [('Total CRIT_RATE', DNode('Lithic_Blade Passive', '%', info[refine][1]*stack))]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ATK', adds[0], '千岩古剑'],
              ['AUTO', BuffType.ATTR, 0, buff.source,
               'CRIT_RATE', adds[1], '千岩古剑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Katsuragikiri_Nagamasa_PS(buff: Buff, inter) -> List[Buff]:
    info = [6, 7.5, 9, 10.5, 12]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [[
        ('Elemental Skill Bonus', DNode('Katsuragikiri_Nagamasa Passive', '%', info[refine]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '桂木斩长正']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Akuoumaru_PS(buff: Buff, inter) -> List[Buff]:
    return Watatsumi_Wavewalker(buff, inter, '恶王丸', 'Akuoumaru')


def Forest_Regalia_PS(buff: Buff, inter) -> List[Buff]:
    info = [60, 75, 90, 105, 120]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [('Total EM', DNode('Forest_Regalia Passive', '', info[refine]))]]
    config = [['PS', BuffType.ATTR, 12*60, inter.stage,
               'EM', adds[0], '森林王器:森林的瑞佑']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Skyward_Pride_PS(buff: Buff, inter) -> List[Buff]:
    info = [8, 10, 12, 14, 16]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [[('Damage Bonus', DNode('Skyward_Pride Passive', '%', info[refine]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '天空之傲']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Wolfs_Gravestone_PS(buff: Buff, inter) -> List[Buff]:
    info = [40, 50, 60, 70, 80]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[('Bonus Scalers', DNode('Wolfs_Gravestone Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 12*60, 'all',
               'ATK', adds[0], '狼的末路']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Song_of_Broken_Pines_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [('Bonus Scalers', DNode('Song_of_Broken_Pines Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 12*60, 'all',
               'ATK', adds[0], '松籁响起之时:千年的大乐章']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def The_Unforged_PS(buff: Buff, inter) -> List[Buff]:
    return Golden_Majesty(buff, inter, '无工之剑', 'The_Unforged')


def Redhorn_Stonethresher_PS(buff: Buff, inter) -> List[Buff]:
    info = [40, 50, 60, 70, 80]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK)
    adds = [[
        ('Basic Multiplier', DNode('Redhorn_Stonethresher Passive', '*')),
        ('Redhorn_Stonethresher Passive',
         DNode('Redhorn_Stonethresher Scaler', '%', info[refine])),
        ('Redhorn_Stonethresher Passive', inter.characters[buff.source].attr.DEF)]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '赤角石溃杵']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def White_Tassel_PS(buff: Buff, inter) -> List[Buff]:
    info = [24, 30, 36, 42, 48]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [[
        ('Normal Attack Bonus', DNode('White_Tassel Passive', '%', info[refine]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '白缨枪']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Dragons_Bane_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 24, 28, 32, 36]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [[
        ('Damage Bonus', DNode('Dragons_Bane Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '匣里灭辰']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Crescent_Pike_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK)
    adds = [[('Ability Scaler', DNode('Crescent_Pike Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 0, buff.source,
               func, adds[0], '流月针']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Blackcliff_Pole_PS(buff: Buff, inter) -> List[Buff]:
    return Press_The_Advantage(buff, inter, '黑岩刺枪', 'Blackcliff_Pole')


def Deathmatch_PS(buff: Buff, inter) -> List[Buff]:
    info = [[16, 24], [20, 30], [24, 36], [28, 42], [32, 48]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = buff.args.get('stack', '1')
    buff.name += stack
    adds = [
        [('Bonus Scalers', DNode('Deathmatch Passive1', '%', info[refine][0]))],
        [('Bonus Scalers', DNode('Deathmatch Passive2', '%', info[refine][1]))]]
    config = [['PS1', BuffType.ATTR, 5*60, buff.source,
               'ATK', adds[0], '决斗之枪:多于两人'],
              ['PS1', BuffType.ATTR, 5*60, buff.source,
               'DEF', adds[0], '决斗之枪:多于两人'],
              ['PS2', BuffType.ATTR, 5*60, buff.source,
               'ATK', adds[1], '决斗之枪:少于两人']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Lithic_Spear_PS(buff: Buff, inter) -> List[Buff]:
    info = [[7, 3], [8, 4], [9, 5], [10, 6], [11, 7]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = sum([c.base.region == 2 for c in inter.characters.items()])
    adds = [[('Bonus Scalers', DNode('Lithic_Spear Passive', '%', info[refine][0]*stack))],
            [('Total CRIT_RATE', DNode('Lithic_Spear Passive', '%', info[refine][1]*stack))]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ATK', adds[0], '千岩长枪'],
              ['AUTO', BuffType.ATTR, 0, buff.source,
               'CRIT_RATE', adds[1], '千岩长枪']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kitain_Cross_Spear_PS(buff: Buff, inter) -> List[Buff]:
    info = [6, 7.5, 9, 10.5, 12]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [[
        ('Elemental Skill Bonus', DNode('Kitain_Cross_Spear Passive', '%', info[refine]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '喜多院十文字']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def The_Catch_PS(buff: Buff, inter) -> List[Buff]:
    info = [[16, 6], [20, 7.5], [24, 9], [28, 10.5], [32, 12]]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.ELEM_BURST)
    adds = [[('Elemental Burst Bonus',
              DNode('The_Catch Passive', '%', info[refine][0]))],
            [('Critical Rate',
              DNode('The_Catch Passive', '%', info[refine][1]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '渔获'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[1], '渔获']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Wavebreakers_Fin_PS(buff: Buff, inter) -> List[Buff]:
    return Watatsumi_Wavewalker(buff, inter, '断浪长鳍', 'Wavebreakers_Fin')


def Moonpiercer_PS(buff: Buff, inter) -> List[Buff]:
    info = [16, 20, 24, 28, 32]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[
        ('Bonus Scalers', DNode('Moonpiercer Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 12*60, buff.source,
               'ATK', adds[0], '贯月矢:幽林月影']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Staff_of_Homa_PS(buff: Buff, inter) -> List[Buff]:
    info = [[0.8, 1], [1, 1.2], [1.2, 1.4], [1.4, 1.6], [1.6, 1.8]]
    refine: int = inter.weapons[buff.source].refine-1
    name = 'Staff_of_Homa'
    adds = [
        [('Total ATK', DNode(f'{name} Passive', '*')),
         (f'{name} Passive', DNode(f'{name} Scalers', '+')),
         (f'{name} Scalers',
          DNode(f'{name} Passive1 Scaler', '%', info[refine][0])),
         (f'{name} Passive', inter.characters[buff.source].attr.HP)],
        [(f'{name} Scalers',
          DNode(f'{name} Passive2 Scaler', '%', info[refine][1]))]]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ATK', adds[0], '护摩之杖:固定被动'],
              ['PS', BuffType.ATTR, 5*60, buff.source,
               'ATK', adds[1], '护摩之杖:无羁的朱赤之蝶']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Vortex_Vanquisher_PS(buff: Buff, inter) -> List[Buff]:
    return Golden_Majesty(buff, inter, '贯虹之槊', 'Vortex_Vanquisher')


def Primordial_Jade_WingedSpear_PS(buff: Buff, inter) -> List[Buff]:
    info = [[3.2, 12], [3.9, 1.5], [4.6, 18], [5.3, 21], [6, 24]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker()
    adds = [[('Bonus Scalers',
              DNode('Primordial_Jade_WingedSpear Passive1', '%', info[refine][0]*stack))],
            [('Damage Bonus',
              DNode('Primordial_Jade_WingedSpear Passive2', '%', info[refine][1]))]]
    config = [['PS', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[0], f'和璞鸢:昭理的鸢之枪:{stack}层']]
    if stack == 7:
        config.append(['PS', BuffType.DMG, 6*60, buff.source,
                       func, adds[1], '和璞鸢:昭理的鸢之枪:满层'])
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Calamity_Queller_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 3.2], [15, 4], [18, 4.8], [21, 5.6], [24, 6.4]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [
        [(f'Total {k}',
          DNode('Calamity_Queller Passive1', '%', info[refine][0]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']],
        [('Bonus Scalers', DNode('Calamity_Queller Passive2', '%', info[refine][1]*stack))]
    ]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ELEM_DMG',  adds[0], '息灾:固定被动'],
              ['PS', BuffType.ATTR, 1*60, buff.source,
               'ATK',       adds[1], f'息灾:灭却之戒法:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Engulfing_Lightning_PS(buff: Buff, inter) -> List[Buff]:
    info = [[28, 80, 30],
            [35, 90, 35],
            [42, 100, 40],
            [49, 110, 45],
            [56, 120, 50]]
    refine: int = inter.weapons[buff.source].refine-1
    name = 'Engulfing_Lightning'
    adds = [
        [('Bonus Scalers', DNode(f'{name} Passive1', 'THRESH')),
         (f'{name} Passive1',
          DNode(f'{name} Passive1 Threshold', '%', info[refine][1])),
         (f'{name} Passive1', DNode(f'{name} Bonus', '*')),
         (f'{name} Bonus', DNode(f'{name} Scaler', '%', info[refine][0])),
         (f'{name} Bonus', DNode(f'{name} Stat', '+')),
         (f'{name} Stat', DNode(f'{name} Bias', '', -1)),
         (f'{name} Stat', inter.characters[buff.source].attr.ER)],
        [('Total ER', DNode(f'{name} Passive2', '%', info[refine][2]))]
    ]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ATK',  adds[0], '薙草之稻光:固定被动'],
              ['PS', BuffType.ATTR, 12*60, buff.source,
               'ER',   adds[1], '薙草之稻光:常世灶食']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Thrilling_Tales_of_Dragon_Slayers_PS(buff: Buff, inter) -> List[Buff]:
    info = [24, 30, 36, 42, 48]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [('Bonus Scalers', DNode('Thrilling_Tales_of_Dragon_Slayers Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 10*60, inter.stage,
               'ATK', adds[0], '讨龙英杰谭']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def The_Widsith_PS(buff: Buff, inter) -> List[Buff]:
    info = [[60,  48, 240],
            [75,  60, 300],
            [90,  72, 360],
            [105, 84, 420],
            [120, 96, 480]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = buff.args.get('stack', '1')
    buff.name += stack
    adds = [[('Bonus Scalers', DNode('The_Widsith Passive1', '%', info[refine][0]))],
            [(f'Total {k}',
              DNode('The_Widsith Passive2', '%', info[refine][1]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']],
            [('Total EM', DNode('The_Widsith Passive3', '', info[refine][2]))]]
    config = [['PS1', BuffType.ATTR, 10*60, buff.source,
               'ATK', adds[0], '流浪乐章:攻击力'],
              ['PS2', BuffType.ATTR, 10*60, buff.source,
               'ELEM_DMG', adds[1], '流浪乐章:全元素伤害'],
              ['PS3', BuffType.ATTR, 10*60, buff.source,
               'EM', adds[2], '流浪乐章:元素精通']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Solar_Pearl_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    stack = buff.args.get('stack', '1')
    buff.name += stack
    func1 = _DamageTypeChecker(DamageType.ELEM_SKILL,
                               DamageType.ELEM_BURST)
    func2 = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [[('Elemental Skill Bonus', DNode('Solar_Pearl Passive1', '%', info[refine])),
             ('Elemental Burst Bonus', DNode('Solar_Pearl Passive1', '%', info[refine]))],
            [('Normal Attack Bonus', DNode('Solar_Pearl Passive2', '%', info[refine]))]]
    config = [['PS1', BuffType.DMG, 6*60, buff.source,
               func1, adds[0], '匣里日月:EQ'],
              ['PS2', BuffType.DMG, 6*60, buff.source,
               func2, adds[1], '匣里日月:A']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Mappa_Mare_PS(buff: Buff, inter) -> List[Buff]:
    info = [8, 10, 12, 14, 16]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [[(f'Total {k}',
              DNode('Mappa_Mare Passive', '%', info[refine]*stack))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']]]
    config = [['PS', BuffType.ATTR, 10*60, buff.source,
               'ELEM_DMG', adds[0], f'万国诸海图谱:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Blackcliff_Agate_PS(buff: Buff, inter) -> List[Buff]:
    return Press_The_Advantage(buff, inter, '黑岩绯玉', 'Blackcliff_Agate')


def Wine_and_Song_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[('Bonus Scalers', DNode('Wine_and_Song Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 5*60, buff.source,
               'ATK', adds[0], '暗巷的酒与诗']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Dodoco_Tales_PS(buff: Buff, inter) -> List[Buff]:
    info = [[16, 8], [20, 10], [24, 12], [28, 14], [32, 16]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = buff.args.get('stack', '1')
    buff.name += stack
    func = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [[('Charged Attack Bonus', DNode('Dodoco_Tales Passive1', '%', info[refine][0]))],
            [('Bonus Scalers', DNode('Dodoco_Tales Passive2', '%', info[refine][1]))]]
    config = [['PS1', BuffType.DMG, 6*60, buff.source,
               func, adds[0], '嘟嘟可故事集:重击'],
              ['PS2', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[1], '嘟嘟可故事集:攻击力']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Hakushin_Ring_PS(buff: Buff, inter) -> List[Buff]:
    info = [10, 12.5, 15, 17.5, 20]
    refine: int = inter.weapons[buff.source].refine-1
    elem = buff.args.get('elem', ElementType.PHYSICAL)
    adds = [[(f'Total {elem.name}_DMG',
              DNode('Hakushin_Ring Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 6*60, 'all',
               f'{elem.name}_DMG', adds[0], f'白辰之环:{c_trans[elem.name]}']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Fruit_of_Fulfillment_PS(buff: Buff, inter) -> List[Buff]:
    info = [24, 27, 30, 33, 36]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [[('Total EM', DNode('Fruit_of_Fulfillment Passive', '', info[refine]*stack))],
            [('Bonus Scalers', DNode('Fruit_of_Fulfillment Passive', '%', -5*stack))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 6*60, buff.source,
               'EM', adds[0], f'盈满之实:{stack}层', True],
              ['PS', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[1], f'盈满之实:{stack}层', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Skyward_Atlas_PS(buff: Buff, inter) -> List[Buff]:
    info = [12, 15, 18, 21, 24]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [(f'Total {k}',
          DNode('Skyward_Atlas Passive', '%', info[refine]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']]
    ]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ELEM_DMG', adds[0], '天空之卷']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Lost_Prayer_to_the_Sacred_Winds_PS(buff: Buff, inter) -> List[Buff]:
    info = [8, 10, 12, 14, 16]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [
        [(f'Total {k}',
          DNode('Lost_Prayer_to_the_Sacred_Winds Passive', '%', info[refine]*stack))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']]
    ]
    config = [['PS', BuffType.ATTR, 4*60, buff.source,
               'ELEM_DMG', adds[0], f'四风原典:无边际的眷顾:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Memory_of_Dust_PS(buff: Buff, inter) -> List[Buff]:
    return Golden_Majesty(buff, inter, '尘世之锁', 'Memory_of_Dust')


def Everlasting_Moonglow_PS(buff: Buff, inter) -> List[Buff]:
    info = [1, 1.5, 2, 2.5, 3]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [[
        ('Basic Multiplier', DNode('Everlasting_Moonglow Passive', '*')),
        ('Everlasting_Moonglow Passive',
         DNode('Everlasting_Moonglow Passive Scaler', '%', info[refine])),
        ('Everlasting_Moonglow Passive', inter.characters[buff.source].attr.HP)]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '不灭月华']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Kaguras_Verity_PS(buff: Buff, inter) -> List[Buff]:
    info = [12, 15, 18, 21, 24]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker(DamageType.ELEM_SKILL)
    adds = [
        [('Elemental Skill Bonus',
          DNode('Kaguras_Verity Passive', '%', info[refine]*stack))],
        [(f'Total {k}',
          DNode('Kaguras_Verity Passive', '%', info[refine]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']]
    ]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.DMG, 16*60, buff.source,
               func, adds[0], f'神乐之真意:{stack}层', True]]
    if stack == 3:
        config.append(['PS', BuffType.ATTR, 16*60, buff.source,
                       'ELEM_DMG', adds[1], '神乐之真意:满层', False])
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Slingshot_PS(buff: Buff, inter) -> List[Buff]:
    info = [36, 42, 48, 54, 60]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK)
    adds = [[('Normal Attack Bonus', DNode('Slingshot Passive', '%', info[refine])),
             ('Charged Attack Bonus', DNode('Slingshot Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 60, buff.source,
               func, adds[0], '弹弓']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings, view=False)


def The_Stringless_PS(buff: Buff, inter) -> List[Buff]:
    info = [24, 30, 36, 42, 48]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker(DamageType.ELEM_SKILL,
                              DamageType.ELEM_BURST)
    adds = [[('Elemental Skill Bonus', DNode('The_Stringless Passive', '%', info[refine])),
             ('Elemental Burst Bonus', DNode('The_Stringless Passive', '%', info[refine]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '绝弦']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Rust_PS(buff: Buff, inter) -> List[Buff]:
    info = [40, 50, 60, 70, 80]
    refine: int = inter.weapons[buff.source].refine-1
    func1 = _DamageTypeChecker(DamageType.NORMAL_ATK)
    func2 = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [[('Normal Attack Bonus', DNode('Rust Passive', '%', info[refine]))],
            [('Charged Attack Bonus', DNode('Rust Passive', '%', -10))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func1, adds[0], '弓藏'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func2, adds[1], '弓藏']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Prototype_Crescent_PS(buff: Buff, inter) -> List[Buff]:
    info = [36, 45, 54, 63, 72]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [('Bonus Scalers', DNode('Prototype_Crescent Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 10*60, buff.source,
               'ATK', adds[0], '试作澹月']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Compound_Bow_PS(buff: Buff, inter) -> List[Buff]:
    info = [4, 5, 6, 7, 8]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    adds = [
        [('Bonus Scalers', DNode('Compound_Bow Passive', '%', info[refine]*stack))]]
    config = [['PS', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[0], f'钢轮弓:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Blackcliff_Warbow_PS(buff: Buff, inter) -> List[Buff]:
    return Press_The_Advantage(buff, inter, '黑岩战弓', 'Blackcliff_Warbow')


def Alley_Hunter_PS(buff: Buff, inter) -> List[Buff]:
    info = [2, 2.5, 3, 3.5, 4]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker()
    adds = [
        [('Damage Bonus', DNode('Alley_Hunter Passive', '%', info[refine]*stack))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], f'暗巷猎手:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Fading_Twilight_PS(buff: Buff, inter) -> List[Buff]:
    info = [[6,    10,   14],
            [7.5,  12.5, 17.5],
            [9,    15,   21],
            [10.5, 17.5, 24.5],
            [12,   20,   28]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = buff.args.get('stack', '1')
    buff.name += stack
    func = _DamageTypeChecker()
    adds = [[('Damage Bonus', DNode('Fading_Twilight Passive1', '%', info[refine][0]))],
            [('Damage Bonus', DNode('Fading_Twilight Passive2', '%', info[refine][1]))],
            [('Damage Bonus', DNode('Fading_Twilight Passive3', '%', info[refine][2]))]]
    config = [['PS1', BuffType.DMG, 7*60, buff.source,
               func, adds[0], '落霞:夕暮'],
              ['PS2', BuffType.DMG, 7*60, buff.source,
               func, adds[1], '落霞:流霞'],
              ['PS3', BuffType.DMG, 7*60, buff.source,
               func, adds[2], '落霞:朝晖']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Mitternachts_Waltz_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    stack = buff.args.get('stack', '1')
    buff.name += stack
    func1 = _DamageTypeChecker(DamageType.ELEM_SKILL)
    func2 = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [[('Elemental Skill Bonus', DNode('Mitternachts_Waltz Passive', '%', info[refine]))],
            [('Normal Attack Bonus', DNode('Mitternachts_Waltz Passive', '%', info[refine]))]]
    config = [['PS1', BuffType.DMG, 5*60, buff.source,
               func1, adds[0], '幽夜华尔兹:元素战技'],
              ['PS2', BuffType.DMG, 5*60, buff.source,
               func2, adds[1], '幽夜华尔兹:普通攻击']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Windblume_Ode_PS(buff: Buff, inter) -> List[Buff]:
    info = [16, 20, 24, 28, 32]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[('Bonus Scalers', DNode('Windblume_Ode Passive', '%', info[refine]))]]
    config = [['PS', BuffType.ATTR, 6*60, buff.source,
               'ATK', adds[0], '风花之颂']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Hamayumi_PS(buff: Buff, inter) -> List[Buff]:
    info = [[16, 12], [20, 15], [24, 18], [28, 21], [32, 24]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func1 = _DamageTypeChecker(DamageType.NORMAL_ATK)
    func2 = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [[('Normal Attack Bonus', DNode('Hamayumi Passive', '%', info[refine][0]*stack))],
            [('Charged Attack Bonus', DNode('Hamayumi Passive', '%', info[refine][1]*stack))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func1, adds[0], f'破魔之弓:{stack}层', True],
              ['PS', BuffType.DMG, 5*60, buff.source,
               func2, adds[1], f'破魔之弓:{stack}层', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Mouuns_Moon_PS(buff: Buff, inter) -> List[Buff]:
    return Watatsumi_Wavewalker(buff, inter, '曚云之月', 'Mouuns_Moon')


def Kings_Squire_PS(buff: Buff, inter) -> List[Buff]:
    info = [60, 80, 100, 120, 140]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [[
        ('Total EM', DNode('Kings_Squire Passive', '', info[refine]))]]
    config = [['PS', BuffType.ATTR, 12*60, buff.source,
               'EM', adds[0], '王下近侍:迷宫之王的教导']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Amos_Bow_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 8], [15, 10], [18, 12], [21, 14], [24, 16]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func1 = _DamageTypeChecker(DamageType.NORMAL_ATK,
                               DamageType.CHARGED_ATK)
    func2 = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [[('Normal Attack Bonus', DNode('Amos_Bow Passive1', '%', info[refine][0])),
             ('Charged Attack Bonus', DNode('Amos_Bow Passive1', '%', info[refine][0]))],
            [('Damage Bonus', DNode('Amos_Bow Passive2', '%', info[refine][1]*stack))]]
    if not buff.args.get('seq', False):
        config = [['AUTO', BuffType.DMG, 0, buff.source,
                   func1, adds[0], '阿莫斯之弓:固定被动'],
                  ['PS', BuffType.DMG, 30, buff.source,
                   func2, adds[1], f'阿莫斯之弓:矢志不忘:{stack}层']]
        mappings = [dict(zip(__buff_keys, c)) for c in config]
        return _auto_generate_buff(buff, mappings, view=False)
    else:
        buffs = []
        proto = deepcopy(buff)
        for i in range(5):
            dur = 6 if i != 4 else 30
            add = [('Damage Bonus',
                    DNode('Amos_Bow Passive2', '%', info[refine][1]*(i+1)))]
            mappings = [dict(
                zip(__buff_keys, ['PS', BuffType.DMG, dur, buff.source,
                                  func2, add, f'阿莫斯之弓:矢志不忘:{i+1}层']))]
            proto.begin = buff.begin+6*(i+1)
            buffs.extend(_auto_generate_buff(proto, mappings, view=False))
        return buffs


def Elegy_for_the_End_PS(buff: Buff, inter) -> List[Buff]:
    info = [[20, 100], [25, 125], [30, 150], [35, 175], [40, 200]]
    refine: int = inter.weapons[buff.source].refine-1
    adds = [
        [('Bonus Scalers', DNode('Elegy_for_the_End Passive1', '%', info[refine][0]))],
        [('Total EM', DNode('Elegy_for_the_End Passive2', '', info[refine][1]))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 12*60, 'all',
               'ATK', adds[0], '终末嗟叹之诗:千年的大乐章', True],
              ['PS', BuffType.ATTR, 12*60, 'all',
               'EM',  adds[1], '终末嗟叹之诗:千年的大乐章', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Polar_Star_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 10,   20, 30,   48],
            [15, 12.5, 25, 37.5, 60],
            [18, 15,   30, 45,   72],
            [21, 17.5, 35, 52.5, 84],
            [24, 20,   40, 60,   96]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker(DamageType.ELEM_SKILL,
                              DamageType.ELEM_BURST)
    adds = [
        [('Damage Bonus', DNode('Polar_Star Passive1', '%', info[refine][0]))],
        [('Bonus Scalers', DNode('Polar_Star Passive2', '%', info[refine][stack]))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '冬极白星:固定被动'],
              ['PS', BuffType.ATTR, 12*60, buff.source,
               'ATK',  adds[1], f'冬极白星:极昼的先兆者:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Aqua_Simulacra_PS(buff: Buff, inter) -> List[Buff]:
    info = [20, 25, 30, 35, 40]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageTypeChecker()
    adds = [
        [('Damage Bonus', DNode('Aqua_Simulacra Passive', '%', info[refine]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '若水']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Thundering_Pulse_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 24, 40],
            [15, 30, 50],
            [18, 36, 60],
            [21, 42, 70],
            [24, 48, 80]]
    refine: int = inter.weapons[buff.source].refine-1
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [
        [('Normal Attack Bonus', DNode('Thundering_Pulse Passive', '%', info[refine][stack-1]))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], f'飞雷之弦振:飞雷之巴印:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def Hunters_Path_PS(buff: Buff, inter) -> List[Buff]:
    info = [[12, 1.6], [15, 2], [18, 2.4], [21, 2.8], [24, 3.2]]
    refine: int = inter.weapons[buff.source].refine-1
    func = _DamageCounter(12,
                          ElementType.NONE,
                          DamageType.CHARGED_ATK)
    adds = [
        [(f'Total {k}',
          DNode('Hunters_Path Passive1', '%', info[refine][0]))
            for k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                      'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']],
        [('Basic Multiplier', DNode('Hunters_Path Passive2', '*')),
         ('Hunters_Path Passive2',
          DNode('Hunters_Path Scaler', '', info[refine][1])),
         ('Hunters_Path Passive2', inter.characters[buff.source].attr.EM)]
    ]
    config = [['AUTO', BuffType.ATTR, 0, buff.source,
               'ELEM_DMG', adds[0], '猎人之径:固定被动'],
              ['PS', BuffType.DMG, 10*60, buff.source,
               func, adds[1], '猎人之径:无休止的狩猎']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)

# ---artifact---


def GLADIATORS_FINALE_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [[('Normal Attack Bonus', DNode('GLADIATORS_FINALE Piece4', '%', 35))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '角斗士的终幕礼']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def WANDERERS_TROUPE_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [[('Charged Attack Bonus', DNode('WANDERERS_TROUPE Piece4', '%', 35))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '流浪大地的乐团']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def BLOODSTAINED_CHIVALRY_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.CHARGED_ATK)
    adds = [
        [('Charged Attack Bonus', DNode('BLOODSTAINED_CHIVALRY Piece4', '%', 50))]]
    config = [['PS', BuffType.DMG, 10*60, buff.source,
               func, adds[0], '染血的骑士道']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def NOBLESSE_OBLIGE_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.ELEM_BURST)
    adds = [[('Elemental Burst Bonus',  DNode('NOBLESSE_OBLIGE Piece2', '%', 20))],
            [('Bonus Scalers',          DNode('NOBLESSE_OBLIGE Piece4', '%', 20))]]
    config = [['AUTO', BuffType.DMG,  0, buff.source,
               func,  adds[0], '昔日宗室之仪:二件套'],
              ['PS',   BuffType.ATTR, 12*60, 'all',
               'ATK', adds[1], '昔日宗室之仪:四件套']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def VIRIDESCENT_VENERER_PS(buff: Buff, inter) -> List[Buff]:
    elem = buff.args.get('elem', ElementType.NONE)
    if elem != ElementType.NONE:
        buff.name += f'_{elem.name}'
    func1 = _ReactTypeChecker(ReactType.SWIRL)
    func2 = _ResistanceChecker(elem)
    adds = [[('Reaction Bonus',     DNode('VIRIDESCENT_VENERER Piece4', '%', 60))],
            [('Resistance Debuff',  DNode('VIRIDESCENT_VENERER Piece4', '%', -40))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func1,  adds[0], '翠绿之影:扩散增伤'],
              [f'PS_{elem.name}', BuffType.DMG, 10*60, 'all',
               func2,  adds[1], f'翠绿之影:减抗:{c_trans[elem.name]}']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def MAIDEN_BELOVED_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Total HEAL_INCOME', DNode('MAIDEN_BELOVED Piece4', '%', 20))]]
    config = [['PS', BuffType.ATTR, 10*60, 'all',
               'HEAL_INCOME', adds[0], '被怜爱的少女']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def THUNDERSOOTHER_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker()
    adds = [[('Damage Bonus', DNode('THUNDERSOOTHER Piece4', '%', 35))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '平息鸣雷的尊者']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def THUNDERING_FURY_PS(buff: Buff, inter) -> List[Buff]:
    func1 = _ReactTypeChecker(ReactType.SUPERCONDUCT,
                              ReactType.ELECTRO_CHARGED,
                              ReactType.OVERLOADED,
                              ReactType.HYPERBLOOM)
    func2 = _ReactTypeChecker(ReactType.AGGRAVATE)
    adds = [[('Reaction Bonus', DNode('THUNDERING_FURY Piece4', '%', 40))],
            [('Reaction Bonus', DNode('THUNDERING_FURY Piece4', '%', 20))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func1, adds[0], '如雷的盛怒:剧变反应'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func2, adds[1], '如雷的盛怒:激化反应']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def LAVAWALKER_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker()
    adds = [[('Damage Bonus', DNode('LAVAWALKER Piece4', '%', 35))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '渡过烈火的贤人']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def CRIMSON_WITCH_OF_FLAMES_PS(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '1'))
    func1 = _ReactTypeChecker(ReactType.VAPORIZE,
                              ReactType.VAPORIZE_REVERSE,
                              ReactType.MELT,
                              ReactType.MELT_REVERSE)
    func2 = _ReactTypeChecker(ReactType.OVERLOADED,
                              ReactType.BURNING,
                              ReactType.BURGEON)
    adds = [[('Reaction Bonus',  DNode('CRIMSON_WITCH_OF_FLAMES Piece4', '%', 15))],
            [('Reaction Bonus',  DNode('CRIMSON_WITCH_OF_FLAMES Piece4', '%', 40))],
            [('Total PYRO_DMG',  DNode('CRIMSON_WITCH_OF_FLAMES Piece4', '%', 7.5*stack))], ]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func1,       adds[0], '炽烈的炎之魔女:增幅反应'],
              ['AUTO', BuffType.DMG, 0, buff.source,
               func2,       adds[1], '炽烈的炎之魔女:剧变反应'],
              ['PS', BuffType.ATTR, 10*60, buff.source,
               'PYRO_DMG',  adds[2], f'炽烈的炎之魔女:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def ARCHAIC_PETRA_PS(buff: Buff, inter) -> List[Buff]:
    elem = buff.args.get('elem', ElementType.PHYSICAL)
    adds = [[(f'Totol {elem.name}_DMG',
              DNode('ARCHAIC_PETRA Piece4', '%', 35))]]
    config = [['PS', BuffType.ATTR, 10*60, 'all',
               f'{elem.name}_DMG', adds[0], f'悠古的磐岩:增伤:{c_trans[elem.name]}']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def RETRACING_BOLIDE_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK)
    adds = [[('Charged Attack Bonus', DNode('RETRACING_BOLIDE Piece4', '%', 40)),
            ('Normal Attack Bonus',   DNode('RETRACING_BOLIDE Piece4', '%', 40))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], '逆飞的流星']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def BLIZZARD_STRAYER_PS(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '1'))
    func = _DamageTypeChecker()
    adds = [[('Critical Rate', DNode('BLIZZARD_STRAYER Piece4', '%', 20*stack))]]
    config = [['PS', BuffType.DMG, 5*60, buff.source,
               func, adds[0], f'冰风迷途的勇士:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def HEART_OF_DEPTH_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK)
    adds = [[('Charged Attack Bonus', DNode('HEART_OF_DEPTH Piece4', '%', 30)),
            ('Normal Attack Bonus',   DNode('HEART_OF_DEPTH Piece4', '%', 30))]]
    config = [['PS', BuffType.DMG, 15*60, buff.source,
               func, adds[0], '沉沦之心']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def TENACITY_OF_THE_MILLELITH_PS(buff: Buff, inter) -> List[Buff]:
    adds = [[('Bonus Scalers',          DNode('TENACITY_OF_THE_MILLELITH Piece4', '%', 20))],
            [('Total SHIELD_STRENGTH',  DNode('TENACITY_OF_THE_MILLELITH Piece4', '%', 30))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 3*60, 'all',
               'ATK',               adds[0], '千岩牢固', True],
              ['PS', BuffType.ATTR, 3*60, 'all',
               'SHIELD_STRENGTH',   adds[1], '千岩牢固', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def PALE_FLAME_PS(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '1'))
    adds = [[('Bonus Scalers',      DNode('PALE_FLAME Piece4', '%', 9*stack))],
            [('Total PHYSICAL_DMG', DNode('PALE_FLAME Piece4', '%', 25))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 7*60, buff.source,
               'ATK',           adds[0], f'苍白之火:{stack}层', True],
              ['PS', BuffType.ATTR, 7*60, buff.source,
               'PHYSICAL_DMG',  adds[1], f'苍白之火:{stack}层', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def SHIMENAWAS_REMINISCENCE_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.NORMAL_ATK,
                              DamageType.CHARGED_ATK,
                              DamageType.PLUNGING_ATK)
    adds = [[('Charged Attack Bonus', DNode('SHIMENAWAS_REMINISCENCE Piece4', '%', 50)),
            ('Normal Attack Bonus', DNode('SHIMENAWAS_REMINISCENCE Piece4', '%', 50)),
            ('Plunging Attack Bonus', DNode('SHIMENAWAS_REMINISCENCE Piece4', '%', 50))]]
    config = [['PS', BuffType.DMG, 10*60, buff.source,
               func, adds[0], '追忆之注连']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def EMBLEM_OF_SEVERED_FATE_PS(buff: Buff, inter) -> List[Buff]:
    func = _DamageTypeChecker(DamageType.ELEM_BURST)
    adds = [[('Elemental Burst Bonus',
              DNode('EMBLEM_OF_SEVERED_FATE Piece4', '*')),
            ('EMBLEM_OF_SEVERED_FATE Piece4',
             DNode('EMBLEM_OF_SEVERED_FATE Scaler', '%', 25)),
            ('EMBLEM_OF_SEVERED_FATE Piece4',
             DNode('EMBLEM_OF_SEVERED_FATE Stat', 'THRESH')),
            ('EMBLEM_OF_SEVERED_FATE Stat',
             DNode('EMBLEM_OF_SEVERED_FATE Stat Threshold', '', 3)),
            ('EMBLEM_OF_SEVERED_FATE Stat',
             inter.characters[buff.source].attr.ER)]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '绝缘之旗印']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def OCEANHUED_CLAM_PS(buff: Buff, inter) -> List[Buff]:
    return []


def HUSK_OF_OPULENT_DREAMS_PS(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '0'))
    adds = [
        [('Bonus Scalers', DNode('HUSK_OF_OPULENT_DREAMS Piece4', '%', 6*stack))],
        [('Total GEO_DMG', DNode('HUSK_OF_OPULENT_DREAMS Piece4', '%', 6*stack))]]
    keys = __buff_keys+['view']
    config = [['PS', BuffType.ATTR, 5*60, buff.source,
               'DEF',       adds[0], f'华馆梦醒形骸记:{stack}层', True],
              ['PS', BuffType.ATTR, 5*60, buff.source,
               'GEO_DMG',   adds[1], f'华馆梦醒形骸记:{stack}层', False]]
    mappings = [dict(zip(keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def VERMILLION_HEREAFTER_PS(buff: Buff, inter) -> List[Buff]:
    stack = int(buff.args.get('stack', '0'))
    adds = [
        [('Bonus Scalers', DNode('VERMILLION_HEREAFTER Piece4', '%', 8+10*stack))]]
    config = [['PS', BuffType.ATTR, 5*60, buff.source,
               'ATK', adds[0], f'辰砂往生录:{stack}层']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def ECHOES_OF_AN_OFFERING_PS(buff: Buff, inter) -> List[Buff]:
    # TODO algo need to improve
    func = _DamageTypeChecker(DamageType.NORMAL_ATK)
    adds = [[('Ability Scaler', DNode('ECHOES_OF_AN_OFFERING Piece4', '%', 35))]]
    config = [['AUTO', BuffType.DMG, 0, buff.source,
               func, adds[0], '来歆余响']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def DEEPWOOD_MEMORIES_PS(buff: Buff, inter) -> List[Buff]:
    func = _ResistanceChecker(ElementType.DENDRO)
    adds = [[('Resistance Debuff', DNode('DEEPWOOD_MEMORIES Piece4', '%', -30))]]
    config = [['PS', BuffType.DMG, 8*60, 'all',
               func, adds[0], '深林的记忆']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)


def GILDED_DREAMS_PS(buff: Buff, inter) -> List[Buff]:
    my_elem = inter.characters[buff.source].base.element
    elem = [c.base.element for name, c in inter.characters.items()
            if name != buff.source]
    same = elem.count(my_elem)
    diff = len(elem)-same
    adds = [[('Bonus Scalers',  DNode('GILDED_DREAMS Piece4', '%', 14*same))],
            [('Total EM',       DNode('GILDED_DREAMS Piece4', '', 50*diff))]]
    config = [['PS',  BuffType.ATTR, 8*60,  buff.source,
               'ATK', adds[0],       f'饰金之梦:{same}同元素'],
              ['PS',  BuffType.ATTR, 8*60,  buff.source,
               'EM',  adds[1],       f'饰金之梦:{diff}不同元素']]
    if not diff:
        config.pop(-1)
    if not same:
        config.pop(0)
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    return _auto_generate_buff(buff, mappings)

# ---resonance---


def Resonance_All(buff: Buff, inter) -> List[Buff]:
    protos = []
    result = []
    elem = [c.base.element for c in inter.characters.values()]
    if buff.name == 'AUTO':
        for i in range(1, 8):
            if elem.count(i) >= 2:
                proto = deepcopy(buff)
                proto.name += '_'+ElementType(i).name
                protos.append(proto)
    elif buff.name == 'GEO' and elem.count(ElementType.GEO.value) >= 2:
        proto = deepcopy(buff)
        proto.name += buff.args.get('stack', '1')
        protos.append(proto)
    elif buff.name == 'CRYO' and elem.count(ElementType.CRYO.value) >= 2:
        proto = deepcopy(buff)
        protos.append(proto)
    elif buff.name == 'DENDRO' and elem.count(ElementType.DENDRO.value) >= 2:
        proto = deepcopy(buff)
        proto.name += buff.args.get('stack', '1')
        protos.append(proto)

    func1 = _DamageTypeChecker()
    func2 = _ResistanceChecker(ElementType.GEO)
    adds = [[('Total SHIELD_STRENGTH', DNode('GEO Resonance', '%', 15))],
            [('Bonus Scalers',         DNode('HYDRO Resonance', '%', 25))],
            [('Bonus Scalers',         DNode('PYRO Resonance', '%', 25))],
            [('Total EM',              DNode('DENDRO Resonance', '', 50))],
            [('Damage Bonus',          DNode('GEO Resonance1', '%', 15))],
            [('Resistance Debuff',     DNode('GEO Resonance2', '%', -20))],
            [('Critical Rate',         DNode('CRYO Resonance', '%', 15))],
            [('Damage Bonus',          DNode('GEO Resonance1', '%', 15))],
            [('Total EM',              DNode('DENDRO Resonance1', '', 30))],
            [('Total EM',              DNode('DENDRO Resonance2', '', 20))]]
    config = [['AUTO_GEO',    BuffType.ATTR, 0,     'all',
               'SHIELD_STRENGTH',    adds[0], '元素共鸣:坚定之岩'],
              ['AUTO_HYDRO',  BuffType.ATTR, 0,     'all',
                  'HP',              adds[1], '元素共鸣:愈疗之水'],
              ['AUTO_PYRO',   BuffType.ATTR, 0,     'all',
                  'ATK',             adds[2], '元素共鸣:热诚之火'],
              ['AUTO_DENDRO', BuffType.ATTR, 0,     'all',
                  'EM',              adds[3], '元素共鸣:蔓生之草'],
              ['GEO1',        BuffType.DMG,  5*60,  'stage',
                  func1,             adds[4], '元素共鸣:坚定之岩:增伤'],
              ['GEO2',        BuffType.DMG,  15*60, 'all',
                  func2,             adds[5], '元素共鸣:坚定之岩:减抗'],
              ['CRYO',        BuffType.DMG,  5*60,  'all',
                  func1,             adds[6], '元素共鸣:粉碎之冰'],
              ['DENDRO1',     BuffType.ATTR, 6*60,  'all',
                  'EM',              adds[7], '元素共鸣:蔓生之草:初级反应'],
              ['DENDRO2',     BuffType.ATTR, 6*60,  'all',
                  'EM',              adds[8], '元素共鸣:蔓生之草:次级反应']]
    mappings = [dict(zip(__buff_keys, c)) for c in config]
    for b in protos:
        result.extend(_auto_generate_buff(b, mappings))
    return result


# ---dict---


buff_dict: Dict[str, Callable[[Buff, object], List[Buff]]] = \
    {
    # character
    'Ayaka-PS': Ayaka_PS,
    'Ayaka-CX': Ayaka_CX,
    'Diluc-PS': Diluc_PS,
    'Diluc-CX': Diluc_CX,
    'Xiangling-PS': Xiangling_PS,
    'Xiangling-CX': Xiangling_CX,
    'Xingqiu-PS': Xingqiu_PS,
    'Xingqiu-CX': Xingqiu_CX,
    'Jean-CX': Jean_CX,
    'Zhongli-PS': Zhongli_PS,
    'Zhongli-SK': Zhongli_SK,
    'Bennett-SK': Bennett_SK,
    'Hutao-PS': Hutao_PS,
    'Hutao-CX': Hutao_CX,
    'Hutao-SK': Hutao_SK,
    'Kazuha-PS': Kazuha_PS,
    'Kazuha-CX': Kazuha_CX,
    'Shogun-PS': Shogun_PS,
    'Shogun-CX': Shogun_CX,
    'Shogun-SK': Shogun_SK,
    'Kokomi-PS': Kokomi_PS,
    'Kokomi-CX': Kokomi_CX,
    'Kokomi-SK': Kokomi_SK,
    'Yelan-PS': Yelan_PS,
    'Yelan-CX': Yelan_CX,
    'Shenhe-CX': Shenhe_CX,
    'Shenhe-SK': Shenhe_SK,
    # weapon
    'Cool_Steel': Cool_Steel_PS,
    'Harbinger_of_Dawn': Harbinger_of_Dawn_PS,
    'Lions_Roar': Lions_Roar_PS,
    'Prototype_Rancour': Prototype_Rancour_PS,
    'Iron_Sting': Iron_Sting_PS,
    'Blackcliff_Longsword': Blackcliff_Longsword_PS,
    'The_Black_Sword': The_Black_Sword_PS,
    'The_Alley_Flash': The_Alley_Flash_PS,
    'Festering_Desire': Festering_Desire_PS,
    'Cinnabar_Spindle': Cinnabar_Spindle_PS,
    'Kagotsurube_Isshin': Kagotsurube_Isshin_PS,
    'Sapwood_Blade': Sapwood_Blade_PS,
    'FreedomSworn': FreedomSworn_PS,
    'Summit_Shaper': Summit_Shaper_PS,
    'Primordial_Jade_Cutter': Primordial_Jade_Cutter_PS,
    'Mistsplitter_Reforged': Mistsplitter_Reforged_PS,
    'Haran_Geppaku_Futsu': Haran_Geppaku_Futsu_PS,

    'Rainslasher': Rainslasher_PS,
    'Whiteblind': Whiteblind_PS,
    'Blackcliff_Slasher': Blackcliff_Slasher_PS,
    'Serpent_Spine': Serpent_Spine_PS,
    'Lithic_Blade': Lithic_Blade_PS,
    'Katsuragikiri_Nagamasa': Katsuragikiri_Nagamasa_PS,
    'Akuoumaru': Akuoumaru_PS,
    'Forest_Regalia': Forest_Regalia_PS,
    'Skyward_Pride': Skyward_Pride_PS,
    'Wolfs_Gravestone': Wolfs_Gravestone_PS,
    'Song_of_Broken_Pines': Song_of_Broken_Pines_PS,
    'The_Unforged': The_Unforged_PS,
    'Redhorn_Stonethresher': Redhorn_Stonethresher_PS,

    'White_Tassel': White_Tassel_PS,
    'Dragons_Bane': Dragons_Bane_PS,
    'Crescent_Pike': Crescent_Pike_PS,
    'Blackcliff_Pole': Blackcliff_Pole_PS,
    'Deathmatch': Deathmatch_PS,
    'Lithic_Spear': Lithic_Spear_PS,
    'Kitain_Cross_Spear': Kitain_Cross_Spear_PS,
    'The_Catch': The_Catch_PS,
    'Wavebreakers_Fin': Wavebreakers_Fin_PS,
    'Moonpiercer': Moonpiercer_PS,
    'Staff_of_Homa': Staff_of_Homa_PS,
    'Vortex_Vanquisher': Vortex_Vanquisher_PS,
    'Primordial_Jade_WingedSpear': Primordial_Jade_WingedSpear_PS,
    'Calamity_Queller': Calamity_Queller_PS,
    'Engulfing_Lightning': Engulfing_Lightning_PS,

    'Thrilling_Tales_of_Dragon_Slayers': Thrilling_Tales_of_Dragon_Slayers_PS,
    'The_Widsith': The_Widsith_PS,
    'Solar_Pearl': Solar_Pearl_PS,
    'Mappa_Mare': Mappa_Mare_PS,
    'Blackcliff_Agate': Blackcliff_Agate_PS,
    'Wine_and_Song': Wine_and_Song_PS,
    'Dodoco_Tales': Dodoco_Tales_PS,
    'Hakushin_Ring': Hakushin_Ring_PS,
    'Fruit_of_Fulfillment': Fruit_of_Fulfillment_PS,
    'Skyward_Atlas': Skyward_Atlas_PS,
    'Lost_Prayer_to_the_Sacred_Winds': Lost_Prayer_to_the_Sacred_Winds_PS,
    'Memory_of_Dust': Memory_of_Dust_PS,
    'Everlasting_Moonglow': Everlasting_Moonglow_PS,
    'Kaguras_Verity': Kaguras_Verity_PS,

    'Slingshot': Slingshot_PS,
    'The_Stringless': The_Stringless_PS,
    'Rust': Rust_PS,
    'Prototype_Crescent': Prototype_Crescent_PS,
    'Compound_Bow': Compound_Bow_PS,
    'Blackcliff_Warbow': Blackcliff_Warbow_PS,
    'Alley_Hunter': Alley_Hunter_PS,
    'Fading_Twilight': Fading_Twilight_PS,
    'Mitternachts_Waltz': Mitternachts_Waltz_PS,
    'Windblume_Ode': Windblume_Ode_PS,
    'Hamayumi': Hamayumi_PS,
    'Mouuns_Moon': Mouuns_Moon_PS,
    'Kings_Squire': Kings_Squire_PS,
    'Amos_Bow': Amos_Bow_PS,
    'Elegy_for_the_End': Elegy_for_the_End_PS,
    'Polar_Star': Polar_Star_PS,
    'Aqua_Simulacra': Aqua_Simulacra_PS,
    'Thundering_Pulse': Thundering_Pulse_PS,
    'Hunters_Path': Hunters_Path_PS,
    # artifact
    'GLADIATORS_FINALE': GLADIATORS_FINALE_PS,
    'WANDERERS_TROUPE': WANDERERS_TROUPE_PS,
    'BLOODSTAINED_CHIVALRY': BLOODSTAINED_CHIVALRY_PS,
    'NOBLESSE_OBLIGE': NOBLESSE_OBLIGE_PS,
    'VIRIDESCENT_VENERER': VIRIDESCENT_VENERER_PS,
    'MAIDEN_BELOVED': MAIDEN_BELOVED_PS,
    'THUNDERSOOTHER': THUNDERSOOTHER_PS,
    'THUNDERING_FURY': THUNDERING_FURY_PS,
    'LAVAWALKER': LAVAWALKER_PS,
    'CRIMSON_WITCH_OF_FLAMES': CRIMSON_WITCH_OF_FLAMES_PS,
    'ARCHAIC_PETRA': ARCHAIC_PETRA_PS,
    'RETRACING_BOLIDE': RETRACING_BOLIDE_PS,
    'BLIZZARD_STRAYER': BLIZZARD_STRAYER_PS,
    'HEART_OF_DEPTH': HEART_OF_DEPTH_PS,
    'TENACITY_OF_THE_MILLELITH': TENACITY_OF_THE_MILLELITH_PS,
    'PALE_FLAME': PALE_FLAME_PS,
    'SHIMENAWAS_REMINISCENCE': SHIMENAWAS_REMINISCENCE_PS,
    'EMBLEM_OF_SEVERED_FATE': EMBLEM_OF_SEVERED_FATE_PS,
    'OCEANHUED_CLAM': OCEANHUED_CLAM_PS,
    'HUSK_OF_OPULENT_DREAMS': HUSK_OF_OPULENT_DREAMS_PS,
    'VERMILLION_HEREAFTER': VERMILLION_HEREAFTER_PS,
    'ECHOES_OF_AN_OFFERING': ECHOES_OF_AN_OFFERING_PS,
    'DEEPWOOD_MEMORIES': DEEPWOOD_MEMORIES_PS,
    'GILDED_DREAMS': GILDED_DREAMS_PS,
    # resonance
    'RE': Resonance_All,
}
