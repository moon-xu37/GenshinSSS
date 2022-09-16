from typing import Iterable, List, Tuple, Dict, Union, Callable


class DNode:
    def __init__(self, key='', func='', num=0):
        self.key: str = key
        self.func: str = func
        self.num: float = num
        self.param: bool = False
        self.child: List[DNode] = []

    def __float__(self):
        return self.value

    def __int__(self):
        return int(self.value)

    @property
    def leaf(self) -> bool:
        return (self.func == '%' or self.func == '')

    @property
    def has_param(self) -> bool:
        if self.leaf:
            return self.param
        else:
            return any([c.has_param for c in self.child])

    @property
    def value(self) -> float:
        if self.func == '':
            return self.num
        elif self.func == '%':
            return self.num/100
        else:
            return self.functions(self.func, 1)

    def auto_grad(self) -> Dict[str, float]:
        '''return Dict[param, grad]'''
        if self.leaf:
            if self.param == False:
                return {}
            elif self.func == '':
                return {self.key: 1}
            elif self.func == '%':
                return {self.key: 0.01}
        else:
            return self.functions(self.func, 2)

    def formula(self, merge: bool = False) -> str:
        if self.leaf:
            if self.param == False:
                return self.cut_str(self.value)
            else:
                return f'<{self.key}>{self.value:.4f}'
        else:
            return self.functions(self.func, 3, merge)

    def find(self, key: str) -> 'DNode':
        if self.key == key:
            return self
        elif self.leaf:
            raise Exception('not found')
        que: List[DNode] = []
        que.extend(self.child)
        while(que):
            c = que.pop(0)
            if c.key == key:
                return c
            elif not c.leaf:
                que.extend(c.child)
        raise Exception('not found')

    def insert(self, node: 'DNode') -> 'DNode':
        if not self.leaf:
            self.child.append(node)
            return self.find(node.key)
        else:
            raise KeyError

    def extend(self, iterable: Iterable) -> 'DNode':
        if not self.leaf:
            self.child.extend(iterable)
            return self
        else:
            raise KeyError

    def remove(self, key: str) -> None:
        que: List[DNode] = []
        que.append(self)
        while(que):
            p = que.pop(0)
            if not p.leaf:
                for i, c in enumerate(p.child):
                    if c.key == key:
                        del p.child[i]
                        return
                que.extend(p.child)

    def modify(self, key: str = '', **kwargs) -> 'DNode':
        if key:
            obj = self.find(key)
        else:
            obj = self
        for k, v in kwargs.items():
            obj.__setattr__(k, v)
        return obj

    @staticmethod
    def cut_str(num: float) -> str:
        split = str(num).split('.')
        if len(split) == 2 and len(split[1]) >= 6:
            return f'{num:.4f}'
        else:
            return str(num)

    def __repr__(self) -> str:
        result = []
        que: List[Tuple[DNode, int]] = []
        que.append((self, 0))
        while (que):
            c, n = que.pop()
            num_str = self.cut_str(c.value)
            num = f'({num_str})' if not c.param else f'({num_str})<arg>'
            result.append('\t'*n+'->'+f'[{c.key}][{c.func}]={num}')
            if not c.leaf:
                que.extend([(child, n+1) for child in reversed(c.child)])
        return '\n'.join(result)

    def __eq__(self, other: object) -> bool:
        if self.key == other.key and abs(self.value-other.value) < 1e5:
            if len(self.child) == len(other.child):
                return all([self.child[i] == other.child[i] for i in range(len(self.child))])
            else:
                return False
        else:
            return False

    def argument(self, flag: bool = True) -> 'DNode':
        '''Set this node as an argument'''
        if not self.leaf:
            raise Exception('this node cannot be an argument')
        self.param = flag
        return self

    def functions(self, func: str, mode: int, merge: bool = False) -> Union[float, str, Dict[str, float]]:
        func_mapping: Dict[str, Callable] = {
            '+': self.plus,
            '*': self.multiply,
            'EM_A': self.EM_A,
            'EM_T': self.EM_T,
            'EM_C': self.EM_C,
            'RES': self.RES,
            'DEF': self.DEF,
            'THRESH_E': self.THRESH_E,
            'THRESH': self.THRESH,
        }
        return func_mapping[func](mode, merge)

    def plus(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            self.num = 0
            for c in self.child:
                self.num += c.value
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            for c in self.child:
                for arg, g in c.auto_grad().items():
                    grad.setdefault(arg, 0)
                    grad[arg] += g
            return grad
        else:
            if not merge:
                return '+'.join([c.formula() for c in self.child if c.value])
            else:
                if self.has_param:
                    v = sum([c.value for c in self.child if not c.has_param])
                    a = [self.cut_str(v)] if v else []
                    a += [c.formula(merge) for c in self.child if c.has_param]
                    return '+'.join(a)
                else:
                    return self.cut_str(self.value) if self.value else ''

    def multiply(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            self.num = 1
            for c in self.child:
                self.num *= c.value
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            v = self.value
            for c in self.child:
                for arg, g in c.auto_grad().items():
                    grad.setdefault(arg, 0)
                    grad[arg] += g*v/c.value
            return grad
        else:
            if not merge:
                return '*'.join([f'({c.formula()})' for c in self.child if c.value])
            else:
                if self.has_param:
                    v = 1
                    for c in self.child:
                        if not c.has_param:
                            v *= c.value
                    a = [self.cut_str(v)] if v != 1 else []
                    a += [f'({c.formula(merge)})' for c in self.child if c.has_param]
                    return '*'.join(a)
                else:
                    return self.cut_str(self.value) if self.value else ''

    def EM_A(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            em = sum([c.value for c in self.child])
            self.num = 2.78*em/(em+1400)
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            em = sum([c.value for c in self.child])
            k = (2.78*1400)/(em+1400)**2
            for c in self.child:
                for arg, g in c.auto_grad().items():
                    grad.setdefault(arg, 0)
                    grad[arg] += g*k
            return grad
        else:
            if not merge:
                em = '+'.join([c.formula() for c in self.child if c.value])
            else:
                v = sum([c.value for c in self.child if not c.has_param])
                a = [self.cut_str(v)] if v else []
                a += [c.formula(merge) for c in self.child if c.has_param]
                em = '+'.join(a)
            return f'2.78*({em})/({em}+1400)'

    def EM_T(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            em = sum([c.value for c in self.child])
            self.num = 16*em/(em+2000)
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            em = sum([c.value for c in self.child])
            k = (16*2000)/(em+2000)**2
            for c in self.child:
                for arg, g in c.auto_grad().items():
                    grad.setdefault(arg, 0)
                    grad[arg] += g*k
            return grad
        else:
            if not merge:
                em = '+'.join([c.formula() for c in self.child if c.value])
            else:
                v = sum([c.value for c in self.child if not c.has_param])
                a = [self.cut_str(v)] if v else []
                a += [c.formula(merge) for c in self.child if c.has_param]
                em = '+'.join(a)
            return f'16*({em})/({em}+2000)'

    def EM_C(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            em = sum([c.value for c in self.child])
            self.num = 5*em/(em+1200)
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            em = sum([c.value for c in self.child])
            k = (5*1200)/(em+1200)**2
            for c in self.child:
                for arg, g in c.auto_grad().items():
                    grad.setdefault(arg, 0)
                    grad[arg] += g*k
            return grad
        else:
            if not merge:
                em = '+'.join([c.formula() for c in self.child if c.value])
            else:
                v = sum([c.value for c in self.child if not c.has_param])
                a = [self.cut_str(v)] if v else []
                a += [c.formula(merge) for c in self.child if c.has_param]
                em = '+'.join(a)
            return f'5*({em})/({em}+1200)'

    def RES(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            res = sum([c.value for c in self.child])
            if res < 0:
                return 1-0.5*res
            elif res < 0.75:
                return 1-res
            else:
                return 1/(1+4*res)
        elif mode == 2:
            return {}
        else:
            if not merge:
                formula: List[str] = []
                res = sum([c.value for c in self.child])
                for c in self.child:
                    if c.value:
                        formula.append(c.formula())
                r_formula = '+'.join(formula).replace('+-', '-')
                if res < 0:
                    return f'1-0.5*({r_formula})'
                elif res < 0.75:
                    return f'1-({r_formula})'
                else:
                    return f'1/(1+4*({r_formula}))'
            else:
                return self.cut_str(self.value)

    def DEF(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            lv_char = int(self.find('Character Level').value)
            lv_enemy = int(self.find('Enemy Level').value)
            def_ig = self.find('Defence Ignore').value
            def_red = self.find('Defence Reduction').value
            self.num = (100+lv_char) / \
                ((100+lv_char)+(100+lv_enemy)*(1-def_red)*(1-def_ig))
            return self.num
        elif mode == 2:
            return {}
        else:
            formula: List[str] = []
            if not merge:
                lv_char = str(self.find('Character Level').value+100)
                lv_enemy = str(self.find('Enemy Level').value+100)
                def_ig = self.find('Defence Ignore')
                def_red = self.find('Defence Reduction')
                formula.append(lv_enemy)
                if def_ig.value:
                    formula.append(
                        f'(1-{def_ig.formula()})'.replace('+', '-'))
                if def_red.value:
                    formula.append(
                        f'(1-{def_red.formula()})'.replace('+', '-'))
                return '{}/({}+{})'.format(lv_char, lv_char, '*'.join(formula))
            else:
                return self.cut_str(self.value)

    def THRESH_E(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            c_rate = self.find('Critical Rate').value
            c_dmg = self.find('Critical DMG').value
            cr = max(0, min(1, c_rate))
            self.num = cr * c_dmg
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            c_rate = self.find('Critical Rate')
            c_dmg = self.find('Critical DMG')
            cr = max(0, min(1, c_rate.value))
            if 0 < cr < 1:
                for arg, g in c_rate.auto_grad().items():
                    grad.setdefault(arg, 0)
                    grad[arg] += g*c_dmg.value
            for arg, g in c_dmg.auto_grad().items():
                grad.setdefault(arg, 0)
                grad[arg] += g*cr
            return grad
        else:
            c_rate = self.find('Critical Rate')
            cr = max(0, min(1, c_rate.value))
            cr_formula = c_rate.formula(merge)
            cd_formula = self.find('Critical DMG').formula(merge)
            if cr == 0:
                return '0'
            elif cr == 1:
                return f'({cd_formula})'
            else:
                return f'({cr_formula})*({cd_formula})'

    def THRESH(self, mode: int, merge: bool) -> Union[float, str, Dict[str, float]]:
        if mode == 1:
            threshold = self.find(self.key+' Threshold').value
            num = sum([c.value for c in self.child
                       if c.key != self.key+' Threshold'])
            self.num = min(num, threshold)
            return self.num
        elif mode == 2:
            grad: Dict[str, float] = {}
            threshold = self.find(self.key+' Threshold').value
            num = sum([c.value for c in self.child
                       if c.key != self.key+' Threshold'])
            if num < threshold:
                for c in self.child:
                    if c.key != self.key+' Threshold':
                        for arg, g in c.auto_grad().items():
                            grad.setdefault(arg, 0)
                            grad[arg] += g
            return grad
        else:
            key = self.key+' Threshold'
            threshold = self.find(key).value
            n = sum([c.value for c in self.child if c.key != key])
            if n >= threshold:
                return str(threshold)
            else:
                if not merge:
                    return '+'.join([c.formula() for c in self.child if c.value and c.key != key])
                else:
                    if self.has_param:
                        v = sum([c.value for c in self.child
                                 if not c.has_param and c.key != key])
                        a = [self.cut_str(v)] if v else []
                        a += [c.formula(merge)
                              for c in self.child if c.has_param]
                        return '+'.join(a)
                    else:
                        return self.cut_str(self.value) if self.value else ''
