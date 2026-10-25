from typing import List, Dict, Any, ClassVar

from BaseClasses import Region, Tutorial, MultiWorld, ItemClassification
from worlds.AutoWorld import WebWorld, World
from .Items import TraumaSOItem, item_data_table, item_table, item_filler, item_filler_weight, durability_items
from .Locations import TraumaSOLocation, location_data_table, location_table, locked_locations
from .Options import TraumaSOOptions, trauma_so_options_group
from .Regions import region_data_table
from .Rules import *
# from .Rom import MD5Hash, TraumaSOProcedurePatch, write_tokens
# from .Rom import get_base_rom_path as get_base_rom_path
from .game_data import music_tracks, opening_stages
#from .Client import TraumaSOClient
from worlds.LauncherComponents import Component, components, Type, launch_subprocess, icon_paths, SuffixIdentifier

import Utils
import settings
import os
import logging
#import dataclasses
#import typing
#import random

#import pkgutil
#import Patch

import math


logger = logging.getLogger("Trauma Center Second Opinion")

def launch_client():
    from .Client import launch
    launch_subprocess(launch, name="Trauma Center Second Opinion")

components.append(Component("Trauma Center Second Opinion Client", "TraumaSOClient", func=launch_client, component_type=Type.CLIENT,icon="Trauma Center Second Opinion",file_identifier=SuffixIdentifier(".aptcso")))
icon_paths["Trauma Center Second Opinion"] = "ap:worlds.trauma_so/data/icon.png"

class TraumaSOSettings(settings.Group):
    pass
    # class RomFile(settings.UserFilePath):
    #     """File name of the Trauma Center Second Opinion US rom"""
    #     copy_to = "super_trauma_so.gcn"
    #     description = "Trauma Center Second Opinion (US) ROM File"
    #     md5s = MD5Hash

    # rom_file: RomFile = RomFile(RomFile.copy_to)

class TraumaSOWebWorld(WebWorld):
    theme = "partyTime"

    setup_en = Tutorial(
        tutorial_name="Start Guide",
        description="A guide to playing Trauma Center Second Opinion.",
        language="English",
        file_name="guide_en.md",
        link="guide/en",
        authors=["Happymhappyism"]
    )

    tutorials = [setup_en]
    option_groups = trauma_so_options_group

class TraumaSOWorld(World):
    """Roll monkeys in balls"""

    game = "Trauma Center Second Opinion"
    data_version = 1
    web = TraumaSOWebWorld()
    options_dataclass = TraumaSOOptions
    settings: ClassVar[TraumaSOSettings]
    topology_present = False
    settings_key = "trauma_so_settings"
    options: TraumaSOOptions
    location_name_to_id = location_table
    item_name_to_id = item_table

    def __init__(self, world: MultiWorld, player: int):
        super().__init__(world, player)

    def create_item(self, name: str) -> TraumaSOItem:
        return TraumaSOItem(name, item_data_table[name].type, item_data_table[name].code, self.player)
    
    def create_items(self) -> None:
        item_pool: List[TraumaSOItem] = []
        stage_precollect = ['Prolouge','Standard Procedure']
        stage_excludes = []
        goal_val = self.options.game_goal.value 
        if goal_val == 1:
            stage_excludes.append("Death Awaits All")
        elif goal_val == 2:
            stage_excludes.append("Savato")
            stage_excludes.append("Savato Naomi")
        elif goal_val == 5:
            stage_excludes.append("Vulnerability")
        start_op_list = opening_stages.copy()
        self.random.shuffle(start_op_list)
        for x in range((self.options.starting_operations.value -1)):
            start_op = start_op_list.pop()
            stage_precollect.append(start_op)
        for name, item in item_data_table.items():
            if item.code and item.can_create(self):
                if name in stage_precollect:
                    continue
                if name in stage_excludes:
                    continue
                for x in range(item.num_exist):
                    item_pool.append(self.create_item(name))
        
        for stage in stage_precollect:
            self.multiworld.push_precollected(self.create_item(stage))

        if goal_val == 4:
            for x in range(self.options.goal_objective.value):
                item_pool.append(self.create_item("Angie's Autograph"))

        durability_option = self.options.starting_tool_durability.value
        dura_diff = 100 - durability_option
        dura_count = math.ceil(dura_diff/self.options.durability_boost.value)
        for x in range(dura_count):
            for dura_item in durability_items:
                item_pool.append(self.create_item(dura_item))

        vital_cap_option = self.options.starting_vital_cap.value
        vital_cap_diff = 99 - vital_cap_option
        vital_cap_count = math.ceil(vital_cap_diff/self.options.durability_boost.value)
        for x in range(vital_cap_count):
            item_pool.append(self.create_item("Vitality Boost"))

        junk = len(self.multiworld.get_unfilled_locations(self.player)) - len(item_pool)
        item_pool += [self.create_item(self.get_filler_item_name()) for _ in range(junk)]
        self.multiworld.itempool += item_pool

    def create_regions(self) -> None:
        for region_name in region_data_table.keys():
            region = Region(region_name, self.player, self.multiworld)
            self.multiworld.regions.append(region)

        for region_name, region_data in region_data_table.items():
            
            #if region_name in self.included_stages or region_name in fixed_regions:
            region = self.get_region(region_name)
            region.add_locations({
                location_name: location_data.address for location_name, location_data in location_data_table.items()
                if location_data.region == region_name and location_data.can_create(self)
            }, TraumaSOLocation)
            region.add_exits(region_data_table[region_name].connecting_regions)

    
    def get_filler_item_name(self) -> str:
        junk_item = self.random.choices(item_filler,item_filler_weight)[0]
        return junk_item
    
    
    set_rules = set_rules
    

    def fill_slot_data(self) -> Dict[str, Any]:
        music_set = self.options.included_random_music.value
        music_list = []
        vital_cap = self.options.starting_vital_cap.value
        for track in music_set:
            if track in music_tracks:
                music_list.append(music_tracks[track])
        return {
            "DeathLink": self.options.death_link.value,
            "game_goal": self.options.game_goal.value,
            "starting_vital_cap": self.options.starting_vital_cap.value,
            "vitality_boost": self.options.vitality_boost.value,
            "starting_tool_durability": self.options.starting_tool_durability.value,
            "durability_boost": self.options.durability_boost.value,
            "max_rank": self.options.max_rank.value,
            "goal_objective":self.options.goal_objective.value,
            "randomize_operation_music":self.options.randomize_operation_music.value,
            "included_random_music": music_list,
            "custom_goal_location": self.options.custom_goal_location.value,
            "chainsanity": self.options.chainsanity.value,
            "player_name":self.multiworld.player_name[self.player]
        }
    
    def generate_output(self, output_directory: str):
        pass
        # outfilepname = f"_P{self.player}"
        # outfilepname += f"_{self.multiworld.get_file_safe_player_name(self.player).replace(' ', '_')}"
        # self.rom_name_text = f'MB2{Utils.__version__.replace(".", "")[0:3]}_{self.player}_{self.multiworld.seed:11}\0'
        # self.romName = bytearray(self.rom_name_text, "utf8")[:0x20]
        # self.romName.extend([0] * (0x20 - len(self.romName)))
        # self.rom_name = self.romName
        # self.playerName = bytearray(self.multiworld.player_name[self.player], "utf8")[:0x20]
        # self.playerName.extend([0] * (0x20 - len(self.playerName)))
        # patch = TraumaSOProcedurePatch(player=self.player, player_name=self.multiworld.player_name[self.player])
        # #patch.write_file("base_patch.bsdiff4", pkgutil.get_data(__name__, "bombt.bsdiff4"))
        # #procedure = [("apply_bsdiff4", ["base_patch.bsdiff4"]), ("apply_tokens", ["token_data.bin"])]
        # procedure = [("apply_tokens", ["token_data.bin"])]
        # patch.procedure = procedure
        # write_tokens(self, patch)
        # out_file_name = self.multiworld.get_out_file_name_base(self.player)
        # patch.write(os.path.join(output_directory, f"{out_file_name}{patch.patch_file_ending}"))