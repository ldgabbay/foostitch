# -*- coding: utf-8 -*-

import copy
import cjson
import os.path
import sys

import foostache


TEMPLATE_PATH = [
    "./.foostitch.templates",
    "~/.foostitch.templates",
    "/etc/foostitch.templates",
    os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "templates")
]


class RecipeConfiguration(object):
    def __init__(self):
        self.scripts = []
        self.inputs = []
        self.configuration_file = None
        self.recipe_name = None

    def __len__(self):
        assert len(self.scripts) == len(self.inputs)
        return len(self.scripts)

    def __getitem__(self, index):
        return self.scripts[index], self.inputs[index]


def load_configuration_file(*args):
    filenames = ['./.foostitch', '~/.foostitch', '/etc/foostitch']
    if args:
        filenames = list(args) + filenames
    body = None
    for fn in filenames:
        fn = os.path.expanduser(fn)
        if os.path.isfile(fn):
            with open(fn, 'rb') as f:
                body = f.read().decode("utf_8")
                break
    if body:
        return cjson.decode(body)
    else:
        return {}


def parse_recipe(recipes, name, default_context, templates, contexts):
    if not isinstance(name, basestring):
        raise TypeError("name must be a basestring")
    if not isinstance(default_context, dict):
        raise TypeError("context must be a dict")
    if not isinstance(templates, list):
        raise TypeError("scripts must be a list")
    if not isinstance(contexts, list):
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
            default_context.update(item)
        elif isinstance(item, basestring):
            if item.startswith("*"):
                parse_recipe(recipes, item[1:], copy.deepcopy(default_context), templates, contexts)
            else:
                templates.append(item)
                if (i < len(sequence)) and isinstance(sequence[i], dict):
                    data = copy.deepcopy(default_context)
                    data.update(sequence[i])
                    contexts.append(data)
                    i = i + 1
                else:
                    contexts.append(copy.deepcopy(default_context))
        else:
            return ValueError("unexpected item in recipe")


def render(cfg):
    if cfg.configuration_file:
        recipes = load_configuration_file(cfg.configuration_file)
    else:
        recipes = load_configuration_file()

    if cfg.recipe_name not in recipes:
        raise ValueError("recipe {} not found".format(cfg.recipe_name))

    if "*" in recipes:
        context = recipes["*"]
    else:
        context = {}

    parse_recipe(recipes, cfg.recipe_name, context, cfg.scripts, cfg.inputs)

    assert len(cfg.inputs) == len(cfg.scripts)

    parts = []
    for i in xrange(len(cfg)):
        template_fn, context = cfg[i]
        found = False
        for p in TEMPLATE_PATH:
            fn = os.path.join(p, template_fn)
            if os.path.isfile(fn):
                with open(fn, "rb") as f:
                    parts.append(foostache.Template(f.read().decode('utf_8')).render(context))
                    found = True
                    break
        if not found:
            raise ValueError("template {} not found".format(template_fn))
    return u"\n".join(parts)
