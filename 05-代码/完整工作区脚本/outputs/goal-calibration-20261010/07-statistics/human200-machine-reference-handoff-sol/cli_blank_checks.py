"""Execute real CLI gates only on issued UNFILLED review, never real labels."""
import sys
sys.dont_write_bytecode=True
import json
import subprocess
from pathlib import Path
import handoff as h

def main():
    results=[]
    for mode in ('validate','analyze'):
        for stage in ('machine_reference','combined'):
            for annual in (False,True):
                out=h.HERE/'rejected-blank-runs'/(mode+'-'+stage+('-annual' if annual else '-noannual'))
                argv=[sys.executable,str(h.HERE/'handoff.py'),mode,'--review',str(h.HERE/'review.UNFILLED.template.json'),'--receive-dir',str(h.ROOT/'05-validation/human200-reception-root/checks/blank200-dry-run'),'--stage',stage,'--output-dir',str(out)]
                if annual:argv.append('--annual')
                run=subprocess.run(argv,text=True,capture_output=True)
                results.append({'mode':mode,'stage':stage,'annual':annual,'returncode':run.returncode,'refusal':'Actual review is unfilled' in run.stderr,'new_output_directory_created':out.exists(),'passed':run.returncode!=0 and 'Actual review is unfilled' in run.stderr and not out.exists(),'stderr':run.stderr,'stdout':run.stdout})
    payload={'status':'real_CLI_on_blank_review_only','code_binding':h.binding(h.HERE/'handoff.py'),'review_binding':h.binding(h.HERE/'review.UNFILLED.template.json'),'cases':results,'passed_N':sum(x['passed'] for x in results),'actual_human_reference_N':0,'actual_LLM_label_files_opened':0,'actual_statistics_or_annual_results_created':0}
    with (h.HERE/'cli-blank-control-results.json').open('x') as f:json.dump(payload,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':payload['passed_N'],'expected':8,'actual_statistics':0}))

if __name__=='__main__':main()
