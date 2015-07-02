import argparse

def setup_parent():
    shared_arguments = argparse.ArgumentParser(add_help=False)
    shared_arguments = tool_dirs(shared_arguments)
    shared_arguments.add_argument('--report_dir', required=True, help='Directory to write test report to.')
    shared_arguments.add_argument('--build_number', required=True,  help='Build number in jenkins.')
    shared_arguments = cores(shared_arguments)
    return shared_arguments

def shed_args(subparser):
    subparser.add_argument('--api_keys', required=True, default=None, help='Yaml file containing api keys required for shed_test.')
    subparser = shed_target(subparser)
    return subparser

def shed_target(subparser):
    subparser.add_argument('--shed_target', required=True, default=None, help='toolshed to target. Can be toolshed, testtoolshed or an URL.')
    return subparser

def tool_dirs(subparser):
    subparser.add_argument('--tool_dirs', nargs='+', default = ['.'], help='tool directories to scan recursively.')
    return subparser

def cores(subparser):
    subparser.add_argument('--cores', type=int, default=1, help='Number of cores to use for parallelizing planemo.')
    return subparser
