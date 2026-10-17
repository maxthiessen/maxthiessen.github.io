import sys
from pathlib import Path

import bibtexparser
from bibtexparser.customization import *
from bibtexparser.bparser import BibTexParser


def filter_pubtype(list, pubtype):
    '''filter by pubtype and sort in reverse chronological order'''
    filtered_list = [b for b in list if b['publicationtype'] == pubtype]
    
    for b in list:
    	 if 'month' not in b:
    	     b['month'] = 12
 
    return sorted(filtered_list, key=lambda b: (int(b['year']), int(b['month'])), reverse=True)

def nonempty(string, item):
    return (string in item) and (item[string] != '')


def cf(s1, s2, format):
    if format == 'html':
        return s1
    if format == 'tex':
        return s2

def format_bibitem(item, format):
    '''the main workhorse'''
    if 'doi' in item:
        link = f'https://dx.doi.org/{item["doi"]}'
    elif 'url' in item:
        link = item['url']
    else:
        link = ''


    # abstract as mouseover if available
    if nonempty('abstract', item):
        abstract = cf(f'title="{item["abstract"]}"', '', format)
    else:
        abstract = ''

    # start list item
    s = cf('<li>\n', '\\item\n', format)

    # add a label, if desired (for tex this is useful for referencing)
    s += cf('', f'\\label{{{item["ID"]}}}\n', format)

    # authors and title
    if  link:
        s += cf(f'<a {abstract} href="{link}">{item["title"]}</a>', f'\\href{{{link}}}{{{item["title"]}}}', format)
    else:
        s += cf(f'<a {abstract} href="javascript:;">{item["title"]}</a>', f'\\href{{{link}}}{{{item["title"]}}}', format)
    s += cf('<br />\n', '\\newline\n', format)

    # glue the last author to the previous one, so MT never ends up alone on a line
    authors, sep, lastauthor = ' '.join(item["author"].split()).rpartition(', ')
    if sep:
        s += authors + ',' + cf('&nbsp;', '~', format) + lastauthor
    else:
        s += item["author"]

    if "alphabetical" in item:
        s += "<sup><small>αβ</small></sup>"
    
    s += cf('<br />\n', '\\newline\n', format)

    # venue formatting
    if item['ENTRYTYPE'] == 'article':
        if nonempty('abbreviatedvenue', item):
            s += f'{item["abbreviatedvenue"]} ({item["year"]})'
            s += cf('<br />\n', '\\newline\n', format)
        elif nonempty('journal', item):
            s += f'{item["journal"]}'
            if nonempty("volume", item):
                s += f' ({item["volume"]})'
            s += cf('<br />\n', '\\newline\n', format)

    if item['ENTRYTYPE'] == 'inproceedings':
        if nonempty('booktitle', item):
            s += f'{item["abbreviatedvenue"]} ({item["year"]})'
            s += cf('<br />\n', '\\newline\n', format)


    if nonempty('comment', item):
        s += f'({item["comment"]})'
        s += cf('<br />\n', '\\newline\n', format)

    # footer row with optionals
    links = []
    if nonempty('pdf', item):
        links.append(cf(f'[<a href="{item["pdf"]}">pdf</a>]', f'[\\href{{{item["pdf"]}}}{{pdf}}]', format))
    if nonempty('poster', item):
        links.append(cf(f'[<a href="{item["poster"]}">poster</a>]', f'[\\href{{{item["poster"]}}}{{poster}}]', format))
    if nonempty('slides', item):
        links.append(cf(f'[<a href="{item["slides"]}">slides</a>]', f'[\\href{{{item["slides"]}}}{{slides}}]', format))
    if nonempty('video', item):
        links.append(cf(f'[<a href="{item["video"]}">video</a>]', f'[\\href{{{item["video"]}}}{{video}}]', format))
    if nonempty('code', item):
        links.append(cf(f'[<a href="{item["code"]}">code</a>]', f'[\\href{{{item["code"]}}}{{code}}]', format))
    if nonempty('reproduciblerun', item):
        links.append(cf(f'[<a href="{item["reproduciblerun"]}">reproducible run</a>]', f'[\\href{{{item["reproduciblerun"]}}}{{reproducible run}}]', format))
    if nonempty('doi', item):
        links.append(cf(f'[<a href="https://dx.doi.org/{item["doi"]}">doi</a>]', f'[\\href{{https://dx.doi.org/{item["doi"]}}}{{doi}}]', format))
    if nonempty('reviews', item):
        links.append(cf(f'[<a href="{item["reviews"]}">reviews</a>]', f'[\\href{{{item["reviews"]}}}{{reviews}}]', format))
    if nonempty('eprint', item):
        links.append(cf(f'[<a href="https://arxiv.org/abs/{item["eprint"]}">arXiv</a>]', f'[\\href{{https://arxiv.org/abs/{item["eprint"]}}}{{arxiv}}]', format))
    if nonempty('biburl', item):
        links.append(cf(f'[<a href="{item["biburl"]}">bibtex</a>]', f'[\\href{{{item["biburl"]}}}{{bibtex}}]', format))
    if nonempty('venuetype', item) and nonempty('venueurl', item):
        links.append(cf(f'[<a href="{item["venueurl"]}">{item["venuetype"]}</a>]', f'[\\href{{{item["venueurl"]}}}{{{item["venuetype"]}}}]', format))

    # thin spaces keep the html links close together, latex keeps its own spacing
    if links:
        s += cf('<p class="discreet">\n', f'{{\\footnotesize\n', format)
        s += cf('&thinsp;', '\n', format).join(links)
        s += '\n'
        s += cf('</p>\n', f'}}\n', format)
    s += cf('</li>\n', '', format)
    return s


def group_by_year(items):
    '''group an already sorted list of items into [(year, items)] pairs'''
    groups = []
    for b in items:
        if groups and groups[-1][0] == b['year']:
            groups[-1][1].append(b)
        else:
            groups.append((b['year'], [b]))
    return groups


def get_pubtype_html(items):
    '''Create a html list of all (sorted) items, grouped by year'''
    s = '<div class="pubyears">\n'
    for year, group in group_by_year(items):
        s += '<div class="pubyear">\n'
        s += f'<div class="year">{year}</div>\n'
        s += '<ul class="pubs">\n'
        for b in group:
            s += format_bibitem(b, 'html')
        s += '</ul>\n'
        s += '</div>\n'
    s += '</div>\n'
    return s


def get_pubtype_tex(items):
    '''Create a tex enumeration of all (sorted) items'''
    s = '\\begin{enumerate}\n\\conti\n'
    for b in items:
        s += format_bibitem(b, 'tex')
    if not items:
        # suppress 'perhaps a missing \item?' latex error  
        s += '\\makeatletter\\let\\@noitemerr\\relax\\makeatother\n'
    s += '\\seti\n\\end{enumerate}'
    return s


def get_pubtype(list, pubtype, format):
    '''Create a list of all (sorted) items of type pubtype'''
    items = filter_pubtype(list, pubtype)
    if format == 'html':
        return get_pubtype_html(items)
    if format == 'tex':
        return get_pubtype_tex(items)


def authorfirstlast(record):
    record = author(record)

    authors = list()
    for a in record['author']:
        l, f = a.split(', ')
        if f == "Maximilian" and l == "Thiessen":
            s = "MT"
        elif f == "Maximilian" and l == "Thiessen*":
            s = "MT*"
        else:
            s = f + ' ' + l
        authors.append(s)
    record['author'] = ', '.join(authors)
    return record


def customizations(record):
    '''A function to customize our entries.
    It takes a record and return this record.'''

    record = convert_to_unicode(record)
    record = authorfirstlast(record)
    return record

def convert(bibfile, pubtypes=['preprint', 'publication', 'lecturenote', 'nonarchival', 'book'], format='html'):
    with open(bibfile) as bibtex_file:
        parser = BibTexParser()
        parser.customization = customizations
        bibdict = bibtexparser.load(bibtex_file, parser=parser)

        for pubtype in pubtypes:
            pubs = get_pubtype(bibdict.entries, pubtype, format=format)
            with open(f'{pubtype}.{format}_part', 'w') as o:
                o.write(pubs)


if __name__ == '__main__':

    if len(sys.argv) == 2:
        bibfile = sys.argv[1]
    else:
        sys.stderr.write(f'Usage: python {sys.argv[0]} BIBFILE\n')
        sys.exit(1)

    convert(bibfile)
