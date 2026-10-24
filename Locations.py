from typing import Callable, Dict, NamedTuple, Optional, TYPE_CHECKING

from BaseClasses import Location
from .game_data import stage_data, rank_list

if TYPE_CHECKING:
    from . import TraumaSOWorld

import logging
logger = logging.getLogger("Trauma Center Second Opinion")

BASE_ID = 0x1C5200

class TraumaSOLocation(Location):
    game = "Trauma Center Second Opinion"

class TraumaSOLocationData(NamedTuple):
    region: str
    address: Optional[int] = None
    can_create: Callable[["TraumaSOWorld"], bool] = lambda world: True
    #sanity: Callable[["TraumaSOWorld"], bool] = lambda world: True
    locked_item: Optional[str] = None
    id: Optional[int] = None
    loc_type: Optional[str] = None
    

location_data_table: Dict[str, TraumaSOLocation] = {
    
}

#logger.warning(f"stage_data_table = {stage_loc_table}")
for rank_id in range(5):
    rank = rank_list[rank_id]

    location_data_table.update({f"{data.chapter}-{data.episode} {name} {rank} Rank": TraumaSOLocationData(
        region= name,
        address = BASE_ID + (rank_id*0x50) + data.id,
        id = data.id,
        can_create = lambda world, rank_id=rank_id, chapter=data.chapter: (world.options.max_rank.value > rank_id) and (chapter <= world.options.max_chapter.value ),
        loc_type = "Clear"
    )
    for name, data in stage_data.items() if data.type == "Operation"})

location_data_table.update(
    {f"{data.chapter}-{data.episode} {name} Chain" : TraumaSOLocationData(
        region= name,
        address = BASE_ID + 0x400 + data.id,
        id = data.id,
        can_create = lambda world, chapter=data.chapter: world.options.chainsanity.value and (chapter <= world.options.max_chapter.value ),
        loc_type = "Chain"
    )
    for name, data in stage_data.items() if data.chain_score is not None
    }
    )

#opclear_loc_data = {data.address: data.id for name, data in location_data_table.items() if data.loc_type == "Clear"}


location_table = {name: data.address for name, data in location_data_table.items() if data.address is not None}
locked_locations = {name: data for name, data in location_data_table.items() if data.locked_item}