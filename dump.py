#!/usr/bin/env python3
import argparse
from configparser import ConfigParser

import os
import os.path
import sys
import time
import importlib
import inspect
import requests

import sentry_sdk
import vk_api

NAME = 'VK Dump Tool'
VERSION = '0.9.10'
API_VERSION = '5.95'


# ----------------------------------------------------------------------------


class CUI:
    """
    Console User interface
    """
    _width = 0
    _height = 0

    _colors = {
        'red': '\x1b[31m',
        'green': '\x1b[32m',
        'yellow': '\x1b[33m',
        'blue': '\x1b[36m',
        'purple': '\x1b[35m',
        'cyan': '\x1b[36m',
        'white': '\x1b[37m'
    }
    _mods = {
        'nc': '\x1b[0m',
        'bold': '\x1b[1m'
    }

    _ANSI_AVAILABLE = True

    def __init__(self):
        if sys.platform.startswith('win32'):
            from platform import platform
            if int(platform().split('-')[1]) < 10:
                import colorama
                colorama.init()
                self._ANSI_AVAILABLE = False
            else:
                os.system('')
                self._ANSI_AVAILABLE = True
        elif sys.platform.startswith('linux') or \
             sys.platform.startswith('darwin'):
            self._ANSI_AVAILABLE = True

        try:
            self._width, self._height = os.get_terminal_size()
        except OSError as e:
            if e.errno == 25:
                print('Данное устройство не поддерживает полноценную работу с консолью. Используйте CLI.')
                raise SystemExit(1)
            else:
                raise

        if self._ANSI_AVAILABLE:
            sys.stdout.write(f'\x1b]0;{NAME}\x07')

    @staticmethod
    def _clear():
        """Clears console"""
        print('\x1b[2J', '\x1b[1;1H', sep='', end='', flush=True)

    def _print_slow(self, *args, **kwargs):
        """Prints msg symbol by symbol with some delay"""
        if self._ANSI_AVAILABLE:
            print('\x1b[?25l', end='')
        for s in args:
            if (s.find('\x1b') == -1) and kwargs.get('slow'):
                for ch in s:
                    sys.stdout.write(ch)
                    sys.stdout.flush()
                    time.sleep(kwargs.get('delay') or 1/50)
            else:
                print(s, end='')
        if self._ANSI_AVAILABLE:
            print('\x1b[?25h', end=kwargs['sep'])

    def _print_center(self, msg, **kwargs):
        """Prints msg at center of console"""
        if not kwargs.get('offset'):
            kwargs['offset'] = 0
        if not kwargs.get('sep'):
            kwargs['sep'] = '\n'

        if isinstance(msg, list):
            for i, val in enumerate(msg):
                kwargs['color'][i] = self._colors[kwargs['color'][i]] \
                                     if ('color' in kwargs and kwargs['color'][i]) \
                                     else self._mods['nc']
                if 'mod' in kwargs and kwargs['mod'][i]:
                    kwargs['color'][i] += self._mods[kwargs['mod'][i]]
                self._print_slow(kwargs['color'][i] + '\x1b[{y};{x}H'.format(
                    x=int(self._width/2 - len(val)/2),
                    y=int(self._height/2 - len(msg)/2+i)+1 - kwargs['offset']),
                    val, self._mods['nc'], **kwargs
                )
        else:
            kwargs['color'] = self._colors[kwargs['color']] \
                              if kwargs.get('color') \
                              else self._mods['nc']
            if 'mod' in kwargs:
                kwargs['color'] += self._mods[kwargs['mod']]

            self._print_slow(kwargs['color'] + '\x1b[{y};{x}H'.format(
                x=int(self._width/2 - len(msg)/2),
                y=int(self._height/2 - (len(msg.split('\n'))/2)+1-kwargs['offset'])),
                msg, self._mods['nc'], **kwargs)

    def welcome(self):
        """
        Shows welcome screen
        """
        if self._ANSI_AVAILABLE:
            sys.stdout.write('\x1b]0;{}\x07'.format(NAME))
        self._clear()
        self._print_center([NAME, 'v' + VERSION],
                           color=['green', None],
                           mod=['bold', None],
                           slow=True, delay=1/50)

        if self._ANSI_AVAILABLE:
            print('\x1b[?25l')
        time.sleep(2)
        if self._ANSI_AVAILABLE:
            print('\x1b[?25h')

    def goodbye(self):
        """
        Shows goodbye screen
        """
        self._clear()
        self._print_center(['Спасибо за использование скрипта :з', '', 'Made with ♥ by hikiko4ern'],
                           color=['green', None, 'red'], mod=['bold', None, 'bold'], offset=-1)
        if self._ANSI_AVAILABLE:
            print('\x1b[?25h')
        raise SystemExit

    @staticmethod
    def _print_user_info(dmp):
        """
        Prints info about logged user

        dmp: Dumper object
        """
        log_info = [
            'Login: \x1b[1;36m{}\x1b[0m'.format(dmp._account.get('phone') or '***'),
            'Name: \x1b[1;36m{fn} {ln}\x1b[0m'.format(
                fn=dmp._account.get('first_name'), ln=dmp._account.get('last_name'))
        ]
        ln = max([len(l) for l in log_info])

        print('\x1b[1;31m┌' + '─' * (ln - 9), end='┐\x1b[0m\n')
        for l in log_info:
            print('\x1b[1;31m│\x1b[0m ' + l + ' '*(ln-len(l)+1) + '\x1b[1;31m│\x1b[0m')
        print('\x1b[1;31m└' + '─' * (ln - 9), end='┘\x1b[0m\n')

    def menu(self, dmp, title, actions, **kwargs):
        """
        Prints menu

        dmp: Dumper object

        title: title to be printed before the list of actions
        actions: list of tuples ('name1', function1)
                 # use False as name for blank line

        kwargs:
            add_actions: object {
                                    'key1': {
                                                name: str,
                                                action: function,
                                                ? args: *args,
                                                ? nl: bool
                                    },
                                    'key2': {...}
                                }
        """
        self._clear()
        self._print_user_info(dmp)
        print()

        print(title, end='\n\n')

        num = 0
        for a in actions:
            if a[1] is False:
                print()
            else:
                print('{clr}[{ind}]{nc} {name}'.format(ind=num+1,
                                                       name=a[0],
                                                       clr=self._colors['blue'],
                                                       nc=self._mods['nc']))
                num += 1

        if 'add_actions' in kwargs:
            for key in kwargs['add_actions']:
                act = kwargs['add_actions'][key]
                if act.get('nl'):
                    print()
                print('{clr}[{key}]{nc} {name}'.format(key=key.upper(),
                                                       name=act['name'],
                                                       clr=self._colors['blue'],
                                                       nc=self._mods['nc']))

        print()
        try:
            choice = input('> ').lower()
            args = None

            if choice == 'magic':
                self._print_center(
                    chr(0x4e)+chr(0x59)+chr(0x41)+chr(0x48),
                    color='cyan',
                    mod='bold',
                    slow=True,
                    delay=1/50,
                    offset=-1
                )
                time.sleep(2)
                return None, None
            elif ('add_actions' in kwargs) and (choice in kwargs['add_actions']):
                if 'args' in kwargs['add_actions'][choice]:
                    args = kwargs['add_actions'][choice]['args']
                choice = kwargs['add_actions'][choice]['action']
            else:
                if int(choice) not in range(1, len(actions)+1):
                    raise IndexError
                choice = actions[int(choice)-1][1]
            return choice, args
        except IndexError:
            self._print_center('Выберите действие из доступных',
                               color='red', mode='bold')
            time.sleep(2)
            self._clear()
            return self.menu(dmp, title, actions, **kwargs)
        except ValueError:
            return self.menu(dmp, title, actions, **kwargs)
        except KeyboardInterrupt:
            self.goodbye()

    def modules_menu(self, dmp):
        """
        Modules viewer

        dmp: Dumper object
        """
        def modules_wp():
            import webbrowser
            webbrowser.open('https://github.com/hikiko4ern/vk_dump/tree/master/modules')

        while True:
            dmp._load_modules(True)
            modules = {}
            for f in next(os.walk('modules'))[2]:
                if not f.startswith('__'):
                    modules[f] = []

            for name, value in inspect.getmembers(dmp):
                if name.startswith('dump_') and not name.startswith('dump_menu_'):
                    modules[os.path.basename(inspect.getfile(value))].append(value.__name__)

            actions = []
            for n in modules:
                if modules[n]:
                    actions.append(('{clr}{n}{nc} ({modules})'.format(
                                 clr=self._colors['yellow'], n=n, nc=self._mods['nc'],
                                 modules=', '.join(modules[n])), None))

            fun, args = dmp._interface.menu(dmp, title='Установленные модули:', actions=actions,
                                            add_actions={'m': {'name': 'Скачать дополнительные модули', 'action': modules_wp, 'nl': True},
                                                         'r': {'name': 'Перезагрузить модули', 'action': dmp._load_modules, 'args': True},
                                                         '0': {'name': 'В меню', 'action': None, 'nl': True}})
            if fun:
                if args:
                    fun(args)
                else:
                    fun()
            else:
                break
        return False

    def settings_menu(self, dmp):
        """
        Settings editor

        dmp: Dumper object
        """
        self._clear()
        self._print_user_info(dmp)
        print()
        print('Настройки:\n')

        i = 0
        for s in dmp._settings:
            value = dmp._settings[s]

            if isinstance(value, bool):
                color = self._colors['green' if value else 'red']
                value = 'Да' if value else 'Нет'

            print('{ind_clr}[{ind}]{nc} {name}: {clr}{value}{nc}'.format(
                ind=i+1,
                name=dmp._settings_names[s],
                value=value,
                ind_clr=self._colors['blue'],
                clr=color if 'color' in locals() else self._colors['yellow'],
                nc=self._mods['nc']
            ))
            i += 1

            if 'color' in locals():
                del color

        print('\n{clr}[0]{nc} В меню'.format(clr=self._colors['blue'],
                                             nc=self._mods['nc']))

        print()
        try:
            choice = int(input('> '))
            if choice == 0:
                return 0
            elif choice not in range(1, len(dmp._settings) + 1):
                raise IndexError
            else:
                s = [s for s in dmp._settings][choice - 1]
                new = None
                if isinstance(dmp._settings[s], bool):
                    dmp._settings[s] = not dmp._settings[s]
                else:
                    while not isinstance(new, type(dmp._settings[s])) or (s == 'REPLACE_CHAR' and new in dmp._INVALID_CHARS):
                        try:
                            print('\nВведите новое значение для {clr}{}{nc} ({type_clr}{type}{nc})\n> '.format(
                                s,
                                clr=self._colors['red'],
                                type_clr=self._colors['yellow'],
                                nc=self._mods['nc'],
                                type=type(dmp._settings[s])), end='')
                            new = input()
                            if not new:
                                new = dmp._settings[s]
                                break
                            if isinstance(dmp._settings[s], int):
                                new = int(new)
                        except ValueError:
                            continue
                    dmp._settings[s] = new
                dmp._settings_save()

            self.settings_menu(dmp)
        except IndexError:
            self._print_center('Выберите одну из доступных настроек',
                               color='red', mode='bold')
            time.sleep(2)
            self._clear()
            self.settings_menu(dmp)
        except ValueError:
            self.settings_menu(dmp)
        except KeyboardInterrupt:
            self.goodbye()

    def update(self, dmp, **kwargs):
        """
        Updates script and modules

        dmp: Dumper obj
        """
        from modules._download import _download
        import itertools
        from multiprocess import Pool

        def apply_args_and_kwargs(fn, args, kwargs):
            return fn(*args, **kwargs)

        def starmap_with_kwargs(pool, fn, args_iter, kwargs_iter):
            args_for_starmap = zip(itertools.repeat(fn), args_iter, kwargs_iter)
            return pool.starmap(apply_args_and_kwargs, args_for_starmap)

        if kwargs.get('quite'):
            print('Проверка на наличие обновлений...')
        else:
            self._clear()
            self._print_center([f'{NAME} [{VERSION}]', '', 'Проверка на наличие обновлений...'],
                               color=['green', None, 'yellow'])

        res = requests.get('https://api.github.com/repos/hikiko4ern/vk_dump/releases/latest').json()
        queue = {}
        if 'tag_name' in res:
            cv = [int(i) for i in VERSION.split('-dev')[0].split('.')]
            nv = [int(i) for i in res['tag_name'].split('v')[1].split('-dev')[0].split('.')]
            if (nv[0]>cv[0]) or (nv[0]==cv[0] and nv[1]>cv[1]) or (nv[0]==cv[0] and nv[1]==cv[1] and nv[2]>cv[2]):
                if kwargs.get('quite'):
                    print('Найдена новая версия ({})'.format(res['tag_name']))
                else:
                    self._print_center('Найдена новая версия ({})'.format(
                        res['tag_name']), color='green', mod='bold', offset=-2)

                for a in res['assets']:
                    if 'name' in a:
                        queue[a['name']] = a['browser_download_url']

                with Pool(dmp._settings['POOL_PROCESSES']) as pool:
                    kw = {'force': True, 'text_mode': True}
                    q = [queue[k] for k in queue.keys() if (k != 'dump.py' and os.path.exists(os.path.join('modules', k)))]
                    rem = starmap_with_kwargs(pool, _download,
                                              zip(
                                                  itertools.repeat(dmp.__class__),
                                                  q, itertools.repeat('modules')),
                                              itertools.repeat(kw))
                if kwargs.get('quite'):
                    print('Обновлено модулей: {}'.format(sum(filter(None, rem))))
                else:
                    self._print_center('Обновлено модулей: {}'.format(
                        sum(filter(None, rem))), color='green', mod='bold', offset=-3)

                if queue.get('dump.py'):
                    if _download(dmp.__class__, queue['dump.py'], os.getcwd(), force=True, text_mode=True):
                        if kwargs.get('quite'):
                            print('Обновление успешно!\nПерезапустите программу вручную :3')
                        else:
                            self._print_center(['Обновление успешно!', 'Перезапустите программу вручную :3'],
                                               color=['green', 'yellow'], mod=['bold', 'bold'], offset=-5)
                        raise SystemExit
                    else:
                        if kwargs.get('quite'):
                            print('Не удалось обновить\nСкачайте и замените dump.py вручную\nhttps://github.com/hikiko4ern/vk_dump/releases/latest')
                        else:
                            self._print_center(['Не удалось обновить', 'Скачайте и замените dump.py вручную', 'https://github.com/hikiko4ern/vk_dump/releases/latest'],
                                               color=['red', 'yellow', None], mod=['bold', 'bold', None], offset=-3)
                        raise SystemExit
            else:
                if kwargs.get('quite'):
                    print('Обновлений не найдено')

    def login(self, dmp, *msg):
        """
        Login interface

        dmp: Dumper obj
        msg: str to print
        """
        def auth_handler():
            key = input('Введите код двухфакторой аутентификации: ')
            remember_device = True
            return key, remember_device

        def captcha_handler(captcha):
            key = input(f'Введите капчу {captcha.get_url()} : ').strip()
            return captcha.try_again(key)

        if cli_args.dump:
            if msg:
                print(msg[0])
                raise SystemExit(1)
        else:
            self._clear()
            self._print_center(msg[0] if msg else '[для продолжения необходимо войти]',
                               color='red', mod='bold', offset=2, delay=1/50)

        try:
            if cli_args.token:
                vk_session = vk_api.VkApi(token=cli_args.token,
                                          auth_handler=auth_handler,
                                          api_version=API_VERSION)
            else:
                if cli_args.login and not msg:
                    login = cli_args.login
                    password = cli_args.password if cli_args.password else ''
                else:
                    print('\tlogin: {}'.format(self._colors['cyan']), end='')
                    login = input()
                    print(self._mods['nc'], '\tpassword: {}'.format(self._colors['cyan']), sep='', end='')
                    password = input()
                    print(self._mods['nc'], end='')

                vk_session = vk_api.VkApi(login, password,
                                          app_id=2685278,
                                          api_version=API_VERSION,
                                          scope=2+4+8+16+4096+65536+131072,
                                          auth_handler=auth_handler,
                                          captcha_handler=captcha_handler)
                vk_session.auth()

            dmp.auth(vk_session, interface=self)
        except KeyboardInterrupt:
            self.goodbye()
        except vk_api.exceptions.ApiError:
            self.login(dmp, 'Произошла ошибка при попытке авторизации.')
        except vk_api.exceptions.BadPassword:
            self.login(dmp, 'Неправильный пароль.')
        except vk_api.exceptions.Captcha:
            self.login(dmp, 'Необходим ввод капчи.')
        except Exception as e:
            raise e


# ----------------------------------------------------------------------------


class Dumper:
    __modules = None

    _AVAILABLE_THREADS = os.cpu_count()

    _settings = {
        'REPLACE_SPACES': False,  # заменять пробелы на _
        'REPLACE_CHAR': '_',  # символ для замены запрещённых

        'POOL_PROCESSES': 4*_AVAILABLE_THREADS,  # макс. число создаваемых процессов
        'LIMIT_VIDEO_PROCESSES': True,  # ограничивать число процессов при загрузке видео?

        'DIALOG_APPEND_MESSAGES': False,  # дописывать новые сообщения в файл вместо полной перезаписи?
        'KEEP_DIALOG_NAMES': True,  # сохранять имена файлов в случае изменения имени диалога?
        'SAVE_DIALOG_ATTACHMENTS': True,  # сохранять вложения из диалогов?
        'HIDE_EXCLUDED_DIALOGS': True
    }

    _settings_names = {
        'REPLACE_SPACES': 'Заменять пробелы на символ "_"',
        'REPLACE_CHAR': 'Символ для замены запрещённых в имени файла',

        'POOL_PROCESSES': 'Число создаваемых процессов при мультипоточной загрузке',
        'LIMIT_VIDEO_PROCESSES': 'Ограничивать число процессов при загрузке видео',

        'DIALOG_APPEND_MESSAGES': 'Дописывать новые сообщения в файл вместо полной перезаписи',
        'KEEP_DIALOG_NAMES': 'Сохранять название диалога в случае его изменения',
        'SAVE_DIALOG_ATTACHMENTS': 'Сохранять вложения из диалогов',
        'HIDE_EXCLUDED_DIALOGS': 'Не выводить информацию об исключённых диалогах'
    }

    _INVALID_CHARS = ['\\', '/', ':', '*', '?', '<', '>', '|', '"', '$']

    _DUMP_DIALOGS_ONLY = []
    _EXCLUDED_DIALOGS = []

    def __init__(self, interface=None):
        self._interface = interface

        config = ConfigParser()
        if not config.read('settings.ini'):
            with open('settings.ini', 'w') as cf:
                config['SETTINGS'] = Dumper._settings
                config['EXCLUDED_DIALOGS'] = {'id': ','.join([str(i) for i in Dumper._EXCLUDED_DIALOGS])}
                config['DUMP_DIALOGS_ONLY'] = {'id': ','.join([str(i) for i in Dumper._DUMP_DIALOGS_ONLY])}
                config.write(cf)
        else:
            for s in config['SETTINGS']:
                c = config['SETTINGS'][s]
                try:
                    Dumper._settings[s.upper()] = int(c)
                except ValueError:
                    Dumper._settings[s.upper()] = True if c == 'True' else \
                                                  False if c == 'False' else \
                                                  c
            try:
                if len(config['EXCLUDED_DIALOGS']['id']) > 0:
                    for pid in config['EXCLUDED_DIALOGS']['id'].split(','):
                        try:
                            Dumper._EXCLUDED_DIALOGS.append(int(pid))
                        except ValueError:
                            if pid[0] == 'c':
                                Dumper._EXCLUDED_DIALOGS.append(2000000000+int(pid[1:]))
            except KeyError:
                config['EXCLUDED_DIALOGS'] = {'id': ','.join([str(i) for i in Dumper._EXCLUDED_DIALOGS])}
                Dumper._settings_save()

            try:
                if len(config['DUMP_DIALOGS_ONLY']['id']) > 0:
                    for pid in config['DUMP_DIALOGS_ONLY']['id'].split(','):
                        try:
                            Dumper._DUMP_DIALOGS_ONLY.append(int(pid))
                        except ValueError:
                            if pid[0] == 'c':
                                Dumper._DUMP_DIALOGS_ONLY.append(2000000000+int(pid[1:]))
            except KeyError:
                config['DUMP_DIALOGS_ONLY'] = {'id': ','.join([str(i) for i in Dumper._DUMP_DIALOGS_ONLY])}
                Dumper._settings_save()

        self._load_modules()

    def auth(self, vk_session, interface=None):
        self._interface = self._interface or interface
        self._vk_session = vk_session
        self._vk = self._vk_session.get_api()
        self._vk_tools = vk_api.VkTools(self._vk)

        # self._vk.stats.trackVisitor()
        self._account = self._vk.account.getProfileInfo()

    def _load_modules(self, reload=False):
        if reload:
            for m in dir(self.__modules):
                if not m.startswith('__'):
                    self.__delattr__(m)
            self.__modules = importlib.reload(self.__modules)
        else:
            self.__modules = importlib.import_module('modules')
        for m in dir(self.__modules):
            if not m.startswith('__'):
                self.__setattr__(m, getattr(self.__modules, m))

    @staticmethod
    def _settings_save():
        config = ConfigParser()

        with open('settings.ini', 'w') as cf:
            config['SETTINGS'] = Dumper._settings
            config['EXCLUDED_DIALOGS'] = {'id': ','.join([str(i) for i in Dumper._EXCLUDED_DIALOGS])}
            config['DUMP_DIALOGS_ONLY'] = {'id': ','.join([str(i) for i in Dumper._DUMP_DIALOGS_ONLY])}
            config.write(cf)

    def _dump_all(self):
        for name, func in inspect.getmembers(self):
            if name.startswith('dump_'):
                func(self)
                print()

    def _dump_all_fave(self):
        for name, func in inspect.getmembers(self):
            if name.startswith('dump_fave_'):
                func(self)
                print()

# ----------------------------------------------------------------------------


if __name__ == '__main__':
    sentry_sdk.init(
        'https://588cc3d709f84953b6779479eecd931e@sentry.io/1452327',
        release=VERSION)
    with sentry_sdk.configure_scope() as scope:
        if sys.platform == 'win32':
            from platform import platform
            scope.set_tag('os', f'{sys.platform}_{platform().split("-")[1]}')
        else:
            scope.set_tag('os', sys.platform)

    dmp = Dumper()
    ch = dict([[n.replace('dump_', ''), v] for n, v in inspect.getmembers(dmp)
               if (n.startswith('dump_') or
                   n.startswith('dump_fave_')) and
                   not n.startswith('dump_menu_')])

    # cli
    parser = argparse.ArgumentParser(usage='%(prog)s [options]')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('--update', action='store_true', help='update only')
    auth = parser.add_argument_group('Аутентификация')
    auth.add_argument('-l', '--login', type=str, metavar='\b', help='логин')
    auth.add_argument('-p', '--password', type=str, metavar='\b', help='пароль')
    auth.add_argument('-t', '--token', type=str, metavar='\b', help='access_token')
    dump = parser.add_argument_group('Дамп данных')
    dump.add_argument('--dump', type=str, nargs='*',
                      choices=ch.keys(),
                      help='Данные для сохранения.')

    cli_args = parser.parse_args()
    # end of cli

    cui = CUI()
    cui.update(dmp, quite=(cli_args.dump or cli_args.update))

    if cli_args.update:
        raise SystemExit

    if cli_args.dump:
        if (not cli_args.login or not cli_args.password) and (not cli_args.token):
            print('┌────────────────────────────────────────────────────────┐')
            print('│  Необходимо передать либо логин и пароль, либо токен.  │')
            print('└────────────────────────────────────────────────────────┘')
        else:
            cui.login(dmp)
            for d in cli_args.dump:
                ch.get(d)(dmp)
            print()
    else:
        cui.welcome()
        cui.login(dmp)
        while True:
            dmp._load_modules(True)
            actions = []
            for name, value in inspect.getmembers(dmp):
                if name.startswith('dump_') and not name.startswith('dump_fave_'):
                    actions.append((value.__doc__.splitlines()[0], value))

            fun, args = cui.menu(dmp, title='Дамп данных:', actions=actions,
                                 add_actions={'f': {'name': 'Все данные', 'action': dmp._dump_all, 'nl': True},
                                              'm': {'name': 'Модули', 'action': cui.modules_menu, 'args': dmp, 'nl': True},
                                              's': {'name': 'Настройки', 'action': cui.settings_menu, 'args': dmp},
                                              'q': {'name': 'Выход', 'action': cui.goodbye}})
            if fun:
                if fun.__name__.startswith('dump_'):
                    if not fun(dmp) is False:
                        print('\n{clr}Сохранение завершено :з{nc}'.format(
                              clr=cui._colors['green'], nc=cui._mods['nc']))
                        print('\n[нажмите {clr}Enter{nc} для продолжения]'.format(
                              clr=cui._colors['cyan'], nc=cui._mods['nc']), end='')
                        input()
                else:
                    if args:
                        fun(args)
                    else:
                        fun()
