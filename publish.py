import os
import re
import sys
import nuke

from pathlib import Path
from logger import Logger

import hooks
reload (hooks)
from hooks import PrePublishHook

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
    """docstring for ProjectPath"""
    def __init__(self):
        self.path_teplates = PathTemplates()
        self.root = self.get_root()
        self.template = None
        self.version_padding = 3

    def get_root(self):
        # project_root = Path(os.environ['PROJECT_ROOT'])

        box_conf_file = ''

        if sys.platform == 'darwin':
            user = os.environ['USER']
            box_conf_file = Path('/Users/%s/Library/Application Support/Box/Box Sync/sync_root_folder.txt' % user)
        elif sys.platform == 'win32':
            user = os.environ['USERNAME']
            box_conf_file = Path('C:/Users/%s/AppData/Local/Box Sync/sync_root_folder.txt' %  user)
        else:
            log.error('Failed to identify current OS: %s' % sys.platform)

        # Read box root path from config file
        # It will return empty string if box is not launched
        with box_conf_file.open() as f:
            data = f.read()

        if data:
            project_root = Path(data)
        else:
            # Path from config file is empty
            # Most likely that Box Sync is not running
            raise Exception(
                'Box Sync is not running. Please stat Box Sync app first.'
            )

        return project_root

    def set_template(self, template_name):
        self.template = self.path_teplates[template_name]

    def apply_fields(self, context):

        path = self.template

        for k, v in context.items():
            # print 'Key: ', key, 'Val: ', v
            if k == 'version':
                v = str(v).zfill(self.version_padding)
            key = '{%s}' % k
            path = str(path).replace(key, str(v))

        return Path(path)

    def context_from_path(self, path):

        context = {'project_root': self.root}
        templ_val = self.template.parent.parts[1:]
        path_val = Path(path).relative_to(self.root).parent.parts

        print 'TEMPL_VAL: ', templ_val
        print 'PATH_VAL: ', path_val

        if len(templ_val) != len(path_val):
            raise Exception('Path %s does not match %s template' % (path_val, templ_val))

        for k, v in zip(templ_val, path_val):
            result = re.search(r'({)(\D+)(})', k)
            if result is not None:
                templ_key = result.group(2)
                context[templ_key] = v

        print 'CONTEXT: ', context

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

    def save_scene(self, scene_path):

        # Create parent folder if not exists
        if not scene_path.parent.exists():
            scene_path.parent.mkdir(parents=True)

        scene_path = str(scene_path)
        nuke.scriptSaveAs(str(scene_path))

    def publish(self):

        log.info('Publishing...')

        current_scene_path = self._get_scene_path()
        current_version = self._get_version_from_name(current_scene_path.name)

        self.project_path.set_template('nuke_publish_file')
        context = self.project_path.context_from_path(self._get_scene_path())

        context.update({'version': current_version})

        # Get nuke publish file path from the template
        publish_nuke_path = self.project_path.apply_fields(context)

        # Run prepublish hook
        pre_pub = PrePublishHook(root_dir=self.project_path.root)
        pre_pub.run()

        # Save published scene
        self.save_scene(publish_nuke_path)

        # Version current scene up
        publish_version = current_version + 1
        context.update({'version': publish_version})
        self.project_path.set_template('nuke_working_file')
        working_nuke_path = self.project_path.apply_fields(context)
        # Save current working scene
        self.save_scene(working_nuke_path)

        log.info('Published to ', publish_nuke_path)

        msg = ('Version %s successfully published!' % publish_version)
        nuke.message(msg)
