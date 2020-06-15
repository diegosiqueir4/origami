import skimage
import math
import collections
import numpy as np
import PIL.Image
import shapely
import imghdr

from cached_property import cached_property
from pathlib import Path

from origami.core.math import resize_transform, to_shapely_matrix


class Annotations:
	def __init__(self, page, segmentation):
		self._page = page
		self._segmentation = segmentation

	@property
	def page(self):
		return self._page

	@property
	def segmentation(self):
		return self._segmentation

	@property
	def size(self):
		return self.segmentation.size

	@property
	def magnitude(self):
		w, h = self.size
		return math.sqrt(w * h)

	@property
	def scale(self):
		lw, lh = self.size
		pw, ph = self._page.size
		return math.sqrt(lw * lw + lh * lh) / math.sqrt(pw * pw + ph * ph)

	@cached_property
	def label_to_image_matrix(self):
		m = resize_transform(self.size, self._page.size)
		return to_shapely_matrix(m)

	def create_multi_class_contours(self, labels, c):
		data = c(labels)

		results = collections.defaultdict(list)
		matrix = self.label_to_image_matrix
		for prediction_class, shapes in data.items():
			for shape in shapes:
				if isinstance(shape, shapely.geometry.base.BaseGeometry):
					t_shape = shapely.affinity.affine_transform(shape, matrix)
				else:
					t_shape = shape.affine_transform(matrix)
				results[prediction_class].append(t_shape)

		return results


def _find_image_path(path):
	path = Path(path)
	if path.exists():
		return path
	else:
		# do not be picky about image extension type, e.g.
		# allow jp2 or png instead of jpg.
		candidates = []
		for candidate in path.parent.glob(path.stem + ".*"):
			if candidate.name.endswith(".jp2") or imghdr.what(candidate) is not None:
				candidates.append(candidate)
		if len(candidates) != 1:
			raise FileNotFoundError(path)
		return candidates[0]


class Page:
	def __init__(self, path):
		self._im = PIL.Image.open(str(_find_image_path(path))).convert("L")

	@property
	def size(self):
		return tuple(reversed(list(self.pixels.shape)[:2]))

	@property
	def image(self):
		return self._im

	@property
	def pixels(self):
		return np.array(self._im)

	@cached_property
	def grayscale(self):
		return skimage.color.rgb2gray(self.pixels)
