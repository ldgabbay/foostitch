import copy
import os.path
import sys

import foostache
import ujson


def _load_configuration_file(*args):
    filenames = ["./.foostitch", "~/.foostitch", "/etc/foostitch"]
    if args:
        filenames = list(args) + filenames
    result = {}
    for filename in reversed(filenames):
        try:
            body = None
            with open(os.path.expanduser(filename), "rb") as f:
                body = f.read()
            try:
                body = ujson.decode(body)
            except:
                print("error parsing {}".format(filename), file=sys.stderr)
                continue
            for k, v in body.iteritems():
                result[k] = v
        except:
            pass
    return result


def _parse_recipe(recipes, name, base_context, templates, contexts):
    if not isinstance(recipes, dict):
        raise TypeError("recipes must be a dict")
    if not isinstance(name, basestring):
        raise TypeError("name must be a basestring")
    if not isinstance(base_context, dict):
        raise TypeError("base_context must be a dict")
    if not isinstance(templates, list):
        raise TypeError("templates must be a list")
    if not isinstance(contexts, list):
        raise TypeError("contexts must be a list")

    if name not in recipes:
        raise ValueError("recipe {} not found".format(name))
    sequence = recipes[name]
    if not isinstance(sequence, list):
        raise TypeError("recipe {} not a list".format(name))

    # if the first entry is a dict, overlay the base context for the recipe
    if (len(sequence) != 0) and isinstance(sequence[0], dict):
        recipe_base_context = copy.deepcopy(base_context)
        recipe_base_context.update(sequence[0])
        i = 1
    else:
        recipe_base_context = base_context
        i = 0

    while i != len(sequence):
        item = sequence[i]
        i = i + 1
        if isinstance(item, basestring):
            if (i != len(sequence)) and isinstance(sequence[i], dict):
                item_context = copy.deepcopy(recipe_base_context)
                item_context.update(sequence[i])
                i = i + 1
            else:
                item_context = recipe_base_context
            if item.startswith("*"):
                # include this recipe
                _parse_recipe(recipes, item[1:], item_context, templates, contexts)
            else:
                # include this template with optional context
                templates.append(item)
                contexts.append(item_context)
        else:
            raise ValueError("unexpected item in recipe")


_TEMPLATE_PATH = [
    "./.foostitch-templates",
    "~/.foostitch-templates",
    "/etc/foostitch-templates",
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
            base_context = recipes["*"]
            if not isinstance(base_context, dict):
                raise ValueError("default context must be a dict")
        else:
            base_context = {}

        _parse_recipe(recipes, self.recipe_name, base_context, self._templates, self._contexts)

        assert len(self._contexts) == len(self._templates)

        parts = []
        for i in range(len(self)):
            template, context = self[i]
            found = False
            for p in self.template_directories + _TEMPLATE_PATH:
                fn = os.path.expanduser(os.path.join(p, template))
                if os.path.isfile(fn):
                    with open(fn, "rb") as f:
                        parts.append(foostache.Template(f.read().decode("utf_8")).render(context))
                        found = True
                        break
            if not found:
                raise ValueError("template {} not found".format(template))
        return "\n".join(parts)
