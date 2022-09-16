from typing import Dict, Callable, List
from utils.event import Event


def _auto_generate_creation(proto: Event, dur: List[int], view: List[bool], desc: List[str], **args):
    i = 0
    if 'index' in args:
        i = args['index']
    if not proto.endtime:
        proto.endtime = proto.time + dur[i]
    proto.visible = proto.args.get('view', view[i])
    proto.desc = desc[i]
    return proto


def Ayaka_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [5*60], [False], ['神里绫华:创造物:霜见雪关扉'])


def Jean_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [10*60], [True], ['琴:创造物:蒲公英领域'])


def Xiangling_Creation(event: Event, inter) -> Event:
    if event.family == 'E':
        return _auto_generate_creation(event, [7*60], [True], ['香菱:创造物:锅巴'])
    elif event.family == 'Q':
        cx = event.args.get(
            'cx', inter.characters[event.source].attr.cx_lv >= 4)
        i = 1 if cx else 0
        return _auto_generate_creation(event, [10*60, 14*60], [True, True],
                                       ['香菱:创造物:旋火轮非四命', '香菱:创造物:旋火轮'], index=i)


def Xingqiu_Creation(event: Event, inter) -> Event:
    cx = event.args.get(
        'cx', inter.characters[event.source].attr.cx_lv >= 2)
    i = 1 if cx else 0
    return _auto_generate_creation(event, [15*60, 18*60], [True, True],
                                   ['行秋:创造物:雨帘剑非二命', '行秋:创造物:雨帘剑'], index=i)


def Klee_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [10*60], [True], ['可莉:创造物:轰轰火花'])


def Zhongli_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [30*60], [True], ['钟离:创造物:岩脊'])


def Bennett_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [12*60], [True], ['班尼特:创造物:鼓舞领域'])


def Kazuha_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [9*60], [True], ['枫原万叶:创造物:流风秋野'])


def Kokomi_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [12*60], [True], ['心海:创造物:化海月'])


def Sara_Creation(event: Event, inter) -> Event:
    if event.family == 'E':
        return _auto_generate_creation(event, [91], [True], ['九条裟罗:创造物:天狗咒雷'])
    elif event.family == 'Q':
        return _auto_generate_creation(event, [4*60], [False], ['九条裟罗:创造物:金刚坏'])


def Shenhe_Creation(event: Event, inter) -> Event:
    cx = event.args.get(
        'cx', inter.characters[event.source].attr.cx_lv >= 2)
    i = 1 if cx else 0
    return _auto_generate_creation(event, [12*60, 18*60], [True, True],
                                   ['申鹤:创造物:领域', '申鹤:创造物:领域二命'], index=i)


def Skyward_Atlas_Creation(event: Event, inter) -> Event:
    return _auto_generate_creation(event, [15*60], [False], ['天空之卷:创造物:高天流云'])


create_dict: Dict[str, Callable[[Event, object], Event]] = \
    {
        'Ayaka->Q': Ayaka_Creation,
        'Jean->Q': Jean_Creation,
        'Xiangling->E': Xiangling_Creation,
        'Xiangling->Q': Xiangling_Creation,
        'Xingqiu->Q': Xingqiu_Creation,
        'Klee->Q': Klee_Creation,
        'Zhongli->E': Zhongli_Creation,
        'Bennett->Q': Bennett_Creation,
        'Kazuha->Q': Kazuha_Creation,
        'Kokomi->E': Kokomi_Creation,
        'Sara->E': Sara_Creation,
        'Sara->Q': Sara_Creation,
        'Shenhe->Q': Shenhe_Creation,

        'Skyward_Atlas': Skyward_Atlas_Creation,
}
