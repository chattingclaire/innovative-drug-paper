"""Layout removal counterexamples plus an actual source-only cross-page proof."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
from pdf_layout_reconstruction_v34 import reconstruct_pages,reconstruct_pdf
from source_context_adapter_v34 import norm,authenticated_source_text


def line(text,y):return {'text':text,'y_min':y,'y_max':y+10}


def main():
 pages=[]
 for i in range(1,4):
  body=[line('通用文档页眉',60),line('重复的完整实质内容必须保留。',70),
        line('内文重复行',500),line('X',870),line(f'- {i} -',910),line('通用文档页脚',950)]
  body.insert(3,line('并符合临床必需、安' if i==1 else '全有效、价格合理。' if i==2 else '其他实质内容。',600))
  pages.append({'height':1000,'lines':body})
 result=reconstruct_pages(pages)
 removed=[x['text'] for x in result['removed_layout_lines']]
 assert all(x in removed for x in ['通用文档页眉','通用文档页脚','X','- 1 -','- 2 -','- 3 -'])
 assert result['text'].count('内文重复行')==3
 assert result['text'].count('重复的完整实质内容必须保留。')==3
 # A one-off margin line and a wrong number are not identified as layout.
 counter=reconstruct_pages([{'height':1000,'lines':[line('一次性实质标题',60),line('- 99 -',910),line('1',500)]}])
 assert not counter['removed_layout_lines']
 # The source proof uses the first supplied explicit article, never labels.
 base=HERE.parents[1]
 record=next(json.loads(x)['input'] for x in (base/'rule_inputs_shared_v12.jsonl').read_text().splitlines()
             if json.loads(x)['input'].get('llm_v29_shared_context',{}).get('explicitly_cited_articles_v10'))
 cited=record['llm_v29_shared_context']['explicitly_cited_articles_v10'][0]
 raw=authenticated_source_text(cited['source_path']);actual=reconstruct_pdf(cited['source_path'])
 assert norm(cited['text']) not in norm(raw)
 assert norm(cited['text']) in norm(actual['text'])
 assert actual['removed_layout_lines'] and actual['raw_extraction_claimed_contiguous'] is False
 report={'scope':'source-only layout control; no labels or reference answers',
         'controls':['repeated_outer_lines_removed','interior_repeats_retained',
                     'punctuated_substantive_margin_sentence_retained',
                     'one_off_margin_and_wrong_page_number_retained',
                     'actual_cross_page_quote_reconstructed_only_after_logged_layout_removal'],
         'all_passed':True,'constructed_removed_layout_lines':result['removed_layout_lines'],
         'actual_source_layout_audit':{k:v for k,v in actual.items() if k!='text'},
         'actual_source_quote':cited['text']}
 (HERE/'layout_reconstruction_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'controls':5,'all_passed':True}))


if __name__=='__main__':main()
