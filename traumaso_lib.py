from typing import TYPE_CHECKING
import dolphin_memory_engine as dme
import logging
import time
import traceback
import random
from .Items import item_id_to_name
from .Locations import BASE_ID, location_data_table
from .game_data import stage_data, clear_vals, story_ids, stage_item_data, stage_clear_dict, chain_data

from NetUtils import NetworkItem
if TYPE_CHECKING:
    from .Client import TraumaSOClient
logger = logging.getLogger("TCSO Debug")

opclear_loc_data = {}
stageid_to_name = {}

RECV_ADR = 0x80711c70
SEED_ADR = 0x80711c74

MEM_GAME_ID = 0x80000000
MEM_SCORE_BASE = 0x80711b50
MEM_GAME_STATE = 0x80287828
MEM_TOOL_USAGE = 0x802990f4
MEM_DURABILITY_BASE = 0x8023f7f4
MEM_TOOL_BASE = 0x802990B4
MEM_TOOL_HAVE_BASE = 0x80299038
MEM_HEAL_TOUCH = 0x8029a654
MEM_EPISODE_UNLOCKS = 0x8070DB00
MEM_EPISODE_SELECTED = 0x81285b34
MEM_CHAPTER_SELECTED = 0x81285b46
MEM_EPISEL_SCROLLCAP = 0x81282d04
MEM_OPERATION_BASE_STATS = 0x802508d8
MEM_DIFFICULTY = 0x80711b0c
MEM_PLAYER_NAME = 0x80711DD0
#MEM_OP_LOSS = 0x80287828
PTR_OPERATION_STATS = 0x803A7870
AP_TOOL_DURA_SAVE = 0x80711d20
AP_FIRST_RUN = 0x816ffff0
CONST_TOTAL_STAGES = 0x4D

DOL_BAUDOADVANCE = 0x8005a804
DOL_BADDNEXTSTAGE = 0x8005a544

NOP = 0x60000000


def set_bit(offset, bit, reset=False):
    try:
        old_val = dme.read_byte(offset)
        mask = 1 << bit
        if reset:
            mask_off = 0xFF - mask
            new_val = old_val & mask_off
        else:
            new_val = old_val | mask
        dme.write_byte(offset, new_val)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def set_wbit(offset, bit, reset=False):
    try:
        old_val = dme.read_word(offset)
        mask = 1 << bit
        if reset:
            mask_off = 0xFFFFFFFF - mask
            new_val = old_val & mask_off
        else:
            new_val = old_val | mask
        dme.write_word(offset, new_val)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def write_word_mask(offset, mask, reset=False):
    try:
        old_val = dme.read_word(offset)
        if reset:
            mask_off = 0xFFFFFFFF - mask
            new_val = old_val & mask_off
        else:
            new_val = old_val | mask
        new_val = old_val | mask
        dme.write_word(offset, new_val)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def get_vitals_adr(operation_stat_ptr):
    try:
        
        if operation_stat_ptr == 0:
            return 0
        vitals_ptr = dme.read_word(operation_stat_ptr+0x18)
        return vitals_ptr
    except Exception as e:
            logger.critical(f"Error processing items: {e}\n{traceback.format_exc()}")

def randomize_music(ctx:"TraumaSOClient"):
    try:
        if dme.read_word(MEM_OPERATION_BASE_STATS+0x10) == 0xB:
            for offset in range(MEM_OPERATION_BASE_STATS, MEM_OPERATION_BASE_STATS+ (0x34 * 0x3D), 0x34):
                if offset == 0x8025106C:
                    continue
                music_offset = offset + 0x10
                random_track_id = random.choice(ctx.included_random_music)
                dme.write_word(music_offset, random_track_id)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def init_vars():
    try:
        stageid_to_name.update({data.id: name for name, data in stage_data.items()})
        # opclear_loc_data
        for x in range(CONST_TOTAL_STAGES+1):
            opclear_loc_data[x] = {}
        for rank_id in range(5):
            for name, data in stage_data.items(): 
                stage_id = data.id
                if stage_id in story_ids:
                    continue
                apid = BASE_ID + (rank_id*0x50) + stage_id
                rank_val = rank_id + 1
                opclear_loc_data[stage_id][rank_val] = apid
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def verify_patches(ctx:"TraumaSOClient"):
    try:
        patch_state = dme.read_word(DOL_BAUDOADVANCE)
        if patch_state != NOP:
            livepatch_game(ctx)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def livepatch_game(ctx:"TraumaSOClient"):
    try:
        #dme.write_word(0x80015d3c, NOP)
        dme.write_word(DOL_BAUDOADVANCE, NOP) # Do not autoadvance stage after a clear
        dme.write_word(DOL_BADDNEXTSTAGE, NOP) # Do not autoadvance stage after a clear
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def sync_state(ctx:"TraumaSOClient"):
    try:
        # Runs one time when the game is found to be in a valid state.
        if ctx.randomize_operation_music:
            randomize_music(ctx)
        for offset, mask in clear_vals.items():
            old_val = dme.read_word(MEM_EPISODE_UNLOCKS+offset)
            new_val = old_val | mask
            dme.write_word(MEM_EPISODE_UNLOCKS+offset, new_val)
        livepatch_game(ctx)
        dme.write_word(AP_FIRST_RUN, 1)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def handle_healing_touch(current_stage):
    # set healing touch
    cur_tool = dme.read_word(MEM_TOOL_BASE + 0x14)
    item_have_flags = dme.read_word(RECV_ADR + 0x8)
    ht_exceptions = [0x8, 0x13]# Life or Death has a scripted HT sequence and defib breaks with HT
    savato_stages = [0x31, 0x39, 0x41, 0x4D]
    heal_touch_state = dme.read_word(MEM_HEAL_TOUCH)
    if current_stage in ht_exceptions: 
        pass
    elif current_stage in savato_stages:
        if item_have_flags & 0x1:
            pass
        else:
            dme.write_word(MEM_HEAL_TOUCH, 0x2)
    elif cur_tool == 0xC:
        dme.write_word(MEM_HEAL_TOUCH, 0x2)
    elif heal_touch_state & 1:
        pass
    elif (item_have_flags & 0x1) and (cur_tool != 0xC):
        # Make sure the select tool isn't the defib
        dme.write_word(MEM_HEAL_TOUCH, 0x0)
    else:
        dme.write_word(MEM_HEAL_TOUCH, 0x2)

def set_operation_items(ctx:"TraumaSOClient", vitals_ptr):
    try:
        current_stage = dme.read_word(MEM_EPISODE_SELECTED)
        stage_name = stageid_to_name[current_stage]
        handle_healing_touch(current_stage)
        # set vital cap
        stage_vital_cap = stage_data[stage_name].vitalcap
        vital_boost_have = dme.read_word(RECV_ADR+0xC)
        new_vital_cap = min((ctx.starting_vital_cap + (ctx.vitality_boost * vital_boost_have)), stage_vital_cap)
        dme.write_float(vitals_ptr+0x8, new_vital_cap)

        # Set durability caps
        tool_id = 0
        starting_dura = ctx.starting_tool_durability
        dura_boost = ctx.durability_boost
        for offset in range(MEM_DURABILITY_BASE, MEM_DURABILITY_BASE + (0x14 * 0x8), 0x14):
            tool_count = dme.read_word(AP_TOOL_DURA_SAVE + (tool_id * 4))
            dura_increase = dura_boost * tool_count
            dura_value = min(starting_dura + dura_increase, 100)
            dme.write_float(offset+0x10, dura_value)
            tool_use_offset = MEM_TOOL_USAGE + (0xC * tool_id)
            tool_usage = dme.read_float(tool_use_offset)
            if tool_usage > dura_value:
                dme.write_float(tool_use_offset, dura_value)
            tool_id += 1
        #logger.info(f"locals: {locals()}, start_vital: {ctx.starting_vital_cap}, vital_boost: {ctx.vitality_boost}")
    except Exception as e:
        logger.critical(f"Error setting operation items: {e}\n{traceback.format_exc()}")
        logger.info(f"locals: {locals()}")

def check_deathlink(ctx:"TraumaSOClient"):
    try:
        if ctx.last_death_link + 6 < time.time():
            if (ctx.game_state == 0x2D)  and (ctx.death_state_triggered == False):
                ctx.dl_triggered = True
                ctx.last_death_link = time.time()
                ctx.death_state_triggered = True
            elif ctx.game_state != 0x2D:
                ctx.death_state_triggered == False
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def process_items(ctx:"TraumaSOClient", item_list, start_index):
    try:
        recv_index = dme.read_word(RECV_ADR)
        new_idx = start_index
        #stages_unlocked = dme.read_bytes(MEM_EPISODE_UNLOCKS, 0xC)
        #stage_array = bytearray(stages_unlocked)
        for item in item_list:
            netItem =  NetworkItem(*item)
            item_id = netItem.item
            ctx.recieved_items.add(item_id_to_name[item_id])
            new_idx += 1
            if recv_index >= new_idx:
                continue
            if item_id in stage_item_data:
                stage_data = stage_item_data[item_id]
                stage_word = stage_data[0]
                stage_mask = stage_data[1]
                write_word_mask(MEM_EPISODE_UNLOCKS+stage_word, stage_mask)
                #set_wbit(MEM_EPISODE_UNLOCKS+stage_word, stage_bit)
            else:
                match item_id:
                    case 0x1C5250: # Vitality Boost
                        offset = RECV_ADR + 0xC
                        dme.write_word(offset,(dme.read_word(offset)+1))
                    case 0x1C5251: # Derek Healing Touch
                        offset = RECV_ADR + 0x8
                        set_wbit(offset,0)
                    case 0x1C5252: # Naomi Healing Touch
                        offset = RECV_ADR + 0x8
                        set_wbit(offset,1)
                    case 0x1C5253: # Gel Durability
                        offset = AP_TOOL_DURA_SAVE
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C5254: # Syringe Durability
                        offset = AP_TOOL_DURA_SAVE + (1 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C5255: # Sutures Durability
                        offset = AP_TOOL_DURA_SAVE + (2 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C5256: # Drain Durability
                        offset = AP_TOOL_DURA_SAVE + (3 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C5257: # Laser Durability
                        offset = AP_TOOL_DURA_SAVE + (4 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C5258: # Ultrasound Durability
                        offset = AP_TOOL_DURA_SAVE + (5 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C5259: # Scalpel Durability
                        offset = AP_TOOL_DURA_SAVE + (6 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C525A: # Forceps Durability
                        offset = AP_TOOL_DURA_SAVE + (7 * 4)
                        dme.write_word(offset,( dme.read_word(offset)+1))
                    case 0x1C52B: # Stabilizer Shot
                        pass
                    case 0x1C525C: # Angie's Autograph
                        offset = RECV_ADR + 0x10
                        dme.write_word(offset,(dme.read_word(offset)+1))
                    case _:
                        pass
        dme.write_word(RECV_ADR, new_idx)
    except Exception as e:
        logger.critical(f"Error processing items: {e}\n{traceback.format_exc()}")

def check_clear_count(ctx:"TraumaSOClient"):
    try:
        if ctx.clear_count >= ctx.goal_objective:
            match ctx.game_goal:
                case 1: # Savato
                    set_wbit(MEM_EPISODE_UNLOCKS+4, 18)
                    ctx.goal_unlock = True
                case 2: # Savato
                    set_wbit(MEM_EPISODE_UNLOCKS+8, 6)
                    set_wbit(MEM_EPISODE_UNLOCKS+8, 13)
                    ctx.goal_unlock = True
                case 5: # Vulnerability
                    set_wbit(MEM_EPISODE_UNLOCKS+4, 26)
                    ctx.goal_unlock = True
    except Exception as e:
        logger.critical(f"Error processing items: {e}\n{traceback.format_exc()}")

def seed_init(ctx:"TraumaSOClient"):
    dme.write_word(SEED_ADR,ctx.seed_word)
    ctx.seed_passed = True
    if ctx.player_name:
        player_name_bytes = (ctx.player_name).encode("utf-8")
        dme.write_bytes(MEM_PLAYER_NAME,player_name_bytes)

def check_seed(ctx:"TraumaSOClient"):
    try:
        game_seed_mem = dme.read_word(SEED_ADR)
        game_seed_server = ctx.seed_word
        cur_progress = dme.read_word(MEM_EPISODE_UNLOCKS+0x8)
        if not game_seed_server:
            ctx.seed_passed = False
            return False
        # if cur_progress == 0:
        #     return False
        if game_seed_mem == 0:
            #if cur_progress == 0x00010000:
            seed_init(ctx)
            logger.warning(f"Seed initialized")
            return True
        elif game_seed_mem == game_seed_server:
            logger.warning(f"Seed Check Passed")
            ctx.seed_passed = True
            return True
        else:
            logger.warning(f"invalid seed, {hex(game_seed_mem)} found, expected: {hex(game_seed_server)}")
            ctx.seed_passed = False
            return False
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def check_locations(ctx:"TraumaSOClient"):
    try:
        ctx.clear_count = 0
        sending = []
        if ctx.game_state == 0x14:
            # Check rank clears
            difficulty = dme.read_word(MEM_DIFFICULTY)
            
            if difficulty > 0x100:
                difficulty_offset = 0x30
            else:
                match difficulty:
                    case 0x1:
                        difficulty_offset = 0
                    case 0x10:
                        difficulty_offset = 0x10
                    case 0x100:
                        difficulty_offset = 0x20
            score_data = dme.read_bytes(MEM_SCORE_BASE, 0x40 * (CONST_TOTAL_STAGES + 1))
            score_bytes = bytearray(score_data)
            for stage_id in range(CONST_TOTAL_STAGES + 1):
                if stage_id in story_ids:
                    continue
                rank = score_bytes[(stage_id * 0x40) + difficulty_offset + 3]
                chain = score_bytes[(stage_id * 0x40) + difficulty_offset + 0xF]
                
                if rank >= 1:
                    ctx.clear_count += 1
                for rank_check in range(rank):
                    rank_val = rank_check + 1
                    apid = opclear_loc_data[stage_id][rank_val]
                    sending.append(apid)
                chain_apid = 0x1C5600 + stage_id
                
                if ctx.chainsanity and chain_apid in chain_data:
                    
                    chain_needed = chain_data[chain_apid]
                    if chain >= chain_needed:
                        sending.append(chain_apid)
        return sending
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")
        return []

def check_goal(ctx:"TraumaSOClient"):
    try:
        match ctx.game_goal:
            case 0: # custom
                custom_goals_reached = 0
                for custom_loc in ctx.goal_loc:
                    if custom_loc in ctx.local_checked_locations:
                        custom_goals_reached += 1
                if custom_goals_reached >= len(ctx.goal_loc):
                    return True
            case 1: # Savato
                clear_apid = location_data_table["5-9 Death Awaits All C Rank"].address
                if clear_apid in ctx.local_checked_locations:
                    return True
            case 2: # Savato X
                clear_apid_1 = location_data_table["8-7 Savato C Rank"].address
                clear_apid_2 = location_data_table["8-7 Savato Naomi C Rank"].address
                if clear_apid_1 in ctx.local_checked_locations or clear_apid_2 in ctx.local_checked_locations:
                    return True
            case 3:
                #clear_count = get_clear_count(ctx)
                if ctx.clear_count >= ctx.goal_objective:
                    return True
            case 4:
                offset = RECV_ADR + 0x10
                autographs_have = dme.read_word(offset)
                if autographs_have >= ctx.goal_objective:
                    return True
            case 5: # Vulnerability
                clear_apid = location_data_table["6-8 Vulnerability C Rank"].address
                if clear_apid in ctx.local_checked_locations:
                    return True
        return False
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")
        return False