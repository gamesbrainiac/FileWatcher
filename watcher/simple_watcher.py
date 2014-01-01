"""
"""
import os
from collections import deque
import time
import datetime

from .utils import FileTuple


class Watcher:

    def __init__(self, watch_dir=''):
        self.dir = watch_dir

    @property
    def _file_list(self):
        """
        Lists every single file in content directory
        @return: list[FileTuple]
        """
        # TODO: Make this function better, because we're using os.walk twice
        # Problem is, there is no do while loop in python
        root, dirs, files = tuple(os.walk(self.dir))[0]
        all_files = [FileTuple(os.path.join(root, f), os.stat(os.path.join(root, f)).st_mtime)
                     for f in files]

        q = deque([os.path.join(root, d) for d in dirs])

        while q:
            d = q.pop()
            r, drs, fs = tuple(os.walk(d))[0]
            all_files.extend([FileTuple(os.path.join(r, f), os.stat(os.path.join(r, f)).st_mtime)
                              for f in fs])
            q.extend([os.path.join(r, d) for d in drs])

        return all_files

    def _print_changelist(self, changed_files):
        for var in changed_files:
            print var.path, datetime.datetime.fromtimestamp(var.time)

    def activate(self, interval=1):

        # Adding display text
        print "#{:+^98}#".format(" watcher Activated! ")
        print "{:.^100}".format(" Watching {{{}}} recursively ".format(self.dir))
        print "=" * 100

        last_file_list = set()

        try:
            while True:
                time.sleep(interval)
                update = set(self._file_list)
                changed = update - last_file_list
                if changed:
                    self._print_changelist(changed)
                    last_file_list = update
        except KeyboardInterrupt:
            print "!!{:+^20}!!".format("Ending Watch")