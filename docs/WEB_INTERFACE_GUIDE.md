# web interface user guide

comprehensive guide for using the MAPS web interface.

## table of contents

1. [getting started](#getting-started)
2. [dashboard](#dashboard)
3. [uploading files](#uploading-files)
4. [profile management](#profile-management)
5. [processing history](#processing-history)
6. [exporting data](#exporting-data)
7. [troubleshooting](#troubleshooting)

## getting started

### accessing the interface

1. ensure the api backend is running
2. navigate to http://localhost:3000 in your browser
3. the dashboard will load automatically

### navigation

the interface uses a sidebar navigation with the following sections:
- **dashboard**: overview of processing statistics
- **upload**: upload and process xml files
- **profiles**: manage parsing profiles
- **history**: view processing jobs and results
- **documents**: browse processed documents (coming soon)
- **export**: bulk export operations (coming soon)

## dashboard

the dashboard provides an overview of your data processing activity.

### statistics cards

- **total documents**: number of successfully processed documents
- **active jobs**: currently running processing jobs
- **success rate**: percentage of successful processing operations
- **errors**: number of failed processing attempts

### charts and visualizations

- **processing trends**: line chart showing processing activity over time
- **parse case distribution**: pie chart of different parse case types
- **storage usage**: bar chart showing data storage by category

### date range filtering

use the date picker to filter statistics by time period:
1. click the date range selector
2. choose start and end dates
3. click apply to update the dashboard

## uploading files

### single file upload

1. navigate to **upload** page
2. click the upload area or drag a file onto it
3. select an xml file from your computer
4. choose a profile from the list
5. click **start processing**

### batch upload

1. navigate to **upload** page
2. drag multiple xml files onto the upload area
3. or click to select multiple files
4. review the file list
5. choose a profile
6. click **start processing (n files)**

### upload requirements

- **file types**: xml, json
- **file size**: maximum 10mb per file
- **batch limit**: 100 files per batch

### profile selection

profiles define how xml data is parsed and mapped. choose a profile that matches your xml structure:
- **lidc-idri**: for lung image database consortium xml files
- **standard**: generic xml parsing profile
- **custom profiles**: any custom profiles you have created

### monitoring progress

during processing, you will see:
- overall progress bar
- individual file status
- estimated time remaining
- any errors or warnings

### canceling or pausing

use the controls at the bottom of the processing section:
- **pause**: temporarily stop processing
- **resume**: continue paused processing
- **cancel**: stop and discard current batch

## profile management

profiles define how xml files are parsed and mapped to the canonical data model.

### viewing profiles

1. navigate to **profiles** page
2. browse the list of available profiles
3. click a profile to view details

### profile details

each profile shows:
- **name**: unique profile identifier
- **description**: what the profile is used for
- **file type**: supported input file types
- **mappings**: how xml elements are mapped to output fields

### creating a profile

1. click **create new profile** button
2. fill in profile information:
   - name (required, unique)
   - description (optional)
   - file type (xml, json, etc)
3. define mappings:
   - source path (xpath or json path)
   - target path (output field name)
   - data type (string, number, boolean, array)
   - required (yes/no)
4. add validation rules (optional)
5. click **save profile**

### editing a profile

1. select a profile from the list
2. click **edit** button
3. modify profile settings or mappings
4. click **save changes**

### deleting a profile

1. select a profile from the list
2. click **delete** button
3. confirm deletion in the dialog

**warning**: deleting a profile does not affect previously processed files, but you will not be able to process new files with that profile.

### importing/exporting profiles

profiles can be shared as json files:

**export**:
1. select a profile
2. click **export** button
3. profile json file will download

**import**:
1. click **import profile** button
2. select a profile json file
3. review and confirm import

## processing history

view all past and current processing jobs.

### job list

the history page shows a table of all jobs with:
- **job id**: unique identifier (shortened for display)
- **profile**: which profile was used
- **files**: number of files processed
- **status**: pending, processing, completed, failed, cancelled
- **created**: when the job was started
- **actions**: buttons for job operations

### filtering jobs

use filters to find specific jobs:
- **status**: filter by processing status
- **profile**: show only jobs using a specific profile
- **date range**: filter by creation date

### job details

click a job row to see detailed information:
- full job id
- profile name
- status and timestamps
- file count and progress
- error messages (if any)
- processing duration

### job actions

available actions depend on job status:
- **export**: download results (completed jobs only)
- **retry**: reprocess failed files
- **cancel**: stop running job
- **delete**: remove job from history

### pagination

use pagination controls at the bottom:
- **previous/next**: navigate pages
- **page size**: change number of jobs per page
- **jump to page**: enter page number directly

## exporting data

export processed data in various formats.

### export formats

- **excel**: spreadsheet with multiple sheets
  - includes metadata, annotations, difficulty metrics
  - formatted with colors and grouping
  - supports template or standard layouts
- **json**: structured json format
  - canonical document format
  - easy to parse programmatically
- **csv**: comma-separated values
  - flat structure for simple analysis
  - compatible with spreadsheet applications

### exporting from history

1. navigate to **history** page
2. find the completed job
3. click **export** button
4. choose format (excel, json, csv)
5. click **download**

### bulk export

for exporting multiple jobs:
1. navigate to **export** page (coming soon)
2. select date range or filters
3. choose jobs to export
4. select format
5. click **bulk export**

### export options

**excel exports**:
- template layout: uses predefined template structure
- standard layout: flexible column arrangement
- multi-folder: separate sheets for each folder

**json exports**:
- pretty printed for readability
- compact for smaller file size
- includes schema reference

## troubleshooting

### common issues

**cannot connect to server**:
- verify api is running: curl http://localhost:8000/health
- check vite_api_url in .env file
- ensure no firewall blocking port 8000

**file upload fails**:
- check file size (must be under 10mb)
- verify file type (xml or json only)
- ensure file is not corrupted

**profile not found**:
- refresh the profiles list
- verify profile exists in api
- check api logs for errors

**processing stuck**:
- check job status in history
- review api logs for errors
- try canceling and restarting

**export download fails**:
- ensure job is completed
- check browser download settings
- verify disk space available

### getting help

if you encounter issues:
1. check api logs for error details
2. verify api endpoints are responding
3. review browser console for javascript errors
4. consult api documentation at /docs
5. open an issue on github with details

### performance tips

- process files in smaller batches (20-50 files)
- close unused browser tabs to free memory
- use chrome or firefox for best performance
- enable browser caching for faster page loads
- compress large xml files before uploading

### browser compatibility

supported browsers:
- chrome 90+
- firefox 88+
- safari 14+
- edge 90+

not supported:
- internet explorer (any version)
- browsers with javascript disabled

### keyboard shortcuts

- `ctrl/cmd + /`: search profiles
- `ctrl/cmd + u`: go to upload page
- `ctrl/cmd + h`: go to history page
- `esc`: close modals or dialogs

## advanced features

### real-time updates

the interface automatically refreshes:
- processing job status (every 2 seconds)
- dashboard statistics (every 30 seconds)
- profile list when changes occur

### offline mode

basic browsing works offline:
- view cached dashboard data
- browse previously loaded profiles
- view downloaded history

operations requiring api:
- uploading new files
- processing files
- refreshing data
- exporting new results

### accessibility

the interface follows wcag 2.1 aa standards:
- keyboard navigation supported
- screen reader compatible
- high contrast mode available
- focus indicators visible
- aria labels on interactive elements

to enable high contrast:
1. open browser settings
2. enable high contrast mode
3. refresh the page

### mobile usage

the interface is responsive and works on mobile devices:
- optimized touch targets
- swipe gestures for navigation
- compressed views for small screens
- mobile-friendly modals

limitations on mobile:
- file upload may be slower
- large batches not recommended
- some charts simplified
- no drag-and-drop on ios safari

## best practices

### file organization

- name files consistently
- use meaningful identifiers
- organize by study or patient
- keep backups of original files

### profile management

- document profile purpose and mappings
- test profiles on sample files first
- version control profile json files
- share profiles with team members

### processing workflow

1. prepare files and verify format
2. select or create appropriate profile
3. test with a single file first
4. process in batches if successful
5. review results before bulk export
6. archive or delete old jobs periodically

### data export

- export regularly to prevent data loss
- use json for programmatic access
- use excel for manual review
- keep export files organized by date
