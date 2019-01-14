import copy
import os.path
import sys

import foostache
import ujson


def apply_context(base: dict, overlay: dict) -> dict:
    new = copy.deepcopy(base)
    new.update(overlay)
    return new


class Cookbook(object):
    def __init__(self):
        self._recipes = {}

    def __contains__(self, item: str):
        return item in self._recipes

    def __getitem__(self, key: str) -> list:
        return self._recipes[key]

    def add_recipe(self, name: str, recipe: list):
        self._recipes[name] = recipe

    def add_cookbook(self, cookbook: dict):
        for name, recipe in cookbook.items():
            self.add_recipe(name, recipe)

    def load(self, fn: str):
        fn = os.path.expanduser(fn)
        if not os.path.isfile(fn):
            return
        with open(fn, "rb") as f:
            self.add_cookbook(ujson.decode(f.read()))


def _load_configuration_file(*args) -> Cookbook:
    """Loads all configuration files into single recipe map.
    
    Earlier files take precedent over later ones.
    """

    cookbook = Cookbook()
    for fn in reversed([*args, "./.foostitch", "~/.foostitch", "/etc/foostitch"]):
        if not isinstance(fn, str):
            raise TypeError("fn must be a str")

        fn = os.path.expanduser(fn)
        if not os.path.isfile(fn):
            continue

        try:
            cookbook.load(fn)
        except Exception as e:
            print("{0}: {1}".format(fn, str(e)), file=sys.stderr)
            continue

    return cookbook


class Step(object):
    def __init__(self, template: str, context: dict):
        self.template = template
        self.context = context


class Recipe(object):

    def __init__(self):
        self.steps = []

    def add_step(self, template: str, context: dict):
        self.steps.append(Step(template, context))

    def add_subrecipe(self, recipe: 'Recipe'):
        self.steps.extend(recipe.steps)


def _parse_recipe(cookbook, name, base_context) -> Recipe:
    """Assemble templates and contexts for a recipe.
    
    Accumulates result into templates and contexts arguments.
    
    Arguments:
        cookbook {dict} -- recipe map
        name {str} -- recipe name
        base_context {dict} -- base context
    """
    if not isinstance(cookbook, Cookbook):
        raise TypeError("cookbook must be a Cookbook")
    if not isinstance(name, str):
        raise TypeError("name must be a str")
    if not isinstance(base_context, dict):
        raise TypeError("base_context must be a dict")

    recipe = Recipe()

    if name not in cookbook:
        raise ValueError("recipe {} not found".format(name))
    sequence = cookbook[name]
    if not isinstance(sequence, list):
        raise TypeError("recipe {} not a list".format(name))

    # if the first entry is a dict, overlay the base context for the recipe
    if (len(sequence) != 0) and isinstance(sequence[0], dict):
        recipe_base_context = apply_context(base_context, sequence[0])
        i = 1
    else:
        recipe_base_context = base_context
        i = 0

    while i != len(sequence):
        item = sequence[i]
        i = i + 1
        if isinstance(item, str):
            if (i != len(sequence)) and isinstance(sequence[i], dict):
                item_context = apply_context(recipe_base_context, sequence[i])
                i = i + 1
            else:
                item_context = recipe_base_context
            if item.startswith("*"):
                # include this recipe
                recipe.add_subrecipe(_parse_recipe(cookbook, item[1:], item_context))
            else:
                # include this template with optional context
                recipe.add_step(item, item_context)
        else:
            raise ValueError("unexpected item in recipe")

    return recipe


class TemplateRepository(object):
    _PATH = [
        "./.foostitch-templates",
        "~/.foostitch-templates",
        "/etc/foostitch-templates",
    ]

    def __init__(self):
        self.path = []

    def load(self, relative_path: str) -> 'foostache.Template':
        for p in self.path + TemplateRepository._PATH:
            fn = os.path.expanduser(os.path.join(p, relative_path))
            if os.path.isfile(fn):
                with open(fn, "r") as f:
                    return foostache.Template(f.read())
        raise FileNotFoundError("template not found: {}".format(relative_path))


class Session(object):
    def __init__(self):
        self.template_repo = TemplateRepository()
        self.configuration_files = []
        self.recipe_name = None

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

        recipe = _parse_recipe(cookbook, self.recipe_name, base_context)

        parts = []
        for step in recipe.steps:
            parts.append(self.template_repo.load(step.template).render(step.context))
        return "\n".join(parts)
