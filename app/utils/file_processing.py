import cropresize2
import uuid
from PIL import Image


def hash_filename(filename):
    _, _, suffix = filename.rpartition('.')
    return '{hash}.{suffix}'.format(hash=uuid.uuid4().hex, suffix=suffix)


def rsize(file_path, weight, height):
    img = cropresize2.crop_resize(
        Image.open(file_path), (int(weight), int(height)))
    return img
