# This file is NOT licensed under the GPLv3, which is the license for the rest
# of YouCompleteMe.
#
# Here's the license text for this file:
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# For more information, please refer to <http://unlicense.org/>

import os
import ycm_core
import itertools
import yaml
import logging
from pathlib import Path

log_prefix = 'lyude-ycm-conf: '
def info(msg, *args, **kwargs): logging.info(log_prefix + msg, *args, **kwargs)
def error(msg, *args, **kwargs): logging.error(log_prefix + msg, *args, **kwargs)
def debug(msg, *args, **kwargs): logging.debug(log_prefix + msg, *args, **kwargs)

class CompilationDatabase(ycm_core.CompilationDatabase):
    HEADER_EXTS = {'.h', '.hxx', '.hpp', '.hh'}
    SOURCE_EXTS = {'.cpp', '.cxx', '.cc', '.c', '.m', '.mm'}

    def __init__(self, directory, config):
        super().__init__(directory)
        self.config = config

        if 'extensions' in config:
            ext_cfg = config['extensions']
            if 'header' in ext_cfg:
                self.header_exts = frozenset(ext_cfg['header'])
            if 'source' in ext_cfg:
                self.source_exts = frozenset(ext_cfg['source'])

        if not hasattr(self, 'header_exts'):
            self.header_exts = self.HEADER_EXTS
        if not hasattr(self, 'source_exts'):
            self.source_exts = self.SOURCE_EXTS

    def get_flags_for_file(self, filename):
        info('Searching for flags for %s' % filename)

        # If this is header file, we're not going to have any entry for it in
        # the compilation database, so try searching for source files with
        # matching names
        name, ext = os.path.splitext(filename)
        if ext in self.header_exts:
            debug(('Header detected, trying to guess which file to use for '
                   'compilation flags'))
            for ext in self.source_exts:
                res = self.get_flags_for_file(name + ext)
                if res:
                    return res
            return

        comp_info = self.GetCompilationInfoForFile(filename)
        if not comp_info.compiler_flags_:
            return None

        flags = comp_info.compiler_flags_
        debug('Found flags: %s' % list(flags))

        if self.config and 'flags' in self.config:
            flags_cfg = self.config['flags']
            if 'remove' in flags_cfg:
                remove_set = set(flags_cfg['remove'])
                flags = filter(lambda e: e not in remove_set, flags)
            if 'add' in flags_cfg:
                flags = itertools.chain(flags, flags_cfg['add'])

        flags = CompilationDatabase._make_relative_paths_in_flags_absolute(
            flags, comp_info.compiler_working_dir_)

        debug('Final flags: %s' % flags)
        return flags

    PATH_FLAGS = {'-isystem', '-I', '-iquote', '--sysroot='}
    @classmethod
    def _make_relative_paths_in_flags_absolute(cls, flags, working_directory):
        if not working_directory:
            return list(flags)
        new_flags = []
        make_next_absolute = False
        for flag in flags:
            new_flag = flag

            if make_next_absolute:
                make_next_absolute = False
                if not flag.startswith('/'):
                    new_flag = os.path.join(working_directory, flag)

            for path_flag in cls.PATH_FLAGS:
                if flag == path_flag:
                    make_next_absolute = True
                    break

                if flag.startswith(path_flag):
                    path = flag[len(path_flag):]
                    new_flag = path_flag + os.path.join(working_directory, path)
                    break

            if new_flag:
                new_flags.append(new_flag)
        return new_flags

class FileManager:
    def __init__(self):
        self._dbs = dict()
        self._configs = dict()

    def find_db_for_file(self, filename):
        path = Path(filename)
        # It's possible that this might not actually be a path to a real file,
        # and might be a URI that's from a vim plugin. So, see if the file
        # actually exists
        if not path.exists():
            debug("'%s' is not a valid file path, ignoring" % filename)
            return None

        path = path.absolute()
        found = None
        for parent in path.parents:
            debug('Searching %s for compilation databases...' % str(parent))
            if parent in self._dbs:
                info('Using database %s for %s' % (str(parent), filename))
                return self._dbs[parent]

            db_file = parent.joinpath('compile_commands.json')
            if db_file.is_file():
                found = parent
                break

        if not found:
            return

        info('Found new compilation database %s/compile_commands.json' % found)
        self._dbs[found] = CompilationDatabase(
            str(found), self._find_config_for_db(found))
        return self._dbs[found]

    def _find_config_for_db(self, db_dir):
        assert isinstance(db_dir, Path)

        for parent in itertools.chain([db_dir], db_dir.parents):
            debug('Searching %s for config files...' % str(parent))

            if parent in self._configs:
                debug('Using previously loaded config %s' % str(parent))
                return self._configs[parent]

            config_file = parent.joinpath('ycm_extra_conf.yml')
            if config_file.is_file():
                info('Found new configuration file %s' % str(config_file))
                self._configs[parent] = yaml.load(open(str(config_file)))
                return self._configs[parent]

file_man = FileManager()
class NoFlagsFound(Exception):
    pass

def c_settings(**kwargs):
    filename = kwargs['filename']
    try:
        database = file_man.find_db_for_file(filename)
        if not database:
            raise NoFlagsFound('No database available for %s' % filename)

        flags = database.get_flags_for_file(filename)
        if not flags:
            raise NoFlagsFound('No compilation info available for %s' %
                               filename)
    except NoFlagsFound as e:
        error(e.args[0])
        return { 'flags': [] }

    return {
        'flags': flags,
        'do_cache': True
    }

def Settings(**kwargs):
    language = kwargs['language']
    if language == 'cfamily':
        return c_settings(**kwargs)

    return {}
# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
