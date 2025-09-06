import asyncio
import time
import json
import win32api
import win32con
import win32gui
from pymem import Pymem

# -------------------------
# Load Config
# -------------------------
with open("config.json", "r") as f:
    config = json.load(f)

# -------------------------
# Base + Offsets
# -------------------------
base_offset = 0x041C1210

offsets = {
    "CurHP": [0x00, 0x08, 0x48, 0x08, 0x98, 0x50, 0x360],
    "MaxHP": [0x00, 0x08, 0x48, 0x08, 0x98, 0x50, 0x364],
    "CurMP": [0x00, 0x08, 0x48, 0x08, 0xB8, 0x50, 0x360],
    "MaxMP": [0x00, 0x08, 0x48, 0x08, 0xB8, 0x50, 0x364],
    "CurES": [0x00, 0x08, 0x48, 0x08, 0x98, 0x50, 0x36C],
    "MaxES": [0x00, 0x08, 0x48, 0x08, 0x98, 0x50, 0x370],
}

# -------------------------
# Memory Helpers
# -------------------------
def get_final_address(pm: Pymem, base_address: int, offsets: list[int]) -> int:
    addr = pm.read_longlong(base_address)
    for offset in offsets[:-1]:
        addr = pm.read_longlong(addr + offset)
    return addr + offsets[-1]

# -------------------------
# Async Wait for memory
# -------------------------
async def wait_for_memory(pm, base_address, offsets, retry_delay=1.0):
    last_msg_time = 0
    while True:
        try:
            cur_hp_addr = get_final_address(pm, base_address, offsets["CurHP"])
            max_hp_addr = get_final_address(pm, base_address, offsets["MaxHP"])
            cur_mp_addr = get_final_address(pm, base_address, offsets["CurMP"])
            max_mp_addr = get_final_address(pm, base_address, offsets["MaxMP"])
            cur_es_addr = get_final_address(pm, base_address, offsets["CurES"])
            max_es_addr = get_final_address(pm, base_address, offsets["MaxES"])

            # Test reading
            cur_hp = pm.read_int(cur_hp_addr)
            max_hp = pm.read_int(max_hp_addr)
            cur_mp = pm.read_int(cur_mp_addr)
            max_mp = pm.read_int(max_mp_addr)
            cur_es = pm.read_int(cur_es_addr)
            max_es = pm.read_int(max_es_addr)

            print("PoEHelper: Offsets found and memory is ready!")
            print(f"HP: 0x{cur_hp_addr:08X} > {cur_hp}/{max_hp}")
            print(f"MP: 0x{cur_mp_addr:08X} > {cur_mp}/{max_mp}")
            print(f"ES: 0x{cur_es_addr:08X} > {cur_es}/{max_es}")
            return

        except Exception:
            now = time.time()
            if now - last_msg_time >= 10:
                print("PoEHelper: Searching for memory offsets...")
                last_msg_time = now
            await asyncio.sleep(retry_delay)

# -------------------------
# Extra Condition for HP
# -------------------------
def hp_extra_condition(pm):
    try:
        cures_address = get_final_address(pm, base_address, offsets["CurES"])
        return pm.read_int(cures_address) == 0
    except:
        return True

# -------------------------
# Extra Condition for ES
# -------------------------
def es_extra_condition(pm):
    try:
        maxes_address = get_final_address(pm, base_address, offsets["MaxES"])
        max_es = pm.read_int(maxes_address)
        return max_es > 0  # Only use ES if character has ES
    except:
        return False

# -------------------------
# Generic Routine with auto-resume and reporting
# -------------------------
async def stat_routine(pm, handle, name, offsets, extra_condition=None):
    if not config[name]["enabled"]:
        return
    key = config[name]["key"]
    threshold = config[name]["threshold"]
    cooldown = float(config[name]["cooldown"])
    post_use_delay = float(config[name].get("post_use_delay", 0.0))
    last_used = 0
    search_last_msg = 0
    memory_was_invalid = False
    memory_ever_valid = False

    while True:
        try:
            cur_address = get_final_address(pm, base_address, offsets[f"Cur{name}"])
            max_address = get_final_address(pm, base_address, offsets[f"Max{name}"])
            current_val = pm.read_int(cur_address)
            max_val = pm.read_int(max_address)

            if memory_was_invalid and memory_ever_valid:
                print(f"PoEHelper: {name} memory restored!")
                print(f"{name}: 0x{cur_address:08X} > {current_val}/{max_val}")
                memory_was_invalid = False

            memory_ever_valid = True

            # Check thresholds and extra condition
            percent = (current_val / max_val) * 100 if max_val != 0 else 0
            now = time.time()
            if percent <= threshold and (extra_condition is None or extra_condition(pm)) and (now - last_used) >= cooldown:
                win32api.PostMessage(handle, win32con.WM_KEYDOWN, ord(key.upper()), 0)
                win32api.PostMessage(handle, win32con.WM_KEYUP, ord(key.upper()), 0)
                last_used = now
                print(f"[{time.strftime('%H:%M:%S')}]: Used {name} key {key} (CD {cooldown}s)")

                if post_use_delay > 0:
                    await asyncio.sleep(post_use_delay)

            await asyncio.sleep(0.2)

        except Exception:
            if memory_ever_valid:
                memory_was_invalid = True
            now = time.time()
            if now - search_last_msg >= 10:
                print(f"PoEHelper: Searching for {name} memory offsets...")
                search_last_msg = now
            await asyncio.sleep(1)

# -------------------------
# Main
# -------------------------
async def main():
    possible_processes = [
        "PathOfExile.exe",
        "PathOfExile_KG.exe",
        "PathOfExileSteam.exe",
        "PathOfExile_x64.exe",
        "PathOfExileEGS.exe"
    ]
    window_name = "Path of Exile 2"

    # Wait for window
    handle = None
    while handle == 0 or handle is None:
        handle = win32gui.FindWindow(None, window_name)
        if handle == 0:
            print("Waiting for game window...")
            await asyncio.sleep(1)

    # Wait for process
    pm = None
    while pm is None:
        for proc_name in possible_processes:
            try:
                pm = Pymem(proc_name)
                process_name = proc_name
                break
            except Exception:
                pm = None
        if pm is None:
            print("Waiting for game process...")
            await asyncio.sleep(1)

    global base_address
    base_address = pm.base_address + base_offset
    print(f"Attached to {process_name} | Window: {window_name}")

    # Wait until memory is ready
    await wait_for_memory(pm, base_address, offsets)

    # Start routines
    async with asyncio.TaskGroup() as tg:
        print("PoEHelper is ON")
        tg.create_task(stat_routine(pm, handle, "HP", offsets, extra_condition=hp_extra_condition))
        tg.create_task(stat_routine(pm, handle, "MP", offsets))
        tg.create_task(stat_routine(pm, handle, "ES", offsets, extra_condition=es_extra_condition))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("PoEHelper stopped.")
