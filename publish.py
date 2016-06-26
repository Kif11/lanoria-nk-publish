import os
import re
import sys
import nuke

from pathlib import Path
from logger import Logger

import hooks
reload (hooks)
from hooks import PrePublishHook

import project_manager
reload(project_manager)
from project_manager import ProjectManager

log = Logger()

class NukePublish(object):

    def __init__(self):
        self.pm = ProjectManager()
        self.pm.set_template('nuke_shot_publish_file')
        self.ctx = self.pm.context_from_path(self._get_scene_path())
        self.current_scene_path = self._get_scene_path()
        self.publish_area = self._get_publish_area()
        self.working_area = self._get_working_area()
        self.current_version = self._get_current_version()
        self.latest_working_version = self._scan_for_latest_version(self._get_working_nuke_path().parent)
        self.latest_publish_version = self._scan_for_latest_version(self._get_publish_nuke_path().parent)
        self.master_version = int(sorted([self.current_version, self.latest_working_version, self.latest_publish_version])[-1:][0])

        log.debug('Latest working version: ', self.latest_working_version)

    def _get_scene_path(self):
        current_scene = Path(nuke.root().knob('name').value())

        if current_scene == Path():
            raise Exception (
                'Can not determine current scene path. '
                'Probably scene is not saved.'
            )

        return current_scene

    def _get_publish_area(self):
        self.pm.set_template('nuke_shot_publish_area')
        publish_nuke_area = self.pm.apply_fields(self.ctx)
        return publish_nuke_area

    def _get_working_area(self):
        self.pm.set_template('nuke_shot_working_area')
        working_nuke_area = self.pm.apply_fields(self.ctx)
        return working_nuke_area

    def _get_publish_nuke_path(self, version=None):
        # Get nuke publish file path from the template
        self.pm.set_template('nuke_shot_publish_file')
        self.ctx.update({'version': version})
        publish_nuke_path = self.pm.apply_fields(self.ctx)
        return publish_nuke_path

    def _get_working_nuke_path(self, version=None):
        # Get nuke publish file path from the template
        self.pm.set_template('nuke_shot_working_file')
        self.ctx.update({'version': version})
        working_nuke_path = self.pm.apply_fields(self.ctx)
        return working_nuke_path

    def _get_current_version(self):
        # Find Publish version number base on the file name
        result = re.search(r'(v)(\d+)', self.current_scene_path.name)
        if result:
            v = int(result.group(2))
        else:
            raise Exception(
                'Can not determine Publish Version from the file name '
                'Make sure that you use v### naming convention in your file name'
            )

        return v

    def _scan_for_latest_version(self, directory):

        scaned_files = os.listdir(str(directory))

        # If files in directory
        if len(scaned_files) == 0:
            version = 1
        # If there are files find the last version
        else:
            version_list = []
            for f in scaned_files:
                search = re.search(r'(?<=v)[0-9]+', f)
                if search:
                    version_list.append(int(search.group()))
            version = sorted(version_list)[-1:][0]

        return version

    def save_scene(self, scene_path):
        # Create parent folder if not exists
        if not scene_path.parent.exists():
            scene_path.parent.mkdir(parents=True)

        nuke.scriptSaveAs(str(scene_path))

    def save_as_working(self):
        new_working_version = self.master_version + 1
        working_nuke_file = self._get_working_nuke_path(new_working_version)
        # Save current working scene
        self.save_scene(working_nuke_file)
        log.info('New working saved to ', working_nuke_file)

    def save_as_publish(self):
        publish_nuke_file = self._get_publish_nuke_path(self.master_version)
        # Save published scene
        self.save_scene(publish_nuke_file)
        log.info('New publish saved to ', publish_nuke_file)

    def publish(self):

        log.info('Publishing...')

        log.debug('Current version: ', self.current_version)
        log.debug('Latest working version: ', self.latest_working_version)
        log.debug('Latest publish version: ', self.latest_publish_version)
        log.debug('Master version: ', self.master_version)

        # Check if user trying to publish from publish area
        if str(self.current_scene_path).startswith(str(self.publish_area)):
            msg = ('This file is a publish. Do you want to save it as working?')
            save_as_working = nuke.ask(msg)
            if save_as_working:
                self.save_as_working()
                log.info('Working version numbe %s created' % self.master_version + 1)
                return
            else:
                log.info('Publish canceled by user')
                return

        # Check if user try to create a pulish not from the lates version
        if self.current_version < self.master_version:
            promote = nuke.ask(
                'Your current file version is %s. '
                'However there is version %s of this file exists. '
                'Are you sure you want to promote this version to the latest?'
                % (self.current_version,  self.master_version)
            )
            if not promote:
                log.info('Publish canceled by user')
                return

        # Run prepublish hook
        pre_pub = PrePublishHook(project_root=self.pm.root)
        pre_pub.run()

        self.save_as_publish()
        self.save_as_working()

        msg = ('Version %s successfully published!' % self.master_version)
        nuke.message(msg)
