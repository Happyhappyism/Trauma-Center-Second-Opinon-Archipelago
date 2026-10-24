from typing import Callable, TYPE_CHECKING

from BaseClasses import CollectionState
from .game_data import stage_list, stage_data, rank_list
from .Items import durability_items
if TYPE_CHECKING:
    from . import TraumaSOWorld

from worlds.generic.Rules import add_rule, set_rule

import logging
import math

from worlds.generic.Rules import add_rule, set_rule

logger = logging.getLogger("Trauma Center Second Opinion")

START_TIME = 30


def has_enough_vitals(state, player, world:"TraumaSOWorld", vital_level):
    vital_cap_start = world.options.starting_vital_cap.value
    vital_cap_boost = world.options.durability_boost.value
    vital_boost_need = max(math.ceil((vital_level - vital_cap_start)/vital_cap_boost), 0)
    return state.has("Vitality Boost", player, vital_boost_need)

def has_enough_tool_dura(state, player, world:"TraumaSOWorld", tool, durability_req):
    dura_start = world.options.starting_tool_durability.value
    dura_boost = world.options.durability_boost.value
    dura_need = max(math.ceil((durability_req - dura_start)/dura_boost), 0)
    tool_item = f"{tool} Durability"
    return state.has(tool_item, player, dura_need)

def get_region_rules(player, world:"TraumaSOWorld"):
    region_rules = {}
    goal_stage = None
    goal_val = world.options.game_goal.value
    if goal_val == 1:
        goal_stage = "Death Awaits All"
    elif goal_val == 2:
        goal_stage = "Savato"
        
    for stage, data in stage_data.items():
        entrance_name = f"Menu -> {stage}"
        #if stage == "Standard Procedure":
        #    continue
        if data.type == "Story":
            region_rules[entrance_name] = lambda state, stage_name=stage: state.has(f"{stage_name}", player)
            continue
        dura_start = world.options.starting_tool_durability.value
        #dura_diff = 100 - dura_start
        dura_boost = world.options.durability_boost.value

        vital_cap_start = world.options.starting_vital_cap.value
        #vital_cap_diff = 99 - vital_cap_start
        vital_cap_boost = world.options.durability_boost.value
        vital_boost_need = max(math.ceil((data.vitalreq - vital_cap_start)/vital_cap_boost), 0)
        dura_tool_list = {
            "Gel Durability":data.gel, 
            "Syringe Durability":data.syringe,
            "Sutures Durability":data.sutures, 
            #"Drain Durability":data.drain, 
            "Laser Durability":data.laser, 
            #"Ultrasound Durability":data.ultrasound, 
            "Scalpel Durability":data.scalpel, 
            #"Forceps Durability":data.forceps
            }
        if stage == goal_stage:
            stage = "Healing Touch" # This is a dumb way to do it but this ensures that 
        region_rules[entrance_name] = lambda state, stage_name=stage, vital_boost_need= vital_boost_need, dura_tool_list=dura_tool_list, dura_start=dura_start, dura_boost=dura_boost, healtouch = data.healtouch: \
            state.has(f"{stage_name}", player) and \
            state.has("Vitality Boost", player, vital_boost_need) and \
                all([state.has(tool, player, max(math.ceil((durability - dura_start)/dura_boost), 0)) for tool, durability in dura_tool_list.items() if durability > 0]) and \
                (state.has("Healing Touch", player) or (not healtouch))
        

    #logger.warning(region_rules)
    return region_rules

def get_location_rules(player, world:"TraumaSOWorld"):
    location_rules = {
        "1-1 Standard Procedure B Rank": lambda state: has_enough_vitals(state, player, world, 70),
        "1-1 Standard Procedure A Rank": lambda state: has_enough_vitals(state, player, world, 70),
        "1-1 Standard Procedure S Rank": lambda state: has_enough_vitals(state, player, world, 99),
        "1-1 Standard Procedure XS Rank": lambda state: has_enough_vitals(state, player, world, 99)

    }
    loc_list =  list(world.multiworld.get_locations(world.player))
    for rank_id in range(3, world.options.max_rank.value):
        rank = rank_list[rank_id]
        for name, data in stage_data.items() :
            if data.type == "Operation":
                loc_name = f"{data.chapter}-{data.episode} {name} {rank} Rank"
                try:
                    if loc_name in loc_list:
                        location = world.multiworld.get_location(loc_name, world.player)
                        add_rule(location, lambda state: has_enough_vitals(state, player, world, 80))
                except Exception as e:
                    logger.error(f"Error: {e}")
    return location_rules


def set_rules(world: "TraumaSOWorld"):
    player = world.player
    region_rules = get_region_rules(player, world)
    
    for entrance_name, rule in region_rules.items():
        entrance = world.multiworld.get_entrance(entrance_name, player)
        entrance.access_rule = rule
    
    
        

    location_rules = get_location_rules(player, world)

    for location in world.multiworld.get_locations(player):
        name = location.name
        #if name in location_rules and location_data_table[name].can_create(self.multiworld, player):
        if name in location_rules:
            location.access_rule = location_rules[name]

    game_goal = world.options.game_goal.value
    logger.warning(f"goal = {game_goal}")
    match game_goal:
        
        case 0: # Custom
            custom_goal_location = world.options.custom_goal_location.value
            logger.warning(f"goal = {custom_goal_location}")
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.can_reach_location(custom_goal_location, world.player)
            )
        case 1: # Savato
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.can_reach_location("5-9 Death Awaits All C Rank", world.player) and \
                state.has_from_list(stage_list, world.player, world.options.goal_objective.value)
            )
        case 2: # Savato X
            world.multiworld.completion_condition[world.player] = (
                lambda state: (state.can_reach_location("8-7 Savato C Rank", world.player) or state.can_reach_location("8-7 Savato Naomi C Rank", world.player)) \
                and state.has_from_list(stage_list, world.player, world.options.goal_objective.value)
            )
        case 3: # Needed Clears
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.has_from_list(stage_list, world.player, world.options.goal_objective.value)
            )
        case 4: # Angie Hunt
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.has("Angie's Autograph", world.player, world.options.goal_objective.value)
            )
