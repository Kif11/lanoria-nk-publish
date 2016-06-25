import os
import re
import sys
import nuke

from pathlib import Path
from logger import Logger

import hooks
reload (hooks)
from hooks import PrePublishHook
import box_util
reload(box_util)
from box_util import BoxUtil

log = Logger()


class PathTemplates(object):
    """docstring for PathTemplates"""

    def __init__(self):
        pass
        # TODO Read templates from yaml file
        self.templates = {
            'nuke_working_file': '{project_root}/{show}/{entity}/{entity_type}/{sequence}/{shot}/working/{task}/nuke/{shot}_{task}_v{version}.nk',
            'nuke_publish_file': '{project_root}/{show}/{entity}/{entity_type}/{sequence}/{shot}/publish/{task}/nuke/{shot}_{task}_v{version}.nk',
        }

    def __iter__(self):
        return self.templates.iteritems()

    def __getitem__(self, i):
        return Path(self.templates[i])


class ProjectPath(object):
    """
    Class for handeling all project context and path resolution
    It make use of PathTemplates class to resolve files locations
    """

    def __init__(self):
        self.path_teplates = PathTemplates()
        self.boxutil = BoxUtil()
        self.root = self.get_root()
        self.template = None
        self.version_padding = 3

    def get_root(self):
        """
        Retrive project root directory
        In this case it is BoxSync application root directory on user machine
        """
        project_root = self.boxutil.get_storage_root()

        return project_root

    def set_template(self, template_name):
        self.template = self.path_teplates[template_name]

    def apply_fields(self, context):
        """
        Given context dictionary apply its field to given template path
        """

        path = self.template

        for k, v in context.items():
            if k == 'version':
                v = str(v).zfill(self.version_padding)
            key = '{%s}' % k
            path = str(path).replace(key, str(v))

        return Path(path)

    def context_from_path(self, path):
        """
        Given a file path try to pupulate
        the context by using current template

        Note:

        This procedu is not robust and might produce unexpected result
        since we can have the following situation:
            1. {shot}/{step} with SH01/comp
            2. {shot}/{step} with Room/comp
        In second case it will populate shot field with an asset name
        which is not desired

        """

        context = {'project_root': self.root}
        templ_val = self.template.parent.parts[1:]
        path_val = Path(path).relative_to(self.root).parent.parts

        if len(templ_val) != len(path_val):
            raise Exception('Path %s does not match %s template' % (path_val, templ_val))

        for k, v in zip(templ_val, path_val):
            result = re.search(r'({)(\D+)(})', k)
            if result is not None:
                templ_key = result.group(2)
                context[templ_key] = v

        return context


class NukePublish(object):

    def __init__(self):
        self.project_path = ProjectPath()

    def _get_scene_path(self):
        current_scene = Path(nuke.root().knob('name').value())

        return current_scene

    def _get_version_from_name(self, name):
        # Find Publish version number base on the file name
        result = re.search(r'(v)(\d+)', name)
        if result:
            v = int(result.group(2))
        else:
            raise Exception(
                'Can not determine Publish Version from the file name '
                'Make sure that you use v### naming convention in your file name'
            )

        return v

    def save_scene(self, scene_path, read_only=False):

        # Create parent folder if not exists
        if not scene_path.parent.exists():
            scene_path.parent.mkdir(parents=True)

        nuke.scriptSaveAs(str(scene_path))

        if read_only:
            # Set file to read-only
            scene_path.chmod(0o444)

    def publish(self):

        log.info('Publishing...')

        current_scene_path = self._get_scene_path()

        if current_scene_path == Path():
            raise Exception (
                'Can not determine current scene path. '
                'Probably scene is not saved.'
            )

        current_version = self._get_version_from_name(current_scene_path.name)

        self.project_path.set_template('nuke_publish_file')
        context = self.project_path.context_from_path(self._get_scene_path())

        context.update({'version': current_version})

        # Get nuke publish file path from the template
        publish_nuke_path = self.project_path.apply_fields(context)

        # Run prepublish hook
        pre_pub = PrePublishHook(project_root=self.project_path.root)
        pre_pub.run()

        # Save published scene
        self.save_scene(publish_nuke_path, read_only=True)

        # Version current scene up
        new_working_version = current_version + 1
        context.update({'version': new_working_version})
        self.project_path.set_template('nuke_working_file')
        working_nuke_path = self.project_path.apply_fields(context)
        # Save current working scene
        self.save_scene(working_nuke_path)

        log.info('Published to ', publish_nuke_path)

        msg = ('Version %s successfully published!' % current_version)
        nuke.message(msg)
