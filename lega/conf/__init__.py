"""\
Configuration Module provides a dictionary-like with configuration settings.
It also loads the logging settings when ``setup`` is called.

* The ``--log <file>`` argument is used to configuration where the logs go.
  Without it, there is no logging capabilities.
* The ``<file>`` can be a path to an ``INI`` or ``YAML`` format, or a string
  representing the defaults loggers (ie default, debug or syslog)
* The ``--conf <file>`` allows the user to override the configuration settings.
  The settings are loaded, in order:

    * from environment variables (the naming convetion is according to
    ``default.ini`` ``section`` and ``option``, both uppercased e.g. KEYSERVER_ENDPOINT_PGP or POSTGRES_DB);
    * from ``default.ini`` (located in the package)
    * from ``/etc/ega/conf.ini``
    * from the file specified as the ``--conf`` argument.
* ``--list`` argument lists the content of the configuration file
The files must be either in ``INI`` format or in ``YAML`` format, in
which case, it must end in ``.yaml`` or ``.yml``.
"""

import sys
import os
import configparser
import logging
from logging.config import fileConfig, dictConfig
import lega.utils.logging
from pathlib import Path
import yaml

_here = Path(__file__).parent
_config_files = [
    _here / 'defaults.ini',
    '/etc/ega/conf.ini'
]


class Configuration(configparser.ConfigParser):
    """Configuration from config_files or environment variables or config server (e.g. Spring Cloud Config)."""

    log_conf = None

    def _load_conf(self, args=None, encoding='utf-8'):
        """Load a configuration file from `args`."""
        # Finding the --conf file
        try:
            conf_file = Path(args[args.index('--conf') + 1]).expanduser()
            if conf_file not in _config_files:
                _config_files.append(conf_file)
                print(f"Overriding configuration settings with {conf_file}", file=sys.stderr)
        except ValueError:
            pass
        except (TypeError, AttributeError):  # if args = None
            pass
        except IndexError:
            print("Wrong use of --conf <file>", file=sys.stderr)
            raise ValueError("Wrong use of --conf <file>")

        self.read(_config_files, encoding=encoding)

    def _load_log_file(self, filename):
        """Try to load `filename` as configuration file."""
        if not filename:
            print('No logging supplied', file=sys.stderr)
            self.log_conf = None
            return

        assert(isinstance(filename, str))

        # Try first if it is a default logger
        _logger = _here / f'loggers/{filename}.yaml'
        if _logger.exists():
            with open(_logger, 'r') as stream:
                dictConfig(yaml.load(stream))
                self.log_conf = _logger
                return

        # Otherwise trying it as a path
        filename = Path(filename)

        if not filename.exists():
            print(f"The file '{filename}' does not exist", file=sys.stderr)
            self.log_conf = None
            return

        if filename.suffix in ('.yaml', '.yml'):
            with open(filename, 'r') as stream:
                dictConfig(yaml.load(stream))
                self.log_conf = filename
                return

        if filename.suffix in ('.ini', '.INI'):
            with open(filename, 'r') as stream:
                fileConfig(filename)
                self.log_conf = filename
                return

        print(f"Unsupported log format for {filename}", file=sys.stderr)
        self.log_conf = None

    def _load_log_conf(self, args=None):
        """Finding the `--log` file."""
        try:
            lconf = args[args.index('--log') + 1]
            self._load_log_file(lconf)
        except ValueError:
            self._load_log_file(self.get('DEFAULT', 'log', fallback=None))
        except (TypeError, AttributeError):  # if args = None
            pass  # No log conf
        except IndexError:
            print("Wrong use of --log <file>", file=sys.stderr)
        except Exception as e:
            print('Error with --log:', repr(e), file=sys.stderr)

    def setup(self, args=None, encoding='utf-8'):
        """Setup, that is all."""
        self._load_conf(args, encoding)
        self._load_log_conf(args)

    def __repr__(self):
        """Show the configuration files."""
        res = 'Configuration files:\n\t* ' + '\n\t* '.join(str(s) for s in _config_files)
        if self.log_conf:
            res += '\nLogging settings loaded from ' + str(self.log_conf)
        return res

    def get_value(self, section, option, conv=str, default=None, raw=False):
        """"Get a specific value for this paramater either as env variable or from config files.

        ``section`` and ``option`` are mandatory while ``conv``, ``default`` (fallback) and ``raw`` are optional.
        """
        result = os.environ.get('_'.join([section.upper(), option.upper()]), None)
        if result:
            return self._convert(result, conv)
        elif result is None and self.has_option(section, option):
            return self._convert(self.get(section, option, fallback=default, raw=raw), conv)

    def _convert(self, value, conv):
        """Convert value properly to ``str``, ``float`` or ``int``, also consider ``bool`` type."""
        if conv == bool:
            val = value.lower()
            if val in ('y', 'yes', 't', 'true', 'on', '1'):
                return True
            elif val in ('n', 'no', 'f', 'false', 'off', '0'):
                return False
            else:
                raise ValueError(f"Invalid truth value: {val}")
        else:
            return conv(value)


CONF = Configuration()


class KeysConfiguration(configparser.ConfigParser):
    """Parse keyserver configuration."""

    def __init__(self, args=None, encoding='utf-8'):
        """Load a configuration file from `args`."""
        super().__init__()
        # Finding the --keys file. Raise Error otherwise
        filepath = Path(args[args.index('--keys') + 1]).expanduser()

        if filepath.suffix != '.enc':
            conf = filepath.open(encoding=encoding).read()
        else:
            # Quick solution, just for testing, to decrypt the encrypted keys configuration file (keys.ini)
            # The 'LEGA_PASSWORD' must be defined
            assert 'LEGA_PASSWORD' in os.environ, "LEGA_PASSWORD must be defined as an environment variable"
            s = "openssl enc -aes-256-cbc -d -in {} -k {}".format(str(filepath), os.environ.get('LEGA_PASSWORD',None))
            from subprocess import Popen, PIPE
            with Popen(s.split(), stdout=PIPE) as proc:                
                conf = proc.stdout.read().decode()

        self.read_string(conf, source=str(filepath))
