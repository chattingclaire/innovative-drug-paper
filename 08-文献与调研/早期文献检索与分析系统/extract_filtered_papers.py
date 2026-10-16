import json

def main():
    with open('/Users/moonshot/Desktop/创新药.md/relevant_original_papers.json', 'r') as f:
        papers = json.load(f)
    
    filtered = [p for p in papers if int(p.get('page_count', 0)) >= 5]
    
    with open('/Users/moonshot/Desktop/创新药.md/filtered_relevant_papers.json', 'w') as out:
        json.dump(filtered, out, ensure_ascii=False, indent=4)
    
    print('Filtered papers with 5 or more pages saved to filtered_relevant_papers.json')

if __name__ == '__main__':
    main()