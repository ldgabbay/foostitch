import copy
import os.path
import sys

import foostache
import ujson


class Cookbook(object):
    def __init__(self):
        self._recipes = {}

    def __contains__(self, item):
        return item in self._recipes

    def __getitem__(self, key):
        return self._recipes[key]

    def add_recipe(self, name:str, recipe:dict):
        self._recipes[name] = recipe

    def add_cookbook(self, cookbook:dict):
        for name, recipe in cookbook.items():
            self.add_recipe(name, recipe)


def _load_configuration_file(*args) -> Cookbook:
    """Loads all configuration files into single recipe map.
    
    Earlier files take precedent over later ones.
    """

    cookbook = Cookbook()
    for fn in reversed([fn for fn in (*args, "./.foostitch", "~/.foostitch", "/etc/foostitch")]):
        if not isinstance(fn, str):
            raise TypeError("fn must be a str")

        fn = os.path.expanduser(fn)
        if not os.path.isfile(fn):
            continue

        body = None

        try:
            with open(fn, "rb") as f:
                body = f.read()
        except Exception as e:
            print("{0}: {1}".format(fn, str(e)), file=sys.stderr)
            continue

        try:
            body = ujson.decode(body)
        except Exception as e:
            print("{0}: {1}".format(fn, str(e)), file=sys.stderr)
            continue

        cookbook.add_cookbook(body)

    return cookbook


def _parse_recipe(cookbook, name, base_context, templates, contexts):
    """Assemble templates and contexts for a recipe.
    
    Accumulates result into templates and contexts arguments.
    
    Arguments:
        cookbook {dict} -- recipe map
        name {str} -- recipe name
        base_context {dict} -- base context
        templates {list} -- list of templates
        contexts {list} -- list of contexts
    """
    if not isinstance(cookbook, Cookbook):
        raise TypeError("cookbook must be a Cookbook")
    if not isinstance(name, str):
        raise TypeError("name must be a str")
    if not isinstance(base_context, dict):
        raise TypeError("base_context must be a dict")
    if not isinstance(templates, list):
        raise TypeError("templates must be a list")
    if not isinstance(contexts, list):
        raise TypeError("contexts must be a list")

    if name not in cookbook:
        raise ValueError("recipe {} not found".format(name))
    sequence = cookbook[name]
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
        if isinstance(item, str):
            if (i != len(sequence)) and isinstance(sequence[i], dict):
                item_context = copy.deepcopy(recipe_base_context)
                item_context.update(sequence[i])
                i = i + 1
            else:
                item_context = recipe_base_context
            if item.startswith("*"):
                # include this recipe
                _parse_recipe(cookbook, item[1:], item_context, templates, contexts)
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
        cookbook = _load_configuration_file(*self.configuration_files)

        if self.recipe_name not in cookbook:
            raise ValueError("recipe {} not found".format(self.recipe_name))

        if "*" in cookbook:
            base_context = cookbook["*"]
            if not isinstance(base_context, dict):
                raise ValueError("default context must be a dict")
        else:
            base_context = {}

        _parse_recipe(cookbook, self.recipe_name, base_context, self._templates, self._contexts)

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
