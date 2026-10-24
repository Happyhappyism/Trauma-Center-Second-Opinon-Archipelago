unlock_data = [
    0x05,
    0x0d,

    0x1D,
    0x3d,
    0x7d,
    0xfd,

    0x1fd,
    0x3FD,
    0x7FD,
    0xFFD,

    0x1FFD,
    0x3FFD,
    0x7FFD,
    0xFFFD,

    0x1FFFD,
    0x3FFFD,
    0x7FFFD,
    0xFFFFD,

    0x1FFFFD,
    0x3FFFFD,
    0x7FFFFD,
]
clear_data = [
    0x1,
    0x5,
    0xD,
    0x1D,
    0x3D,
    0x7D,
    0xFD,
    0x1FD,
    0x3FD,
    0x7FD,
    0xFFD,
    0x3FFD,
    0x7FFD,
    0xFFFD
]
episode_list = ["1-1","1-2","1-3","1-4","1-5","1-6","1-7","1-8","2-1","2-2","2-3","2-4","2-5","2-6","2-7","2-8","2-9","2-10","2-11","3-1","3-2"]
episode_counts = [8,11,10,11,9,8, 5,7,7]
value =0
episode = 0
old_val = 1
for value in unlock_data:
    mask = hex(value - old_val)
    episode_id = episode_list[episode]
    print(f"{episode_id} UNLOCK - r0 = {mask} r5 = 0")
    old_val = value
    episode += 1
    
unlock_mask = 0x2
unlock_word_offset = 0
clear_mask = 0x20000
clear_word_offset = 8
chapter = 1
for episode_count in episode_counts:
    match chapter:
        case 7:
            chap_str = "Z"
        case 8:
            chap_str = "X"
        case 9:
            chap_str = "XN"
        case _:
            chap_str = str(chapter)
    for episode in range(1, episode_count+1):
        unlock_mask <<= 1
        if unlock_mask > 0x80000000:
            unlock_mask = 1
            unlock_word_offset += 4
        clear_mask <<= 1
        if clear_mask > 0x80000000:
            clear_mask = 1
            clear_word_offset += 4
        print(f"{chap_str}-{episode}\t{hex(unlock_word_offset)}\t{hex(unlock_mask)}\t{hex(clear_word_offset)}\t{hex(clear_mask)}")
    chapter +=1