# coding: utf_8

import copy
import os.path
import sys

import ujson
import foostache


def _load_configuration_file(*args):
    filenames = ['./.foostitch', '~/.foostitch', '/etc/foostitch']
    if args:
        filenames = list(args) + filenames
    result = {}
    for filename in reversed(filenames):
        try:
            body = None
            with open(os.path.expanduser(filename), 'rb') as f:
                body = f.read()
            try:
                body = ujson.loads(body)
            except:
                print >> sys.stderr, "error parsing {}".format(filename)
                continue
            for k, v in body.iteritems():
                result[k] = v
        except:
            pass
    return result


def _parse_recipe(recipes, name, default_context, templates, contexts):
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
                _parse_recipe(recipes, item[1:], copy.deepcopy(default_context), templates, contexts)
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


_TEMPLATE_PATH = [
    "./.foostitch-templates",
    "~/.foostitch-templates",
    "/etc/foostitch-templates",
    os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "templates")
]


class Session(object):
    def __init__(self):
        self._templates = []
        self._contexts = []
        self.template_directories = []
        self.configuration_files = []
        self.recipe_name = None

    def __len__(self):
        assert len(self._templates) == len(self._contexts)
        return len(self._templates)

    def __getitem__(self, index):
        return self._templates[index], self._contexts[index]

    def render(self):
        recipes = _load_configuration_file(*self.configuration_files)

        if self.recipe_name not in recipes:
            raise ValueError("recipe {} not found".format(self.recipe_name))

        if "*" in recipes:
            context = recipes["*"]
            if not isinstance(context, dict):
                raise ValueError("default context must be a dict")
        else:
            context = {}

        _parse_recipe(recipes, self.recipe_name, context, self._templates, self._contexts)

        assert len(self._contexts) == len(self._templates)

        parts = []
        for i in xrange(len(self)):
            template, context = self[i]
            found = False
            for p in self.template_directories + _TEMPLATE_PATH:
                fn = os.path.join(p, template)
                if os.path.isfile(fn):
                    with open(fn, "rb") as f:
                        parts.append(foostache.Template(f.read().decode('utf_8')).render(context))
                        found = True
                        break
            if not found:
                raise ValueError("template {} not found".format(template))
        return u"\n".join(parts)
