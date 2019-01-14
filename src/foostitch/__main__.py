import getopt
import os
import sys

import foostitch


def print_error(message):
    print("{0}: {1}".format("foostitch", message), file=sys.stderr)


def print_usage():
    print("usage: {0} [option]* [recipe]".format("foostitch"), file=sys.stderr)
    print("    -o, --output-file arg              filename for output",         file=sys.stderr)
    print("    -c, --configuration-file arg       filename for configuration",  file=sys.stderr)
    print("    -t, --template-directory           directory with templates",    file=sys.stderr)
    print(                                                                      file=sys.stderr)
    print("    recipe                             recipe name",                 file=sys.stderr)


def main(args=None):
    if args is None:
        args = sys.argv

    try:

        cfg = foostitch.Session()

        try:
            opts, args = getopt.getopt(args[1:], "o:c:t:", [
                "output-file=",
                "configuration-file=",
                "template-directory=",
            ])
        except getopt.GetoptError as err:
            print_error(err)
            print_usage()
            return os.EX_USAGE

        if len(args) < 1:
            print_usage()
            return os.EX_USAGE

        cfg.recipe_name = args[0]

        output_file = None

        for opt, arg in opts:
            if opt in ("-o", "--output-file"):
                output_file = arg
            elif opt in ("-c", "--configuration-file"):
                cfg.configuration_files.append(arg)
            elif opt in ("-t", "--template-directory"):
                cfg.template_directories.append(arg)
            else:
                assert False

        body = cfg.render()

        if output_file:
            with open(output_file, "wb") as f:
                f.write(body)
        else:
            print(body)

    except Exception as e:
        print_error(str(e))
        return os.EX_SOFTWARE


if __name__ == "__main__":
    sys.exit(main(sys.argv))
