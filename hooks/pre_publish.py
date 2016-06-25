import os
import sys
from pathlib import Path
from logger import Logger
import nuke

log = Logger()

class PrePublishHook(object):
    """docstring for PrePublishHook"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def make_relative(self, project_root):

        project_settings = nuke.root()
        outside_nodes = []

        # Set Nuke project
        project_settings['project_directory'].setValue(str(project_root))

        for n in nuke.allNodes():

            ####################################################################
            # Common path fixups
            ####################################################################
            if n.Class() not in ['Read', 'Camera2', 'DeepRead', 'ReadGeo2']:
                continue

            log.line()
            log.debug('Processing Node: %s, Type: %s ' % (n.name(), n.Class()))

            read_path = Path(n['file'].value())

            # Path is already relative
            if not read_path.is_absolute():
                continue

            # Path point to project root
            if str(read_path).startswith(str(project_root)):
                # Make it relative
                log.debug('Changed to relative.')
                relative_path = read_path.relative_to(project_root)
                n['file'].setValue(str(relative_path))
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

            msg += '\nPlease move your files to the project derectory in order to publish'

            nuke.message(msg)

            raise Exception(msg)

    def set_on_script_load_callback(self):

        cmd = (
            'import on_script_open\n'
            'on_script_open.run()'
        )

        nuke.root().knob('onScriptLoad').setValue(cmd)

        log.debug('On Script Load callback is set')

    def run(self):
        log.info('Running pre-publish hook')
        self.make_relative(self.kwargs.get('project_root'))
        self.set_on_script_load_callback()
