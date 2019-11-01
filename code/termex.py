import aiohttp
import argparse
import asyncio
import configparser
import os
import re
import sys
import traceback

folder = os.path.join(os.path.abspath(os.path.expanduser('~/')), '.termex')
repo_name_pat = re.compile('/([^/]+).git$')


def _normpath(x):
    return os.path.normpath(os.path.abspath(x))


def fetch_git(source_uri, repos):
    print('Fetching git repo %s.' % source_uri)
    cwd = os.getcwd()
    os.chdir(repos)
    try:
        m = repo_name_pat.search(source_uri)
        if not m:
            raise Exception("Can't understand cloneable git URI %s." % source_uri)
        folder = m.group(1)
        if os.path.isdir(os.path.join(folder, '.git')):
            os.chdir(folder)
            os.system('git pull')
        else:
            os.system('git clone %s' % source_uri)
        return os.path.join(repos, folder)
    finally:
        os.chdir(cwd)


def next_doc(root, pat):
    if root.endswith('/'):
        root = root[:-1]
    for parent, folders, files in os.walk(root):
        for f in files:
            candidate = '/' + os.path.relpath(os.path.join(parent, f), root)
            if pat.match(candidate):
                candidate = candidate[1:]
                print('  %s' % candidate)
                yield os.path.join(root, candidate)


def fetch_web(source_uri):
    # Calling async this way is throwing away most of its benefits,
    # but I'm not trying to get asynchronicity out of it; I'm just
    # trying to avoid a dependency on the requests library...
    async def async_fetch(uri):
        with aiohttp.ClientSession() as session:
            async with session.get(uri) as resp:
                return await resp.text()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(async_fetch(source_uri))
    return result


easy_markdown_para_pat = re.compile(r'\n\s*([-*]\s+|>|#+|\d[.]\s+)')
header_pat = re.compile(r'#+')
def is_beginning_of_markdown_para(content, i):
    # Does this line begin in a way that we know is a new paragraph?
    if easy_markdown_para_pat.match(content, i):
        return True
    # Else is this line preceded by a blank line?
    while i > 0:
        i -= 1
        prev = content[i]
        # Found preceding blank line with nothing else but whitespace,
        # so we're at the beginning of a paragraph.
        if prev == '\n':
            return True
        # Found preceding line that ended in punctuation or text.
        elif prev not in ' \t\r':
            # Find start of this preceding line.
            start_of_prev_line = content.rfind('\n', 0, i)
            # Was the preceding line a header? If yes, then the current line
            # is independent content. Otherwise, the line we were asked about
            # is a subsequent line of a longer paragraph.
            return bool(header_pat.match(content, i + 1))
    # If we get here, we got to beginning of string before finding start
    # of paragraph another way--so beginning of string is start.
    return True


end_pat = re.compile(r'\n\s*(\n|[-*]\s+|>|#+|\d[.]\s+)')
def get_markdown_context(content, match):
    i = match.start()
    begin = None
    while begin is None:
        i = content.rfind('\n', 0, i)
        if i == -1:
            begin = 0
        else:
            if is_beginning_of_markdown_para(content, i):
                begin = i + 1
        i -= 1
    if header_pat.match(content, begin):
        end = content.find('\n')
        if end == -1:
            end = len(content)
    else:
        end = end_pat.search(content, match.end())
        end = len(content) if not end else end.start()
    return content[begin:end].strip()


markdown_termdef_pat = re.compile(r'\W__([A-Za-z].*?)__')
def extract_from_markdown(content):
    for match in markdown_termdef_pat.finditer(content):
        md = get_markdown_context(content, match)
        descrip = squeeze(strip_tags(md))
        print(match.group(1) + ':\n' + descrip + '\n\n')


respec_termdef_pat = re.compile((r'<dfn([^>]+)?>(.*?)</dfn\s*>'))
# We want to find this regex searching backward: <(div|p|dt|li|dd)(\s+[^>]*)?>
# However, normal regex doesn't let us search for a regex going backward, and
# a simple reversal of the regex's pattern characters won't produce a valid
# regex that can be run against a reversed string, either. So hand-write that
# regex such that it can be matched against a reversed version of the string
# that comes before.
respec_section_beginner_pat = re.compile(r'>([^<]*\s*)?(vid|p|td|il|dd)\s*<', re.I)
tag_extractor_pat = re.compile(r'<\s*(div|p|dt|li|dd)(\s+[^>]*)?>', re.I)

def get_respec_context(content, reversed, match):
    # Search forward in the reversed string, looking for a tag that's able to begin
    # a paragraph.
    beginner = respec_section_beginner_pat.search(reversed, len(content) - match.start())
    begin_tag = tag_extractor_pat.match(content, len(content) - beginner.end())
    end_tag_pat = re.compile(r'</%s>' % begin_tag.group(1))
    end_tag = end_tag_pat.search(content, match.end())
    return content[begin_tag.end():end_tag.start()].strip()


tag_pat = re.compile(r'</?[-a-zA-Z0-9_]+(\s+[^>]*?)?>')
def strip_tags(txt):
    return tag_pat.sub('', txt)

ws_pat = re.compile('[ \t\r\n]+')
def squeeze(txt):
    return ws_pat.sub(' ', txt)


def extract_from_respec(content):
    # Generate a reversed version of the content once. We need this so we can search
    # backward for regexes, and generating it once instead of many times will save
    # enormous amounts of effort.
    reversed = content[::-1]
    for match in respec_termdef_pat.finditer(content):
        html = get_respec_context(content, reversed, match)
        descrip = squeeze(strip_tags(html))
        print(match.group(2) + ':\n' + descrip + '\n\n')


def extract_from_content(content, content_type):
    if content_type == 'markdown':
        extract_from_markdown(content)
    else:
        extract_from_respec(content)


def extract_from_repo(section, root):
    for content_type in ['markdown', 'respec']:
        for i in range(1, 1000):
            pat_name = '%s pat %s' % (content_type, i)
            print(pat_name)
            if pat_name in section:
                pat = re.compile(section[pat_name])
                for doc_path in next_doc(root, pat):
                    with open(doc_path, 'rt') as f:
                        content = f.read()
                    extract_from_content(content, content_type)
            else:
                break


def get_content_type_from_path(path):
    return "markdown" if path.endswith('.md') else 'respec'


def extract_from_source(cfg, section, out, repos):
    source = section['source uri']
    if source.endswith('.git'):
        root = fetch_git(source, repos)
        extract_from_repo(section, root)
    elif '://' in source:
        content = fetch_web(source)
        extract_from_content(content, 'respec')
    else:
        path = os.path.normpath(os.path.join(os.path.dirname(cfg), source))
        if os.path.isdir(path):
            extract_from_repo(section, path)
        elif os.path.isfile(path):
            with open(path, 'rt') as f:
                content = f.read()
            extract_from_content(content, get_content_type_from_path(path))
        else:
            raise Exception("Unrecognized type for source %s -- doesn't seem to be git repo, URI, or local folder." % source)


def accessible_default_folder():
    if not os.path.isdir(folder):
        os.makedirs(folder)


def main(cfg, out, repos):
    def make_termex_on_demand(possible_child_folder):
        # We don't want to call os.makedirs() here; we only want to make ~/.termex
        # on demand, nothing else.
        if folder in possible_child_folder and not os.path.isdir(folder):
            os.mkdir(folder)

    cfg = _normpath(cfg)
    out = _normpath(out)
    repos = _normpath(repos)
    if not os.path.isfile(cfg):
        raise Exception("Config file %s doesn't exist." % cfg)
    if not os.path.isdir(out):
        make_termex_on_demand(out)
        # We want this to fail if out's parent doesn't exist.
        os.mkdir(out)
    if not os.path.isdir(repos):
        make_termex_on_demand(repos)
        # We want this to fail if repos's parent doesn't exist.
        os.mkdir(repos)
    ini = configparser.ConfigParser()
    ini.read(cfg)
    for section in ini.sections():
        try:
            print("\nExtracting from %s" % section)
            extract_from_source(cfg, ini[section], out, repos)
        except KeyboardInterrupt:
            sys.exit(0)
        except SystemExit:
            return
        except:
            traceback.print_exc()


if __name__ == '__main__':
    syntax = argparse.ArgumentParser(description='Extract terminology from canonical sources.')
    syntax.add_argument('--cfg', metavar='FILE', default=os.path.join(folder, 'cfg.ini'), help='file that defines extraction targets')
    syntax.add_argument('--out', metavar='FOLDER', default=os.path.abspath('.'), help='folder where output should be created')
    syntax.add_argument('--repos', metavar='FOLDER', default=os.path.join(folder, 'repos'), help='folder where git repos should be cloned')
    args = syntax.parse_args()
    main(args.cfg, args.out, args.repos)