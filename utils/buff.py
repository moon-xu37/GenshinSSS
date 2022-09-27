from copy import deepcopy
from typing import Dict, Tuple, List, Callable
from .dnode import DNode
from .dtypes import BuffType


class Buff(object):
    def __init__(self, **config):
        '''
        用于构建buff\n
        储存需要修改伤害树的键和值,包括添加节点和修改节点操作\n
        ---
        `type`: buff类型\n
        `name`: buff名称\n
        `family`:buff所属的族\n
        `source`: buff施加者\n
        `begin`:buff开始时间\n
        `end`:buff结束时间\n
        `func`:判断buff适用的函数\n
        ---
        `visible`: 制图时是否可见\n
        `desc`: buff简介\n
        ---
        `adds`\n
        `changes`\n
        `dur`: 持续时间\n
        (可选项)
        - 对NUMS类型: `num_tar`: buff作用角色, 'all'为所有; `func`:判断buff适用的函数\n
        - 对ATTR类型: `attr_tar`: buff作用角色, 'all'为所有; `attr_val`: buff作用对象值\n
        ---
        ATTR类型: 储存需要修改属性树的键和值 包括添加节点和修改节点操作\n
        DMG类型: 储存需要修改伤害树的键和值\n
        '''
        self.type: BuffType = BuffType.NONE
        self.name: str = ''
        self.family: str = ''
        self.source: str = ''
        self.begin: int = 0
        self.end: int = 0
        self.num_tar: str = ''
        self.func: Callable[[object], bool] = lambda x: False
        self.attr_tar: str = ''
        self.attr_val: str = ''
        self.adds: List[Tuple[str, DNode]] = []
        self.changes: Dict[str, float] = {}
        self.visible: bool = False
        self.desc: str = ''
        self.args: Dict = {}

        self.initialize(**config)

    def initialize(self, **config):
        all_key = [k for k in self.__dict__.keys() if k != 'args']
        for k, v in config.items():
            if k in all_key:
                setattr(self, k, v)
            else:
                self.args[k] = v

    def __eq__(self, other: 'Buff') -> bool:
        return self.name == other.name

    def __lt__(self, other: 'Buff') -> bool:
        return self.begin < other.begin

    def __repr__(self) -> str:
        return 'BUFF :[{:<8}][{:^10}][({:^10})-({:^10})]< {:<4}F- {:<4} F> :{:<20}'.format(
            self.type.name, self.name, self.source, self.family, self.begin, self.end, self.desc)

    @property
    def dur(self):
        return self.end-self.begin

    def add_buff(self, tar_key: str, name: str, value: float, func: str = '', real: DNode = None):
        '''
        `tar_key`: the key on the tree\n
        `name`: the name of the node\n
        `value`: the num of the node\n
        `func`: the func of the node
        '''
        if real:
            self.adds.append((tar_key, real))
        else:
            self.adds.append((tar_key, DNode(name, func, value)))

    def change_buff(self, tar_key: str, value: float):
        '''`tar_key`: the key on the tree\n`value`: the new num of the node'''
        self.change_info[tar_key] = value

    def judge(self, nums) -> bool:
        if self.num_tar == nums.source or self.num_tar == 'all' or self.num_tar == 'stage':
            return self.func(nums)
        else:
            return False

    def work(self, node: DNode):
        for k, new in self.adds:
            try:
                if new.child:  # real node
                    node.find(k).insert(new)
                else:
                    node.find(k).insert(deepcopy(new))
            except:
                continue
        for k, new in self.changes.items():
            try:
                node.modify(k, num=new)
            except:
                continue
