# coding=utf-8

import sys
import os
import datetime
import codecs
import unicodedata

_bull_dir = os.path.join(os.path.expanduser('~'), ".bulldogis")
_log_file = os.path.join(_bull_dir, 'bulldogis.log')

class ConsoleProgressDisplay(object):
    def __init__(self):
        if sys.stdout.isatty():
            sys.stdout.write("  0%")
            sys.stdout.flush()

    def set_ratio(self, ratio):
        if sys.stdout.isatty():
            sys.stdout.write("\b"*4+"% 3d%%"%(int(ratio*100)))
            sys.stdout.flush()

    def __del__(self):
        if sys.stdout.isatty():
            sys.stdout.write("\n")
        else:
            sys.stdout.write("100%\n")
        sys.stdout.flush()

class SilentLogger(object):
    def __init__(self):
        pass

    def error(self, title, message):
        sys.stderr.write("ERROR: " + message + "\n")

    def warning(self, title, message):
        pass

    def notice(self, title, message):
        pass

    def progress(self, title, message):
        sys.stdout.write("PROGRESS: %s "%(message))
        return ConsoleProgressDisplay()

    def clear_progress(self):
        if sys.stdout.isatty():
            sys.stdout.flush()
            sys.stdout.write("\n")

class ConsoleLogger(object):
    def __init__(self):
        pass

    def error(self, title, message):
        sys.stderr.write("ERROR: " + message + "\n")

    def warning(self, title, message):
        sys.stderr.write("WARNING: " + message + "\n")

    def notice(self, title, message):
        sys.stdout.write("NOTICE: " + message + "\n")

    def progress(self, title, message):
        sys.stdout.write("PROGRESS: %s "%(message))
        return ConsoleProgressDisplay()

    def clear_progress(self):
        if sys.stdout.isatty():
            sys.stdout.flush()
            sys.stdout.write("\n")

class LogManager(object):
    def __init__(self, logger=ConsoleLogger(), app_name="BulldoGis"):
        self.logger = logger
        self.title = app_name

    def error(self, message):
        normalized_message = self.__normalize(message)
        with codecs.open(_log_file, 'a') as file:
            file.write(datetime.datetime.now().strftime("\n%d/%m/%Y %H:%M") + ': ERROR\n' + normalized_message + '\n')
        self.logger.error(self.title, normalized_message)

    def warning(self, message):
        normalized_message = self.__normalize(message)
        with codecs.open(_log_file, 'a') as file:
            file.write(datetime.datetime.now().strftime("\n%d/%m/%Y %H:%M") + ': WARNING\n' + normalized_message + "\n")
        self.logger.warning(self.title, normalized_message)

    def notice(self, message):
        normalized_message = self.__normalize(message)
        with codecs.open(_log_file, 'a') as file:
            file.write(datetime.datetime.now().strftime("\n%d/%m/%Y %H:%M") + ': NOTICE\n' + normalized_message + "\n")
        self.logger.notice(self.title, normalized_message)

    def continuous_notice(self, message):
        normalized_message = self.__normalize(message)
        with codecs.open(_log_file, 'a') as file:
            file.write(normalized_message + "\n")
        self.logger.notice(self.title, normalized_message)

    def silent_notice(self, message):
        normalized_message = self.__normalize(message)
        with codecs.open(_log_file, 'a') as file:
            file.write(datetime.datetime.now().strftime("\n%d/%m/%Y %H:%M") + ': NOTICE\n' + normalized_message + "\n")

    def progress(self, message):
        normalized_message = self.__normalize(message)
        return self.logger.progress(self.title, normalized_message)

    def clear_progress(self):
        self.logger.clear_progress()

    def __normalize(self, message):
        # TODO remove this function, it shouldn't be necessary in python3 (test on windows required)
        try:
            if not isinstance(message, str) and sys.stdin.encoding is not None:
                message = message.decode(sys.stdin.encoding)
            normalized_message = message # unicodedata.normalize('NFKD', str(message)).encode('ASCII', 'ignore')
        except Exception as e:
            raise TypeError("Error handling following text in log manager:\n{}".format(message))
        return normalized_message

    def cleanup(self):
        open(_log_file, 'w').close()
