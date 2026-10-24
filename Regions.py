from typing import Dict, List, NamedTuple
from .game_data import stage_list

class TraumaSORegionData(NamedTuple):
    connecting_regions: List[str] = []

import logging
logger = logging.getLogger("Trauma Center Second Opinion")

region_data_table: Dict[str, TraumaSORegionData] = {
    "Menu": TraumaSORegionData([
        name for name in stage_list
    ]),
}
region_data_table.update({name: TraumaSORegionData([]) for name in stage_list})

def get_exit(region, exit_name):
    for exit in region.exits:
        if exit.connected_region.name == exit_name:
            return exit