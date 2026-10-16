"""Reconstruct PDF body across pages with auditable layout-line removals.

Only repeated lines in outer page bands or consistent explicit page-number
lines are removed. Interior lines and complete sentences are retained. This
module never inspects policy titles, IDs, institutions or dimension words.
"""
from collections import defaultdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET


def key(text):
    return ''.join(unicodedata.normalize('NFKC',text).split())


def reconstruct_pages(pages):
    occurrences=defaultdict(list)
    for page_no,page in enumerate(pages,1):
        height=page['height']
        for line_no,line in enumerate(page['lines'],1):
            text=key(line['text']);y=line['y_min']/height
            outer=y<=0.12 or y>=0.86
            # A fully punctuated sentence is body content even in a margin.
            if outer and text and len(text)<=60 and not re.search(r'[。；;！？!?]$',text):
                occurrences[text].append((page_no,line_no,y))
    repeated={}
    threshold=max(2,math.ceil(len(pages)*0.6))
    for text,values in occurrences.items():
        if len({x[0] for x in values})>=threshold and max(x[2] for x in values)-min(x[2] for x in values)<=0.025:
            repeated[text]=len({x[0] for x in values})
    kept=[];removed=[]
    for page_no,page in enumerate(pages,1):
        body=[]
        for line_no,line in enumerate(page['lines'],1):
            text=key(line['text']);y=line['y_min']/page['height'];reason=None
            if (y<=0.12 or y>=0.86) and text in repeated:
                reason='repeated_line_in_outer_page_band'
            number=re.fullmatch(r'[-—–－]\s*(\d{1,4})\s*[-—–－]',line['text'].strip())
            if number and int(number.group(1))==page_no and (y<=0.2 or y>=0.8):
                reason='explicit_decorated_page_number_in_outer_band'
            if reason:
                removed.append({'page':page_no,'line':line_no,'text':line['text'],
                                'y_min':line['y_min'],'y_max':line['y_max'],
                                'page_height':page['height'],'reason':reason,
                                'repeated_page_n':repeated.get(text,0)})
            else:
                body.append(line['text'])
        kept.append('\n'.join(body))
    text='\n'.join(kept)
    return {'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'removed_layout_lines':removed,
            'removed_layout_lines_sha256':hashlib.sha256(json.dumps(removed,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
            'method':'pdftotext_bbox_per_page_repeat_and_explicit_page_number_layout_reconstruction',
            'raw_extraction_claimed_contiguous':False}


@lru_cache(maxsize=256)
def reconstruct_pdf(path):
    if Path(path).suffix.lower()!='.pdf':
        return None
    result=subprocess.run(['pdftotext','-bbox-layout','-enc','UTF-8',path,'-'],
                          check=True,capture_output=True,text=True)
    document=ET.fromstring(result.stdout)
    pages=[]
    for page in document.iter():
        if page.tag.rsplit('}',1)[-1]!='page':continue
        lines=[]
        for line in page.iter():
            if line.tag.rsplit('}',1)[-1]!='line':continue
            words=[''.join(w.itertext()) for w in line
                   if w.tag.rsplit('}',1)[-1]=='word']
            if not words:continue
            lines.append({'text':' '.join(words),'y_min':float(line.attrib['yMin']),
                          'y_max':float(line.attrib['yMax'])})
        pages.append({'height':float(page.attrib['height']),'lines':lines})
    out=reconstruct_pages(pages)
    out['source_sha256']=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    out['source_path']=str(Path(path).resolve())
    return out
