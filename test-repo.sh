#!/bin/bash
# Remove old reports, just in case...
rm ${WORKSPACE}/reports/*.xml;
# Remember where we started at because CDing in shells can get messy
orig_dir=$(pwd); 
PLANEMO=planemo

# Report output dir
REPORT_DIR="${WORKSPACE}/reports/${BUILD_NUMBER}/"
JUNIT_DIR="${WORKSPACE}/reports/"
mkdir -p "$REPORT_DIR"

# Need an index for the HTML output report
echo "<html><body><h1>Latest Test Results (${BUILD_NUMBER})</h1><ul>" > ${REPORT_DIR}/index.html;

# Test all the things!

# Test function
function test_it {
	test_directory=$(dirname "$directory")
    test_name=$(dirname "$directory" | sed 's|.*\/||g')
    # Prep link for the HTML report
    echo -n '<li><a href="'$test_name.html'">'$test_name'</a></li>' >> ${REPORT_DIR}/index.html;
    
	cd "$test_directory"
    # Test
    ${PLANEMO} test --install_galaxy \
        --test_output_xunit "$JUNIT_DIR/${test_name}.xml" \
        --test_output "$REPORT_DIR/${test_name}.html";
        
    # Return to whence we came
    cd "$orig_dir";

}

TOOL_DIRS=$(find tools/ -name '.shed.yml');
for directory in $TOOL_DIRS;
do
  sem -j 5 test_it
done

sem --wait

# End of HTML report
echo "</ul></body></html>" >> ${REPORT_DIR}/index.html;
