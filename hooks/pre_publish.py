import os
import sys
# import logging as log
from pathlib import Path
import nuke

from logger import Logger
log = Logger()


class PrePublishHook(object):
    """docstring for PrePublishHook"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def make_relative(self, project_root):

        log.info('Fixing all paths to relative...')

        project_settings = nuke.root()
        outside_nodes = []

        # Set Nuke project, always need to be Unix style since Nuke need it
        project_path = str(project_root).replace('\\', '/')
        project_settings['project_directory'].setValue(project_path)

        for n in nuke.allNodes():

            ####################################################################
            # Common path fixups
            ####################################################################
            if n.Class() not in ['Read', 'Camera2', 'DeepRead', 'ReadGeo2']:
                continue

            # log.debug('Repath node: %s, Type: %s ' % (n.name(), n.Class()))

            read_path = Path(n['file'].value())

            # Path is already relative
            if not read_path.is_absolute():
                continue

            # Path point to project root
            if str(read_path).startswith(str(project_root)):
                # Make it relative
                relative_path = read_path.relative_to(project_root)
                # Path should always be forward slashed in Nuke
                relative_path = str(relative_path).replace('\\', '/')
                n['file'].setValue(relative_path)
                continue
            # Path point outside of the project root
            else:
                log.warning('Path is outside of the project: %s' % read_path)
                outside_nodes.append(n)

            ####################################################################
            # Individual path fixups
            ####################################################################

            # Treat Read nodes
            if n.Class() == 'Read':
                pass

            # Treat Camera2 nodes
            elif n.Class() == 'Camera2':
                pass

            # Treat DeepRead nodes
            elif n.Class() == 'DeepRead':
                pass

        # Warn user about outside paths
        if outside_nodes:
            msg = (
                'The following nodes has dependencies '
                'outside of the Box Sync project:\n\n'
            )

            for n in outside_nodes:
                msg = msg + n.name() + '\n'

            msg += '\nPlease move your files to the project derectory in order to continue'
            log.warning(msg)

            raise Exception(msg)

    def set_on_script_load_callback(self):

        cmd = (
            'import on_script_open\n'
            'on_script_open.run()'
        )

        nuke.root().knob('onScriptLoad').setValue(cmd)

        log.debug('"On Script Load" callback is set')

    def set_on_script_save_callback(self):
        cmd = (
            'import on_script_save\n'
            'on_script_save.run()'
        )
        nuke.root().knob('onScriptSave').setValue(cmd)

        log.debug('"On Script Save" callback is set')

    def set_on_script_close_callback(self):
        cmd = (
            'import on_script_close\n'
            'on_script_close.run()'
        )
        nuke.root().knob('onScriptClose').setValue(cmd)

        log.debug('"On Script Close" callback is set')

    def run(self):
        log.info('Running pre-publish hook')
        self.make_relative(self.kwargs.get('project_root'))
        self.set_on_script_load_callback()
        self.set_on_script_save_callback()
        self.set_on_script_close_callback()
