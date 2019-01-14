#!/usr/bin/env python2.7
# coding: utf_8


import getopt
import os
import sys

import foostitch


def usage(*args):
    if args:
        print >> sys.stderr, "{0}: {1}".format(os.path.basename(sys.argv[0]), args[0])
    print >> sys.stderr, "usage: {0} [option]* [recipe]".format(os.path.basename(sys.argv[0]))
    print >> sys.stderr, "Options and arguments:"
    print >> sys.stderr, "  -o, --output-file <arg>        : filename for output"
    print >> sys.stderr, "  -c, --configuration-file <arg> : filename for configuration"
    print >> sys.stderr, "  -t, --template-directory       : directory with templates"
    print >> sys.stderr, "  <recipe>                       : recipe name"
    sys.exit(1)


def parse_command_line(cfg):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:c:t:", [
            "output-file=",
            "configuration-file=",
            "template-directory="
        ])
    except getopt.GetoptError as err:
        usage(err)

    if len(args) < 1:
        usage("missing recipe")

    cfg.recipe_name = args[0]

    output_file = None

    for opt, arg in opts:
        if opt in ('-o', '--output-file'):
            output_file = arg
        elif opt in ('-c', '--configuration-file'):
            cfg.configuration_files.append(arg)
        elif opt in ('-t', '--template-directory'):
            cfg.template_directories.append(arg)
        else:
            assert False

    return cfg, output_file


def main():
    try:
        cfg = foostitch.Session()
        cfg, output_file = parse_command_line(cfg)
        body = cfg.render()

        if output_file:
            with open(output_file, "wb") as f:
                f.write(body)
        else:
            print body
    except Exception as e:
        usage(e)


if __name__ == "__main__":
    main()
