#!/usr/bin/env python

import os
import sys
import glob
import argparse
import subprocess
import yaml
from multiprocessing import Pool
import arguments

def clean_reports(report_dir):
    '''
    Remove old reports, if they exist.
    '''
    xml_files = glob.glob('{0}/*.xml'.format(report_dir))
    [os.remove(report) for report in xml_files]
    
def setup_report_dirs(report_dir, build_number):
    current_report_dir = "{0}/{1}".format(report_dir, build_number)
    if not os.path.exists(current_report_dir):
        os.makedirs(current_report_dir)
    return current_report_dir

def scan_dirs(tool_dirs):
    '''
    returns list with path to .shed.yml
    '''
    paths = []
    for tool_dir in tool_dirs:
        for root, dirs, files in os.walk("{0}".format(tool_dir)):
            for file in files:
                if file == ".shed.yml":
                    path = root+'/'+file
                    paths.append(path)
    return paths

def prepare_tests(tool_dirs, current_report_dir='', report_dir='', api_keys=None):
    '''
    Enter all directories and scan for .shed.yml files.
    Then setup dictionary with required values
    '''
    tool_dirs = [os.path.abspath(dir) for dir in tool_dirs]
    yaml_files = scan_dirs(tool_dirs)
    tests = []
    for file in yaml_files:
        test = {}
        shed_yml = yaml_to_dict(file)
        test['name'] = shed_yml['name']
        test['owner'] = shed_yml['owner']
        test['test_directory'] = file.split('/.shed.yml')[0]
        test['test_output_xunit'] = report_dir+"/{0}.xml".format(shed_yml['name'])
        test['test_output'] = current_report_dir+"/{0}.html".format(shed_yml['name'])
        test['toolshed'] = shed_yml['toolshed']
        tests.append(test)
    return tests

def prepare_html(current_report_dir, build_number, tests):
    '''
    write index for html result.
    '''
    # Need an index for the HTML output report
    header = ["<html><body><h1>Latest Test Results ({0})</h1><ul>".format(build_number)]
    test_result = []
    for test in tests:
        test_result.append('<li><a href="{0}.html">{0}</a></li>'.format(test['name']))
    footer = ["</ul></body></html>"]
    result = header+test_result+footer
    with open("{0}/index.html".format(current_report_dir),'w') as index:
        [index.write(line+'\n') for line in result]

def construct_cmds(tests, action, shed_target=None, api_keys=None, skip_test=False):
    '''
    prepare test commands
    '''
    cmds = []
    if action == 'test':
        for test in tests:
            cmd = "cd {0} && planemo test --install_galaxy --test_output_xunit {1}  --test_output {2}".format(
                test['test_directory'], test['test_output_xunit'], test['test_output'])
            cmds.append(cmd)
    elif action == 'update':
        for test in tests:
            api_key = api_keys['type']['toolshed']['target'][shed_target]['user'][test['owner']]['key']
            for toolshed in test['toolshed']:
                if toolshed==shed_target:
                    cmd = "cd {0} && planemo shed_update --force_repository_creation --shed_target {1} --shed_key {2} . ".format(test['test_directory'], toolshed, api_key )    
                    cmds.append(cmd)
            else:
                continue
    elif action == 'shed_diff':
        cmds = shed_diff(tests, shed_target)
        return cmds
    else:
        for test in tests:
            api_key = api_keys['type']['toolshed']['target'][shed_target]['user'][test['owner']]['key']
            update_cmd = ""
            for toolshed in test['toolshed']:
                if toolshed==shed_target:
                    if skip_test:
                        if test_skippable([test['test_directory'], toolshed]):
                            cmds.append ("echo \"{0} tool unchanged, skip testing\"".format(test['name']))
                            continue
                    update_cmd = "cd {0} && planemo shed_update --force_repository_creation --shed_target {1} --shed_key {2} . || true && ".format(test['test_directory'], toolshed, api_key )
                    cmd = "cd {0} && planemo shed_test --install_galaxy --test_output_xunit {1}  --test_output {2} --shed_target {3} --shed_key {4} .".format(test['test_directory'], test['test_output_xunit'], test['test_output'], shed_target, api_key )
                    cmd = update_cmd+cmd
                    cmds.append(cmd)
    return cmds

def process(func, function_args, cores):
    if cores > 1:
        p = Pool(processes=cores)
        result = p.map_async(func, function_args)
        results = result.get()
        p.close()
        p.join()
        return results
    else:
        results = [func(cmd) for cmd in cmds]
        return results

def shed_diff(tests, shed_target):
    cmds = []
    for test in tests:
        for toolshed in test['toolshed']:
            if toolshed==shed_target:
                cmds.append((test['test_directory'], toolshed))
    return cmds

def test_skippable(function_args):
    test_dir = function_args[0]
    shed_target = function_args[1]
    cmd = "cd {0} && planemo shed_diff --shed_target {1}".format(test_dir, shed_target)
    rc = subprocess.call(cmd, shell=True)
    if rc == 0:
        return True
    else:
        return False

def run_cmd(cmd):
    subprocess.call(cmd, shell=True)

def yaml_to_dict(yaml_file):
    with open(yaml_file) as handle:
        return yaml.load(handle)
    
def run_update(args, api_keys):
    '''
    Update toolsheds with local changes.
    '''
    tests = prepare_tests(args.tool_dirs, '', '', api_keys)
    cmds = construct_cmds ( tests, args.command, args.shed_target, api_keys)
    return cmds

def run_test(args, current_report_dir):
    '''
    Run tests directly on local tool directory(ies).
    '''
    api_keys=None
    tests = prepare_tests(args.tool_dirs, current_report_dir, args.report_dir, api_keys)
    prepare_html(current_report_dir, args.build_number, tests)
    cmds = construct_cmds ( tests, args.command, None, api_keys)
    return cmds

def run_shed_test(args, current_report_dir, api_keys, skip_test):
    '''
    Run tests by using planemo shed_test, which installs tools and tool dependencies from the toolshed.
    Skip test if package is in name.
    '''
    tests = prepare_tests(args.tool_dirs, current_report_dir, args.report_dir, api_keys)
    packages = [test for test in tests if test['name'].startswith('package_')]
    package_cmds = construct_cmds ( packages, 'update', args.shed_target, api_keys)
    tests = [test for test in tests if not test['name'].startswith('package_')]
    prepare_html(current_report_dir, args.build_number, tests)
    cmds = construct_cmds ( tests, args.command, args.shed_target, api_keys, skip_test)
    return package_cmds + cmds

def run_shed_diff(args):
    '''
    Update toolsheds with local changes.
    '''
    tests = prepare_tests(args.tool_dirs, '', '', "")
    cmds = construct_cmds ( tests, args.command, args.shed_target, "")
    return cmds

if __name__ == "__main__":
    
    parent = arguments.setup_parent()
    parser = argparse.ArgumentParser(description='Commands for updating and testing galaxy tools and packages.')
    subparsers = parser.add_subparsers(help='sub-command help', dest='command')
    parser_update = subparsers.add_parser('update', help='update a toolshed.',
                                          description="Update a toolshed if that toolshed is specified in the .shed.yml file",
                                          parents=[parent])
    parser_test = subparsers.add_parser('test', help='Run tool functional tests', parents=[parent],
                                        description="Run functional tests within a disposable galaxy instance. Does not install tool dependencies.")
    parser_shed_test = subparsers.add_parser('shed_test', help='Install from toolshed and run functional tests.', 
                                             description="Upload tool to indicated toolshed and run functional tests within a disposable galaxy instance. Tool and dependencies will be downloaded from the indicated toolshed.", parents=[parent])
    parser_shed_diff = subparsers.add_parser('shed_diff', help='Compare local tools to toolshed tools', 
                                             description="Compare local tools to toolshed tools.")
    parser_shed_diff = arguments.tool_dirs(parser_shed_diff)
    parser_shed_diff = arguments.shed_target(parser_shed_diff)
    parser_shed_diff = arguments.cores(parser_shed_diff)
    parser_update = arguments.shed_args(parser_update)
    parser_shed_test = arguments.shed_args(parser_shed_test)
    parser_shed_test.add_argument('--skip_test', dest="skip_test", action="store_true", \
                                  help='If there is no difference between toolshed and local repo, skip testing')
    args = parser.parse_args()

    if args.command == "shed_diff":
        cmds = run_shed_diff(args)
        results = process(test_skippable, cmds, args.cores)
        if sum(results)==len(results):
            print "No differences with {0} found, exiting".format(args.shed_target)
            sys.exit(1)
        else:
            sys.exit()

    args.report_dir = os.path.abspath(args.report_dir)
    clean_reports(args.report_dir)
    current_report_dir = setup_report_dirs(args.report_dir, args.build_number)

    if args.command == "test":
        cmds = run_test(args, current_report_dir)

    else:
        api_keys = yaml_to_dict(args.api_keys)
    if args.command == "update":
        cmds = run_update(args, api_keys)
    if args.command == "shed_test":
        cmds = run_shed_test(args, current_report_dir, api_keys, args.skip_test)

    process(run_cmd, cmds, args.cores)
