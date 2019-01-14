# foostitch

## Command-Line Usage

    usage: foostitch [option]* [recipe]
    Options and arguments:
      -o, --output-file <arg>        : filename for output
      -c, --configuration-file <arg> : filename for configuration
      -t, --template-directory       : directory with templates
      <recipe>                       : recipe name


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
    * `$FOOSTITCH_DIR/templates`



## Configuration File

```text
{
    RECIPE_NAME: RECIPE
}
```

## Recipe

```text
{
    CONTEXT?,
    FILENAME or *RECIPE_NAME, CONTEXT?,
}
```
