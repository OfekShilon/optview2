#!/usr/bin/env python3

import argparse
import functools
import html
import io
from multiprocessing import cpu_count
import os.path
import re
import shutil
import sys
import json
import glob
import pathlib
import collections
from datetime import datetime
from pygments import highlight
from pygments.lexers.c_cpp import CppLexer
from pygments.formatters import HtmlFormatter
import optpmap
import optrecord
import config_parser
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

desc = '''Generate HTML output to visualize optimization records from the YAML files
generated with -fsave-optimization-record and -fdiagnostics-show-hotness.

The tools requires PyYAML and Pygments Python packages.'''


# This allows passing the global context to the child processes.
class Context:
    def __init__(self, caller_loc = dict()):
       # Map function names to their source location for function where inlining happened
       self.caller_loc = caller_loc

context = Context()

def suppress(remark):
    if remark.Name == 'sil.Specialized':
        return remark.getArgDict()['Function'][0].startswith('\"Swift.')
    elif remark.Name == 'sil.Inlined':
        return remark.getArgDict()['Callee'][0].startswith(('\"Swift.', '\"specialized Swift.'))
    return False


def render_file_source(source_dir, output_dir, filename, line_remarks):
    html_filename = os.path.join(output_dir, optrecord.html_file_name(filename))
    filename = filename if os.path.exists(filename) else os.path.join(source_dir, filename)

    html_formatter = HtmlFormatter(encoding='utf-8')
    cpp_lexer = CppLexer(stripnl=False)

    def render_source_lines(stream, line_remarks):
        file_text = stream.read()

        html_highlighted = highlight(
            file_text,
            cpp_lexer,
            html_formatter)

        # Note that the API is different between Python 2 and 3.  On
        # Python 3, pygments.highlight() returns a bytes object, so we
        # have to decode.  On Python 2, the output is str but since we
        # support unicode characters and the output streams is unicode we
        # decode too.
        html_highlighted = html_highlighted.decode('utf-8')

        # Take off the header and footer, these must be
        #   reapplied line-wise, within the page structure
        html_highlighted = html_highlighted.replace('<div class="highlight"><pre>', '')
        html_highlighted = html_highlighted.replace('</pre></div>', '')

        for (linenum, html_line) in enumerate(html_highlighted.split('\n'), start=1):
            yield [f'<a name="L{linenum}">{linenum}</a>', '', '', f'<div class="highlight"><pre>{html_line}</pre></div>', '']

            cur_line_remarks = line_remarks.get(linenum, [])
            from collections import defaultdict
            d = defaultdict(list)
            count_deleted = defaultdict(int)
            for obj in cur_line_remarks:
                if len(d[obj.Name]) < 5:
                    d[obj.Name].append(obj)
                else:
                    count_deleted[obj.Name] += 1

            for obj_name, remarks in d.items():
                for remark in remarks:
                    if not suppress(remark):
                        yield render_inline_remarks(remark, html_line)
                if count_deleted[obj_name] != 0:
                    yield ['',
                        0,
                        {'class': f"column-entry-yellow", 'text': ''},
                        {'class': 'column-entry-yellow', 'text': f'''<span " class="indent-span">&bull;...{count_deleted[obj_name]} similar remarks omitted.&nbsp;</span>'''},
                        {'class': f"column-entry-yellow", 'text': ''},
                        ]


    def render_inline_remarks(remark, line):
        inlining_context = remark.DemangledFunctionName
        dl = context.caller_loc.get(remark.Function)
        if dl:
            dl_dict = dict(list(dl))
            link = optrecord.make_link(dl_dict['File'], dl_dict['Line'] - 2)
            inlining_context = f"<a href={link}>{remark.DemangledFunctionName}</a>"

        start_line = re.sub("^<span>", "", line)
        spaces = len(start_line) - len(start_line.lstrip())
        indent = f"{spaces + 2}ch"

        # Create expanded message and link if we have a multiline message.
        lines = remark.message.split('\n')
        if len(lines) > 1:
            expand_link = '<a style="text-decoration: none;" href="" onclick="toggleExpandedMessage(this); return false;">+</a>'
            message = lines[0]
            other_lines = "\n".join(lines[1:])
            expand_message = f'''
<div class="full-info" style="display:none;">
  <div class="expanded col-left" style="margin-left: {indent}"><pre>{other_lines}</pre></div>
</div>'''
        else:
            expand_link = ''
            expand_message = ''
            message = remark.message
        return ['',
                remark.RelativeHotness,
                {'class': f"column-entry-{remark.color}", 'text': remark.PassWithDiffPrefix},
                {'class': 'column-entry-yellow', 'text': f'''<span style="margin-left: {indent};" class="indent-span">&bull; {expand_link} {message}&nbsp;</span>{expand_message}'''},
                {'class': f"column-entry-yellow", 'text': inlining_context},
                ]

    with open(html_filename, "w", encoding='utf-8') as f: 
        if not os.path.exists(filename):
            f.write(f'''
    <html>
    <h1>Unable to locate file {filename}</h1>
</html>''')
            return

        try:
            with open(filename, encoding="utf8", errors='ignore') as source_stream:
                entries = list(render_source_lines(source_stream, line_remarks))
        except:
            print(f"Failed to process file {filename}")
            raise

        entries_summary = collections.Counter(e[2]['text'] for e in entries if isinstance(e[2], dict))
        entries_summary_li = '\n'.join(f"<li>{key}: {value}" for key, value in entries_summary.items())

        f.write(f'''
<html>
<meta charset="utf-8" />
<head>
<title>{os.path.basename(filename)}</title>
<link rel="icon" type="image/png" href="assets/favicon.ico"/>
<link rel='stylesheet' type='text/css' href='assets/style.css'>
<link rel='stylesheet' type='text/css' href='https://cdn.datatables.net/1.10.25/css/jquery.dataTables.min.css'>
<script src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script src="https://cdn.datatables.net/1.10.25/js/jquery.dataTables.min.js"></script>
</head>
<body>
<h1 class="filename-title">{os.path.abspath(filename)}</h1>
<h3>{len(entries_summary)} issue types:</h3>
<ul id='entries_summary'>
{entries_summary_li}
</ul>
<p><a class='back' href='index.html'>Back</a></p>
<table id="opt_table_code" class="" width="100%"></table>
<p><a class='back' href='index.html'>Back</a></p>

<script type="text/javascript">
var dataSet = {json.dumps(entries)};

function toggleExpandedMessage(e) {{
  var FullTextElems = e.parentElement.parentElement.getElementsByClassName("full-info");
  if (!FullTextElems || FullTextElems.length < 1) {{
      return false;
  }}
  var FullText = FullTextElems[0];
  if (FullText.style.display == 'none') {{
    e.innerHTML = '-';
    FullText.style.display = 'block';
  }} else {{
    e.innerHTML = '+';
    FullText.style.display = 'none';
  }}
}}

$(document).ready(function() {{
    $('#opt_table_code').DataTable( {{
        data: dataSet,
        paging: false,
        "ordering": false,
        "asStripeClasses": [],
        columns: [
            {{ title: "Line" }},
            {{ title: "Hotness" }},
            {{ title: "Optimization" }},
            {{ title: "Source" }},
            {{ title: "Inline Context" }}
        ],
        columnDefs: [
            {{
                "targets": "_all",
                "createdCell": function (td, data, rowData, row, col) {{
                    if (data.constructor == Object && data['class'] !== undefined) {{
                        $(td).addClass(data['class']);
                    }}
                }},
                "render": function(data, type, row) {{
                    if (data.constructor == Object && data['text'] !== undefined) {{
                        return data['text'];
                    }}
                    return data;
                }}
            }}
        ]
    }} );
    if (location.hash.length > 2) {{
        var loc = location.hash.split("#")[1];
        var aTag = $("a[name='" + loc + "']");
        if (aTag.length > 0) {{
            $('body').scrollTop(parseInt(aTag.offset().top));
        }}
    }}
}} );
</script>
</body>
</html>
''')

def render_index(output_dir, should_display_hotness, max_hottest_remarks_on_index, all_remarks):
    def render_entry(remark):
        return dict(description=remark.Name,
                    loc=f"<a href={remark.Link}>{remark.DebugLocString}</a>",
                    message=remark.message,
                    functionName=remark.DemangledFunctionName,
                    relativeHotness=remark.RelativeHotness,
                    color=remark.color)

    max_entries = None
    if should_display_hotness:
        max_entries = max_hottest_remarks_on_index

    entries = [render_entry(remark) for remark in all_remarks[:max_entries] if not suppress(remark)]

    entries_summary = collections.Counter(e['description'] for e in entries)
    entries_summary_li = '\n'.join(f"<li>{key}: {value}" for key, value in entries_summary.items())

    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f'''
<html>
<meta charset="utf-8" />
<head>
<link rel="icon" type="image/png" href="assets/favicon.ico"/>
<link rel='stylesheet' type='text/css' href='assets/style.css'>
<link rel='stylesheet' type='text/css' href='https://cdn.datatables.net/1.10.25/css/jquery.dataTables.min.css'>
<script src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script src="https://cdn.datatables.net/1.10.25/js/jquery.dataTables.min.js"></script>
<script src="assets/colResizable-1.6.min.js"></script>
<title>OptView2 Index</title>
</head>
<body>
<h3>{len(entries_summary)} issue types:</h3>
<ul id='entries_summary'>
{entries_summary_li}
</ul>
<div class="centered">
<table id="opt_table" class="" width="100%"></table>
</div>
<script type="text/javascript">
var dataSet = {json.dumps(entries)};
$(document).ready(function() {{
    $('#opt_table').DataTable( {{
        data: dataSet,
        "lengthMenu": [[100, 500, -1], [100, 500, "All"]],
        columns: [
            {{ title: "Location", data: "loc" }},
            {{ title: "Description", data: "description" }},
            {{ title: "Function", data: "functionName" }},
            {{ title: "Message", data: "message" }},
            {{ title: "Hotness", data: "relativeHotness" }},
        ],
        columnDefs: [
            {{
                "targets": [1],
                "createdCell": function (td, data, rowData, row, col) {{
                    $(td).addClass("column-entry-" + rowData['color']);
                }},
            }}
        ]
    }} );
    $("#opt_table").colResizable()
}} );
</script>
</body>
</html>
''')
    return index_path

# TODO: make pmap and _wrapped_func pack arguments, so these dummies won't be needed
def _render_file(source_dir, output_dir, ctx, entry, exclude_names, exclude_text,  collect_opt_success, remarks_src_dir):
    global context
    context = ctx
    filename, remarks = entry
    render_file_source(source_dir, output_dir, filename, remarks)


def map_remarks(all_remarks):
    # Set up a map between function names and their source location for
    # function where inlining happened
    for remark in optrecord.itervalues(all_remarks):
        if isinstance(remark, optrecord.Passed) and remark.Pass == "inline" and remark.Name == "Inlined":
            for arg in remark.Args:
                arg_dict = dict(list(arg))
                caller = arg_dict.get('Caller')
                if caller:
                    try:
                        context.caller_loc[caller] = arg_dict['DebugLoc']
                    except KeyError:
                        pass


def generate_report(all_remarks,
                    file_remarks,
                    source_dir,
                    output_dir,
                    should_display_hotness,
                    max_hottest_remarks_on_index,
                    num_jobs,
                    open_browser=False):
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    logging.info('Rendering index page...')
    logging.info(f"  {len(all_remarks):d} raw remarks")
    if len(all_remarks) == 0:
        logging.warning("Not generating report!")
        return
        
    sorted_remarks = sorted(optrecord.itervalues(all_remarks), key=lambda r: (r.File, r.Line, r.Column, r.PassWithDiffPrefix))
    unique_lines_remarks = [sorted_remarks[0]]
    for rmk in sorted_remarks:
        last_unq_rmk = unique_lines_remarks[-1]
        last_rmk_key = (last_unq_rmk.File, last_unq_rmk.Line, last_unq_rmk.Column, last_unq_rmk.PassWithDiffPrefix)
        rmk_key = (rmk.File, rmk.Line, rmk.Column, rmk.PassWithDiffPrefix)
        if rmk_key != last_rmk_key:
            unique_lines_remarks.append(rmk)
    logging.info("  {:d} unique source locations".format(len(unique_lines_remarks)))

    filtered_remarks = [r for r in unique_lines_remarks if not suppress(r)]
    logging.info("  {:d} after suppressing irrelevant".format(len(filtered_remarks)))

    if should_display_hotness:
        sorted_remarks = sorted(filtered_remarks, key=lambda r: (r.Hotness, r.File, r.Line, r.Column, r.PassWithDiffPrefix, r.yaml_tag, r.Function), reverse=True)
    else:
        sorted_remarks = sorted(filtered_remarks, key=lambda r: (r.File, r.Line, r.Column, r.PassWithDiffPrefix, r.yaml_tag, r.Function))

    index_path = render_index(output_dir, should_display_hotness, max_hottest_remarks_on_index, sorted_remarks)

    logging.info("Copying assets")
    assets_path = pathlib.Path(output_dir) / "assets"
    assets_path.mkdir(parents=True, exist_ok=True)
    for filename in glob.glob(os.path.join(str(pathlib.Path(os.path.realpath(__file__)).parent), "assets", '*.*')):
        shutil.copy(filename, assets_path)

    _render_file_bound = functools.partial(_render_file, source_dir, output_dir, context)
    logging.info('Rendering HTML files...')
    optpmap.pmap(func=_render_file_bound,
                 iterable=file_remarks.items(),
                 processes=num_jobs)

    url_path = f'file://{os.path.abspath(index_path)}'
    logging.info(f'Done - check the index page at {url_path}')
    if open_browser:
        try:
            import webbrowser
            webbrowser.open(url_path)
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        'yaml_dirs_or_files',
        nargs='+',
        help='List of optimization record files or directories searched '
             'for optimization record files.')
    parser.add_argument(
        '--output-dir',
        '-o',
        default='html',
        help='Path to a directory where generated HTML files will be output. '
             'If the directory does not already exist, it will be created. '
             '"%(default)s" by default.')
    parser.add_argument(
        '--jobs',
        '-j',
        default=None,
        type=int,
        help='Max job count (defaults to %(default)s, the current CPU count)')

    parser.add_argument(
        '--source-dir',
        '-s',
        default='',
        help='set source directory')

    parser.add_argument(
        '--max-hottest-remarks-on-index',
        default=1000,
        type=int,
        help='Maximum number of the hottest remarks to appear on the index page')

    parser.add_argument(
        '--demangler',
        help='Set the demangler to be used (defaults to %s)' % optrecord.Remark.default_demangler)

    parser.add_argument(
        '--exclude-name',
        default='',
        help='Omit optimization remarks with names matched by this regex')

    parser.add_argument(
        '--exclude-text',
        default='',
        help='Omit optimization remarks with names matched by this regex')

    parser.add_argument(
        '--collect-opt-success',
        action='store_true',
        help='Collect all optimization remarks, not just failures')

    parser.add_argument(
        '--annotate-external',
        action='store_true',
        help='Annotate all files, including system headers')

    parser.add_argument(
        '--open-browser',
        action='store_true',
        help='Open browser after generating HTML files')

    parser.add_argument(
        '--split-top-folders',
        action='store_true',
        help='Operate separately on every top level subfolder containing opt files - to workaround out-of-memory crashes')

    # Do not make this a global variable.  Values needed to be propagated through
    # to individual classes and functions to be portable with multiprocessing across
    # Windows and non-Windows.
    cur_folder = pathlib.Path(__file__).parent.resolve()
    conf_file = os.path.join(cur_folder, "config.yaml")
    with open(conf_file, 'r') as config_file:
        config = config_parser.parse(config_file)
    parser.set_defaults(**config)
    args = parser.parse_args()

    if args.demangler:
        optrecord.Remark.set_demangler(args.demangler)

    start_time = datetime.now()

    if args.split_top_folders:
        subfolders = []
        for item in os.listdir(args.yaml_dirs_or_files[0]):
            if os.path.isfile(os.path.join(args.yaml_dirs_or_files[0], item)):
                continue
            subfolders.append(item)

        for subfolder in subfolders:
            files = optrecord.find_opt_files(os.path.join(args.yaml_dirs_or_files[0], subfolder))
            if not files:
                continue

            logging.info(f"Processing subfolder {subfolder}")

            all_remarks, file_remarks, should_display_hotness = \
                optrecord.gather_results(filenames=files, num_jobs=args.jobs,
                                         exclude_names=args.exclude_names,
                                         exclude_text=args.exclude_text,
                                         collect_opt_success=args.collect_opt_success,
                                         annotate_external=args.annotate_external)

            map_remarks(all_remarks)

            generate_report(all_remarks=all_remarks,
                        file_remarks=file_remarks,
                        source_dir=args.source_dir,
                        output_dir=os.path.join(args.output_dir, subfolder),
                        should_display_hotness=should_display_hotness,
                        max_hottest_remarks_on_index=args.max_hottest_remarks_on_index,
                        num_jobs=args.jobs,
                        open_browser=args.open_browser)
    else: # not split_top_foders
        files = optrecord.find_opt_files(os.path.join(*args.yaml_dirs_or_files))
        if not files:
            parser.error("No *.opt.yaml files found")
            sys.exit(1)

        all_remarks, file_remarks, should_display_hotness = \
            optrecord.gather_results(filenames=files, num_jobs=args.jobs,
                                     exclude_names=args.exclude_names,
                                     exclude_text=args.exclude_text,
                                     collect_opt_success=args.collect_opt_success,
                                     annotate_external=args.annotate_external)

        map_remarks(all_remarks)

        generate_report(all_remarks=all_remarks,
                        file_remarks=file_remarks,
                        source_dir=args.source_dir,
                        output_dir=args.output_dir,
                        should_display_hotness=should_display_hotness,
                        max_hottest_remarks_on_index=args.max_hottest_remarks_on_index,
                        num_jobs=args.jobs,
                        open_browser=args.open_browser)

    end_time = datetime.now()
    logging.info(f"Ran for {end_time-start_time}")

if __name__ == '__main__':
    main()

