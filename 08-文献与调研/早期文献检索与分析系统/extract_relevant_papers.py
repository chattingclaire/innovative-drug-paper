import json

def main():
    with open('chuangxinyao.json', 'r') as f:
        all_papers = json.load(f)
    
    with open('framework_relevant_papers.json', 'r') as g:
        relevant = json.load(g)
    
    extracted = []
    for rel in relevant:
        title = rel['original_paper']['title']
        for paper in all_papers:
            if paper['title'] == title:
                extracted.append(paper)
                break
    
    with open('relevant_original_papers.json', 'w') as h:
        json.dump(extracted, h, ensure_ascii=False, indent=4)
    
    print('Extracted and saved to relevant_original_papers.json')

if __name__ == '__main__':
    main()