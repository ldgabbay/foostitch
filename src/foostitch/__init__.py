__version__ = "1.0.0.dev1"

import copy
import os.path
import sys
from typing import Optional

import foostache
import mkciud
import ujson


def apply_context(base: dict, overlay: dict) -> dict:
    new = copy.deepcopy(base)
    new.update(overlay)
    return new


class TemplateRepository(object):
    _PATH = [
        "./.foostitch-templates",
        "~/.foostitch-templates",
        "/etc/foostitch-templates",
    ]

    def __init__(self):
        self.search_path = []

    def load(self, relative_path: str) -> 'foostache.Template':
        for p in self.search_path + TemplateRepository._PATH:
            fn = os.path.expanduser(os.path.join(p, relative_path))
            if os.path.isfile(fn):
                with open(fn, "r") as f:
                    return foostache.Template(f.read())
        raise FileNotFoundError("template not found: {}".format(relative_path))


class Cookbook(object):
    def __init__(self):
        self.template_repo = TemplateRepository()
        self._recipes = {}

    def __contains__(self, item: str):
        return item in self._recipes

    def __getitem__(self, key: str) -> list:
        return self._recipes[key]

    def add_recipe(self, name: str, instructions: list, base_context: Optional[dict] = None):
        if not isinstance(name, str):
            raise TypeError()
        if name in self._recipes:
            raise ValueError(f"recipe {repr(name)} already defined")
        self._recipes[name] = Recipe.parse(instructions, base_context)

    def add_cookbook(self, cookbook: dict):
        if not isinstance(cookbook, dict):
            raise TypeError()

        if "*" in cookbook:
            context = cookbook["*"]
            if not isinstance(context, dict):
                raise ValueError()
        else:
            context = {}

        for name, instructions in cookbook.items():
            if name == "*":
                continue
            self.add_recipe(name, instructions, context)

    def load_cookbook(self, fn: str):
        if not isinstance(fn, str):
            raise TypeError("fn must be a str")

        fn = os.path.expanduser(fn)
        if not os.path.isfile(fn):
            return

        with open(fn, "rb") as f:
            self.add_cookbook(ujson.decode(f.read()))


class Step(object):
    def __init__(self, template: str, context: dict):
        if not isinstance(template, str):
            raise TypeError()
        if not isinstance(context, dict):
            raise TypeError()

        self.template = template
        self.context = context


class Recipe(object):
    def __init__(self):
        self._steps = []

    @staticmethod
    def parse(instructions: list, base_context: Optional[dict] = None):
        if not isinstance(instructions, list):
            raise TypeError()
        if base_context is None:
            base_context = {}
        if not isinstance(base_context, dict):
            raise TypeError()

        recipe = Recipe()

        # if the first entry is a dict, overlay the base context for the recipe
        if len(instructions) != 0 and isinstance(instructions[0], dict):
            recipe_context = apply_context(base_context, instructions[0])
            i = 1
        else:
            recipe_context = base_context
            i = 0

        while i != len(instructions):
            template = instructions[i]
            i = i + 1

            if not isinstance(template, str):
                raise ValueError("unexpected step")

            if (i != len(instructions)) and isinstance(instructions[i], dict):
                template_context = apply_context(recipe_context, instructions[i])
                i = i + 1
            else:
                template_context = recipe_context

            recipe._steps.append(Step(template, template_context))

        return recipe



class Session(object):
    def __init__(self):
        self.cookbook = Cookbook()
        self.template_repo = TemplateRepository()
        self.configuration_files = []
        for fn in reversed(["./.foostitch", "~/.foostitch", "/etc/foostitch"]):
            self.cookbook.load_cookbook(fn)

    def _render(self, recipe_name: str, userdata: 'mkciud.UserData', context: Optional[dict] = None):
        if not isinstance(recipe_name, str):
            raise TypeError()
        if not isinstance(userdata, mkciud.UserData):
            raise TypeError()
        if context is None:
            context = {}
        if not isinstance(context, dict):
            raise TypeError()

        if recipe_name not in self.cookbook:
            raise ValueError(f"recipe {repr(recipe_name)} not found")

        recipe = self.cookbook[recipe_name]

        for step in recipe._steps:
            step_context = apply_context(step.context, context)
            if step.template.startswith("*"):
                self._render(step.template[1:], userdata, step_context)
            else:
                userdata.add(self.template_repo.load(step.template).render(step_context))

    def render(self, recipe_name: str, fileobj, context: Optional[dict] = None):
        userdata = mkciud.UserData()
        self._render(recipe_name, userdata, context)
        userdata.export(fileobj)
