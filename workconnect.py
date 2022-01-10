from typing import Optional
from plumbum import local, FG
from getpass import getpass
import sys
import pathlib
import configparser
import argparse
import tempfile

def local_gp():
    return local['globalprotect']

def globalprotect_disconnect():
    x = local_gp()['disconnect']
    x.run_fg(retcode=1)

def globalprotect_connect(portal, user):
    x = local_gp()['connect', '-p', portal, '-u', user]
    x.run_fg(retcode=1)

def globalprotect_isconnected():
    with tempfile.NamedTemporaryFile() as tmp:
        y = (local_gp()['show', '--status'] > tmp.name)
        z = y.run_fg(retcode=None)

        with open(tmp.name, 'r') as f:
            lines = f.readlines()
            return lines[-1].endswith('Connected\n')

def freerdp(multimon, user, server, password, domain, scale, fg):
    multimon_arg = '/multimon'
    sound_arg = '/sound'
    user_arg = f'/u:{user}'
    server_arg = f'/v:{server}'
    pass_arg = f'/p:{password}'
    domain_arg = f'/d:{domain}'
    scale_arg = f'/scale:{scale}'

    x = local['xfreerdp']
    y = x[multimon_arg, sound_arg, user_arg, server_arg, pass_arg, domain_arg, scale_arg]
    if fg:
        y.run_fg(retcode=0)
    else:
        y.run_bg(retcode=0)

def run_gp(config: configparser.ConfigParser):
    section = 'GlobalProtect'
    config_section = config[section]

    globalprotect_connect(config_section['Portal'], config_section['User'])

def run_status():
    if globalprotect_isconnected():
        print('Connected')
    else:
        print('Disconnected')

def run_rdp(config: configparser.ConfigParser, fg_arg: Optional[bool]):
    section = 'RDP'
    config_section = config[section]

    multimon = config_section.getboolean('Multimon')
    user = config_section['User']
    server = config_section['Server']
    domain = config_section['Domain']
    scale = config_section.getint('Scale')
 
    fg: bool = config_section.getboolean('FG')
    if fg_arg is not None:
        fg = fg_arg

    p = getpass('RDP Password:')

    freerdp(multimon, user, server, p, domain, scale, fg)


def run_connect_all(config: configparser.ConfigParser, fg_arg: Optional[bool]):
    if globalprotect_isconnected():
        print('GP already connected.')
    else:
        run_gp(config)
    run_rdp(config, fg_arg)


def default_config_path():
    return pathlib.Path.home() / '.config' / 'workconnect' / 'config.ini'

def main():
    #debug_args = ['-c', 'example_config.ini']

    parser = argparse.ArgumentParser(description="vpn + rdp")
    parser.add_argument("-c", "-config", type=str, help="config files", default=str(default_config_path()))

    subparsers = parser.add_subparsers(dest='subparser_name')

    gp_parser = subparsers.add_parser('gp', help='GlobalProtect')

    rdp_parser = subparsers.add_parser('rdp')

    d_parser = subparsers.add_parser('d', help='Disconnect')

    status_parser = subparsers.add_parser('status')


    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.c)

    if args.subparser_name == 'gp':
        run_gp(config)
    elif args.subparser_name == 'rdp':
        run_rdp(config, None)
    elif args.subparser_name == 'd':
        globalprotect_disconnect()
    elif args.subparser_name == 'status':
        run_status()
    elif args.subparser_name is None:
        run_connect_all(config, None)
    else:
        raise NotImplementedError

if __name__ == "__main__":
    sys.exit(main())
