# -*- coding: utf-8 -*-
"""
Author   : Alexandre
Created  : 2021-04-21 15:38:07

Comments : Abstract classes for data handling
"""
# %% IMPORTS

# -- global
import cv2
import re
import numpy as np
import logging
from pathlib import Path


# -- local
from HAL.classes.data.abstract import AbstractCameraPictureData

# -- logger
logger = logging.getLogger(__name__)

# %% CLASS DEFINITION

# == MAIN CLASS, COMMON TO ABS AND FLUO


class XenicsData(AbstractCameraPictureData):
    """docstring for Dummy"""

    def __init__(self, path=Path(".")):
        super().__init__()

        # - general
        self.name = "Xenics (He2)"
        self.dimension = 2  # should be 1, 2 or 3
        self.path = path

        # - special for camera
        self.pixel_size = 6.45  # µm
        self.pixel_size_unit = "µm"
        self.magnification = 1
        self.default_display_scale = (0, 1)

        # - special for Xenics
        self.name_pattern = "^(im_)(\d+)(\.png)$"
        self.images_per_run = 2  # 3 for abs, 2 for fluo
        self.display_name_pattern = "run {}"

        # - data related
        x = self.pixel_size / self.magnification
        self.pixel_scale = (x, x)
        self.pixel_unit = (self.pixel_size_unit, self.pixel_size_unit)
        self.data = []

    def _get_image_number(self):
        """checks name format, and return image number (or -1 if did not work)"""
        # get name
        name = self.path.name

        # get number
        m = re.match(self.name_pattern, name)
        if m:
            number_str = m.groups()[1]
            return int(number_str)
        else:
            return -1

    def filter(self):
        """check whether path is compatible with extension / naming"""
        # get image number
        n = self._get_image_number()
        # _get_image_number returns -1 if the name does not match the expected pattern
        # moreover, we are looking for groups of  `images_per_run` images,
        # so we will only display images such that n % images_per_run == 0.
        # Since -1 % images_per_run does not satisfy this condition, we can wrap the two
        # tests into one ;). After writing this comment, I realize that what I gained
        # using this elegant way of filtering the image name was totally compensated
        # by the time it took me to write this comment
        return not n % self.images_per_run

    def getDisplayName(self):
        n = self._get_image_number()
        i_run = n // self.images_per_run
        return self.display_name_pattern.format(i_run)


# ==  CLASS FOR ABSORPTION IMAGING


class XenicsAbsData(XenicsData):
    """docstring for Dummy"""

    def __init__(self, path=Path(".")):
        super().__init__()

        # - general
        self.name = "Xenics (abs)"
        self.path = path
        self.images_per_run = 3

    def load(self):
        """loads data"""
        # - get image number
        n = self._get_image_number()
        # - generate images path
        image_paths = {}
        # laser on image = detected image
        image_paths["laser on"] = self.path
        # other images are n+1 and n+2
        # prepare substitution with regexp
        m = re.compile(self.name_pattern)
        sub_fmt = "\g<1>{}\g<3>"
        for i, name in enumerate(["laser off", "background"]):
            image_name = m.sub(sub_fmt.format(n + i + 1), self.path.name)
            image_paths[name] = self.path.with_name(image_name)
            if not image_paths[name].is_file():
                logger.warning(f"'{name}' image not found at {image_paths[name]}")
                return
        # - load  images (as 16bit array)
        image_data = {}
        for name, path in image_paths.items():
            data_in = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            # rotate to match former orientation
            data = np.rot90(data_in, -1)
            image_data[name] = data
        # - process to compute OD
        # differences
        abs_signal = image_data["laser on"] - image_data["background"]
        reference = image_data["laser off"] - image_data["background"]
        # replace zeros in reference by Nan to avoid errors in division
        reference = np.where(reference == 0, np.nan, reference)
        # divide
        optical_depth = -np.log(abs_signal / reference)
        # set OD to -1 if Nan
        # store
        self.data = optical_depth
