from . import BaseTool
import logging
import json
from scholarly import scholarly
logger = logging.getLogger('heymans')


class search_google_scholar(BaseTool):
    """Search Google Scholar for scientific articles"""
    
    arguments = {
        "queries": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of search queries",
        }
    }
    required_arguments = ["queries"]
    
    def __call__(self, queries):
        results = []
        for query in queries:
            for i, result in enumerate(scholarly.search_pubs(query)):
                logger.info(f'appending doc for google scholar search: {query}')
                info = result['bib']
                if 'eprint_url' in result:
                    info['fulltext_url'] = result['eprint_url']
                results.append(info)
                if i >= 3:
                    break
        results = f'''I found {len(results)} articles ...
        
<div class="google-scholar-search-results">
{json.dumps(results)}
</div>'''
        return 'Searching for articles on Google Scholar ...', \
            results, True
