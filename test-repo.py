#!/usr/bin/env python
## Script to automatize testing of galaxy tools using planemo.
## Based on shell script by Eric Rasche (https://github.com/galaxy-iuc/jenkins-testing).
##

import os
import glob
import argparse
import subprocess
from multiprocessing import Pool


def clean_reports(workspace):
    '''
    Remove old reports, if they exist.
    '''
    xml_files = glob.glob('{0}/reports/*.xml'.format(workspace))
    [os.remove(report) for report in xml_files]
    
def setup_report_dirs(workspace, build_number):
    report_dir = "{0}/reports/{1}".format(workspace, build_number)
    junit_dir = "{0}/reports".format(workspace)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    return (report_dir, junit_dir)

def prepare_tests(workspace, report_dir, junit_dir):
    '''
    Enter all directories and scan for .shed.yml files.
    '''
    commandlines = []
    for root, dirs, files in os.walk("{0}".format(workspace)):
        for file in files:
            if file == ".shed.yml":
                test_directory = root
                test_name = root.split('/')[-1]
                test_output_xunit = junit_dir+"/{0}.xml".format(test_name)
                test_output = report_dir+"/{0}.html".format(test_name)
                commandlines.append((test_name, test_directory, test_output_xunit, test_output))
    return commandlines

def prepare_cmds(report_dir, build_number, commandlines):
    '''
    write index for html result.
    prepare test commands
    '''
    # Need an index for the HTML output report
    header = ["<html><body><h1>Latest Test Results ({0})</h1><ul>".format(build_number)]
    test_result = []
    footer = ["</ul></body></html>"]
    
    cmds = []
    for test_name, test_directory, test_output_xunit, test_output in commandlines:
        test_result.append('<li><a href="{0}">{1}</a></li>'.format(test_output, test_name))
        cmd = "cd {0} && planemo test --install_galaxy --test_output_xunit {1}  --test_output {2}".format(
            test_directory, test_output_xunit, test_output)
        cmds.append(cmd)
    result = header+test_result+footer
    index = open("{0}/index.html".format(report_dir),'w')
    [index.write(line+'\n') for line in result]
    index.close()
    return cmds

def mp_run(cmd):
    process = subprocess.call(cmd, shell=True)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Get a list of repos with .shed.yml and commence testing')
    parser.add_argument('--workspace', help='Workspace variable in jenkins')
    parser.add_argument('--build_number', help='Build number in jenkins')
    parser.add_argument('--cores', type=int, default=1, help='Number of cores to use for parallelizing planemo')
    args = parser.parse_args()
    args.workspace = os.path.abspath(args.workspace)
    clean_reports(args.workspace)
    report_dir, junit_dir = setup_report_dirs(args.workspace, args.build_number)
    commandlines = prepare_tests(args.workspace, report_dir, junit_dir)
    cmds = prepare_cmds ( report_dir, args.build_number, commandlines)
    if args.cores > 1:
        p = Pool(processes=args.cores)
        result = p.map_async(mp_run, cmds) 
        result.get()
    else:
        [mp_run(cmd) for cmd in cmds]
