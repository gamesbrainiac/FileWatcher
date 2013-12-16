"""
@warning Watcher.py is not completely reusable right now!
"""

from Watcher import Watcher
from docutils.core import publish_string


CONTENT_PATH = 'content'
OUTPUT_PATH = 'output'


def make(filename='', content_path='', output_path='', out_format='html'):
    def corresponding_output_path():
        return "{name}.{extension}".format(name=filename.replace(content_path, output_path, 1).split('.')[0], extension=out_format)

    with open(filename) as f:
        s = publish_string(f.read(), writer_name=out_format)

        with open(corresponding_output_path(), 'w') as w:
            w.write(s)


if __name__ == '__main__':
    rst_watcher = Watcher(CONTENT_PATH, OUTPUT_PATH, func=make)
    rst_watcher.activate_and_serve()