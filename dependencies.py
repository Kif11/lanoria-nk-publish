import nuke
import re
# import logging as log
from logger import Logger

import fileseq

reload(fileseq)

from pathlib import Path
from fileseq import FileSequence

log = Logger()

class LocalFile(object):
    """docstring for LocalFile"""

    def __init__(self, path):
        self.path = Path(path)
        self.version_patterns = [
            r'(v)(?P<version_number>[0-9]+)', # v001
            r'([A-Za-z]+)_(?P<version_number>[0-9]+)' # name_01
        ]

    @property
    def type(self):
        return self.__class__.__name__

    @property
    def base_name(self):
        n = self.path.stem
        return n

    @property
    def version(self):
        """
        Try to determine file version base on differnt regex paterns
        """
        for p in self.version_patterns:
            result = re.search(p, str(self.base_name))
            if result is not None:
                # log.debug('Regex version result: %s', result.group('version_number'))
                version = int(result.group('version_number'))
                return version

        return None

    def download(self):
        pass

class ImageSequence(LocalFile):
    """docstring for ImageSequence"""

    def __init__(self, path):
        super(self.__class__, self).__init__(path)
        self.path = Path(path)
        self.seq = FileSequence.findSequencesOnDisk(str(path.parent))[0]

    @property
    def base_name(self):
        n = self.seq.basename
        return n

class Image(LocalFile):
    """docstring for Image"""
    def __init__(self, path):
        super(self.__class__, self).__init__(path)
        self.path = Path(path)

class Geometry(LocalFile):
    """docstring for AlembicFile"""
    def __init__(self, path):
        super(self.__class__, self).__init__(path)

class Video(LocalFile):
    """docstring for AlembicFile"""
    def __init__(self, path):
        super(self.__class__, self).__init__(path)
        self.path = Path(path)

class NukeScript(LocalFile):
    """docstring for NukeScript"""
    def __init__(self, path):
        super(self.__class__, self).__init__(path)

def dependency_from_path(path):

    image_formats = ['.dpx', '.jpg', '.png', '.exr', '.psd']
    geo_formats = ['.fbx', '.abc', '.obj']
    video_formats = ['.mov', '.mp4']

    # Image Sequence
    result = re.search(r'%[0-9]+d', str(path))
    if result is not None:
        # This path is a sequence
        dep_object = ImageSequence(path)
        return dep_object

    # Image
    if path.suffix in image_formats:
        dep_object = Image(path)
        return dep_object

    # Geometry
    if path.suffix in geo_formats:
        dep_object = Geometry(path)
        return dep_object

    # Video
    if path.suffix in video_formats:
        dep_object = Video(path)
        return dep_object

    return None

class NukeDependencies(object):
    """docstring for NukeDependency"""

    def __init__(self):
        self.dependencies = []

    def __iter__(self):
        return iter(self.dependencies)

    def print_info(self):
        for i in self.dependencies:
            log.info('Type: %s' % i.type)
            log.info('Base name: %s' % i.base_name)
            log.info('Version: %s' % i.version)

    def scan_scene(self):

        log.info('Scanning scene for dependencies...')

        project_settings = nuke.root()
        project_dir = Path(project_settings['project_directory'].getValue())

        for n in nuke.allNodes():

            if n.Class() not in ['Read', 'Camera2', 'DeepRead', 'ReadGeo2']:
                continue

            log.debug('Collecting dependecy of %s of type: %s ' % (n.name(), n.Class()))

            read_path = Path(n['file'].value())

            # If path is relative make it absolute again
            if not read_path.is_absolute():
                read_path = project_dir / read_path

            dep_obj = dependency_from_path(read_path)

            if dep_obj is not None:
                self.dependencies.append(dep_obj)
            else:
                log.warning('Unknown asset type: %s' % read_path.name)
