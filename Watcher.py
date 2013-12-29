import os
import time
import shutil
import thread
import datetime
from functools import partial
from collections import namedtuple, deque

from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor

# Named Tuple classes
FileTuple = namedtuple('FileTuple', ['path', 'time'])


class Watcher:
    def __init__(self, content='', output='output', func=None, ext='.rst', clean=True):
        """
        Watcher will watch the content directory, and output data to the
        output directory based on the func method. The func method will be expected
        to deal with relative file paths of files and deal with them as it deems fit.

        The content and the output directory are relative to directory of where the
        Watcher class is being activated.

        @type func: callable
        @type output: str
        @type content: str
        @param content: content directory
        @param output: output directory
        @param func: Function that deals with what to do with individual paths.
        relative paths will be provided
        @param ext: extension files that will be processed (will not remain in final version)
        @param clean: Will the output folder be cleaned after use!
        """
        self.dir = content
        self.out = output
        self.ext = ext
        self.produce = partial(func, content_path=self.dir, output_path=self.out, out_format='html')
        self.printlock = thread.allocate_lock()

        if clean:
            self._clean_out_dir()

    def _clean_out_dir(self):
        """
        Cleans output directory
        """
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
            os.makedirs(self.out)

    def _make_dirs_from_file_paths(self, files):
        """
        Creates directories in output folder that match with the content folder.
        @param files: List of FileTuple objects
        """
        dirs = [os.path.dirname(fl.path.replace(self.dir, self.out, 1))
                for fl in files]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    @property
    def _file_list(self):
        """
        Lists every single file in content directory
        @return: list[FileTuple]
        """
        # TODO: Make this function better, because we're using os.walk twice
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

    def _print_whats_being_updated(self, changed_files):
        # TODO: Need to reconsider this function as often, its just a changed file and not a list of files
        for var in changed_files:
            print var.path, datetime.datetime.fromtimestamp(var.time)

    def _convert(self, changed):
        """
        The function that transforms the files you want converted, in default case, .rst files
        @param changed:
        """
        for path in [f.path for f in changed if os.path.splitext(f.path)[1] == self.ext]:
            self.produce(filename=path)

    def _copy_non_converted_to_out_dir(self, fs):
        """
        Just copy files that don't need conversion to output directory
        @param fs: list of files that were not converted
        """
        for var in [f for f in fs if os.path.splitext(f.path)[1] != self.ext]:
            shutil.copyfile(var.path, var.path.replace(self.dir, self.out, 1))

    def activate(self, interval=1):
        """
        Activates the watcher
        @type interval: int
        @param interval: Interval of sleep
        """
        with self.printlock:
            print "#{:+^98}#".format(" Watcher Activated! ")
            print "{:.^100}".format(" Watching {{{}}} recursively ".format(self.dir))
            print "=" * 100

        last_file_list = set()
        try:
            while True:
                time.sleep(interval)
                update = set(self._file_list)
                changed = update - last_file_list
                if changed:
                    self._make_dirs_from_file_paths(update)
                    self._print_whats_being_updated(changed)
                    self._convert(changed)
                    self._copy_non_converted_to_out_dir(changed)
                    last_file_list = update
        except KeyboardInterrupt:
            with self.printlock:
                print "!!{:+^20}!!".format("Ending Watch")
            return

    def activate_and_serve(self, port=8000):
        """
        Activates the watcher and serves the files on localhost
        @param port:
        @return:
        """
        with thread.allocate_lock():
            thread.start_new_thread(self.activate, (1,))

        try:
            resource = File(self.out)
            factory = Site(resource)
            reactor.listenTCP(port, factory)
            with self.printlock:
                print ""
                print "Serving now on http://{}:{}".format('localhost', port)
            reactor.run()
        except KeyboardInterrupt:
            print "Closing server"
            return None