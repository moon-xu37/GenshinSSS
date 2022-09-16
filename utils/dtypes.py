from enum import Enum


class ElementType(Enum):
    '''元素类型'''
    NONE = 0  # 无
    ANEMO = 1  # 风
    GEO = 2  # 岩
    ELECTRO = 3  # 雷
    HYDRO = 4  # 水
    PYRO = 5  # 火
    CRYO = 6  # 冰
    DENDRO = 7  # 草
    PHYSICAL = 8  # 物理


class ReactType(Enum):
    '''元素反应类型'''
    NONE = 0
    # 已知
    SWIRL = 10
    # 扩散 风->元
    CRYSTALLIZE = 20
    # 结晶 岩->元
    ELECTRO_CHARGED = 34
    # 感电 水<->雷
    OVERLOADED = 35
    # 超载 火<->雷
    SUPERCONDUCT = 36
    # 超导 冰<->雷
    SHATTERED = 86
    # 碎冰 无->冻
    FROZEN = 46
    # 冻结 水<->冰
    VAPORIZE = 45
    # 蒸发 水->火
    VAPORIZE_REVERSE = 54
    # 蒸发弱 火->水
    MELT = 56
    # 融化 火->冰
    MELT_REVERSE = 65
    # 融化弱 冰->火
    BURNING = 57
    # 燃烧 火<->草
    BLOOM = 47
    # 绽放 水<->草
    HYPERBLOOM = 473
    # 超绽放 雷
    BURGEON = 475
    # 烈绽放 火
    CATALYZE = 37
    # 激化 雷<->草
    QUICKEN = 7
    # 原激化
    AGGRAVATE = 373
    # 超激化 雷
    SPREAD = 377
    # 蔓激化 草


class WeaponType(Enum):
    '''武器类型'''
    SWORD = 1  # 单手剑
    CLAYMORE = 2  # 双手剑
    POLEARM = 3  # 长柄武器
    CATALYST = 4  # 法器
    BOW = 5  # 弓


class NationType(Enum):
    '''人物所属地区类型'''
    MONDSTADT = 1  # 蒙德
    LIYUE = 2  # 璃月
    INAZUMA = 3  # 稻妻
    SUMERU = 4  # 须弥
    FONTAINE = 5  # 枫丹
    NATLAN = 6  # 纳塔
    SNEZHNAYA = 7  # 至冬
    KHAENRIAH = 8  # 坎瑞亚
    OTHER = 9  # 异世界/其他


class ArtpositionType(Enum):
    '''圣遗物位置类型'''
    FLOWER = 1  # 生之花
    PLUME = 2  # 死之羽
    SANDS = 3  # 时之沙
    GOBLET = 4  # 空之杯
    CIRCLET = 5  # 理之冠


class StatType(Enum):
    ATK_PER = 1
    ATK_CONST = 2
    DEF_PER = 3
    DEF_CONST = 4
    HP_PER = 5
    HP_CONST = 6
    EM = 7
    ER = 8
    CRIT_RATE = 9
    CRIT_DMG = 10
    HEAL_BONUS = 11
    ANEMO_DMG = 12
    GEO_DMG = 13
    ELECTRO_DMG = 14
    HYDRO_DMG = 15
    PYRO_DMG = 16
    CRYO_DMG = 17
    DENDRO_DMG = 18
    PHYSICAL_DMG = 19


class SetType(Enum):
    '''圣遗物套装类型'''
    NONE = 0
    # ---5star---
    GLADIATORS_FINALE = 1           # 角斗士的终幕礼
    WANDERERS_TROUPE = 2            # 流浪大地的乐团
    BLOODSTAINED_CHIVALRY = 3       # 染血的骑士道
    NOBLESSE_OBLIGE = 4             # 昔日宗室之仪
    VIRIDESCENT_VENERER = 5         # 翠绿之影
    MAIDEN_BELOVED = 6              # 被怜爱的少女
    THUNDERSOOTHER = 7              # 平息鸣雷的尊者
    THUNDERING_FURY = 8             # 如雷的盛怒
    LAVAWALKER = 9                  # 渡过烈火的贤人
    CRIMSON_WITCH_OF_FLAMES = 10    # 炽烈的炎之魔女
    ARCHAIC_PETRA = 11              # 悠古的磐岩
    RETRACING_BOLIDE = 12           # 逆飞的流星
    BLIZZARD_STRAYER = 13           # 冰风迷途的勇士
    HEART_OF_DEPTH = 14             # 沉沦之心
    TENACITY_OF_THE_MILLELITH = 15  # 千岩牢固
    PALE_FLAME = 16                 # 苍白之火
    SHIMENAWAS_REMINISCENCE = 17    # 追忆之注连
    EMBLEM_OF_SEVERED_FATE = 18     # 绝缘之旗印
    OCEANHUED_CLAM = 19             # 海染砗磲
    HUSK_OF_OPULENT_DREAMS = 20     # 华馆梦醒形骸记
    VERMILLION_HEREAFTER = 21       # 辰砂往生录
    ECHOES_OF_AN_OFFERING = 22      # 来歆余响
    DEEPWOOD_MEMORIES = 23          # 深林的记忆
    GILDED_DREAMS = 24              # 饰金之梦
    # ---4star---


class EventType(Enum):
    '''事件类型'''
    NONE = 0
    SWITCH = 1
    CREATION = 2
    DAMAGE = 3
    ELEMENT = 4
    HEALTH = 5
    SHIELD = 6
    ENERGY = 7


class DamageType(Enum):
    '''造成的伤害类型'''
    NONE = 0
    NORMAL_ATK = 1
    CHARGED_ATK = 2
    PLUNGING_ATK = 3
    ELEM_SKILL = 4
    ELEM_BURST = 5
    TRANS = 6


class BuffType(Enum):
    '''buff的类型'''
    NONE = 0
    ATTR = 1
    DMG = 2
    ELEMENT = 3
    HEALTH = 4
    SHIELD = 5


class ModeType(Enum):
    EXPECT = 0
    CRIT = 1
    NOTCRIT = 2
    MISS = 3
    SIM = 4
