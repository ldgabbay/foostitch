#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


import getopt
import os
import sys

from foo.stitch import Session


def usage():
    print >> sys.stderr, "usage: {0} [option]* [recipe]".format(os.path.basename(sys.argv[0]))
    print >> sys.stderr, "Options and arguments:"
    print >> sys.stderr, "  -o, --output-file <arg>        : filename for output"
    print >> sys.stderr, "  -c, --configuration-file <arg> : filename for configuration"
    print >> sys.stderr, "  <recipe>                       : recipe name"
    sys.exit(1)


def parse_command_line():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:c:", [
            "output-file=",
            "configuration-file="
        ])
    except getopt.GetoptError as err:
        print >> sys.stderr, err
        usage()

    cfg = Session()
    output_file = None

    for opt, arg in opts:
        if opt in ('-o', '--output-file'):
            output_file = arg
        elif opt in ('-c', '--configuration-file'):
            cfg.configuration_file = arg
        else:
            assert False

    cfg.recipe_name = args[0]

    return cfg, output_file


def main():
    cfg, output_file = parse_command_line()

    body = cfg.render()
    
    if output_file:
        with open(output_file, "wb") as f:
            f.write(body)
    else:
        print body


if __name__ == "__main__":
    main()
