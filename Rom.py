import hashlib
import math
import os
import struct
import random

from settings import get_settings
import Utils
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from worlds.AutoWorld import World
import logging
logger = logging.getLogger("Trauma Center Second Opinion")

MD5Hash = [
    "217ebd710577b541cb15adaab3fa79ba", # ISO
]

ROM_DATA_FREESPACE = 0x2300
ROM_NAME_ADR = ROM_DATA_FREESPACE + 0x10
PLAYER_NAME_ADR = ROM_DATA_FREESPACE + 0x30
OPTION_ADR = ROM_DATA_FREESPACE

class TraumaSOProcedurePatch(APProcedurePatch, APTokenMixin):
    game = "Trauma Center Second Opinion"
    hash = MD5Hash
    patch_file_ending = ".aptraumaso"
    result_file_ending = ".iso"

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_bytes()
    
def write_tokens(world:World, patch:TraumaSOProcedurePatch):
    for j, b in enumerate(world.romName):
        patch.write_token(APTokenTypes.WRITE, ROM_NAME_ADR + j, struct.pack("<B", b))
    for j, b in enumerate(world.playerName):
        patch.write_token(APTokenTypes.WRITE, PLAYER_NAME_ADR + j, struct.pack("<B", b))
    patch.write_token(APTokenTypes.WRITE, OPTION_ADR + 0x0, bytes([world.options.game_goal.value]))
    patch.write_token(APTokenTypes.WRITE, OPTION_ADR + 0x1, bytes([world.options.death_link.value]))
    
    if world.options.death_link:
        patch.write_token(APTokenTypes.WRITE, OPTION_ADR + 0x2, bytes([0x01]))
 

    patch.write_file("token_data.bin", patch.get_token_binary())

def get_base_rom_bytes(file_name: str ="") -> bytes:
    base_rom_bytes = getattr(get_base_rom_bytes, "base_rom_bytes", None)
    if not base_rom_bytes:
        file_name = get_base_rom_path(file_name)
        base_rom_bytes = bytes(Utils.read_snes_rom(open(file_name, "rb")))

        basemd5 = hashlib.md5()
        basemd5.update(base_rom_bytes)
        md5hash = basemd5.hexdigest()
        if md5hash not in MD5Hash:
            raise Exception("Supplied Rom does not match known MD5 for Trauma Center Second Opinion")
        get_base_rom_bytes.base_rom_bytes = base_rom_bytes
    return base_rom_bytes

def get_base_rom_path(file_name: str="")-> str:
    if not file_name:
        file_name = get_settings().trauma_so_settings.rom_file
    if not os.path.exists(file_name):
        file_name= Utils.user_path(file_name)
    return file_name