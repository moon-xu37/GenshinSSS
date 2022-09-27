from typing import List, Tuple, Dict
from .dtypes import SetType, ElementType
from data.std import std_data


class Artifact(object):
    subs = ['ATK_PER', 'ATK_CONST',
            'DEF_PER', 'DEF_CONST',
            'HP_PER', 'HP_CONST',
            'EM', 'ER',
            'CRIT_RATE', 'CRIT_DMG']

    positions = ['FLOWER', 'PLUME', 'SANDS', 'GOBLET', 'CIRCLET']

    def __init__(self, p1: str, p2: str, p3: str, main: List[str]):
        self.piece2_1: SetType = SetType[p1] if p1 else SetType.NONE
        self.piece2_2: SetType = SetType[p2] if p2 else SetType.NONE
        self.piece4:   SetType = SetType[p3] if p3 else SetType.NONE
        self.main: List[str] = main
        self.sub:  List[int] = [0]*10
        self.owner:  str = ''
        self.rarity: str = '5'  # TODO

    def set_owner(self, owner):
        self.owner = owner

    def set_rarity(self, rarity):
        if rarity == '4' or rarity == '5':
            self.rarity = rarity

    def use_std(self, std: str):
        if not self.owner or self.owner not in std_data[std]:
            self.sub = std_data[std]['default']
        else:
            self.sub = std_data[std][self.owner]

    @property
    def sub_value(self) -> List[Tuple[str, float]]:
        result: List[Tuple[str, float]] = []
        for i, s in enumerate(self.subs):
            unit = sub_stat_data[self.rarity][s][-1]/10
            result.append((s, self.sub[i]*unit))
        return result

    @property
    def main_value(self) -> List[Tuple[str, str, float]]:
        result: List[Tuple[str, str, float]] = []
        for i, s in enumerate(self.positions):
            k = self.main[i]
            if k in ['ANEMO_DMG', 'GEO_DMG', 'ELECTRO_DMG',
                     'HYDRO_DMG', 'PYRO_DMG', 'CRYO_DMG', 'DENDRO_DMG']:
                k = 'ELEM_DMG'
            unit = main_stat_data[self.rarity][k][-1]
            result.append((s, self.main[i], unit))
        return result

    @property
    def piece_effect(self) -> List[Tuple[str, str, int, str]]:
        result: List[Tuple[str, str, int, str]] = []
        t1 = artifact_piece2_data.get(self.piece2_1.name)
        t2 = artifact_piece2_data.get(self.piece2_2.name)
        if t1[0]:
            result.append(t1+(self.piece2_1.name,))
        if t2[0]:
            result.append(t2+(self.piece2_2.name,))
        return result


sub_stat_data: Dict[str, Dict[str, List[float]]] = \
    {
    "4": {
        "CRIT_RATE": [2.18, 2.49, 2.8, 3.11],
        "CRIT_DMG": [4.35, 4.97, 5.6, 6.22],
        "HP_PER": [3.26, 3.73, 4.2, 4.66],
        "ATK_PER": [3.26, 3.73, 4.2, 4.66],
        "DEF_PER": [4.08, 4.66, 5.25, 5.83],
        "HP_CONST": [167.3, 191.2, 215.1, 239.0],
        "ATK_CONST": [10.89, 12.45, 14.0, 15.56],
        "DEF_CONST": [12.96, 14.82, 16.67, 18.52],
        "ER": [3.63, 4.14, 4.66, 5.18],
        "EM": [13.06, 14.92, 16.79, 18.65]
    },
    "5": {
        "CRIT_RATE": [2.72, 3.11, 3.5, 3.89],
        "CRIT_DMG": [5.44, 6.22, 6.99, 7.77],
        "HP_PER": [4.08, 4.66, 5.25, 5.83],
        "ATK_PER": [4.08, 4.66, 5.25, 5.83],
        "DEF_PER": [5.1, 5.83, 6.56, 7.29],
        "HP_CONST": [209.13, 239.0, 268.88, 298.75],
        "ATK_CONST": [13.62, 15.56, 17.51, 19.45],
        "DEF_CONST": [16.2, 18.52, 20.83, 23.15],
        "ER": [4.53, 5.18, 5.83, 6.48],
        "EM": [16.32, 18.65, 20.98, 23.31]
    }
}

main_stat_data: Dict[str, Dict[str, List[float]]] = \
    {
    "4": {
        "CRIT_RATE": [
            4.2, 5.4, 6.6, 7.8, 9.0, 10.1, 11.3, 12.5, 13.7, 14.9, 16.1, 17.3, 18.5, 19.7, 20.8, 22.0, 23.2
        ],
        "CRIT_DMG": [
            8.4, 10.8, 13.1, 15.5, 17.9, 20.3, 22.7, 25.0, 27.4, 29.8, 32.2, 34.5, 36.9, 39.3, 41.7, 44.1, 46.4
        ],
        "HP_PER": [
            6.3, 8.1, 9.9, 11.6, 13.4, 15.2, 17.0, 18.8, 20.6, 22.3, 24.1, 25.9, 27.7, 29.5, 31.3, 33.0, 34.8
        ],
        "ATK_PER": [
            6.3, 8.1, 9.9, 11.6, 13.4, 15.2, 17.0, 18.8, 20.6, 22.3, 24.1, 25.9, 27.7, 29.5, 31.3, 33.0, 34.8
        ],
        "DEF_PER": [
            7.9, 10.1, 12.3, 14.6, 16.8, 19.0, 21.2, 23.5, 25.7, 27.9, 30.2, 32.4, 34.6, 36.8, 39.1, 41.3, 43.5
        ],
        "ATK_CONST": [42, 54, 66, 78, 90, 102, 113, 125, 137, 149, 161, 173, 185, 197, 209, 221, 232],
        "HP_CONST": [
            645, 828, 1011, 1194, 1377, 1559, 1742, 1925, 2108, 2291, 2474, 2657, 2839, 3022, 3205, 3388, 3571
        ],
        "ER": [7.0, 9.0, 11.0, 12.9, 14.9, 16.9, 18.9, 20.9, 22.8, 24.8, 26.8, 28.8, 30.8, 32.8, 34.7, 36.7, 38.7],
        "EM": [
            25.2, 32.3, 39.4, 46.6, 53.7, 60.8, 68.0, 75.1, 82.2, 89.4, 96.5, 103.6, 110.8, 117.9, 125.0, 132.2,
            139.3
        ],
        "HEAL_BONUS": [
            4.8, 6.2, 7.6, 9.0, 10.3, 11.7, 13.1, 14.4, 15.8, 17.2, 18.6, 19.9, 21.3, 22.7, 24.0, 25.4, 26.8
        ],
        "PHYSICAL_DMG": [
            7.9, 10.1, 12.3, 14.6, 16.8, 19.0, 21.2, 23.5, 25.7, 27.9, 30.2, 32.4, 34.6, 36.8, 39.1, 41.3, 43.5
        ],
        "ELEM_DMG": [
            6.3, 8.1, 9.9, 11.6, 13.4, 15.2, 17.0, 18.8, 20.6, 22.3, 24.1, 25.9, 27.7, 29.5, 31.3, 33.0, 34.8
        ]
    },
    "5": {
        "CRIT_RATE": [
            4.7, 6.0, 7.3, 8.6, 9.9, 11.3, 12.6, 13.9, 15.2, 16.6, 17.9, 19.2, 20.5, 21.8, 23.2, 24.5, 25.8, 27.1,
            28.4, 29.8, 31.1
        ],
        "CRIT_DMG": [
            9.3, 12.0, 14.6, 17.3, 19.9, 22.5, 25.2, 27.8, 30.5, 33.1, 35.7, 38.4, 41.0, 43.7, 46.3, 49.0, 51.6,
            54.2, 56.9, 59.5, 62.2
        ],
        "HP_PER": [
            7.0, 9.0, 11.0, 12.9, 14.9, 16.9, 18.9, 20.9, 22.8, 24.8, 26.8, 28.8, 30.8, 32.8, 34.7, 36.7, 38.7,
            40.7, 42.7, 44.6, 46.6
        ],
        "ATK_PER": [
            7.0, 9.0, 11.0, 12.9, 14.9, 16.9, 18.9, 20.9, 22.8, 24.8, 26.8, 28.8, 30.8, 32.8, 34.7, 36.7, 38.7,
            40.7, 42.7, 44.6, 46.6
        ],
        "DEF_PER": [
            8.7, 11.2, 13.7, 16.2, 18.6, 21.1, 23.6, 26.1, 28.6, 31.0, 33.5, 36.0, 38.5, 40.9, 43.4, 45.9, 48.4,
            50.8, 53.3, 55.8, 58.3
        ],
        "ATK_CONST": [
            47, 60, 73, 86, 100, 113, 126, 139, 152, 166, 179, 192, 205, 219, 232, 245, 258, 272, 285, 298, 311
        ],
        "HP_CONST": [
            717, 920, 1123, 1326, 1530, 1733, 1936, 2139, 2342, 2545, 2749, 2952, 3155, 3358, 3561, 3764, 3967,
            4171, 4374, 4577, 4780
        ],
        "ER": [
            7.8, 10.0, 12.2, 14.4, 16.6, 18.8, 21.0, 23.2, 25.4, 27.6, 29.8, 32.0, 34.2, 36.4, 38.6, 40.8, 43.0,
            45.2, 47.4, 49.6, 51.8
        ],
        "EM": [
            28.0, 35.9, 43.8, 51.8, 59.7, 67.6, 75.5, 83.5, 91.4, 99.3, 107.2, 115.2, 123.1, 131.0, 138.9, 146.9,
            154.8, 162.7, 170.6, 178.6, 186.5
        ],
        "HEAL_BONUS": [
            5.4, 6.9, 8.4, 10.0, 11.5, 13.0, 14.5, 16.1, 17.6, 19.1, 20.6, 22.1, 23.7, 25.2, 26.7, 28.2, 29.8, 31.3,
            32.8, 34.3, 35.9
        ],
        "PHYSICAL_DMG": [
            8.7, 11.2, 13.7, 16.2, 18.6, 21.1, 23.6, 26.1, 28.6, 31.0, 33.5, 36.0, 38.5, 40.9, 43.4, 45.9, 48.4,
            50.8, 53.3, 55.8, 58.3
        ],
        "ELEM_DMG": [
            7.0, 9.0, 11.0, 12.9, 14.9, 16.9, 18.9, 20.9, 22.8, 24.8, 26.8, 28.8, 30.8, 32.8, 34.7, 36.7, 38.7,
            40.7, 42.7, 44.6, 46.6
        ]
    }
}

artifact_piece2_data: Dict[str, Tuple[str, str, int]] = \
    {
        'NONE': ('', '', 0),
        'GLADIATORS_FINALE': ('ATK_PER', '%', 18),
        'WANDERERS_TROUPE': ('EM', '', 80),
        'BLOODSTAINED_CHIVALRY': ('PHYSICAL_DMG', '%', 25),
        'NOBLESSE_OBLIGE': ('', '', 0),
        'VIRIDESCENT_VENERER': ('ANEMO_DMG', '%', 15),
        'MAIDEN_BELOVED': ('HEAL_BONUS', '%', 15),
        'THUNDERSOOTHER': ('', '', 0),
        'THUNDERING_FURY': ('ELECTRO_DMG', '%', 15),
        'LAVAWALKER': ('', '', 0),
        'CRIMSON_WITCH_OF_FLAMES': ('PYRO_DMG', '%', 15),
        'ARCHAIC_PETRA': ('GEO_DMG', '%', 15),
        'RETRACING_BOLIDE': ('SHIELD_STRENGTH', '%', 35),
        'BLIZZARD_STRAYER': ('CRYO_DMG', '%', 15),
        'HEART_OF_DEPTH': ('HYDRO_DMG', '%', 15),
        'TENACITY_OF_THE_MILLELITH': ('HP_PER', '%', 20),
        'PALE_FLAME': ('PHYSICAL_DMG', '%', 25),
        'SHIMENAWAS_REMINISCENCE': ('ATK_PER', '%', 18),
        'EMBLEM_OF_SEVERED_FATE': ('ER', '%', 20),
        'OCEANHUED_CLAM': ('HEAL_BONUS', '%', 15),
        'HUSK_OF_OPULENT_DREAMS': ('DEF_PER', '%', 30),
        'VERMILLION_HEREAFTER': ('ATK_PER', '%', 18),
        'ECHOES_OF_AN_OFFERING': ('ATK_PER', '%', 18),
        'DEEPWOOD_MEMORIES': ('DENDRO_DMG', '%', 15),
        'GILDED_DREAMS': ('EM', '', 80),
}
