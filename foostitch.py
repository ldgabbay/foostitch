#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import cjson
import copy

import foostache


class RecipeConfiguration(object):
    def __init__(self):
        self.data = {}
        self.scripts = []
        self.inputs = []
        self.output_file = None
        self.configuration_file = None
        self.recipe_name = None

    def __len__(self):
        assert len(self.scripts) == len(self.inputs)
        return len(self.scripts)

    def __getitem__(self, item):
        if self.inputs[item]:
            data = copy.deepcopy(self.inputs[item])
            data.update(self.data)
            return self.scripts[item], data
        return self.scripts[item], self.data


def load_configuration_file(*args):
    import cjson
    import os

    filenames = ['./.foostitch', '~/.foostitch', '/etc/foostitch']
    if args:
        filenames = list(args) + filenames
    body = None
    for filename in filenames:
        try:
            with open(os.path.expanduser(filename), 'rb') as f:
                body = f.read()
        except:
            continue
    if body:
        return cjson.decode(body)
    else:
        return {}


def usage():
    print >> sys.stderr, "usage: {0} [option]* [recipe]".format(os.path.basename(sys.argv[0]))
    print >> sys.stderr, "Options and arguments:"
    print >> sys.stderr, "  -d, --data <arg>               : template input data"
    print >> sys.stderr, "  -f, --data-file <arg>          : template input data file"
    print >> sys.stderr, "  -o, --output-file <arg>        : filename for output"
    print >> sys.stderr, "  -c, --configuration-file <arg> : filename for configuration"
    print >> sys.stderr, "  <recipe>                       : recipe name"
    sys.exit(1)


def parse_recipe(recipes, name, context, scripts, inputs):
    if not isinstance(name, basestring):
        raise TypeError("name must be a basestring")
    if not isinstance(context, dict):
        raise TypeError("context must be a dict")
    if not isinstance(scripts, list):
        raise TypeError("scripts must be a list")
    if not isinstance(inputs, list):
        raise TypeError("inputs must be a list")

    if name not in recipes:
        raise ValueError("recipe {} not found".format(name))
    sequence = recipes[name]
    if not isinstance(sequence, list):
        raise TypeError("recipe {} not a list".format(name))

    i = 0
    while i < len(sequence):
        item = sequence[i]
        i = i + 1
        if isinstance(item, dict):
            context.update(item)
        elif isinstance(item, basestring):
            if item.startswith("*"):
                parse_recipe(recipes, item[1:], copy.deepcopy(context), scripts, inputs)
            else:
                scripts.append(item)
                if (i < len(sequence)) and isinstance(sequence[i], dict):
                    data = copy.deepcopy(context)
                    data.update(sequence[i])
                    inputs.append(data)
                    i = i + 1
                else:
                    inputs.append(copy.deepcopy(context))
        else:
            return ValueError("unexpected item in recipe")


def parse_command_line():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:f:o:c:", [
            "data=",
            "data-file=",
            "output-file=",
            "configuration-file="
        ])
    except getopt.GetoptError as err:
        print >> sys.stderr, err
        usage()

    cfg = RecipeConfiguration()

    for opt, arg in opts:
        if opt in ('-d', '--data'):
            cfg.data = cjson.decode(arg)
        elif opt in ('-f', '--data-file'):
            with open(arg, "rb") as f:
                cfg.data = cjson.decode(f.read())
        elif opt in ('-o', '--output-file'):
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

    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
    parts = []
    for i in xrange(len(cfg)):
        template_fn, context = cfg[i]
        with open(os.path.join(template_path, template_fn), "rb") as f:
            parts.append(foostache.Template(unicode(f.read())).render(context))
    body = u"\n".join(parts)

    if cfg.output_file:
        with open(cfg.output_file, "wb") as f:
            f.write(body)
    else:
        print body


if __name__ == "__main__":
    main()
