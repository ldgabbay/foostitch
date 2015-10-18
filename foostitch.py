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

    for s in recipes.get(cfg.recipe_name, []):
        if isinstance(s, dict):
            assert len(cfg.scripts) == len(cfg.inputs) + 1
            cfg.inputs.append(s)
        elif isinstance(s, (str, unicode)):
            if len(cfg.inputs) < len(cfg.scripts):
                cfg.inputs.append({})
            assert len(cfg.scripts) == len(cfg.inputs)
            cfg.scripts.append(s)
        else:
            raise ValueError()

    if len(cfg.inputs) < len(cfg.scripts):
        cfg.inputs.append({})

    return cfg


def main():
    cfg = parse_command_line()

    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
    parts = []
    for i in xrange(len(cfg)):
        script, input = cfg[i]
        with open(os.path.join(template_path, script), "rb") as f:
            parts.append(foostache.Template(unicode(f.read())).render(input))
    body = u"\n".join(parts)

    if cfg.output_file:
        with open(cfg.output_file, "wb") as f:
            f.write(body)
    else:
        print body


if __name__ == "__main__":
    main()
