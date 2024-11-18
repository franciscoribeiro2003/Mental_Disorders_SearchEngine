# Variables
PYTHON=python
SCRIPT=scripts/Fill_content.py
INFO_SCRIPT=scripts/info.py
SEARCH_SCRIPT=scripts/search.py
QUERIES_SCRIPT=scripts/queries.py

# Help command to display available options
help:
	@echo "Available Makefile commands:"
	@echo "  - Fill content script:"
	@echo "     Usage: make <target> <input_file> <output_file>"
	@echo "     fill_content      <input_file> <output_file>        - Fill content and description of JSON"
	@echo "     associate_info    <input_file> <output_file>        - Associate new information to JSON"
	@echo "     add_wikidata_link <input_file> <output_file>        - Add Wikidata link and revisions"
	@echo "     edit_content      <input_file> <output_file>        - Edit content and partial Wikipedia scraping"
	@echo "     add_infobox       <input_file> <output_file>        - Add infobox data from Wikipedia"
	@echo "     add_views_edits   <input_file> <output_file>        - Add Wikipedia views and edit count"
	@echo "     clean_fields      <input_file> <output_file>        - Clean redundant text fields"
	@echo "     clean_infobox     <input_file> <output_file>        - Clean infobox fields"
	@echo "     help_script                                         - Show help for the Python script"
	@echo "  - Info:"
	@echo "     names			   - List of all available disorders names"
	@echo "  - Solr server:"
	@echo "     run_solr                                    - Run Solr server"
	@echo "     search_test <schema int>                    - Test Solr search"
	@echo "     queries <schema int> <query settings int>   - Queries Solr search"
	@echo  " Other"
	@echo "     clean               - Remove specified input file"
	@echo "     help                - Show this help"

# Define the input and output files from command line arguments
# The first argument is the input file, and the second is the output file
file1 = $(word 2, $(MAKECMDGOALS))
file2 = $(word 3, $(MAKECMDGOALS))

# Mode 1: Fill content and description
fill_content:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make fill_content <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 1 $(file1) $(file2)

# Mode 2: Associate new information
associate_info:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make associate_info <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 2 $(file1) $(file2)

# Mode 3: Add Wikidata link and revisions
add_wikidata_link:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make add_wikidata_link <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 3 $(file1) $(file2)

# Mode 4: Edit content with partial Wikipedia scraping
edit_content:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make edit_content <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 4 $(file1) $(file2)

# Mode 5: Add infobox from Wikipedia
add_infobox:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make add_infobox <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 5 $(file1) $(file2)

# Mode 6: Add Wikipedia views and edit count
add_views_edits:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make add_views_edits <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 6 $(file1) $(file2)

# Mode 7: Clean redundant text fields
clean_fields:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make clean_fields <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 7 $(file1) $(file2)

# Mode 8: Clean infobox fields
clean_infobox:
	@if [ -z "$(file1)" ] || [ -z "$(file2)" ]; then \
		echo "Input and output files must be specified. Usage: make clean_infobox <input_file> <output_file>"; \
		exit 1; \
	fi
	$(PYTHON) $(SCRIPT) 8 $(file1) $(file2)

# List of all available disorders names
names:
	$(PYTHON) $(INFO_SCRIPT) 1 $(file1)

# Run Solr server
run_solr:
	./scripts/startup.sh

# queries Solr search
queries:
	$(PYTHON) $(QUERIES_SCRIPT) $(file1) $(file2)

# Test Solr search, choose mode 1 for a core with a less complex schema, and mode 2 for a core with a more complex schema
search_test:
	$(PYTHON) $(SEARCH_SCRIPT) $(file1)
# Clean command to remove any generated or intermediate files
clean:
	rm -f $(file1)

# Help command to display help for the Python script
help_script:
	$(PYTHON) $(SCRIPT) --help

# Prevent errors if no arguments are provided
%:
	@echo "Input and output files must be specified. Usage: make <target> <input_file> <output_file>"
	@echo "Type 'make help' for more information."

.PHONY: help fill_content associate_info add_wikidata_link edit_content add_infobox add_views_edits clean_fields clean
