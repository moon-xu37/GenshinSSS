import os
import re
from copy import deepcopy
from typing import List, Dict, Tuple
from collections import OrderedDict
from queue import PriorityQueue
from utils.char import Char, Panel
from utils.artifact import Artifact
from utils.weapon import Weapon
from utils.enemy import Enemy
from utils.nums import *
from utils.buff import Buff
from utils.event import Event
from utils.dtypes import *
from data.namedict import name_dict
from func.buffs import *
from func.skills import *
from func.creates import *


class Interpreter(object):
    def __init__(self):
        # basic info
        self.characters: OrderedDict[str, Char] = OrderedDict()
        self.weapons:    OrderedDict[str, Weapon] = OrderedDict()
        self.artifacts:  OrderedDict[str, Artifact] = OrderedDict()
        self.char_name_map: Dict[str, str] = {}
        self.buff_proto_queue: PriorityQueue[Buff] = PriorityQueue()
        self.buff_que:  PriorityQueue[Buff] = PriorityQueue()
        self.event_que: PriorityQueue[Event] = PriorityQueue()

        # sim info
        self.clock: int = -1
        self.stage: str = ''
        self.enemy = Enemy()
        self.event_now: Event = None
        self.event_log: List[Event] = []
        self.buff_tmp: Buff = None
        self.buff_now: List[Buff] = []
        self.buff_log: List[Buff] = []
        self.creation_now: Dict[str, Tuple[int, Panel]] = {}
        # {name: (end, panel)}

        # data
        self.record_attr:   Dict[str, Dict[str, List[Tuple[int, float]]]] = {}
        # {char: {attr: [(time, num)]}}
        self.record_dmg:    Dict[str, Dict[str, List[Tuple[int, float]]]] = {}
        # {char: {dmg_type: [(time, num)]}}
        self.record_heal:   Dict[str, List[Tuple[int, float]]] = {}
        # {char: [(time, num)]}
        self.record_shield: Dict[str, List[Tuple[int, int, float]]] = {}
        # {char: [(start, end, num)]}
        self.record_stage:  Dict[int, str] = {}
        # {frame: char}
        self.record_for_sim: List[Tuple[float, float, float]] = []
        # [(dmg, cr, cd)]
        self.record_for_attr_buff: \
            Dict[str, Dict[str, List[Tuple[int, bool, str]]]] = {}
        # {char: {attr: [(time, flag, desc)]}}
        self.record_trees:  List[Nums] = []
        self.log:           List[List] = []

        # plot
        self.start: int = 0  # start of the sim
        self.end:   int = 0  # end of the sim
        self.bias:  int = 0  # the bias used in plot
        self.circle: bool = False
        self.path: str = ''
        self.author: str = ''
        self.output: bool = True

    @staticmethod
    def std_time(s: str) -> int:
        'convert time string to standard frame data'
        if s.isnumeric() or '.' in s or s.endswith('s') or s.endswith('S') or s.endswith('秒'):
            return round(60*float(s))
        elif s.endswith('f') or s.endswith('F') or s.endswith('帧'):
            return int(s[:-1])

    @staticmethod
    def std_line(s: str) -> str:
        s = s.strip()
        replacement = {'【': '[', '】': ']',
                       '《': '<', '》': '>',
                       '（': '(', '）': ')',
                       '，': ',', '；': ';'}
        for ch, en in replacement.items():
            s = s.replace(ch, en)
        return s

    def std_char_name(self, name: str) -> str:
        if name in self.char_name_map:
            return self.char_name_map[name]
        elif name in name_dict['character']:
            return name_dict['character'][name]
        elif name in name_dict['buff_src']:
            return name_dict['buff_src'][name]

    def std_arg(self, dic: dict):
        for k, v in list(dic.items()):
            if not k in name_dict['arg']:
                return
            else:
                dic.pop(k)
                k = name_dict['arg'][k]
            if k == 'mode':
                n: int = name_dict['mode'][v]
                dic[k] = ModeType(n)
            elif k == 'elem':
                n: int = name_dict['elem'][v]
                dic[k] = ElementType(n)
            elif k == 'react':
                n: str = name_dict['react'][v]
                dic[k] = ReactType[n]
            elif k == 'actiontime' or k == 'cooltime':
                dic[k] = self.std_time(v)
            elif k in ['view', 'manual', 'seq', 'cx']:
                if v.upper() in ['T', 'TRUE', 'Y', 'YES', '是']:
                    dic[k] = True
                else:
                    dic[k] = False
            else:
                dic[k] = v

    def read_file(self):
        if not self.path:
            dirlist = os.listdir('./')
            filelist = []
            for dir in dirlist:
                if dir.endswith('txt'):
                    filelist.append(dir)
            for i, f in enumerate(filelist):
                print(f'{i+1:<2}:{f}')
            index = input('请输入你要处理的文件的序号:')
            self.path = filelist[int(index)-1]
        self.process_file()

    def process_file(self):
        with open(self.path, 'r', encoding='utf8') as f:
            lines = f.readlines()
            for line in lines:
                command = self.std_line(line)
                if command.startswith('#') or not command:
                    continue
                for each in command.split(';')[:-1]:
                    cmd_elem = self.process_line(each)
                    if self.output:
                        print(cmd_elem)
                    self.command_case(*cmd_elem)
        folder = os.path.splitext(self.path)[0]
        if not os.path.exists(folder):
            os.mkdir(folder)

    def process_line(self, command: str):
        single = command.strip()
        cmd = re.match('(.*)(?:\[)', single).groups()[0].strip()
        pri_arg = re.search('(?:\[)(.*)(?:\])',          # []
                            single).groups()[0].strip()
        req_arg = re.search('(?:\<)(.*)(?:\>)',          # <>
                            single).groups()[0].strip()
        sec_arg = re.search('(?:\{)(.*)(?:\})', single)  # {}
        sec_arg = sec_arg.groups()[0].strip() if sec_arg else ''
        opt_arg = re.search('(?:\()(.*)(?:\))', single)  # ()
        opt_arg = opt_arg.groups()[0].strip() if opt_arg else ''
        # separate in order -> tuple
        pri_arg = [s.strip() for s in pri_arg.split(',')]
        req_arg = [s.strip() for s in req_arg.split(',')]
        # abstract arguments -> dict
        opt_arg = [s.strip() for s in opt_arg.split(',')]
        opt_args = {}
        for item in opt_arg:
            if not item:
                continue
            k, v = item.split('=')[0].strip(), item.split('=')[1].strip()
            opt_args[k] = v
        return cmd, pri_arg, sec_arg, req_arg, opt_args

    def command_case(self, cmd: str, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        cmd = name_dict['cmd'][cmd]
        if cmd == 'character':
            self.set_characters(prime, require, optional)
        elif cmd == 'weapon':
            self.set_weapons(prime, second, require)
        elif cmd == 'artifact':
            self.set_artifacts(prime, second, require, optional)
        elif cmd == 'buff':
            self.create_buff(prime, second, require, optional)
        elif cmd in ['damage', 'transformative', 'heal', 'shield']:
            self.create_nums(cmd, prime, second, require, optional)
        elif cmd == 'creation':
            self.create_creations(prime, second, require, optional)
        elif cmd == 'switch':
            self.switch_person(prime, require)
        elif cmd == 'plot':
            self.plot_set(prime, second, require, optional)

    def set_characters(self, prime: List[str], require: List[str], optional: Dict[str, str]):
        name = name_dict['character'][prime[0]]
        [lv_str, cx, a_, e_, q_] = require
        cx, a, e, q = int(cx), int(a_), int(e_), int(q_)
        asc = lv_str.upper().endswith('T')
        lv = int(lv_str[:-1]) if asc else int(lv_str)
        self.characters[name] = Char(name, lv, asc, cx,  a, e, q)
        if n := optional.get('nickname'):
            self.char_name_map[n] = name
        else:
            n = str(len(self.characters))
            self.char_name_map[n] = name

    def set_weapons(self, prime: List[str], second: str, require: List[str]):
        name = name_dict['weapon'][prime[0]]
        owner = self.std_char_name(second)
        lv_str = require[0]
        asc = lv_str.endswith('T')
        lv = int(lv_str[:-1]) if asc else int(lv_str)
        self.weapons[owner] = Weapon(name, int(require[1]), lv, asc)

    def set_artifacts(self, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        piece21, piece22, piece4 = None, None, None
        if len(prime) == 1:
            piece4 = name_dict['artifact'].get(prime[0])
            piece21 = piece4
        elif len(prime) == 2:
            piece21 = name_dict['artifact'].get(prime[0])
            piece22 = name_dict['artifact'].get(prime[1])
        [sands, goblet, circlet] = require
        sands = name_dict['stat'][sands]
        goblet = name_dict['stat'][goblet]
        circlet = name_dict['stat'][circlet]
        m = ['HP_CONST', 'ATK_CONST', sands, goblet, circlet]
        owner = self.std_char_name(second)
        self.artifacts[owner] = Artifact(piece21, piece22, piece4, m)
        self.artifacts[owner].set_owner(owner)
        if std := optional.get('std'):
            self.artifacts[owner].use_std(std)
        else:
            sub_list, id_list = [0]*10, self.artifacts[owner].subs
            for s, v in optional.items():
                s = name_dict['stat'][s]
                sub_list[id_list.index(s)] = int(v)
            self.artifacts[owner].sub = sub_list

    def create_buff(self, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        # find formal name, family, type
        source = self.std_char_name(second)

        if prime[0] in name_dict['buff']:
            name = name_dict['buff'][prime[0]]
            buff_family = name_dict['buff_family'][name]
        elif prime[0] in name_dict['artifact'] or prime[0].upper() in ['ART', 'A', '圣遗物']:
            name = 'PS'
            buff_family = self.artifacts[source].piece4.name
        elif prime[0] in name_dict['weapon'] or prime[0].upper() in ['WP', 'W', '武器']:
            name = 'PS'
            buff_family = self.weapons[source].name
        elif prime[0] in name_dict['elem']:
            elem_i = name_dict['elem'][prime[0]]
            name = ElementType(elem_i).name
            buff_family = 'RE'

        self.std_arg(optional)
        if flag := optional.get('manual'):
            time_list = [require[0]]
        else:
            time_list = require
        for time_str in time_list:
            begin = self.std_time(time_str)
            end = self.std_time(require[1]) if flag else 0
            proto = Buff(name=name, family=buff_family, source=source,
                         begin=begin, end=end, **optional)
            self.buff_proto_queue.put(proto)

    def create_nums(self, cmd: str, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        # find formal skill name, family, type
        name = self.std_char_name(second)

        if prime[0] in name_dict['skill']:
            skill_name = name_dict['skill'][prime[0]]
        else:
            skill_name = prime[0].upper()
        if skill_name in name_dict['react']:
            skill_name = name_dict['react'][skill_name]

        skill_family = name_dict['family'][skill_name]

        self.std_arg(optional)
        optional['lv'] = self.characters[name].base.lv
        form = EventType.NONE
        if cmd == 'damage':
            form = EventType.DAMAGE
        elif cmd == 'transformative':
            form = EventType.ELEMENT
        elif cmd == 'heal':
            form = EventType.HEALTH
        elif cmd == 'shield':
            form = EventType.SHIELD
        for time_str in require:
            t = self.std_time(time_str)
            proto = Event(type=form, name=skill_name, family=skill_family, source=name,
                          time=t, **optional)
            self.skill_find(proto)

    def create_creations(self, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        name = name_dict['create'][prime[0]] \
            if prime[0] in name_dict['create'] else prime[0].upper()
        source = self.std_char_name(second)
        create_find = source+'->'+name if name not in create_dict else name
        self.std_arg(optional)
        begin = self.std_time(require[0])
        end = self.std_time(require[1]) if optional.get('manual') else 0
        event = Event(type=EventType.CREATION, name=source+'->'+name, family=name, source=source,
                      time=begin, endtime=end, **optional)
        create_event = create_dict[create_find](event, self)
        self.event_que.put(create_event)

    def switch_person(self, prime: List[str], require: List[str]):
        t = self.std_time(require[0])
        name = self.std_char_name(prime[0])
        event = Event(type=EventType.SWITCH, name=name, time=t)
        self.event_que.put(event)

    def plot_set(self, prime: List[str], second: str, require: List[str], optional: Dict[str, str]):
        name = name_dict['plot'][prime[0]]
        if name == 'start':
            self.start = self.std_time(require[0])
        elif name == 'end':
            self.end = self.std_time(require[0])
        elif name == 'bias':
            self.bias = self.std_time(require[0])
        elif name == 'author':
            self.author = require[0]

    def buff_find(self, proto: Buff):
        key = proto.source+'-'+proto.family if proto.family not in buff_dict else proto.family
        if key not in buff_dict:
            return
        for buff in buff_dict[key](proto, self):
            self.buff_que.put(buff)

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
        for event in skill_dict[key](proto, self):
            self.event_que.put(event)

    def main_loop(self):
        # initialize
        for char_name, char in self.characters.items():
            weapon = self.weapons.get(char_name)
            artifact = self.artifacts.get(char_name)
            char.connect(weapon, artifact)
            self.init_buff(char_name)
        self.init_record()
        self.clock = 0
        self.stage = list(self.characters.keys())[0]
        self.record_stage[self.clock] = self.stage
        self.write_record()

        # work
        proto: Buff = None
        next_event: bool = True
        next_buff:  bool = True
        while True:
            if self.event_que.unfinished_tasks > 0 and next_event:
                self.event_now = self.event_que.get()
                self.event_que.task_done()
                next_event = False
            if self.buff_que.unfinished_tasks > 0 and next_buff:
                self.buff_tmp = self.buff_que.get()
                self.buff_que.task_done()
                next_buff = False
            if not proto and self.buff_proto_queue.unfinished_tasks > 0:
                proto = self.buff_proto_queue.get()
                self.buff_proto_queue.task_done()
            # decide what to do
            event_begin = self.event_now.time
            buff_begin = self.buff_tmp.begin if self.buff_tmp else 1_000_000
            buff_end, end_index = self.find_buff_end()
            create_end, create_name = self.find_creation_end()
            proto_begin = proto.begin if proto else 1_000_000
            self.clock = priority = \
                min([event_begin, buff_begin, buff_end, create_end, proto_begin])
            if proto_begin == priority:
                self.buff_find(proto)
                proto = None
            elif create_end == priority:
                self.remove_creation(create_name)
            elif buff_end == priority:
                self.remove_buff(end_index)
            elif buff_begin == priority:
                self.execute_buff()
                next_buff = True
            elif event_begin == priority:
                self.execute_event()
                next_event = True
            # break condition
            if self.event_que.unfinished_tasks == 0 and next_event:
                while self.buff_now:
                    self.buff_log.append(self.buff_now.pop())
                if self.end:
                    self.clock = self.end
                self.write_record()
                break

    def find_buff_end(self) -> Tuple[int, int]:
        '''find the buff that is first to end. return time, index'''
        t, index = 1_000_000, 0
        if self.buff_now:
            t = min([b.end for b in self.buff_now])
        for i, b in enumerate(self.buff_now):
            if b.end == t:
                index = i
                break
        return t, index

    def find_creation_end(self) -> Tuple[int, str]:
        '''find the creation that is first to end. return time, name'''
        t, name = 1_000_000, ''
        if self.creation_now:
            t, name = min([(v[0], k) for k, v in self.creation_now.items()])
        return t, name

    def init_buff(self, name: str):
        # artifact
        a = self.artifacts[name]
        a_pieces = [a.piece4.name] if a.piece4 != SetType.NONE else []
        if a.piece2_1 == SetType.NOBLESSE_OBLIGE and a.piece4 != SetType.NOBLESSE_OBLIGE:
            a_pieces.append(a.piece2_1.name)
        elif a.piece2_2 == SetType.NOBLESSE_OBLIGE and a.piece4 != SetType.NOBLESSE_OBLIGE:
            a_pieces.append(a.piece2_2.name)
        for piece in a_pieces:
            a_buff = Buff(name='AUTO', family=piece, source=name)
            self.buff_proto_queue.put(a_buff)
        # weapon
        w = self.weapons[name]
        w_buff = Buff(name='AUTO', family=w.name, source=name)
        self.buff_proto_queue.put(w_buff)
        # character
        c_buff1 = Buff(name='AUTO', family='PS', source=name)
        c_buff2 = Buff(name='AUTO', family='CX', source=name)
        self.buff_proto_queue.put(c_buff1)
        self.buff_proto_queue.put(c_buff2)
        # resonance
        if name != list(self.characters.keys())[0]:
            return
        r_buff = Buff(name='AUTO', family='RE', source='Resonance')
        self.buff_proto_queue.put(r_buff)

    def init_record(self):
        attr_list = ['ATK', 'DEF', 'HP', 'EM', 'ER', 'CRIT_RATE', 'CRIT_DMG'] +\
            [f'{c}_DMG' for c in ElementType.__members__ if c != 'NONE']
        for char in self.characters.keys():
            self.record_attr[char] = dict.fromkeys(attr_list)
            self.record_for_attr_buff[char] = dict.fromkeys(attr_list)
            # decide what to record by the character
            self.record_dmg[char] = dict.fromkeys(
                DamageType.__members__.keys())
            self.record_heal[char] = []
            self.record_shield[char] = []
            for damage_type in DamageType.__members__:
                self.record_dmg[char][damage_type] = []
            for attr_type in self.record_attr[char].keys():
                self.record_attr[char][attr_type] = []
                self.record_for_attr_buff[char][attr_type] = []

    def write_record(self):
        for name, char in self.characters.items():
            for attr_type in self.record_attr[name].keys():
                val = getattr(char.attr, attr_type).value
                self.record_attr[name][attr_type].append((self.clock, val))

    def write_attr_buff(self, buff: Buff, target: str, flag: bool):
        if buff.attr_val in self.record_for_attr_buff[target]:
            self.record_for_attr_buff[target][buff.attr_val].append(
                (self.clock, flag, buff.desc))

    def remove_creation(self, name: str):
        self.creation_now.pop(name)

    def remove_buff(self, index: int):
        buff = self.buff_now[index]
        self.write_record()
        if buff.type == BuffType.ATTR:
            tar = buff.attr_tar
            if tar == 'all':
                tar_list = list(self.characters.keys())
            elif tar == 'stage':
                tar_list = []
                self.remove_buff_delay(index)
            else:
                tar_list = [tar]
            for target in tar_list:
                self.characters[target].attr.disconnect(buff)
                self.write_attr_buff(buff, target, False)
        self.log.append(['BUFFOFF', buff.source,
                         self.clock, buff.name, buff.desc])
        self.buff_log.append(self.buff_now.pop(index))
        self.write_record()

    def remove_buff_delay(self, index: int):
        buff = deepcopy(self.buff_now[index])
        buff.attr_tar = self.stage
        buff.end = self.clock+buff.args.get('delay', 0)
        buff.visible = False
        self.buff_now.append(buff)

    def execute_buff(self):
        if self.output:
            print(self.buff_tmp)
        self.write_record()
        if self.buff_tmp.type == BuffType.ATTR:
            tar = self.buff_tmp.attr_tar
            if tar == 'all':
                tar_list = list(self.characters.keys())
            elif tar == 'stage':
                tar_list = [self.stage]
            else:
                tar_list = [tar]
            for target in tar_list:
                self.characters[target].attr.connect(self.buff_tmp)
                self.write_attr_buff(self.buff_tmp, target, True)
        self.log.append(['BUFFON', self.buff_tmp.source,
                         self.clock, self.buff_tmp.name, self.buff_tmp.desc])
        self.buff_now.append(self.buff_tmp)
        self.buff_tmp = None
        self.write_record()

    def execute_event(self):
        if self.output:
            print(self.event_now)
        if self.event_now.type == EventType.SWITCH:
            self.do_switch()
        elif self.event_now.type == EventType.CREATION:
            self.do_creations()
        elif self.event_now.type == EventType.DAMAGE:
            self.do_damage()
        elif self.event_now.type == EventType.ELEMENT:
            self.do_transformative()
        elif self.event_now.type == EventType.HEALTH:
            self.do_health()
        elif self.event_now.type == EventType.SHIELD:
            self.do_shield()
        self.log.append([self.event_now.type.name, self.event_now.source,
                         self.clock, self.event_now.name, self.event_now.desc])
        self.event_log.append(self.event_now)

    def do_switch(self):
        self.event_now.source = self.stage
        # automatically update stage buff
        for i, b in enumerate(self.buff_now):
            if b.type == BuffType.ATTR and b.attr_tar == 'stage':
                self.remove_buff_delay(i)
        self.stage = self.event_now.name
        self.record_stage[self.clock] = self.stage
        self.write_record()
        for i, b in enumerate(self.buff_now):
            if b.type == BuffType.ATTR and b.attr_tar == 'stage':
                self.characters[self.stage].attr.connect(b)
                self.write_attr_buff(b, self.stage, True)
        self.write_record()

    def do_creations(self):
        panel = Panel(self.characters[self.event_now.source])
        self.creation_now[self.event_now.name] = \
            (self.event_now.endtime, panel)

    def do_damage(self):
        damage = Damage()
        damage.to_event(self.event_now)
        damage.to_enemy(self.enemy)
        src = self.event_now.source
        src_panel = Panel(self.characters[src]) \
            if not self.event_now.snapshot else self.creation_now[self.event_now.snapshot][1]
        damage.to_panel(src_panel)
        em_panel = Panel(self.characters[src], 'EM')  # dynamic EM dependency
        damage.to_panel(em_panel)
        for buff in self.buff_now:
            if buff.type == BuffType.ATTR or (buff.num_tar == 'stage' and damage.source != self.stage):
                continue
            if buff.judge(damage):
                damage.to_buff(buff)
        if damage.value <= 0:
            return
        self.record_dmg[src][damage.damage_type.name].append(
            (self.clock, round(damage.value)))
        self.record_trees.append(deepcopy(damage))
        self.record_for_sim.append(damage.for_sim())

    def do_transformative(self):
        damage = TransDamage()
        damage.to_event(self.event_now)
        damage.to_enemy(self.enemy)
        src = self.event_now.source
        src_panel = Panel(self.characters[src], 'EM')  # dynamic EM dependency
        damage.to_panel(src_panel)
        for buff in self.buff_now:
            if buff.type == BuffType.ATTR or (buff.num_tar == 'stage' and damage.source != self.stage):
                continue
            if buff.judge(damage):
                damage.to_buff(buff)
        if damage.value <= 0:
            return
        self.record_dmg[src][damage.damage_type.name].append(
            (self.clock, round(damage.value)))
        self.record_trees.append(deepcopy(damage))
        self.record_for_sim.append(damage.for_sim())

    def do_health(self):
        src = self.event_now.source
        tar = self.event_now.args.get('tar', src)
        tar = tar if tar != 'stage' else self.stage
        tar_list = list(self.characters.keys()) if tar == 'all' else [tar]
        src_panel = Panel(self.characters[src])\
            if not self.event_now.snapshot else self.creation_now[self.event_now.snapshot][1]
        for target in tar_list:
            heal = Heal()
            heal.to_event(self.event_now)
            tar_panel = Panel(self.characters[target], 'HEAL_INCOME')
            heal.to_panel(src_panel)
            heal.to_panel(tar_panel)
            for buff in self.buff_now:
                if buff.type != BuffType.HEALTH or (buff.num_tar == 'stage' and heal.source != self.stage):
                    continue
                if buff.judge(heal):
                    heal.to_buff(buff)
            self.record_heal[target].append((self.clock, round(heal.value)))
            self.record_trees.append(deepcopy(heal))

    def do_shield(self):
        shield = Shield()
        shield.to_event(self.event_now)
        src = self.event_now.source
        src_panel = Panel(self.characters[src])\
            if not self.event_now.snapshot else self.creation_now[self.event_now.snapshot][1]
        shield.to_panel(src_panel)
        for buff in self.buff_now:
            if buff.type != BuffType.SHIELD or (buff.num_tar == 'stage' and shield.source != self.stage):
                continue
            if buff.judge(shield):
                shield.to_buff(buff)
        self.record_shield[src].append(
            (self.clock, self.event_now.actiontime, round(shield.value)))
        self.record_trees.append(deepcopy(shield))


if __name__ == '__main__':
    import pprint
    import time
    from collections import Counter
    a = Interpreter()
    a.read_file()
    t1 = time.perf_counter()
    a.main_loop()
    t2 = time.perf_counter()
    # pprint.pprint(a.record_dmg)
    # pprint.pprint(a.record_attr['Ayaka'])
    grad = Counter()
    for i, t in enumerate(a.record_trees):
        if i % 5 == 0:
            g = Counter(t.root.auto_grad())
            grad += g
            pprint.pprint(t.root.formula())
            pprint.pprint(t.root.auto_grad())
    pprint.pprint(grad)
    print(f'total time: {t2-t1:.6f}s')
    print('done')
