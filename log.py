#!/usr/bin/env python
#
# Copyright 2012 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Logging support for Tornado. """
from __future__ import absolute_import, division, print_function, with_statement

import logging
import logging.handlers
import sys
import time
import datetime
import os 

logger = ''
try:
    import curses
except ImportError:
    curses = None


def _stderr_supports_color():
    color = False
    if curses and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except Exception:
            pass
    return color


if type('') is not type(b''):
    def u(s):
        return s

    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')

    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring


class LogFormatter(logging.Formatter):
    def __init__(self, color=True, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._color = color and _stderr_supports_color()
        if self._color:
            fg_color = (curses.tigetstr("setaf") or
                        curses.tigetstr("setf") or "")
            if (3, 0) < sys.version_info < (3, 2, 3):
                fg_color = unicode_type(fg_color, "ascii")
            self._colors = {
                logging.DEBUG: unicode_type(curses.tparm(fg_color, 4),  # Blue
                                            "ascii"),
                logging.INFO: unicode_type(curses.tparm(fg_color, 2),  # Green
                                           "ascii"),
                logging.WARNING: unicode_type(curses.tparm(fg_color, 3),  # Yellow
                                              "ascii"),
                logging.ERROR: unicode_type(curses.tparm(fg_color, 1),  # Red
                                            "ascii"),
            }
            self._normal = unicode_type(curses.tigetstr("sgr0"), "ascii")

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        # guaranteed by logging
        assert isinstance(record.message, basestring_type)
        record.asctime = time.strftime(
            "%H:%M:%S", self.converter(record.created))
        # prefix = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]' % \
        #          record.__dict__
        prefix = '[%(levelname)1.1s %(asctime)s]' % \
                 record.__dict__
        if self._color:
            prefix = (self._colors.get(record.levelno, self._normal) +
                      prefix + self._normal)

        def safe_unicode(s):
            return s
#            try:
#                return s.decode("utf-8")
#            except UnicodeDecodeError:
#                return repr(s)

        formatted = prefix + " " + safe_unicode(record.message)
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            lines = [formatted.rstrip()]
            lines.extend(safe_unicode(ln)
                         for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)
        return formatted.replace("\n", "\n    ")

def get_logger(modulename="", level=logging.INFO):  
    file_name = os.path.join(os.getcwd(),"zipalign.log")
  
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        filename=file_name,
                        filemode="a")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logger = logging.getLogger(modulename)
    logger.addHandler(console)



   
    return logger

