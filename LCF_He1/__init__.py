# -*- coding: utf-8 -*-
"""
Author   : Alexandre
Created  : 2021-06-09 10:21:17

Comments :
"""

from .metadata.gus import GusData
from .metadata.hev_fit import HevFitData
from .data.xenics import XenicsData

user_modules = [
    # metadata
    GusData,
    HevFitData,
    # data
    XenicsData,
]
