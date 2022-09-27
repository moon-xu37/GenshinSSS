from typing import List, Dict
from ctrl.interpret import Interpreter
from utils.buff import Buff
from utils.event import Event
from data.namedict import name_dict
from func.buffs import buff_dict
from func.skills import skill_dict
from func.shapley_case import *


class ShapleyInterpreter(Interpreter):
    def __init__(self, total_char: List[str], comb: tuple):
        super().__init__()
        self.output = False
        self.forbid_char: List[str] = [c for i, c in enumerate(total_char)
                                       if i not in comb]

    def command_case(self, cmd: str, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        cmd = name_dict['cmd'][cmd]
        pri_arg = self.std_char_name(prime[0])
        sec_arg = self.std_char_name(second)
        if cmd != 'character' and pri_arg in self.forbid_char or sec_arg in self.forbid_char:
            return
        elif cmd == 'character':
            super().command_case(cmd, prime, second, require, optional)
            for c in self.forbid_char:
                self.characters.pop(c, None)
        else:
            super().command_case(cmd, prime, second, require, optional)

    def buff_find(self, proto: Buff):
        key = proto.source+'-'+proto.family if proto.family not in buff_dict else proto.family
        if key not in buff_dict:
            return
        if key in shapley_case_judge:
            proto = shapley_case_process(proto, key, self)
        if proto:
            return super().buff_find(proto)

    def skill_find(self, proto: Event):
        source, family = proto.source, proto.family
        key = family
        if family not in skill_dict:
            if family != 'WP' and family != 'ART':
                key = source+'-'+family
            elif family == 'WP':
                key = self.weapons[source].name
            elif family == 'ART':
                key = self.artifacts[source].piece4.name
        if key not in skill_dict:
            return
        if key in shapley_case_judge:
            proto = shapley_case_process(proto, key, self)
        if proto:
            proto = shapley_nontrans_constrain(proto, self)
            return super().skill_find(proto)
