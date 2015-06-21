# %load /home/marius/src/gedtools/test-repo2.py
import os
import glob
import argparse
import subprocess
import yaml
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

def scan_dirs(workspace):
    '''
    returns list with path to .shed.yml
    '''
    paths = []
    for root, dirs, files in os.walk("{0}".format(workspace)):
        for file in files:
            if file == ".shed.yml":
                path = root+'/'+file
                paths.append(path)
    return paths

def prepare_tests(workspace, report_dir, junit_dir, api_keys=None):
    '''
    Enter all directories and scan for .shed.yml files.
    Then setup dictionary with required values
    '''
    paths = scan_dirs(workspace)
    tests = []
    for path in paths:
        test = {}
        shed_yml = yaml_to_dict(path)
        test['name'] = shed_yml['name']
        test['owner'] = shed_yml['owner']
        test['test_directory'] = path.split('/.shed.yml')[0]
        test['test_output_xunit'] = junit_dir+"/{0}.xml".format(shed_yml['name'])
        test['test_output'] = report_dir+"/{0}.html".format(shed_yml['name'])
        tests.append(test)
    return tests

def prepare_html(report_dir, build_number, tests):
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
    with open("{0}/index.html".format(report_dir),'w') as index:
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
            cmd = "cd {0} && planemo shed_test --install_galaxy --test_output_xunit {1}  --test_output {2} --shed_target {3} --shed_key {4} .".format(test['test_directory'], test['test_output_xunit'],
                                                test['test_output'], shed_target, api_key )
            print cmd
            cmds.append(cmd)
    return cmds
        
def mp_run(cmd):
    process = subprocess.call(cmd, shell=True)

def yaml_to_dict(yaml_file):
    with open(yaml_file) as handle:
        return yaml.load(handle)
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Get a list of repos with .shed.yml and commence testing')
    parser.add_argument('--workspace', required=True, help='Workspace variable in jenkins/working directory to scan recursively')
    parser.add_argument('--build_number', required=True,  help='Build number in jenkins')
    parser.add_argument('--cores', type=int, default=1, help='Number of cores to use for parallelizing planemo')
    parser.add_argument('--test_type', type=str, choices=['test', 'shed_test'], default='test', help='Select whether to do a shed_test or a simple test')    
    parser.add_argument('--api_keys', default=None, help='Yaml file containing api keys required for shed_test')    
    parser.add_argument('--shed_target', default=None, help='Yaml file containing api keys required for shed_test')
    args = parser.parse_args()

    args.workspace = os.path.abspath(args.workspace)
    clean_reports(args.workspace)
    report_dir, junit_dir = setup_report_dirs(args.workspace, args.build_number)
    if args.test_type == "shed_test":
        try:
            api_keys = yaml_to_dict(args.api_keys)
        except:
            print 'If choosing shed_test provide a valid yaml file.'
            raise
    else:
        api_keys=None
    tests = prepare_tests(args.workspace, report_dir, junit_dir, api_keys)
    prepare_html(report_dir, args.build_number, tests)
    cmds = construct_cmds ( tests, args.test_type, args.shed_target, api_keys)
    if args.cores > 1:
        p = Pool(processes=args.cores)
        result = p.map_async(mp_run, cmds) 
        result.get()
    else:
        [mp_run(cmd) for cmd in cmds]



