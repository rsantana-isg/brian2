'''
File system tools
'''

import os
import sys
from contextlib import contextmanager

__all__ = ['ensure_directory', 'ensure_directory_of_file', 'in_directory',
           'copy_directory', 'stdout_redirected']


def ensure_directory_of_file(f):
    '''
    Ensures that a directory exists for filename to go in (creates if
    necessary), and returns the directory path.
    '''
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def ensure_directory(d):
    '''
    Ensures that a given directory exists (creates it if necessary)
    '''
    if not os.path.exists(d):
        os.makedirs(d)
    return d


class in_directory(object):
    '''
    Safely temporarily work in a subdirectory
    
    Usage::
    
        with in_directory(directory):
            ... do stuff here
            
    Guarantees that the code in the with block will be executed in directory,
    and that after the block is completed we return to the original directory.
    '''
    def __init__(self,new_dir):
        self.orig_dir = os.getcwd()
        self.new_dir = new_dir
    def __enter__(self):
        os.chdir(self.new_dir)
    def __exit__(self,*exc_info):
        os.chdir(self.orig_dir)


def copy_directory(source, target):
    '''
    Copies directory source to target.
    '''
    relnames = []
    sourcebase = os.path.normpath(source)+os.path.sep
    for root, dirnames, filenames in os.walk(source):
        for filename in filenames:
            fullname = os.path.normpath(os.path.join(root, filename))
            relname = fullname.replace(sourcebase, '')
            relnames.append(relname)
            tgtname = os.path.join(target, relname)
            ensure_directory_of_file(tgtname)
            contents = open(fullname).read()
            if os.path.exists(tgtname) and open(tgtname).read()==contents:
                continue
            open(tgtname, 'w').write(contents)
    return relnames

# The following code is based on J.F. Sebastian's answer on stackoverflow:
# http://stackoverflow.com/a/22434262/543465

@contextmanager
def stdout_redirected(to):
    stdout = sys.__stdout__
    stdout_fd = stdout.fileno()
    # copy stdout_fd before it is overwritten
    #NOTE: `copied` is inheritable on Windows when duplicating a standard stream
    with os.fdopen(os.dup(stdout_fd), 'wb') as copied:
        stdout.flush()  # flush library buffers that dup2 knows nothing about
        try:
            os.dup2(to.fileno(), stdout_fd)  # $ exec >&to
        except ValueError:  # filename
            with open(to, 'wb') as to_file:
                os.dup2(to_file.fileno(), stdout_fd)  # $ exec > to
        try:
            yield stdout # allow code to be run with the redirected stdout
        finally:
            # restore stdout to its previous value
            #NOTE: dup2 makes stdout_fd inheritable unconditionally
            stdout.flush()
            os.dup2(copied.fileno(), stdout_fd)  # $ exec >&copied
