import getopt
import io
import os
import sys
import traceback

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

        recipe_name = args[0]

        output_file = None
        configuration_files = []

        for opt, arg in opts:
            if opt in ("-o", "--output-file"):
                output_file = arg
            elif opt in ("-c", "--configuration-file"):
                configuration_files.append(arg)
            elif opt in ("-t", "--template-directory"):
                cfg.template_repo.search_path.append(arg)
            else:
                assert False

        for fn in reversed(configuration_files):
            cfg.cookbook.load_cookbook(fn)

        with io.BytesIO() as f:
            cfg.render(recipe_name, f)
            b = f.getvalue()

        if output_file is not None:
            with open(output_file, "wb") as f:
                f.write(b)
        else:
            sys.stdout.buffer.write(b)

    except Exception as e:
        print_error(str(e))
        traceback.print_exc(file=sys.stderr)
        return os.EX_SOFTWARE


if __name__ == "__main__":
    sys.exit(main(sys.argv))
