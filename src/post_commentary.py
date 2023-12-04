from bht.bht_common import *
from bht.bht_analysis import BHTAnalyzer

folder_to_check = "bht gen 2"
bht_analyzer = BHTAnalyzer()
bht_analyzer.post_all_commentary_json(folder_to_check)