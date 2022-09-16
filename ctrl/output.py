import csv
import json
from copy import deepcopy
from typing import Union, Tuple, Dict, List
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from utils.dtypes import ElementType, BuffType, DamageType, EventType, SetType
from utils.event import Event
from utils.buff import Buff
from data.translation import chinese_translation as c_trans
from ctrl.interpret import Interpreter

plt.style.use("seaborn-bright")
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class ColorManager(object):
    colormap = {
        'ANEMO': [
            mcolors.LinearSegmentedColormap.from_list(
                'anemo1', [(0, '#c1f8dc'), (1, '#95ddb9')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'anemo2', [(0, '#acdacb'), (1, '#74c2a8')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'anemo3', [(0, '#9de9c2'), (1, '#5cdb99')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'anemo4', [(0, '#72e8cb'), (1, '#30c8a2')], N=32)
        ],
        'GEO': [
            mcolors.LinearSegmentedColormap.from_list(
                'geo1', [(0, '#f9e7a0'), (1, '#f5d761')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'geo2', [(0, '#fcd384'), (1, '#fab632')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'geo3', [(0, '#f2df82'), (1, '#eaca2e')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'geo4', [(0, '#fee8bb'), (1, '#fed88e')], N=32)
        ],
        'ELECTRO': [
            mcolors.LinearSegmentedColormap.from_list(
                'electro1', [(0, '#e8cfff'), (1, '#c8a7e6')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'electro2', [(0, '#d4bfdf'), (1, '#b795c9')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'electro3', [(0, '#be8ada'), (1, '#892bbc')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'electro4', [(0, '#c694d8'), (1, '#a04cbe')], N=32),
        ],
        'DENDRO': [
            mcolors.LinearSegmentedColormap.from_list(
                'dendro1', [(0, '#c1f8dc'), (1, '#95ddb9')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'dendro2', [(0, '#acdacb'), (1, '#74c2a8')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'dendro3', [(0, '#9de9c2'), (1, '#5cdb99')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'dendro4', [(0, '#72e8cb'), (1, '#30c8a2')], N=32)
        ],
        'HYDRO': [
            mcolors.LinearSegmentedColormap.from_list(
                'hydro1', [(0, '#52eeff'), (1, '#07cfe6')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'hydro2', [(0, '#94daf7'), (1, '#4cc2f1')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'hydro3', [(0, '#91a6e2'), (1, '#476bcf')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'hydro4', [(0, '#76a1e0'), (1, '#1b63cb')], N=32),
        ],
        'PYRO': [
            mcolors.LinearSegmentedColormap.from_list(
                'pyro1', [(0, '#f68675'), (1, '#f03619')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'pyro2', [(0, '#ffcaa9'), (1, '#ffa76f')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'pyro3', [(0, '#e96761'), (1, '#ca221a')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'pyro4', [(0, '#f5af88'), (1, '#ef7938')], N=32),
        ],
        'CRYO': [
            mcolors.LinearSegmentedColormap.from_list(
                'cryo1', [(0, '#caecf4'), (1, '#a6e0ed')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'cryo2', [(0, '#dcfdfd'), (1, '#c4fbfb')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'cryo3', [(0, '#b7e3f9'), (1, '#93d5f6')], N=32),
            mcolors.LinearSegmentedColormap.from_list(
                'cryo4', [(0, '#d5e8ff'), (1, '#b9d8ff')], N=32),
        ],
        'NONE': [
            mcolors.LinearSegmentedColormap.from_list(
                'none', [(0, '#e2e2e2'), (1, '#bababa')], N=32)
        ]
    }

    def __init__(self, inter: Interpreter):
        self.char_map: Dict[str, 'mcolors.LinearSegmentedColormap'] = \
            dict.fromkeys(inter.characters.keys())

        elem_map = dict.fromkeys(inter.characters.keys())
        for name, char in inter.characters.items():
            elem_map[name] = ElementType(char.base.element)
        cnt = dict.fromkeys(ElementType.__members__.keys(), 0)
        for k, v in elem_map.items():
            i = cnt[v.name]
            cnt[v.name] += 1
            self.char_map[k] = self.colormap[v.name][i]

    def get_char_colormap(self, name: str) -> mcolors.LinearSegmentedColormap:
        return self.char_map[name]

    def get_char_color(self, name: str):
        return self.char_map[name](1.0)

    def get_element_color(self, element: Union[ElementType, str]):
        if isinstance(element, str):
            return self.colormap[element.upper()][0](1.0)
        elif isinstance(element, ElementType):
            return self.colormap[element.name][0](1.0)

    def get_skill_color(self, skill: Union[Event, Tuple[str, str]]):
        if isinstance(skill, Event):
            return self.char_map[skill.source](skill.args.get('damage_type').value/6)
        elif isinstance(skill, Tuple):
            return self.char_map[skill[0]](DamageType[skill[1].upper()].value/6)

    def get_action_color(self, action: Event):
        if t := action.args.get('damage_type'):
            v = (t.value-2.5)/3
            return self.char_map[action.source](v)
        else:
            return self.char_map[action.source](1.0)

    def get_buff_color(self, buff: Buff):
        buff_type = buff.type
        cmap_name = ['spring', 'summer', 'winter', 'cool']
        if buff.source in self.char_map:
            id = list(self.char_map.keys()).index(buff.source)
        else:
            rd = np.random.rand()
            return plt.colormaps['viridis'](rd)

        cmap = plt.colormaps[cmap_name[id]]
        if buff_type == BuffType.ATTR:
            return cmap((id+2)/3)
        elif buff_type == BuffType.DMG:
            return cmap((id+1)/3)
        else:
            return cmap((id+0)/3)

    def show_all(self):
        fig, axs = plt.subplots(ncols=29)
        ar = np.linspace(0, 1, 32)
        ar = np.vstack(ar)
        all_map = [vv for v in self.colormap.values() for vv in v]
        for ax, c in zip(axs, all_map):
            ax.imshow(ar, cmap=c, aspect='auto')
            ax.set_axis_off()
        plt.show()


class Plotter(ColorManager):
    damage_translation = dict(
        NONE='其他伤害',
        NORMAL_ATK='普通攻击',
        CHARGED_ATK='重击',
        PLUNGING_ATK='下落攻击',
        ELEM_SKILL='元素战技',
        ELEM_BURST='元素爆发',
        TRANS='剧变伤害'
    )

    def __init__(self, inter: Interpreter):
        super().__init__(inter)
        self.inter = inter
        self.start: int = inter.start
        self.end:  int = inter.end
        self.bias: int = inter.bias
        self.width1 = 0.0
        self.width2 = 0.0
        self.useful_attr: Dict[str, List[str]] = {}
        self.folder = inter.path.split('.')[0]
        self.author = inter.author
        self.find_end()
        self.find_useful_attr()

    @staticmethod
    def text_color(color):
        r, g, b = mcolors.to_rgb(color)
        return 'white' if r*g*b < 0.4 else 'dimgray'

    def find_end(self):
        if self.start <= 0 or self.end <= 0:
            start, end = 0, 0
            for name in self.inter.characters:
                for v in self.inter.record_dmg[name].values():
                    if not v:
                        continue
                    end = max(end, max(v)[0])
                    start = min(start, min(v)[0])
            action_list = sorted([e for e in self.inter.event_log
                                  if e.visible and e.type != EventType.CREATION])
            end = max(end, action_list[-1].time+action_list[-1].actiontime)
            start = min(start, action_list[0].time)
            self.start = start if self.start <= 0 else self.start
            self.end = end if self.end <= 0 else self.end
        dur = np.ceil((self.end-self.start)/60)
        self.width1 = 8 if dur <= 10 else dur*0.8
        self.width2 = 12 if dur <= 10 else dur*1.2

    def find_useful_attr(self):
        grad = Counter()
        elem = {}
        for num in self.inter.record_trees:
            grad += Counter(num.root.auto_grad())
            if num.type == BuffType.DMG:
                l = elem.setdefault(num.source, [])
                if num.elem_type not in l:
                    elem[num.source].append(num.elem_type)
        for k in grad:
            stat, name = k.split()[1], k.split()[2]
            if stat.endswith('PER') or stat.endswith('CONST'):
                stat = stat.split('_')[0]
            l = self.useful_attr.setdefault(name, [])
            if stat not in l:
                self.useful_attr[name].append(stat)
        for name, elements in elem.items():
            for e in elements:
                stat = e.name+'_DMG'
                self.useful_attr[name].append(stat)
        for name in self.inter.characters:
            if name not in self.useful_attr:
                self.useful_attr[name] = ['ATK', 'DEF', 'HP']
            else:
                self.useful_attr[name] = sorted(self.useful_attr[name])

    def char_info(self):
        fig, axs = plt.subplots(
            2, 2, sharex=True, sharey=True, figsize=(10, 10))
        chars = list(self.inter.characters.keys())
        index = 0
        bbox1 = dict(boxstyle='square', ec='black', fc='none')
        bbox2 = dict(boxstyle='round', ec='dimgray', fc='lightgray', alpha=0.8)
        bbox3 = dict(boxstyle='square', ec='silver', fc='silver', alpha=0.7)
        config1 = dict(size=10, ha='left', va='top', bbox=bbox1)
        config2 = dict(size=10, ha='left', va='top', bbox=bbox2)
        config3 = dict(size=8, ha='left', va='top', bbox=bbox3)
        for row in axs:
            for ax in row:
                ax.set_axis_off()
                try:
                    name = chars[index]
                except:
                    continue
                ax.text(0, 1, '角色:', **config1)
                bbox_i = dict(boxstyle='roundtooth',
                              ec=self.get_char_color(name),
                              fc=self.get_char_color(name))
                ax.text(0.4, 1, c_trans[name], size=10,
                        ha='left', va='top', bbox=bbox_i)
                ax.text(0, 0.92, '等级/命座/天赋:', **config1)
                c = self.inter.characters[name]
                ax.text(0.4, 0.92,
                        f'{c.base.lv} / {c.attr.cx_lv} / A:{c.attr.normatk_lv} / E:{c.attr.elemskill_lv} / Q:{c.attr.elemburst_lv}',
                        **config1)
                ax.text(0, 0.8, '武器:', **config1)
                w = self.inter.weapons[name]
                w_name = c_trans[w.name]
                ax.text(0.4, 0.8, w_name, **config2)
                ax.text(0, 0.72, '等级/精炼:', **config1)
                ax.text(0.4, 0.72, f'{w.lv} / {w.refine}', **config1)
                ax.text(0, 0.6, '圣遗物:', **config1)
                a = self.inter.artifacts[name]
                a_list = []
                if a.piece4 != SetType.NONE:
                    a_list.append(c_trans[a.piece4.name])
                else:
                    a_list.extend([c_trans[a_]
                                  for a_ in [a.piece2_1.name, a.piece2_2.name]])
                ax.text(0.2, 0.6, ' / '.join(a_list), **config2)
                ax.text(0, 0.52, '主词条:', **config1)
                ax.text(0.2, 0.52,
                        '/'.join([c_trans[ms]
                                 for ms in a.main[2:]]),
                        **config2)
                ax.text(0, 0.44, '副词条:', **config1)
                for i in range(5):
                    ax.text(0.2*(i+1), 0.44,
                            f'{c_trans[a.subs[2*i]]:<4}:{a.sub[2*i]:<3}',
                            **config3)
                    ax.text(0.2*(i+1), 0.38,
                            f'{c_trans[a.subs[2*i+1]]:<4}:{a.sub[2*i+1]:<3}',
                            **config3)
                ax.text(0, 0.32, '面板:', **config1)
                attr = self.inter.record_attr[name]
                attr_keys = ['HP', 'ATK', 'DEF',
                             'CRIT_RATE', 'CRIT_DMG', 'ER', 'EM']
                attrs = []
                for k in attr_keys:
                    attrs.append(attr[k][0][1])
                ax.text(0.25, 0.32, f'生命:{attrs[0]:.0f}', **config2)
                ax.text(0.5, 0.32, f'攻击:{attrs[1]:.0f}', **config2)
                ax.text(0.75, 0.32, f'防御:{attrs[2]:.0f}', **config2)
                ax.text(0.0, 0.24, f'暴击:{attrs[3]:.1%}', **config2)
                ax.text(0.25, 0.24, f'暴伤:{attrs[4]:.1%}', **config2)
                ax.text(0.50, 0.24, f'充能:{attrs[5]:.1%}', **config2)
                ax.text(0.75, 0.24, f'精通:{attrs[6]:.0f}', **config2)
                elem = ElementType(c.base.element).name
                elem_k = f'{elem}_DMG'
                e_dmg = attr[elem_k][0][1]
                ax.text(0, 0.16,
                        f'{c_trans[elem_k]}:{e_dmg:.1%}',
                        **config2)
                if 'PHYSICAL_DMG' in self.useful_attr[name]:
                    p_dmg = attr['PHYSICAL_DMG'][0][1]
                    ax.text(0.5, 0.16, f'物理伤害:{p_dmg:.1%}', **config2)
                index += 1
        fig.suptitle('角色详情')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\角色详情.jpg', dpi=300, format='jpg')
        plt.close()
        print('角色详情')

    def char_log(self, name: str):
        def draw_annotations(ax: plt.Axes, lim: Tuple, desc: List[Tuple], index: int):
            pre = [0]
            pre_flag = [True]
            for desc_i in desc:
                if desc_i[0] >= self.end or desc_i[0] <= self.start:
                    continue
                flag = desc_i[1]
                close = True if flag == pre_flag[-1] and desc_i[0]-pre[-1] <= 60 \
                    else False
                x = desc_i[0]
                y = lim[1] if flag else lim[0]
                ha = 'right' if close else 'left'
                va = 'top' if flag else 'bottom'
                offset_x = 10 if close else -10
                if len(pre) >= 2 and desc_i[0]-pre[-2] <= 60:
                    offset_x += 10
                offset_y = -5 if flag else 5
                color1 = plt.colormaps['tab20'](2*index+1)
                color2 = plt.colormaps['tab20'](2*index) if flag else color1
                ax.plot([x, x], [lim[0], lim[1]],
                        c=color1, ls='-.', lw=0.7)
                ax.annotate(desc_i[2],
                            (x, y), xycoords='data',
                            xytext=(offset_x, offset_y),
                            textcoords='offset points',
                            fontsize=6, ha=ha, va=va, rotation=90, color=color2)
                pre.append(desc_i[0])
                pre_flag.append(flag)

        rows = sum([bool(self.inter.record_attr[name].get(a)) and
                    bool(self.inter.record_for_attr_buff[name].get(a))
                   for a in self.useful_attr[name]])
        height = rows*3
        if not rows:
            return
        fig = plt.figure(figsize=(self.width1, height+1))
        gs = fig.add_gridspec(rows, hspace=0.06)
        axs = gs.subplots(sharex=True)
        title = f'面板记录-{c_trans[name]}'
        fig.suptitle(title)
        ax_index = 0
        for attr in self.useful_attr[name]:
            line = self.inter.record_attr[name].get(attr)
            desc = self.inter.record_for_attr_buff[name].get(attr)
            if not line or not desc:
                continue
            ax: plt.Axes = axs[ax_index] if rows > 1 else axs
            data = []
            for d in line:
                if d[0] >= self.end or d[0] < self.start:
                    continue
                if not data or d != data[-1]:
                    data.append(d)
            x, y = zip(*data)
            times = np.array(x)
            attrs = np.array(y)
            a_max, a_min = attrs.max(), attrs.min()
            label = c_trans[attr+'_CONST'] if attr in ['ATK', 'DEF', 'HP']\
                else c_trans[attr]
            color = plt.colormaps['tab20'](2*ax_index)
            ax.plot(times, attrs, color=color, label=label)
            if ax_index == 0:
                ax.text(1, 1, f'SSS@{self.author}',
                        fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                        ha='right', va='bottom')
            if a_max < 10:
                step = 0.1
            elif a_max < 10000:
                step = 100
            else:
                step = 1000
            ticks = np.arange(np.floor_divide(a_min, step)*step,
                              np.floor_divide(a_max, step)*step+2*step, step)
            if a_max < 10:
                labels = [f'{t:.0%}' for t in ticks]
            else:
                labels = [f'{t:.0f}' for t in ticks]
            if desc:
                draw_annotations(ax, (ticks.min(), ticks.max()),
                                 desc, ax_index)
            ax.legend(loc='upper left')
            ax.set_ylim(bottom=ticks.min(), top=ticks.max())
            ax.set_xlim(self.start, self.end)
            ax.set_yticks(ticks, labels=labels)
            if ax_index == rows-1:
                ax.set_xticks(range(self.start, self.end+1, 60),
                              labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
                ax.set_xlabel('时间(s)')
            ax.grid(True, 'both', alpha=0.6, ls='--')
            ax_index += 1
        plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
        plt.close()
        print(title)

    def damage_one(self, name: str, interval: int = 60):
        markers = dict(
            NONE='H',
            NORMAL_ATK='^',
            CHARGED_ATK='D',
            PLUNGING_ATK='X',
            ELEM_SKILL='o',
            ELEM_BURST='s',
            TRANS='p'
        )
        dmg_sum = [0]*100
        for k, v in self.inter.record_dmg[name].items():
            if not v:
                continue
            for t, d in v:
                t -= self.start
                if t < 0 or t > self.end-self.start:
                    continue
                dmg_sum[int(t/interval)] += (60*d/interval)
        fig, ax = plt.subplots(figsize=(self.width1, 8))
        char_color = self.get_char_color(name)
        flag = False
        for k, v in self.inter.record_dmg[name].items():
            if not v:
                continue
            else:
                flag = True
            x, y = zip(*v)
            times = np.array(x)
            damages = np.array(y)
            color = self.get_skill_color((name, k))
            label = c_trans[name]+':'+self.damage_translation[k]
            markerline, stemlines, baseline = plt.stem(
                times, damages, label=label)
            markerline.set(color=color, marker=markers[k],
                           markersize=9, markeredgecolor='w',
                           markeredgewidth=1)
            stemlines.set(color=char_color, alpha=0.9, linewidth=2.5)
            baseline.set(color='w')
        if not flag:
            plt.close()
            return
        plt.bar(np.arange(self.start, self.start+100*interval, interval),
                dmg_sum, width=60, align='edge', alpha=0.6, color=char_color)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.legend(loc='upper left', fontsize='large')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('伤害值')
        plt.xlabel('时间(s)')
        title = f'伤害记录-{c_trans[name]}'
        plt.title(title)
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
        plt.close()
        print(title)

    def damage_stack(self):
        fig, ax = plt.subplots(figsize=(self.width1, 8))
        sum_by_char = dict.fromkeys(self.inter.record_dmg.keys())
        for name in self.inter.record_dmg:
            dmg_sum = np.zeros(self.end+1)
            for v in self.inter.record_dmg[name].values():
                for t, d in v:
                    if t < self.start or t > self.end:
                        continue
                    dmg_sum[t] += d
            sum_by_char[name] = np.add.accumulate(dmg_sum)
        colors = [self.get_char_color(n) for n in sum_by_char.keys()]
        labels = [c_trans[n] for n in sum_by_char.keys()]
        plt.stackplot(np.arange(self.end+1),
                      sum_by_char.values(),
                      labels=labels,
                      colors=colors, alpha=0.9)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.legend(loc='upper left')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('伤害值')
        plt.xlabel('时间(s)')
        plt.title('累积伤害值')
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\累积伤害值.jpg', dpi=300, format='jpg')
        plt.close()
        print('累积伤害值')

    def damage_stackbar(self, interval: int = 60):
        fig, ax = plt.subplots(figsize=(self.width1, 8))
        bottom_sum = np.zeros(100)
        for name in self.inter.record_dmg.keys():
            dmg_sum = np.zeros(100)
            for v in self.inter.record_dmg[name].values():
                if not v:
                    continue
                for t, d in v:
                    t -= self.start
                    if t < 0 or t > self.end-self.start:
                        continue
                    dmg_sum[int(t/interval)] += (60*d/interval)
            color = self.get_char_color(name)
            label = c_trans[name]
            plt.bar(np.arange(self.start, self.start+100*interval, interval),
                    dmg_sum, width=60, edgecolor='w', bottom=bottom_sum,
                    align='edge', alpha=0.9, label=label, color=color)
            bottom_sum += dmg_sum
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.legend(loc='upper left')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('伤害值')
        plt.xlabel('时间(s)')
        plt.title('伤害占比柱状图')
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\伤害占比柱状图.jpg', dpi=300, format='jpg')
        plt.close()
        print('伤害占比柱状图')

    def damage_smooth(self):
        sigma = 1/(np.sqrt(2*np.pi))

        def norm(x, nu):
            return (np.exp(-np.power((x-nu)/60, 2)/(2*np.power(sigma, 2))))

        markers = dict(
            NONE='H',
            NORMAL_ATK='^',
            CHARGED_ATK='D',
            PLUNGING_ATK='X',
            ELEM_SKILL='o',
            ELEM_BURST='s',
            TRANS='p'
        )

        dmgs = []
        for name in self.inter.record_dmg:
            fig, ax = plt.subplots(figsize=(self.width1, 8))
            dmg = np.zeros(self.end-self.start+1)
            char_color = self.get_char_color(name)
            for k, v in self.inter.record_dmg[name].items():
                if not v:
                    continue
                for t, d in v:
                    if t < self.start:
                        continue
                    for i in range(-90, 90+1):
                        if t+i > self.end or t+i < self.start:
                            continue
                        dmg[t+i-self.start] += d*norm(t+i, t)
                x, y = zip(*v)
                times = np.array(x)
                damages = np.array(y)
                color = self.get_skill_color((name, k))
                label = c_trans[name] + \
                    ':'+self.damage_translation[k]
                markerline, stemlines, baseline = plt.stem(
                    times, damages, label=label)
                markerline.set(color=color, marker=markers[k],
                               markersize=9, markeredgecolor='w',
                               markeredgewidth=1)
                stemlines.set(color=char_color, alpha=0.9, linewidth=2.5)
                baseline.set(color='w')
            plt.fill_between(np.arange(self.start, self.end+1), dmg,
                             color=char_color, alpha=0.8)
            plt.text(1, 1, f'SSS@{self.author}',
                     fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                     ha='right', va='bottom')
            plt.legend(loc='upper left', fontsize='large')
            plt.ylim(bottom=0)
            plt.xlim(self.start, self.end)
            plt.xticks(range(self.start, self.end+1, 60),
                       labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
            plt.ylabel('伤害值')
            plt.xlabel('时间(s)')
            title = f'伤害记录(平滑)-{c_trans[name]}'
            plt.title(title)
            plt.grid(True, 'both', alpha=0.6, ls='--')
            plt.tight_layout()
            plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
            dmgs.append(dmg)
            print(title)

        fig, ax = plt.subplots(figsize=(self.width1, 8))
        colors = [self.get_char_color(n) for n in self.inter.record_dmg.keys()]
        labels = [c_trans[n] for n in self.inter.record_dmg.keys()]
        plt.stackplot(range(self.start, self.end+1),
                      dmgs, labels=labels,
                      colors=colors, alpha=0.9)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.legend(loc='upper left')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('伤害值')
        plt.xlabel('时间(s)')
        plt.title('伤害占比图(平滑)')
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\伤害占比图(平滑).jpg', dpi=300, format='jpg')
        print('伤害占比图(平滑)')

        fig, ax = plt.subplots(figsize=(self.width1, 8))
        sum_by_char = []
        for i, name in enumerate(self.inter.record_dmg.keys()):
            sum_by_char.append(np.add.accumulate(dmgs[i]))
        plt.stackplot(np.arange(self.start, self.end+1),
                      sum_by_char, labels=labels,
                      colors=colors, alpha=0.9)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.legend(loc='upper left')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('伤害值')
        plt.xlabel('时间(s)')
        plt.title('累积伤害值(平滑)')
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\累积伤害值(平滑).jpg', dpi=300, format='jpg')
        plt.close()
        print('累积伤害值(平滑)')

    def damage_pie(self):
        data = {}
        for char_name, dmgs in self.inter.record_dmg.items():
            data[char_name] = {}
            for types, log in dmgs.items():
                type_sum = sum([i[1] for i in log
                                if self.start <= i[0] <= self.end])
                if type_sum > 0:
                    data[char_name][types] = type_sum
        outer_val = [sum(c.values()) for c in data.values()]
        inner_val = [d for c in data.values() for d in c.values()]
        inner_name = [c_trans[k]+':'+self.damage_translation[types]
                      for k, n in data.items()
                      for types in n.keys()]
        outer_colors = [self.get_char_color(n) for n in data.keys()]
        inner_colors = [self.get_skill_color((k, ty))
                        for k, n in data.items() for ty in n.keys()]
        dmg_total = sum(outer_val)
        dps_total = 60*dmg_total/(self.end-self.start)

        def func(pct, val):
            absolute = int(np.round(pct/100.*np.sum(val)))
            return "{:.1f}%\n({:d})".format(pct, absolute) if pct >= 2.75 else ''

        fig, ax = plt.subplots(figsize=(10, 10))
        size = 0.3
        wedges, texts, autotexts = \
            ax.pie(outer_val, radius=1, colors=outer_colors,
                   autopct=lambda pct: func(pct, inner_val),
                   pctdistance=0.8,
                   wedgeprops=dict(width=size, edgecolor='w'),
                   textprops=dict(color="dimgray", size='large', weight='heavy'))
        wedges2, texts2, autotexts2 = \
            ax.pie(inner_val, radius=1-size, colors=inner_colors,
                   autopct=lambda pct: func(pct, inner_val),
                   pctdistance=0.8,
                   wedgeprops=dict(width=size, edgecolor='w'),
                   textprops=dict(color="dimgray", size='medium', weight='heavy'))
        ax.legend(wedges2, inner_name, loc='upper left')
        ax.set(aspect="equal", title='伤害饼图')
        plt.text(0.5, 1, f'总伤害={dmg_total:.0f}\nDPS={dps_total:.0f}',
                 fontsize=15, color='black', transform=ax.transAxes,
                 ha='center', va='top')
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\伤害饼图.jpg', dpi=500, format='jpg')
        plt.close()
        print('伤害饼图')

    def heal_one(self, name: str, interval: int = 60):
        line = self.inter.record_heal[name]
        if not line:
            return
        fig, ax = plt.subplots(figsize=(self.width1, 8))
        heal_sum = [0]*100
        for t, d in line:
            t -= self.start
            if t < 0 or t > self.end-self.start:
                continue
            heal_sum[int(t/interval)] += (60*d/interval)
        x, y = zip(*line)
        times = np.array(x)
        heals = np.array(y)
        color = self.get_char_color(name)
        markerline, stemlines, baseline = plt.stem(
            times, heals, label=name+'.heal')
        markerline.set(color=color, marker='o',
                       markersize=9, markeredgecolor='w',
                       markeredgewidth=1)
        stemlines.set(color=color, alpha=0.8, linewidth=2)
        baseline.set(color='w')
        plt.bar(np.arange(self.start, self.start+100*interval, interval),
                heal_sum, width=60, align='edge', alpha=0.6, color=color)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('治疗值')
        plt.xlabel('时间(s)')
        title = f'受治疗记录-{c_trans[name]}'
        plt.title(title)
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
        plt.close()
        print(title)

    def shield_one(self, name: str):
        line = self.inter.record_shield[name]
        if not line:
            return
        fig, ax = plt.subplots(figsize=(self.width1, 8))
        for start, end, sh in line:
            plt.fill_between([start, end], [0, 0], [sh, sh],
                             color=self.get_char_color(name), alpha=0.8)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.ylim(bottom=0)
        plt.xlim(self.start, self.end)
        plt.xticks(range(self.start, self.end+1, 60),
                   labels=[f'{x/60:.0f}' for x in np.arange(self.start, self.end+1, 60)-self.bias])
        plt.ylabel('盾值')
        plt.xlabel('时间(s)')
        title = f'盾量记录-{c_trans[name]}'
        plt.title(title)
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
        plt.close()
        print(title)

    def actions(self):
        action_list = sorted([e for e in self.inter.event_log
                              if e.visible and e.type != EventType.CREATION])
        fig, ax = plt.subplots(figsize=(self.width2, 10))

        stage_list: List[Tuple[str, int, int]] = []
        record = sorted(self.inter.record_stage.items())
        for i in range(len(record)-1):
            stage_list.append((record[i][1], record[i][0], record[i+1][0]-1))
        stage_list.append((record[-1][1], record[-1][0], self.end))
        for record in stage_list:
            facecolor = self.get_char_color(record[0])
            textcolor = self.text_color(facecolor)
            rect = ax.barh('站场', record[2]-record[1], left=record[1],
                           color=facecolor, height=0.6, edgecolor='w')
            ax.bar_label(rect, labels=[c_trans[record[0]]], size='x-large',
                         weight='heavy', label_type='center', color=textcolor)

        for event in action_list:
            facecolor = self.get_action_color(event)
            textcolor = self.text_color(facecolor)
            rowname = c_trans[event.source]+':'+event.family
            label = event.name
            if event.cooltime > 0:
                cd_rect = ax.barh(rowname, event.cooltime, left=event.time-event.actiontime,
                                  height=0.4, color='lightgray', alpha=0.5)
            rect = ax.barh(rowname, event.actiontime, left=event.time-event.actiontime,
                           label=rowname, color=facecolor,
                           height=0.7, edgecolor='w')
            ax.bar_label(rect, labels=[label], weight='heavy', size='x-large',
                         label_type='center', color=textcolor)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        dur_sec = int(np.ceil((self.end-self.start)/60))
        ax.set_xlim(self.start, self.end)
        ax.set_axisbelow(True)
        ax.invert_yaxis()
        ax.xaxis.grid(linestyle=':', alpha=0.5, which='both')
        xt = np.linspace(self.start, self.start+60*dur_sec, 2*dur_sec+1)[::2]
        lb = [f'{x:.0f}' for x in (xt-self.bias)/60]
        ax.set_xticks(xt, labels=lb)
        xt_minor = np.linspace(self.start, self.start+60*dur_sec, 2*dur_sec+1)
        ax.set_xticks(xt_minor, minor=True)
        plt.yticks(size='x-large')
        plt.xlabel('时间(s)')
        plt.title('动作甘特图')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\动作甘特图.jpg', dpi=500, format='jpg')
        plt.close()
        print('动作甘特图')

    def buffs(self):
        buff_list = sorted([b for b in self.inter.buff_log if b.visible])
        create_list = [e for e in self.inter.event_log
                       if e.visible and e.type == EventType.CREATION]

        fig, ax = plt.subplots(figsize=(self.width2, 10))

        yt, ylb = ['站场'], ['站场']
        stage_list: List[Tuple[str, int, int]] = []
        record = sorted(self.inter.record_stage.items())
        for i in range(len(record)-1):
            stage_list.append((record[i][1], record[i][0], record[i+1][0]-1))
        stage_list.append((record[-1][1], record[-1][0], self.end))
        for record in stage_list:
            facecolor = self.get_char_color(record[0])
            textcolor = self.text_color(facecolor)
            rect = ax.barh('站场', record[2]-record[1], left=record[1],
                           color=facecolor, height=0.6, edgecolor='w')
            ax.bar_label(rect, labels=[c_trans[record[0]]], size='x-large',
                         weight='heavy', label_type='center', color=textcolor)

        while buff_list:
            buff = buff_list.pop(0)
            facecolor = self.get_buff_color(buff)
            textcolor = self.text_color(facecolor)
            # family = buff.family if buff.family not in c_trans \
            #     else c_trans[buff.family]
            src = c_trans[buff.source]
            rowname = f'{buff.source}:{buff.family}:{buff.name}'
            rowlabel = f'{src}:{buff.name}'
            yt.append(rowname)
            ylb.append(rowlabel)
            label = buff.desc
            dur = buff.dur if buff.end < self.end or buff.begin > self.end else self.end-buff.begin
            rect = ax.barh(rowname, dur, left=buff.begin,
                           color=facecolor, edgecolor='w', height=0.7)
            if buff.dur > 120:
                ax.bar_label(rect, labels=[label], size='large',
                             label_type='center', color=textcolor)
            elif buff.dur > 60:
                ax.bar_label(rect, labels=[label], size='small',
                             label_type='center', color=textcolor)
            else:
                ax.bar_label(rect, labels=[label], size='xx-small',
                             label_type='center', color=textcolor)
        while create_list:
            create = create_list.pop(0)
            facecolor = self.get_char_color(create.source)
            textcolor = self.text_color(facecolor)
            rowname = c_trans[create.name.split('->')[0]]\
                + '->' + create.name.split('->')[1]
            yt.append(rowname)
            ylb.append(rowname)
            label = create.desc
            dur = create.dur if create.endtime < self.end or create.time > self.end else self.end-create.time
            rect = ax.barh(rowname, dur, left=create.time,
                           color=facecolor, edgecolor='w', height=0.7)
            ax.bar_label(rect, labels=[label], size='large',
                         label_type='center', color=textcolor)
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        dur_sec = int(np.ceil((self.end-self.start)/60))
        ax.set_xlim(self.start, self.end)
        ax.set_axisbelow(True)
        ax.set_yticks(yt, ylb)
        ax.invert_yaxis()
        ax.xaxis.grid(linestyle=':', alpha=0.5, which='both')
        xt = np.linspace(self.start, self.start+60*dur_sec, 2*dur_sec+1)[::2]
        lb = [f'{x:.0f}' for x in (xt-self.bias)/60]
        ax.set_xticks(xt, labels=lb)
        xt_minor = np.linspace(self.start, self.start+60*dur_sec, 2*dur_sec+1)
        ax.set_xticks(xt_minor, minor=True)
        plt.yticks(size='large')
        plt.xlabel('时间(s)')
        plt.title('buff甘特图')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\\buff甘特图.jpg', dpi=500, format='jpg')
        plt.close()
        print('buff甘特图')

    def sim(self, n: int = 10000):
        fig, ax = plt.subplots(figsize=(10, 10))
        data = np.array(self.inter.record_for_sim).T
        s = sum(data[0])
        cr = data[1]
        cd = data[0]*data[2]
        test = np.random.rand(n, len(cr))
        result = []
        for t in test:
            r = np.matmul(t < cr, cd)
            result.append(r)
        hist, bin_edge = np.histogram(result, bins=20, density=True)
        diff = np.diff(bin_edge)[0]
        bin_edge += s
        plt.hist(bin_edge[:-1], bin_edge, weights=hist *
                 diff, rwidth=0.95, alpha=0.7)
        ax.yaxis.set_major_formatter('{x:1.1%}')
        plt.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax.transAxes,
                 ha='right', va='bottom')
        plt.xticks(bin_edge, size='small',
                   labels=[f'{b/10000:.1f}W\n({60*b/10000/(self.end-self.start):.2f}W)' for b in bin_edge])
        plt.ylim(bottom=0)
        plt.ylabel('概率')
        plt.xlabel('伤害值')
        title = f'模拟结果-{n}次'
        plt.title(title)
        plt.grid(True, 'both', alpha=0.6, ls='--')
        plt.tight_layout()
        plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
        plt.close()
        print(title)

    def components(self, name: str):
        fig, axs = plt.subplots(ncols=2, figsize=(10, 5))
        aparts = dict(non=0, amp=0)  # components of amplify
        bparts = dict(self=0)        # components of basic
        flag = False
        for num in self.inter.record_trees:
            if num.source != name or num.type == BuffType.ELEMENT:
                continue
            else:
                flag = True
            v = num.value
            base = num.root.find('Basic Multiplier')
            try:
                a = num.root.find('Amplifying Multiplier').value
                aparts['amp'] += v/a
            except:
                aparts['non'] += v
            for child in base.child:
                if child.key == 'Stat x Scaler':
                    bparts['self'] += v*(child.value/base.value)
                else:
                    bparts.setdefault(child.key, 0)
                    bparts[child.key] += v*(child.value/base.value)
        if not flag:
            plt.close()
            return
        cm = plt.colormaps['tab10']
        c1 = [cm(i) for i in range(len(aparts))]
        c2 = [cm(i) for i in range(len(bparts))]

        def func(pct, val):
            absolute = int(np.round(pct/100.*sum(val.values())))
            return "{:.1f}%\n({:d})".format(pct, absolute) if pct > 0 else ''

        dic = c_trans.copy()
        dic.update(self.damage_translation)
        dic.update(dict(self='基础伤害', non='非增幅', amp='增幅',
                        Catalyze='激化', Bonus='增益',
                        Passive='被动', Passive1='被动1', Passive2='被动2'))

        def trans(names):
            result = []
            for n in names:
                s = [dic[i] if i in dic else i for i in n.split()]
                result.append(''.join(s))
            return result

        ax1: plt.Axes = axs[0]
        wedges, texts, autotexts = \
            ax1.pie(bparts.values(), radius=1, colors=c2,
                    autopct=lambda pct: func(pct, bparts),
                    pctdistance=0.75,
                    wedgeprops=dict(width=0.5, edgecolor='w'),
                    textprops=dict(color="w", size='large', weight='heavy'))
        ax1.legend(wedges, trans(bparts.keys()), loc='upper left')
        ax1.set(aspect="equal", title='基础伤害组成')

        ax2: plt.Axes = axs[1]
        wedges, texts, autotexts = \
            ax2.pie(aparts.values(), radius=1, colors=c1,
                    autopct=lambda pct: func(pct, aparts),
                    pctdistance=0.75,
                    wedgeprops=dict(width=0.5, edgecolor='w'),
                    textprops=dict(color="w", size='large', weight='heavy'))
        ax2.legend(wedges, trans(aparts.keys()), loc='upper left')
        ax2.set(aspect="equal", title='增幅伤害组成')
        ax2.text(1, 1, f'SSS@{self.author}',
                 fontsize=15, color='gray', alpha=0.5, transform=ax2.transAxes,
                 ha='right', va='bottom')
        title = f'伤害组成-{c_trans[name]}'
        fig.suptitle(title)
        plt.tight_layout()
        plt.savefig(f'{self.folder}\{title}.jpg', dpi=300, format='jpg')
        plt.close()
        print(title)

    def work(self):
        self.char_info()
        self.damage_pie()
        self.actions()
        self.buffs()
        for char in self.inter.characters:
            self.char_log(char)
            self.damage_one(char)
            # self.heal_one(char)
            # self.shield_one(char)
            self.components(char)
        self.damage_stack()
        self.damage_stackbar()
        self.damage_smooth()
        self.sim()


class ExcelWriter(object):
    type_translation = dict(
        SWITCH='切换人物',
        DAMAGE='造成伤害',
        ELEMENT='造成剧变伤害',
        HEALTH='造成治疗',
        SHIELD='造成护盾',
        BUFFON='buff生效',
        BUFFOFF='buff结束',
        CREATION='创造生成物'
    )

    damage_translation = dict(
        NONE='其他伤害',
        NORMAL_ATK='普通攻击',
        CHARGED_ATK='重击',
        PLUNGING_ATK='下落攻击',
        ELEM_SKILL='元素战技',
        ELEM_BURST='元素爆发',
        TRANS='剧变伤害'
    )

    def __init__(self, inter: Interpreter):
        self.inter = inter
        self.start: int = inter.start
        self.end:  int = inter.end
        self.bias: int = inter.bias
        self.folder = inter.path.split('.')[0]

    def write_log(self):
        with open(f'{self.folder}\\log.csv', 'w', encoding='utf-8-sig', newline='') as file:
            fieldnames = ['事件类型', '发起者', '发生时间', '事件名', '事件简介']
            writer = csv.writer(file)
            writer.writerow(fieldnames)
            for l in self.inter.log:
                l[1] = c_trans.get(l[1], l[1])
                l[2] /= 60
                writer.writerow(l)

    def write_numeric(self):
        with open(f'{self.folder}\\numeric.csv', 'w', encoding='utf-8-sig', newline='') as file:
            fieldnames = ['数值类型', '时间', '发起者', '数值',
                          '暴击', '非暴击', '伤害元素', '伤害类型', '反应类型',
                          '基础区', '增伤区', '暴击区', '抗性区', '防御区', '反应区',
                          '攻击/剧级区', '倍率/剧系区',
                          'buff', '计算式']
            writer = csv.writer(file)
            writer.writerow(fieldnames)
            for num in self.inter.record_trees:
                l = []
                l.append(num.type.name)
                l.append(num.time/60)
                l.append(c_trans[num.source])
                l.append(num.root.value)
                if num.root.value <= 0:
                    continue
                if num.type == BuffType.DMG:
                    dmg, cr, cd = num.for_sim()
                    if cr != 0:
                        l.extend([round(dmg*(1+cd)), round(dmg)])
                    else:
                        l.extend([round(dmg), round(dmg)])
                    l.append(c_trans[num.elem_type.name])
                    l.append(self.damage_translation[num.damage_type.name])
                    l.append(c_trans[num.react_type.name])
                    n = num.root.find('Basic Multiplier')
                    m1 = n.value
                    m2 = num.root.find('Bonus Multiplier').value
                    m3 = num.root.find('Critical Multiplier').value
                    m4 = num.root.find('Resistance Multiplier').value
                    m5 = num.root.find('Defence Multiplier').value
                    try:
                        m6 = num.root.find('Amplifying Multiplier').value
                    except:
                        m6 = 1
                    m7 = n.find('Stat x Scaler').child[1].value
                    m8 = n.find('Stat x Scaler').child[0].value
                    l.extend([m1, m2, m3, m4, m5, m6, m7, m8])
                elif num.type == BuffType.ELEMENT:
                    l.extend(['', ''])
                    l.append(c_trans[num.elem_type.name])
                    l.append('')
                    l.append(c_trans[num.react_type.name])
                    n = num.root.find('Basic Multiplier')
                    m1 = n.value
                    m4 = num.root.find('Resistance Multiplier').value
                    try:
                        m6 = num.root.find('Transformative Multiplier').value
                    except:
                        m6 = 1
                    m7 = n.find('Level Multiplier').value
                    m8 = n.find('ReactType Multiplier').value
                    m2, m3, m5 = '', '', ''
                    l.extend([m1, m2, m3, m4, m5, m6, m7, m8])
                else:
                    l.extend(['', '', '', '', ''])
                    m1 = num.root.find('Basic Multiplier').value
                    m2 = num.root.find('Bonus Multiplier').value
                    m3, m4, m5, m6, m7, m8 = '', '', '', '', '', ''
                    l.extend([m1, m2, m3, m4, m5, m6, m7, m8])
                l.append(' | '.join(num.buffed))
                l.append(num.root.formula())
                writer.writerow(l)

    def write_grad(self):
        art_data = dict(
            CRIT_RATE=0.389,
            CRIT_DMG=0.777,
            HP_PER=0.583,
            ATK_PER=0.583,
            DEF_PER=0.729,
            HP_CONST=29.875,
            ATK_CONST=1.945,
            DEF_CONST=2.315,
            ER=0.648,
            EM=2.331
        )
        with open(f'{self.folder}\\gradient.csv', 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            grad = Counter()
            chars = list(self.inter.characters.keys())
            stat = ['ATK_PER', 'ATK_CONST', 'DEF_PER', 'DEF_CONST',
                    'HP_PER', 'HP_CONST', 'EM', 'ER', 'CRIT_RATE', 'CRIT_DMG']
            title1 = ['1平均词条']+[c_trans[c] for c in chars]
            title2 = ['1单位词条']+[c_trans[c] for c in chars]
            for num in self.inter.record_trees:
                if num.type in [BuffType.SHIELD, BuffType.HEALTH]:
                    continue
                grad += Counter(num.root.auto_grad())
            writer.writerow(title1)
            for s in stat:
                l = [c_trans[s]]
                for c in chars:
                    k = ' '.join(['SubStat', s, c])
                    v = grad.get(k, 0)
                    l.append(v*art_data[s]*8.5)
                writer.writerow(l)
            writer.writerow(['副词条带来的提升(1平均=8.5单位)']+['' for c in chars])
            writer.writerow(title2)
            for s in stat:
                l = [c_trans[s]]
                for c in chars:
                    k = ' '.join(['SubStat', s, c])
                    v = grad.get(k, 0)
                    l.append(v*art_data[s])
                writer.writerow(l)

    def write_tree(self):
        trees = []
        for num in self.inter.record_trees:
            t = {}
            t['type'] = num.type.name
            t['source'] = num.source
            t['depend'] = num.depend
            t['buffed'] = num.buffed
            t['time'] = num.time
            t['root'] = repr(num.root)
            if num.type == BuffType.DMG or num.type == BuffType.ELEMENT:
                t['damage'] = num.damage_type.name
                t['elem'] = num.elem_type.name
                t['react'] = num.react_type.name
            elif num.type == BuffType.HEALTH:
                t['target'] = num.target
            trees.append(t)
        with open(f'{self.folder}\\tree.json', 'w', encoding='utf8') as f:
            json.dump(trees, f, skipkeys=True, indent=4, ensure_ascii=False)

    def write_sum(self):
        data = {}
        avg = {}
        for char_name, dmgs in self.inter.record_dmg.items():
            data[char_name] = {}
            avg[char_name] = {}
            for types, log in dmgs.items():
                type_sum = sum([i[1] for i in log
                                if self.start <= i[0] <= self.end])
                if type_sum > 0:
                    data[char_name][types] = type_sum
                    avg[char_name][types] = np.zeros(6)
        for num in self.inter.record_trees:
            if self.start > num.time or self.end < num.time:
                continue
            v = num.root.value
            if not v:
                continue
            if num.type == BuffType.DMG:
                per = v/data[num.source][num.damage_type.name]
                m1 = num.root.find('Basic Multiplier').value
                m2 = num.root.find('Bonus Multiplier').value
                m3 = num.root.find('Critical Multiplier').value
                m4 = num.root.find('Resistance Multiplier').value
                m5 = num.root.find('Defence Multiplier').value
                try:
                    m6 = num.root.find('Amplifying Multiplier').value
                except:
                    m6 = 1
                avg[num.source][num.damage_type.name] +=\
                    per*np.array([m1, m2, m3, m4, m5, m6])
            elif num.type == BuffType.ELEMENT:
                per = v/data[num.source][num.damage_type.name]
                m1 = num.root.find('Basic Multiplier').value
                m2, m3, m5 = 0, 0, 0
                m4 = num.root.find('Resistance Multiplier').value
                try:
                    m6 = num.root.find('Reaction Multiplier').value
                except:
                    m6 = 1
                avg[num.source][num.damage_type.name] +=\
                    per*np.array([m1, m2, m3, m4, m5, m6])
        with open(f'{self.folder}\\sum.csv', 'w', encoding='utf-8-sig', newline='') as file:
            fieldnames = ['发起者', '伤害类型', '数值和',
                          '基础区', '增伤区', '暴击区', '抗性区', '防御区', '反应区']
            writer = csv.writer(file)
            writer.writerow(fieldnames)
            for char_name, dmgs in data.items():
                for types in dmgs:
                    s = data[char_name][types]
                    a = avg[char_name][types]
                    c = c_trans[char_name]
                    t = self.damage_translation[types]
                    l = [c, t, s]+list(a)
                    writer.writerow(l)

    def write_merge(self):
        numerics = []
        for num in self.inter.record_trees:
            if num.type != BuffType.DMG and num.type != BuffType.ELEMENT:
                continue
            if not numerics:
                numerics.append(deepcopy(num))
                continue
            for merge in numerics:
                if num.type == BuffType.ELEMENT and merge.type == BuffType.ELEMENT:
                    if num.source == merge.source and \
                            num.react_type == merge.react_type and \
                            set(num.buffed) == set(merge.buffed) and \
                            len(num.root.child) == len(merge.root.child) and \
                            all([num.root.child[i+1] == merge.root.child[i+1] for i in range(len(num.root.child)-1)]):
                        merge.root.child[0].child.extend(num.root.child[0].child)
                        break
                elif num.type == BuffType.DMG and merge.type == BuffType.DMG:
                    if num.source == merge.source and \
                            num.elem_type == merge.elem_type and \
                            num.react_type == merge.react_type and \
                            set(num.buffed) == set(merge.buffed) and \
                            len(num.root.child) == len(merge.root.child) and \
                            all([num.root.child[i+1] == merge.root.child[i+1] for i in range(len(num.root.child)-1)]):
                        n0 = len(merge.root.child[0].child)
                        if len(num.root.child[0].child) == n0:
                            flag = False
                            for i in range(n0):
                                n1 = len(merge.root.child[0].child[i].child)
                                if len(num.root.child[0].child[i].child) == n1:
                                    flag = all([num.root.child[0].child[i].child[j+1] == merge.root.child[0].child[i].child[j+1]
                                                for j in range(n1-1)])
                                else:
                                    break
                            if flag:
                                for i in range(n0):
                                    merge.root.child[0].child[i].child[0].child.extend(
                                        num.root.child[0].child[i].child[0].child)
                                break
            else:
                numerics.append(deepcopy(num))
        merges = []
        for num in numerics:
            m = {}
            m['source'] = num.source
            m['type'] = num.damage_type.name
            m['formula'] = num.root.formula(merge=False)
            m['merged'] = num.root.formula(merge=True)
            merges.append(m)
        with open(f'{self.folder}\\merge.json', 'w', encoding='utf8') as f:
            json.dump(merges, f, skipkeys=True, indent=4, ensure_ascii=False)

    def work(self):
        self.write_log()
        self.write_numeric()
        self.write_grad()
        self.write_tree()
        self.write_sum()
        self.write_merge()


if __name__ == '__main__':
    import time
    a = Interpreter()
    a.read_file()
    t1 = time.perf_counter()
    a.main_loop()
    t2 = time.perf_counter()
    print(f'模拟用时: {t2-t1:.4f}s')

    t1 = time.perf_counter()
    b = Plotter(a)
    # b.work()
    t2 = time.perf_counter()
    print('start={}, end={}, bias={}'.format(b.start, b.end, b.bias))
    print(f'绘图用时: {t2-t1:.4f}s')

    t1 = time.perf_counter()
    c = ExcelWriter(a)
    c.work()
    t2 = time.perf_counter()
    print(f'数据汇总用时: {t2-t1:.4f}s')
    input('输入回车结束任务:')
