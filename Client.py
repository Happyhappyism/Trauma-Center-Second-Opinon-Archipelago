
from typing import TYPE_CHECKING, Set, Optional, Dict, Any
# Big thank you to the Lobotomy Corperation Developer K3 for reference on how to setup the client

import dolphin_memory_engine as dme
import logging
import asyncio
import Utils
import time
import traceback

from .game_data import valid_game_states
from .traumaso_lib import *

if __name__ == "__main__":
    Utils.init_logging("TraumaSOClient", exception_logger="Client")

from NetUtils import ClientStatus
from CommonClient import gui_enabled, logger, get_base_parser, ClientCommandProcessor, \
    CommonContext, server_loop



#loggerExternal = logging.getLogger("Monkey Ball 2 Client")
logger = logging.getLogger("TCSO Debug")

#stage_id_table = {data.id: data.address for name, data in stage_data.items()}

class TraumaSOCommandProcessor(ClientCommandProcessor):
    def _cmd_deathlink(self):
        """Use this command to turn Death Link on and off."""
        if self.ctx.death_link:
            self.ctx.death_link = False
            self.output(f"Death Link turned off")
        else:
            self.ctx.death_link = True
            self.output(f"Death Link turned on")
    def _cmd_dolphin_status(self):
        """Returns the current connection state of dolphin"""
        self.output(f"{self.ctx.dolphin_status_text}")
    def _cmd_resync(self):
        """resyncs the game state"""
        dme.write_word(AP_FIRST_RUN, 0x0)
        
    def _cmd_debug(self, *command:str):
        """Returns the value of a specified variable
        game_state, recv_item_storage, recieved_items, timers, send_index, last_death_link, locations_checked"""
        if command:
            match command[0].lower():
                case "game_state":
                    self.output(f"{hex(self.ctx.game_state)}")
                case "recv_item_storage":
                    self.output(f"{self.ctx.recv_item_storage}")
                case "recieved_items":
                    self.output(f"{self.ctx.recieved_items}")
                case "recv_index":
                    self.output(f"{dme.read_word(RECV_ADR)}")
                case "last_death_link":
                    self.output(f"{self.ctx.last_death_link}")
                case "locations_checked":
                    self.output(f"{self.ctx.locations_checked}")
                case "checked_locations":
                    self.output(f"{self.ctx.checked_locations}")
                case _:
                    if command[0].lower() in globals():
                        value = globals()[command[0].lower()]
                        self.output(f"{command[0].lower()} = {value}")
                    else:
                        self.output(f"invalid variable name: {command}")


class TraumaSOClient(CommonContext):
    command_processor: int = TraumaSOCommandProcessor
    game = "Trauma Center Second Opinion"
    local_checked_locations: Set[int]

    items_handling = 0b111 # Full remote

    death_link: bool = False
    game_goal = 0
    goal_objective = 100
    pending_death_link: bool = False
    pack_count: int = 0
    travel_count: int = 0
    recv_item_storage = {}
    recieved_items: Set[str]
    recieved_ids: Set[int]
    dolphin_status_text = "Uninitialized"

    seed_word = None
    seed_passed = False

    max_rank = 1
    starting_vital_cap = 99
    starting_tool_durability = 20
    vitality_boost = 5
    durability_boost = 5
    randomize_operation_music = False
    healing_touch = False
    dura_count = 0
    vital_count = 0
    included_random_music = []
    game_state:int = 0
    operation_stat_ptr: int = 0
    death_state_triggered = False
    goal_loc: str = None
    goal_unlock = False
    chainsanity: bool = False
    player_name: str = None

    tool_sel: int = 0
    clear_count:int = 0

    dl_triggered = False
    gm_current_stage = 0

    def __init__(self, server_address, password) -> None:
        super(TraumaSOClient, self).__init__(server_address, password)
        self.send_index: int = 0
        self.local_checked_locations = set()
        self.recieved_items = set()
        self.syncing = False
        self.slot_data = ""
        

    async def server_auth(self, password_requested: bool= False):
        if password_requested and not self.password:
            await super(TraumaSOClient, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    async def connection_closed(self):
        self.seed_word = None
        self.seed_passed = False
        await super(TraumaSOClient, self).connection_closed()

    @property
    def endpoints(self):
        if self.server:
            return [self.server]
        else:
            return []
        
    async def shutdown(self):
        await super(TraumaSOClient, self).shutdown()

    def on_package(self, cmd: str, args: dict) -> None:
        try:
            if cmd in {"RoomInfo"}:
                self.seed_name = args['seed_name']
                self.seed_word = (int(self.seed_name, 32) & 0xFFFFFFFF)
            if cmd in {"Connected"}:
                player_data = args['players']
                self.slot_id = args['slot']
                
                logger.info(f"Slot Data: {args['slot_data']}")
                if(args['slot_data']['DeathLink']):
                    self.death_link = True
                if(args['slot_data']['game_goal']):
                    self.game_goal = args['slot_data']['game_goal']
                if(args['slot_data']['goal_objective']):
                    self.goal_objective = args['slot_data']['goal_objective']
                if(args['slot_data']['starting_vital_cap']):
                    logger.warning(f"starting_vital_cap reached")
                    self.starting_vital_cap = args['slot_data']['starting_vital_cap']
                if(args['slot_data']['starting_tool_durability']):
                    self.starting_tool_durability = args['slot_data']['starting_tool_durability']
                if(args['slot_data']['vitality_boost']):
                    logger.warning(f"vitality_boost reached")
                    self.vitality_boost = args['slot_data']['vitality_boost']
                if(args['slot_data']['durability_boost']):
                    self.durability_boost = args['slot_data']['vitality_boost']
                if(args['slot_data']['max_rank']):
                    self.max_rank = True
                if(args['slot_data']['randomize_operation_music']):
                    self.randomize_operation_music = True
                if(args['slot_data']['included_random_music']):
                    self.included_random_music = args['slot_data']['included_random_music']
                if(args['slot_data']['custom_goal_location']):
                    self.goal_loc = args['slot_data']['custom_goal_location']
                if(args['slot_data']['chainsanity']):
                    self.chainsanity = args['slot_data']['chainsanity']
                if(args['slot_data']['player_name']):
                    self.player_name = args['slot_data']['player_name']
                #logger.warning(f"name: {args['slot_info']}")
                #self.player_name = args['slot_info']['name']
                    #self.update_death_link(self.death_link)
                #if dme.read_byte(RECV_ADR) == 0x00:
                #    dme.write_bytes(0x805d4d38, bytes([0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]))
            if cmd in {"PrintJSON"}:
                pass
            if cmd in {"ReceivedItems"}:
                try:
                    start_index = args["index"]
                    item_list = args['items']
                    process_items(self, item_list, start_index)
                except Exception as e:
                    self.recv_item_storage[start_index] = item_list
                    logger.critical(f"Error reciving items: {e}\n{traceback.format_exc()}")


        except:
            print("Couldn't open input. Retrying in 1s.")

    

    def run_gui(self):
        from kvui import GameManager
        class LOLManager(GameManager):
            logging_pairs = [
                ("Client", "Archipelago"),
                ("TCSO Debug", "TCSO Debug")
            ]
            base_title = "Archipelago Trauma Center Second Opinion Client"
        self.ui = LOLManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")

    def on_deathlink(self, data):
        # kill player
        try:
            if (self.last_death_link + 6 < time.time()) and (self.operation_stat_ptr):
                vital_ptr = get_vitals_adr(self.operation_stat_ptr)
                if vital_ptr:
                    dme.write_float(vital_ptr+4, 0)
                self.last_death_link = time.time()
                self.death_state_triggered = True
        except Exception as e:
            logger.critical(f"Error: {e}\n{traceback.format_exc()}")
        #set_bit(0x80553973, 2)


def game_loop(ctx:TraumaSOClient):
    try:
        
        if ctx.operation_stat_ptr != 0x0:
            operation_state(ctx)
        elif ctx.game_state == 0x14:
            menu_select_state(ctx)
        check_deathlink(ctx)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def menu_select_state(ctx:TraumaSOClient):
    try:
        dme.write_float(MEM_EPISEL_SCROLLCAP, 6000)
        dme.write_float(MEM_EPISEL_SCROLLCAP-4, 533)
    except Exception as e:
        logger.critical(f"Error: {e}\n{traceback.format_exc()}")

def operation_state(ctx:TraumaSOClient):
    try:
        vital_ptr = get_vitals_adr(ctx.operation_stat_ptr)
        if vital_ptr == 0:
            return
        
        #if ctx.death_link:
            # Check if player is dead
            
        set_operation_items(ctx, vital_ptr)
    except Exception as e:
        logger.critical(f"Error processing items: {e}\n{traceback.format_exc()}")
    
async def game_watcher(ctx: TraumaSOClient):
    while not ctx.exit_event.is_set():
        try:
            if ctx.death_link and "DeathLink" not in ctx.tags:
                await ctx.update_death_link(ctx.death_link)
            if not ctx.death_link and "DeathLink" in ctx.tags:
                await ctx.update_death_link(ctx.death_link)

            if ctx.syncing == True:
                
                sync_msg = [{'cmd': 'Sync'}]
                if ctx.locations_checked:
                    sync_msg.append({"cmd": "LocationChecks", "locations": list(ctx.locations_checked)})
                await ctx.send_msgs(sync_msg)
                ctx.syncing = False

            try:
                #logger.warning(f"status: {ctx.dolphin_status_text}")
                # Connection varfication code taken from Pikmin 1 apworld
                if not dme.is_hooked():
                    dme.hook()  # silently fails?
                if not dme.is_hooked():
                    ctx.dolphin_status_text = "Disconnected - Hook Failed"
                    await asyncio.sleep(1)
                    continue
                else:
                    game = dme.read_bytes(MEM_GAME_ID, 6)
                    if game not in [b"RKDEEB"]:
                        ctx.dolphin_status_text = "Connected - Wrong Game"
                        await asyncio.sleep(1)
                        continue

                    game_version = game
                    ctx.dolphin_status_text = f"Connected - {game.decode()}"
                    game_player_name_bytes = dme.read_bytes(MEM_PLAYER_NAME, 0x20)
                    game_player_name = bytes([byte for byte in game_player_name_bytes if byte != 0]).decode("utf-8")
                    if game_player_name:
                        ctx.auth = game_player_name


            except Exception as e:
                logger.error(e)
                logger.info("Trying to reconnect to Dolphin...")
                ctx.dolphin_status_text = "??? - Exception Occured"
                dme.un_hook()
                continue

            verify_patches(ctx)

            if not ctx.seed_passed or not ctx.seed_word:
                check_seed(ctx)
                await asyncio.sleep(1)
                continue

            ctx.game_state = dme.read_word(MEM_GAME_STATE)
            ctx.operation_stat_ptr = dme.read_word(PTR_OPERATION_STATS)
            if (ctx.game_state not in valid_game_states) and (ctx.operation_stat_ptr == 0):
                await asyncio.sleep(1)
                continue

            if dme.read_word(AP_FIRST_RUN) == 0:
                sync_state(ctx)

            
            game_loop(ctx)

            # Trigger Death Link
            if ctx.death_link and ctx.dl_triggered:
                await ctx.send_death(f"{ctx.player_names[ctx.slot]} killed a patient.")
                ctx.dl_triggered = False
            # Process stored items
            if ctx.recv_item_storage:
                for start_index, item_list in ctx.recv_item_storage.items():
                    process_items(ctx,item_list,start_index)
                ctx.recv_item_storage.clear()

            # Handle outbound locations
            locs_to_send = check_locations(ctx)
            if locs_to_send != ctx.local_checked_locations and locs_to_send:
                ctx.local_checked_locations = locs_to_send
                await ctx.send_msgs([{"cmd": "LocationChecks", "locations": list(locs_to_send)}])

            if (ctx.game_goal == 1 or ctx.game_goal == 2 or ctx.game_goal == 5) and (ctx.goal_unlock == False): # For Savato Goals give the op when clear condition met
                check_clear_count(ctx)

            # Handle game clear
            if not ctx.finished_game and check_goal(ctx):
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True
            await asyncio.sleep(1)
        except Exception as e:
            logger.critical(f"Error in server loop: {e}\n{traceback.format_exc()}")


def launch():
    init_vars()
    async def main(args):
        try:
            ctx = TraumaSOClient(args.connect, args.password)
            ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
            if gui_enabled:
                ctx.run_gui()
            ctx.run_cli()

            progression_watcher = asyncio.create_task(
                game_watcher(ctx), name="TraumaSOProgressionWatcher")
            
            await ctx.exit_event.wait()
            ctx.server_address = None

            await progression_watcher

            await ctx.shutdown()
        except Exception as e:
            logger.critical(f"Error launching client: {e}\n{traceback.format_exc()}")

    import colorama
    parser = get_base_parser(description="Trauma Center Second Opinion Client text interface")

    args, rest = parser.parse_known_args()
    colorama.init()
    asyncio.run(main(args))
    colorama.deinit()