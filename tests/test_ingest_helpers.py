from datetime import date
from fdic_pipeline.ingest import quarter_ends

def test_quarter_ends_inclusive():
    assert quarter_ends(date(2023,1,1),date(2023,12,31)) == ['20230331','20230630','20230930','20231231']

def test_quarter_bounds():
    assert quarter_ends(date(2023,4,1),date(2023,12,31)) == ['20230630','20230930','20231231']
