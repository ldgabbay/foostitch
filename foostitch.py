#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


import sys
import cjson
import getopt
import os

from foo.stitch import RecipeConfiguration, load_configuration_file, parse_recipe, render


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

    cfg = RecipeConfiguration()

    for opt, arg in opts:
        if opt in ('-o', '--output-file'):
            cfg.output_file = arg
        elif opt in ('-c', '--configuration-file'):
            cfg.configuration_file = arg
        else:
            assert False

    cfg.recipe_name = args[0]

    recipes = load_configuration_file(cfg.configuration_file)

    if cfg.recipe_name not in recipes:
        raise ValueError("recipe {} not found".format(cfg.recipe_name))

    context = {}
    parse_recipe(recipes, cfg.recipe_name, context, cfg.scripts, cfg.inputs)

    assert len(cfg.inputs) == len(cfg.scripts)

    return cfg


def main():
    cfg = parse_command_line()

    body = render(cfg)
    
    if cfg.output_file:
        with open(cfg.output_file, "wb") as f:
            f.write(body)
    else:
        print body


if __name__ == "__main__":
    main()
