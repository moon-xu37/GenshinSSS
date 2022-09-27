from typing import Tuple, List, Union
from utils.dtypes import ReactType, ElementType
from utils.buff import Buff
from utils.event import Event


shapley_case_judge = [
    'BLIZZARD_STRAYER', 'VIRIDESCENT_VENERER', 'ARCHAIC_PETRA',
    'Kazuha-PS',
    'Shogun-Q', 'Kazuha-A', 'Kazuha-Q'
]


def shapley_nontrans_constrain(proto: Event, inter) -> Event:
    constraint = {
        ReactType.VAPORIZE: (ElementType.HYDRO, ElementType.PYRO),
        ReactType.VAPORIZE_REVERSE: (ElementType.HYDRO, ElementType.PYRO),
        ReactType.MELT: (ElementType.CRYO, ElementType.PYRO),
        ReactType.MELT_REVERSE: (ElementType.CRYO, ElementType.PYRO),
        ReactType.AGGRAVATE: (ElementType.ELECTRO, ElementType.DENDRO),
        ReactType.SPREAD: (ElementType.ELECTRO, ElementType.DENDRO)
    }
    react: ReactType = proto.args.get('react', ReactType.NONE)
    elem = [c.base.element for c in inter.characters.values()]
    if react in constraint:
        for e in constraint[react]:
            if elem.count(e.value) == 0:
                proto.args['react'] = ReactType.NONE
    return proto


def shapley_case_process(proto: Union[Buff, Event], key: str, inter) -> Union[Buff, Event, None]:
    elem = [c.base.element for c in inter.characters.values()]
    if key == 'BLIZZARD_STRAYER':
        if elem.count(ElementType.CRYO.value) == 0:
            return
        elif elem.count(ElementType.HYDRO.value) == 0:
            proto.args['stack'] = min(int(proto.args.get('stack', '1')), 1)
        return proto
    elif key == 'VIRIDESCENT_VENERER':
        b_elem = proto.args.get('elem', ElementType.NONE)
        if elem.count(b_elem.value) == 0:
            return
        else:
            return proto
    elif key == 'ARCHAIC_PETRA':
        b_elem = proto.args.get('elem', ElementType.NONE)
        if elem.count(b_elem.value) == 0:
            return
        else:
            return proto
    elif key == 'Kazuha-PS':
        b_elem = proto.args.get('elem', ElementType.NONE)
        if elem.count(b_elem.value) == 0:
            return
        else:
            return proto
    elif key == 'Shogun-Q':
        # 2 stack every 3s, let it be additional 12 stack
        stack = int(proto.args.get('stack', '0'))
        energy = [c.base.energy for c in inter.characters.values()
                  if c.base.name != 'Shogun']
        proto.args['stack'] = min(sum(energy)*0.2+12, stack)
        return proto
    elif key == 'Kazuha-A' or key == 'Kazuha-Q':
        if proto.name.endswith('AB'):
            b_elem = proto.args.get('elem', ElementType.NONE)
            if elem.count(b_elem.value) == 0:
                return
            else:
                return proto
    else:
        return proto
