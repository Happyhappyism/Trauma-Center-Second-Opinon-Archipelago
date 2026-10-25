from typing import Callable, Dict, NamedTuple, Optional, TYPE_CHECKING

from BaseClasses import Item, ItemClassification
from .game_data import stage_data

import logging
logger = logging.getLogger("Trauma Center Second Opinion")

if TYPE_CHECKING:
    from . import TraumaSOWorld
    

class TraumaSOItem(Item):
    game = "Trauma Center Second Opinion"

class TraumaSOItemData(NamedTuple):
    code: Optional[int] = None
    type: ItemClassification = ItemClassification.filler
    num_exist: int = 1
    can_create: Callable[["TraumaSOWorld"], bool] = lambda world: True
    fillweight: Optional[float] = None
    item_type: Optional[str] = None
    id: Optional[int] = None

item_data_table: Dict[str, TraumaSOItemData] = {
    

    # "Example Item": TraumaSOItemData(
    #     code=0x40001,
    #     type=ItemClassification.progression,
    # ),
    "Vitality Boost": TraumaSOItemData(
        code=0x1C5250,
        type=ItemClassification.progression,
        num_exist= 0,
    ),
    "Healing Touch": TraumaSOItemData(
        code=0x1C5251,
        type=ItemClassification.progression,
        num_exist= 1,
    ),
    "Naomi Healing Touch": TraumaSOItemData(
        code=0x1C5252,
        type=ItemClassification.progression,
        num_exist= 0,
    ),
    "Gel Durability": TraumaSOItemData(
        code=0x1C5253,
        type=ItemClassification.progression,
        item_type = "durability",
        num_exist= 0,
    ),
    "Syringe Durability": TraumaSOItemData(
        code=0x1C5254,
        type=ItemClassification.progression,
        item_type = "durability",
        num_exist= 0,
    ),
    "Sutures Durability": TraumaSOItemData(
        code=0x1C5255,
        type=ItemClassification.progression,
        item_type = "durability",
        num_exist= 0,
    ),
    "Drain Durability": TraumaSOItemData(
        code=0x1C5256,
        type=ItemClassification.filler,
        #item_type = "durability",
        num_exist= 0,
    ),
    "Laser Durability": TraumaSOItemData(
        code=0x1C5257,
        type=ItemClassification.progression,
        item_type = "durability",
        num_exist= 0,
    ),
    "Ultrasound Durability": TraumaSOItemData(
        code=0x1C5258,
        type=ItemClassification.filler,
        #item_type = "durability",
        num_exist= 0,
    ),
    "Scalpel Durability": TraumaSOItemData(
        code=0x1C5259,
        type=ItemClassification.progression,
        item_type = "durability",
        num_exist= 0,
    ),
    "Forceps Durability": TraumaSOItemData(
        code=0x1C525A,
        type=ItemClassification.filler,
        #item_type = "durability",
        num_exist= 0,
    ),
    "Stabilizer Shot": TraumaSOItemData(
        code=0x1C525B,
        type=ItemClassification.filler,
        num_exist= 0,
        fillweight= 1,
    ),
    "Angie's Autograph": TraumaSOItemData(
        code=0x1C525C,
        type=ItemClassification.progression,
        num_exist= 0
    ),


}
#logger.warning(f"stage_data_table = {stage_item_table}")

item_data_table.update({name: TraumaSOItemData(
    code = 0x1C5200 + data.id,
    type = ItemClassification.progression,
    #type = lambda episode_type=data.type: ItemClassification.progression if episode_type == "Operation" else ItemClassification.filler,
    can_create=lambda world, chapter=data.chapter: chapter <= world.options.max_chapter.value,
    item_type = "stage unlock",
    id = data.id,
)
for name, data in stage_data.items() #if data.goal_operation == False
})
durability_items = [name for name, data in item_data_table.items() if data.item_type == "durability"]


item_table = {name: data.code for name, data in item_data_table.items() if data.code is not None}
item_id_to_name = {data.code: name for name, data in item_data_table.items() if data.code is not None}
item_filler = [name for name, data in item_data_table.items() if data.type == ItemClassification.filler and data.fillweight is not None]
item_filler_weight = [data.fillweight for name, data in item_data_table.items() if data.type == ItemClassification.filler and data.fillweight is not None]