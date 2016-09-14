#!/usr/bin/env python
# author: Kirill Kovalevskiy
# e-mail: kovalewskiy@gmail.com

# Python and Nuke STL
import os
import re
import sys
import traceback
# import logging as log
from logger import Logger
import nuke

# Custom modules
import hooks
import project_manager
import sgmng
import boxmng
import dependencies
import ui

reload(ui)
reload(hooks)
reload(project_manager)
reload(sgmng)
reload(boxmng)
reload(dependencies)

from pathlib import Path
from hooks import PrePublishHook
from project_manager import ProjectManager
from sgmng import ShotgunManager
from boxmng import BoxManager
from dependencies import NukeDependencies

from PySide import QtGui, QtCore
from ui import Ui_PublishDialog

# Global variables
log = Logger()

# Supress SSL warning
# /Library/Python/2.7/site-packages/requests/packages/urllib3/util/ssl_.py:318:
# SNIMissingWarning: An HTTPS request has been made, but the SNI
# (Subject Name Indication) extension to TLS is not available on this platform.
# This may cause the server to present an incorrect TLS certificate, which can
# cause validation failures. You can upgrade to a newer version of Python to
# solve this. For more information, see https://urllib3.readthedocs.org/en/
# latest/security.html snimissingwarning.
import warnings; warnings.filterwarnings("ignore")

class PublishDialogModel(object):
    """
    Publish dialog singleton model
    holds all the the states and ui related data
    """

    _instance = None

    def __init__(self):
        self.comment = ''
        self.info_msg = ''
        self.msg_type = ''
        self.save_as_working = False
        self.promote_version = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(cls.__class__, cls).__new__(cls, *args, **kwargs)
        return cls._instance

class NukePublish(object):

    def __init__(self):
        self.pdm = PublishDialogModel()
        self.pm = ProjectManager()
        self.sgmng = ShotgunManager()
        self.bm = BoxManager()
        self.dependencies = NukeDependencies()
        self.pm.set_template('nuke_shot_publish_file')
        self.ctx = self.pm.context_from_path(self._get_scene_path())
        self.current_scene_path = self._get_scene_path()
        self.publish_area = self._get_publish_area()
        self.working_area = self._get_working_area()
        self.current_version = self._get_current_version()
        self.latest_working_version = self._scan_for_latest_version(self._get_working_nuke_path().parent)
        self.latest_publish_version = self._scan_for_latest_version(self._get_publish_nuke_path().parent)
        self.master_version = int(sorted([self.current_version, self.latest_working_version, self.latest_publish_version])[-1:][0])

    def _get_scene_path(self):
        """
        Get the disc path of currently opened Nuke scene
        """
        current_scene = Path(nuke.root().knob('name').value())

        if current_scene == Path():
            msg = (
                'Can not determine current scene path. '
                'Probably scene is not saved.'
            )
            nuke.message(msg)
            raise Exception (msg)

        return current_scene

    def _get_publish_area(self):
        """ Get Nuke publish area directory """

        self.pm.set_template('nuke_shot_publish_area')
        publish_nuke_area = self.pm.apply_fields(self.ctx)
        return publish_nuke_area

    def _get_working_area(self):
        """ Get Nuke work area directory """

        self.pm.set_template('nuke_shot_working_area')
        working_nuke_area = self.pm.apply_fields(self.ctx)
        return working_nuke_area

    def _get_publish_nuke_path(self, version=None):
        """ Get publish scene Nuke path """

        # Get nuke publish file path from the template
        self.pm.set_template('nuke_shot_publish_file')
        self.ctx.update({'version': version})
        publish_nuke_path = self.pm.apply_fields(self.ctx)
        return publish_nuke_path

    def _get_working_nuke_path(self, version=None):
        """ Get work scene Nuke path """

        # Get nuke publish file path from the template
        self.pm.set_template('nuke_shot_working_file')
        self.ctx.update({'version': version})
        working_nuke_path = self.pm.apply_fields(self.ctx)
        return working_nuke_path

    def _get_current_version(self):
        """ Find Publish version number base on current file name """

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
        """
        Given a directory go through every file in that directory and determine
        the highest version number base on regular expression pattern
        """

        if directory.exists():
            # List all files in the directory excluding dot hidden files
            scanned_files = [str(x) for x in directory.glob('*.nk')]
        else:
            log.debug('Tried to scan for versions but directory does not exists %s' % directory)
            scanned_files = []

        # If files in directory
        if len(scanned_files) == 0:
            version = 1
        # If there are files find the last version
        else:
            version_list = []
            for f in scanned_files:
                search = re.search(r'(?<=v)[0-9]+', f)
                if search:
                    version_list.append(int(search.group()))
            version = sorted(version_list)[-1:][0]

        return version

    def save_scene(self, scene_path, overwrite=-1):
        # Create parent folder if not exists
        if not scene_path.parent.exists():
            scene_path.parent.mkdir(parents=True)

        nuke.scriptSaveAs(str(scene_path), overwrite)

    def save_as_working(self, overwrite=-1):
        new_working_version = self.master_version + 1
        working_nuke_file = self._get_working_nuke_path(new_working_version)
        # Save current working scene
        self.save_scene(working_nuke_file, overwrite)
        log.info('New working saved to %s' % working_nuke_file)

    def upload_publish(self):
        publish_nuke_file = self._get_publish_nuke_path(self.master_version)
        folder_id = self.bm.get_shot_publish_folder(self.ctx.get('shot')).id
        published_file = self.bm.upload_file(folder_id, self.current_scene_path, publish_nuke_file.name)

        return published_file

    def get_unpublished_dep(self):
        # Scan scene for deppendent content
        self.dependencies.scan_scene()

        # Set current shot
        self.sgmng.shot = self.ctx.get('shot')

        published_files = self.sgmng.published_files
        # log.debug('Publish file: %s', p.get('code'))

        # Find all which of this dependencies weren't publish on Shotgun
        not_published_dependencies = []
        for dep in self.dependencies:
            is_published = False
            for pub in published_files:
                if dep.base_name == pub['code']:
                    # This dependency is already published
                    # log.debug('Dependency %s is already published' % dep.base_name)
                    is_published = True
                    continue
            if not is_published:
                # log.debug('Dependency %s is not published' % dep.base_name)
                not_published_dependencies.append(dep)

        return not_published_dependencies

    def is_published_file(self):
        return str(self.current_scene_path).startswith(str(self.publish_area))

    def publish(self, ui=None):

        log.info('Publishing...')
        log.debug('Current version: %s' % self.current_version)
        log.debug('Latest working version: %s' % self.latest_working_version)
        log.debug('Latest publish version: %s' % self.latest_publish_version)
        log.debug('Master version: %s' % self.master_version)

        # Authenticate Shotgun manager
        self.sgmng.authenticate()

        if ui is None:
            self.pdm.promote_version = True
            self.pdm.save_as_working = True

        # Check if user try to create a publish not from the lates version
        if not self.pdm.promote_version:
            if self.current_version < self.master_version:
                msg = (
                    'Your current file version is %s. '
                    'However there is version %s of this file exists. '
                    'Are you sure you want to promote this version to the latest?'
                    % (self.current_version,  self.master_version)
                )
                self.pdm.msg_type = 'promote_version'
                if ui is not None:
                    ui.signals.info_msg.emit(msg)
                else:
                    log.warning(msg)
                return

        if self.pdm.save_as_working:
            self.save_as_working()
            log.info('Working version number %s created' % (int(self.master_version) + 1))

        # Check if user trying to publish from publish area
        elif self.is_published_file():
            msg = (
                'This file is in the publish directory. '
                'Do you want to save it to working?'
            )
            self.pdm.msg_type = 'save_as_working'
            if ui is not None:
                ui.signals.info_msg.emit(msg)
            else:
                log.warning(msg)
            return

        # Case where user copied latest publish version to working
        if self.current_version == self.latest_publish_version:
            log.info(
                'Publish v%03d already exist. Version up.'
                % self.latest_publish_version
            )
            self.master_version = self.master_version + 1

        # Make sure that the file is saved
        nuke.scriptSaveAs(str(self._get_scene_path()), overwrite=True)

        # Run pre-publish hook
        try:
            pre_pub = PrePublishHook(project_root=self.pm.root)
            pre_pub.run()
        except Exception as e:
            if ui is not None:
                ui.signals.info_msg.emit('%s' % e)
            return

        # unpublished_dep = self.get_unpublished_dep()

        # for i in unpublished_dep:
        #     self.sgmng.create_publish

        # Upload Nuke file to Box
        self.bm.authenticate()

        try:
            published_file = self.upload_publish()
            log.info('File %s successfully uploaded to Box' % published_file.name)
        except Exception as e:
            print e
            msg = ('Failed to upload file to BOX.')
            log.error(msg)
            self.pdm.msg_type = 'box_upload_fail'
            if ui is not None:
                ui.signals.info_msg.emit(msg)

        publish_name = '{shot}_{task}'.format(**self.ctx)

        # Publish Nuke file to Shotgun
        nuke_publish_path = self._get_publish_nuke_path(self.master_version)
        nuke_relative_path = nuke_publish_path.relative_to(self.pm.root)

        sg_publish = self.sgmng.create_publish(
            shot = self.ctx.get('shot'),
            task = self.ctx.get('task'),
            name = publish_name,
            code =  str(nuke_relative_path.name),
            version_number = self.master_version,
            local_path = str(nuke_relative_path),
            description = self.pdm.comment,
            publish_file_type = 'Nuke Script',
            box_link = published_file.get_shared_link_download_url(),
            box_id = published_file.id,
        )

        log.info('File %s successfully published to Shotgun' % sg_publish['code'])

        # Save Nuke file localy as a new working version
        if not self.pdm.save_as_working:
            self.save_as_working()

        msg = ('Version %s successfully published!' % self.master_version)
        log.info(msg)

        if ui is not None:
            ui.signals.is_done.emit(True)
        else:
            log.info('Published!')

class WorkerSignals(QtCore.QObject):
    is_done = QtCore.Signal(bool)
    is_msg = QtCore.Signal(bool)
    info_msg = QtCore.Signal(str)

class PublishWorker(QtCore.QThread):

    def __init__(self):
        super(PublishWorker, self).__init__()
        self.signals = WorkerSignals()
        self.np = NukePublish()

    # A QThread is run by calling it's start() function, which calls this run()
    # function in it's own "thread".
    def run(self):
        try:
            self.np.publish(self)
        except Exception as e:
            log.error('Error happened while publishing the scene!')
            traceback.print_exc(file=sys.stdout)
            log.debug(e)
            self.signals.is_done.emit(False)

    def stop(self):
        self.terminate()

    # def __del__(self):
    #     print '[D] Working thread destructor was called'

class PublishDialog(QtGui.QWidget):

    def __init__(self):
        # first, call the base class and let it do its thing.
        QtGui.QWidget.__init__(self)

        # now load in the UI that was created in the UI designer
        self.ui = Ui_PublishDialog()
        self.ui.setupUi(self)
        self.ui.info_btn.hide()

        self.ui.publish_btn.clicked.connect(self.publish)
        self.ui.info_btn.accepted.connect(self.info_btn_accepted)
        self.ui.close_btn.clicked.connect(self.close_ui)

        self.ui.result_msg.hide()

        self.pdm = PublishDialogModel()

        self.script_dir = os.path.dirname(os.path.realpath(__file__))

    def prepare(self):
        self.worker = PublishWorker()
        self.worker.signals.is_done.connect(self.publish_result)
        self.worker.signals.info_msg.connect(self.display_info_msg)

        # Set UI to original state
        self.ui.comment_label.show()
        self.ui.result_msg.hide()
        self.ui.publish_btn.show()
        self.ui.publish_comment.clear()
        self.ui.publish_comment.show()

    def close_ui(self):
        log.debug('Exiting application')
        self.worker.stop()
        self.close()

    def info_btn_accepted(self):
        if self.pdm.msg_type == 'save_as_working':
            self.pdm.save_as_working = True
            self.publish()
        elif self.pdm.msg_type == 'promote_version':
            self.pdm.promote_version = True
            self.publish()
        elif self.pdm.msg_type == 'box_upload_fail':
            self.ui.info_btn.hide()
            self.ui.close_btn.show()

    def display_info_msg(self, msg):
        self.ui.close_btn.hide()
        self.ui.info_btn.show()
        self.ui.result_msg.setText(msg)

    def display_msg(self, msg):
        self.ui.result_msg.setText('Display msg!')

    def publish_result(self, status):
        self.ui.info_btn.hide()
        self.ui.close_btn.show()
        if status:
            success_map_path = Path(self.script_dir, 'resources/success.png')
            success_map = QtGui.QPixmap(str(success_map_path))
            self.ui.result_msg.setPixmap(success_map)
        else:
            failure_map_path = Path(self.script_dir, 'resources/failure.png')
            failure_map = QtGui.QPixmap(str(failure_map_path))
            self.ui.result_msg.setPixmap(failure_map)

    def publish(self):

        # Update model comment
        self.pdm.comment = self.ui.publish_comment.toPlainText()

        self.ui.info_btn.hide()
        self.ui.close_btn.show()

        # Show loading animation
        self.ui.result_msg.show()
        load_map_path = Path(self.script_dir, 'resources/load.gif')
        movie = QtGui.QMovie(str(load_map_path))
        self.ui.result_msg.setMovie(movie)
        movie.start()

        # Start publishing process on
        # a separate thread
        self.worker.start()


if __name__ == '__main__':
    # Nuke test
    # import nk_publish; reload(nk_publish); from nk_publish import NukePublish; NukePublish().publish()

    nuke.scriptOpen('/Users/kif/BoxSync/LaNoria/Shots/lacaja_test/test_seq/test_shot_6/working/comp/nuke/test_shot_6_comp_v001.nk')
    np = NukePublish()
    np.publish()
