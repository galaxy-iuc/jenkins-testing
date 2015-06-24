#!/usr/bin/env python

import os
import glob
import argparse
import subprocess
import yaml
from multiprocessing import Pool


def clean_reports(report_dir):
    '''
    Remove old reports, if they exist.
    '''
    xml_files = glob.glob('{0}/*.xml'.format(report_dir))
    [os.remove(report) for report in xml_files]
    
def setup_report_dirs(report_dir, build_number):
    current_report_dir = "{0}/{1}".format(report_dir, build_number)
    #don't need junit_dir anymore
    #junit_dir = "{0}/reports".format(report_dir)
    if not os.path.exists(current_report_dir):
        os.makedirs(current_report_dir)
    return current_report_dir

def scan_dirs(tool_dir):
    '''
    returns list with path to .shed.yml
    '''
    paths = []
    for root, dirs, files in os.walk("{0}".format(tool_dir)):
        for file in files:
            if file == ".shed.yml":
                path = root+'/'+file
                paths.append(path)
    return paths

def prepare_tests(tool_dir, current_report_dir, report_dir, api_keys=None):
    '''
    Enter all directories and scan for .shed.yml files.
    Then setup dictionary with required values
    '''
    yaml_files = scan_dirs(tool_dir)
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

def construct_cmds(tests, test_type, shed_target=None, api_keys=None):
    '''
    prepare test commands
    '''
    cmds = []
    if test_type == 'test':
        for test in tests:
            cmd = "cd {0} && planemo test --install_galaxy --test_output_xunit {1}  --test_output {2}".format(
                test['test_directory'], test['test_output_xunit'], test['test_output'])
            cmds.append(cmd)
    else:
        for test in tests:
            api_key = api_keys['type']['toolshed']['target'][shed_target]['user'][test['owner']]['key']
            update_cmd = ""
            if args.update_shed:
                for toolshed in test['toolshed']:
                    update_cmd = "cd {0} && planemo shed_update --force_repository_creation --shed_target {1} --shed_key {2} . || true && ".format(test['test_directory'], toolshed, api_key )
                
            cmd = "cd {0} && planemo shed_test --install_galaxy --test_output_xunit {1}  --test_output {2} --shed_target {3} --shed_key {4} .".format(test['test_directory'], test['test_output_xunit'],
                                                test['test_output'], shed_target, api_key )
            cmd = update_cmd+cmd
            cmds.append(cmd)
    return cmds
        
def mp_run(cmd):
    process = subprocess.call(cmd, shell=True)

def yaml_to_dict(yaml_file):
    with open(yaml_file) as handle:
        return yaml.load(handle)
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Get a list of repos with .shed.yml and commence testing.')
    parser.add_argument('--tool_dir', required=True, help='tool directory to scan recursively.')
    parser.add_argument('--report_dir', required=True, help='Directory to write test report to.')
    parser.add_argument('--build_number', required=True,  help='Build number in jenkins.')
    parser.add_argument('--cores', type=int, default=1, help='Number of cores to use for parallelizing planemo.')
    parser.add_argument('--test_type', type=str, choices=['test', 'shed_test'], default='test', help='Select whether to do a shed_test or a simple test.')    
    parser.add_argument('--update_shed', type=bool, default=False, help='Select whether to upload to specified toolshed beforehand.')    
    parser.add_argument('--api_keys', default=None, help='Yaml file containing api keys required for shed_test.')    
    parser.add_argument('--shed_target', default=None, help='Yaml file containing api keys required for shed_test.')
    args = parser.parse_args()

    args.report_dir = os.path.abspath(args.report_dir)
    args.tool_dir = os.path.abspath(args.tool_dir)
    clean_reports(args.report_dir)
    current_report_dir = setup_report_dirs(args.report_dir, args.build_number)
    if args.test_type == "shed_test":
        try:
            api_keys = yaml_to_dict(args.api_keys)
        except:
            print 'If choosing shed_test provide a valid yaml file.'
            raise
    else:
        api_keys=None
    tests = prepare_tests(args.tool_dir, current_report_dir, args.report_dir, api_keys)
    prepare_html(current_report_dir, args.build_number, tests)
    cmds = construct_cmds ( tests, args.test_type, args.shed_target, api_keys)
    if args.cores > 1:
        p = Pool(processes=args.cores)
        result = p.map_async(mp_run, cmds) 
        result.get()
    else:
        [mp_run(cmd) for cmd in cmds]



