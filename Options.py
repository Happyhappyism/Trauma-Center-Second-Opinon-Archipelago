from dataclasses import dataclass
from Options import Choice, Range, OptionGroup, Toggle,FreeText, DefaultOnToggle, Removed, PerGameCommonOptions, OptionSet, StartInventoryPool, DeathLink

class Goal(Choice):
    """Game's Goal"""
    display_name = "Goal"
    option_savato = 1
    option_savatoX = 2
    option_custom = 0
    option_clear_count = 3
    option_angie_hunt = 4
    default = 1

class StartingOperations(Range):
    """Number of operations you start the run with"""
    range_start = 1
    range_end = 5
    default = 2

class NeededClears(Range):
    """
    Number of stage clears needed reach the goal or goal operation
    For Angie Hunt this instead is the number of Angies Autograph items are required to goal
    For Custom Goal this does nothing
    """
    range_start = 1
    range_end = 52
    default = 25

class StartDurability(Range):
    """Starting tool durability, to disable set to 100"""
    range_start = 20
    range_end = 100
    default = 20

class DurabilityBoost(Range):
    """Amount of tool durabilily each durability boost items grant"""
    range_start = 5
    range_end = 25
    default = 20

class StartVitalCap(Range):
    """Starting vitals cap, to disable set to 99"""
    range_start = 5
    range_end = 99
    default = 99

class VitalBoost(Range):
    """Amount of vital cap increase each Vitality item grant"""
    range_start = 5
    range_end = 25
    default = 20

class StartTimeCap(Range):
    """Starting Time limit cap in seconds, to disable set to 99"""
    range_start = 20
    range_end = 99
    default = 99


class MaxRank(Choice):
    """Each rank will include an extra location. 
    S and XS not recommended unless you are very good at the game.
    Choosing C rank will make it so each operation gives 2 checks regardless of your rank"""
    option_C = 1
    option_B = 2
    option_A = 3
    option_S = 4
    option_XS = 5
    default = 3

class includeStoryEpisodes(Toggle):
    """If enabled will include the non operation story episodes, basically free locations"""

class MaxChapter(Range):
    """Will determine which chapters will be included as locations
    If Savato goal is set then this must be at least 5
    7 will include Naomi chapters
    8 will include X operations, Required for Savato X goal"""
    range_start = 4
    range_end = 8
    default = 6
    
class Chainsanity(Toggle):
    """If enabled will include a location for a certain max chain in each operation"""
class LocationLogicCheck(FreeText):
    """Custom Goal Only
    Enter a check below and reaching that check becomes your goal for the seed. 
    """
class RandomMusic(Toggle):
    """Will randomize all the music track that will play during operations"""

class IncludedTracks(OptionSet):
    """Music Tracks that will be included in the music randomization"""
    valid_keys = {
        "Ending",
        "Game Over",
        "Main Map 1",
        "Main Map 2",
        "Truth",
        "Joy",
        "Sadness",
        "Caduceus",
        "Medical Terrorism",
        "Surgery Karte",
        "Normal Operation",
        "Dangerous Operation",
        "GUILT Operation",
        "Last GUILT",
        "Operation Start",
        "Operation Success",
        "Final Operation",
        "Exchange Surgeon",
        "Second Opinion",
        "Main Menu",
        "Unused Track"
    }
    default = {
        "Main Map 1", "Main Map 2", "Truth", "Joy","Sadness", "Caduceus", "Medical Terrorism",
        "Surgery Karte", "Normal Operation", "Dangerous Operation", "GUILT Operation", "Last GUILT",
        "Final Operation", "Exchange Surgeon", "Second Opinion", "Main Menu", "Unused Track"
    }

class LocationLogicCheck(FreeText):
    """Custom Goal Only
    Enter a check below and reaching that check becomes your goal for the seed. 
    You can use randomization to have a random check become your goal. Eg. 
        '7-5 Sayonara C Rank': 50
        '4-10 Prolonged Struggle B': 50
        '6-8 Vulnerability A Rank': 50"""

trauma_so_options_group = [
    OptionGroup("Goal Options", [
        Goal,
        StartingOperations,
        NeededClears,
        MaxChapter,
        LocationLogicCheck,
    ]),
    OptionGroup("Gameplay Options", [
        Chainsanity,
        StartDurability,
        DurabilityBoost,
        StartVitalCap,
        VitalBoost,
        MaxRank,
        #includeStoryEpisodes,
        DeathLink,
    ]),
    OptionGroup("Randomization Options", [
        RandomMusic,
        IncludedTracks
    ])
]

@dataclass
class TraumaSOOptions(PerGameCommonOptions):
    game_goal: Goal
    death_link: DeathLink
    goal_objective: NeededClears
    starting_operations: StartingOperations
    starting_vital_cap: StartVitalCap
    vitality_boost: VitalBoost
    starting_tool_durability: StartDurability
    durability_boost: DurabilityBoost
    max_rank: MaxRank
    chainsanity: Chainsanity
    #include_story_episodes: includeStoryEpisodes
    max_chapter: MaxChapter
    custom_goal_location: LocationLogicCheck
    randomize_operation_music: RandomMusic
    included_random_music: IncludedTracks
