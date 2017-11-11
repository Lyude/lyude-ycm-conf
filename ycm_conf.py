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
from pathlib import Path

SOURCE_EXTENSIONS = ['.cpp', '.cxx', '.cc', '.c', '.m', '.mm']

database = None
ccdb_path = None
config_path = None
config = None

def find_files(filename):
    print("Beginning search for compilation database and config files...")

    filepath = Path(filename)
    ccdb_path = None
    config_path = None

    for parent in filepath.parents:
        print("Searching %s..." % parent.as_posix())

        if not ccdb_path:
            path = parent.joinpath('compile_commands.json')
            if path.is_file():
                ccdb_path = path.resolve().parent
                print("Using %s as compilation database directory" %
                      ccdb_path.as_posix())

        if ccdb_path:
            path = parent.joinpath('ycm_extra_conf.yml')
            if path.is_file():
                config_path = path.resolve()
                print("Found config file: %s" % config_path)
                break

    return (ccdb_path, config_path)

def directory_of_this_script():
    return os.path.dirname(os.path.abspath(__file__))

def apply_config_to_flags(flags):
    if config and 'flags' in config:
        flags = flags.copy()
        flags_config = config['flags']

        if 'remove' in flags_config:
            remove_set = set(flags_config['remove'])
            flags = list(filter(lambda e: e not in remove_set, flags))

        if 'add' in flags_config:
            flags += flags_config['add']

    return flags

def make_relative_paths_in_flags_absolute(flags, working_directory):
    if not working_directory:
        return list(flags)
    new_flags = []
    make_next_absolute = False
    path_flags = ['-isystem', '-I', '-iquote', '--sysroot=']
    for flag in flags:
        new_flag = flag

        if make_next_absolute:
            make_next_absolute = False
            if not flag.startswith('/'):
                new_flag = os.path.join(working_directory, flag)

        for path_flag in path_flags:
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

def is_header_file(filename):
    extension = os.path.splitext(filename)[1]
    return extension in ['.h', '.hxx', '.hpp', '.hh']

def get_compilation_info_for_file(database, filename):
    if is_header_file(filename):
        basename = os.path.splitext(filename)[0]
        for extension in SOURCE_EXTENSIONS:
            replacement_file = basename + extension
            if os.path.exists(replacement_file):
                print("Using %s for finding compilation database flags" %
                      replacement_file)
                compilation_info = database.GetCompilationInfoForFile(
                    replacement_file)
                if compilation_info.compiler_flags_:
                    return compilation_info
        return None

    print("Using %s for finding compilation database flags" % filename)
    compilation_info = database.GetCompilationInfoForFile(filename)
    if compilation_info.compiler_flags_:
        return compilation_info

    print("No files found, giving up")
    return None

def flags_for_file(filename, **kwargs):
    global database
    global ccdb_path
    global config_path
    global config

    if not database:
        print("Searching for compilation database...")
        ccdb_path, config_path = find_files(filename)
        database = ycm_core.CompilationDatabase(ccdb_path)
        if not database:
            print("None found")
            return

        if config_path:
            config = yaml.load(open(config_path))

    compilation_info = get_compilation_info_for_file(database, filename)
    if not compilation_info:
        print("No compilation info found for %s" % filename)
        return

    final_flags = make_relative_paths_in_flags_absolute(
        compilation_info.compiler_flags_,
        compilation_info.compiler_working_dir_)
    final_flags = apply_config_to_flags(final_flags)

    print("Looked up flags for %s" % filename)
    print("Flags for this file: %s" %
          str([f for f in compilation_info.compiler_flags_]))
    print("Working directory: %s" % compilation_info.compiler_working_dir_)
    print("Final flags: %s" % final_flags)

    return {
        'flags': final_flags,
        'do_cache': True
    }

FlagsForFile = flags_for_file
# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
