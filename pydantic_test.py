import pydantic
from medford_models import *

example_paper_data = {
    'Paper': {
        'desc': "Lipopolysaccharide treatment stimulates Pocillopora coral genotype-specific immune responses but does not alter coral-associated bacteria communities",
        'Link': 'https://doi.org/10.1016/j.dci.2020.103717'
    },
    'Date': 
        [{
            'desc': datetime.date.today(),
            'Note': 'Published Date'
        },
        {
            'desc': datetime.date.today(),
            'Note': 'Received'
        }]
}
# How does pydantic handle unknown dict entries?
p = Entity(**example_paper_data)
print(p.Paper.desc)
print(p.Paper.Link)