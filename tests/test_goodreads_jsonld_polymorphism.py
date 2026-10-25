import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_goodreads import StructuredBook

class StructuredDataVariations(unittest.TestCase):
    def parse(self,document):
        parser=StructuredBook()
        parser.feed('<script type="application/ld+json">'+json.dumps(document)+'</script>')
        return parser.books
    def test_multiple_types_include_book(self):
        book={'@type':['Product','Book'],'name':'Coraline','isbn':'9788498382372'}
        self.assertEqual(self.parse(book),[book])
    def test_graph_filters_out_organization_and_webpage(self):
        book={'@type':['Book','CreativeWork'],'name':'Coraline','isbn':'9788498382372'}
        graph={'@graph':[{'@type':'Organization','name':'Editorial'},book,{'@type':'WebPage','name':'Portada'}]}
        self.assertEqual(self.parse(graph),[book])
    def test_multiple_scripts_do_not_erase_previous_books(self):
        parser=StructuredBook()
        for n in (1,2):
            parser.feed('<script type="application/ld+json">'+json.dumps({'@type':'Book','name':str(n)})+'</script>')
        self.assertEqual([b['name'] for b in parser.books],['1','2'])

if __name__=='__main__': unittest.main()
