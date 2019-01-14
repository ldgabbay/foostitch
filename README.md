# foostitch

## Command-Line Usage

```text
usage: foostitch [option]* [recipe]
    -o, --output-file arg              filename for output
    -c, --configuration-file arg       filename for configuration
    -t, --template-directory           directory with templates

    recipe                             recipe name
```

## Configuration (aka Recipe) File Format

* loads configuration files with the following priority (highest to lowest):
    * files specified on the command line
    * `./.foostitch`
    * `~/.foostitch`
    * `/etc/foostitch`
* a JSON file of an object
    * if the key is "\*"
        * the value is an object that is the base context for all recipes
    * otherwise
        * the key is the name of a recipe
        * the value is a recipe
* a recipe is an array
    * if the first item is an object, that object overlays the base context for that recipe
    * if an item is a string
        * if the string begins with "\*", the remainder of the string is the name of a recipe to include at this point in the recipe
        * otherwise, the string is the filename of a `foostache` template; the filename path is relative to a template directory
    * if the item following a string is an object, that object overlays the base context for that item


## Template Files

* looks for templates in the following order:
    * directories specified on the command line
    * `./.foostitch-templates`
    * `~/.foostitch-templates`
    * `/etc/foostitch-templates`



## Configuration File

```text
CONFIG_FILE: {
    "*": CONTEXT
    RECIPE_NAME: RECIPE
}

RECIPE: [ CONTEXT?, (STEP, CONTEXT?)* ]

STEP:
    "*RECIPE_NAME"
    "TEMPLATE_FILENAME"
```

In a configuration file, the `"*"` context is the base context for everything contained in the file. (`[cfg]`)

In a recipe, if there is an initial context, it is applied to the file context to become the recipe context. (`[recipe, cfg]`)

In a step, if there is a context, it is applied to the recipe context to become the step context.  (`[tmpl, recipe, cfg]`)  If the step is an embedded recipe, the step context is applied to each step in the embedded recipe.
