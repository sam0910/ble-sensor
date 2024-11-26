import os
import gc


def get_flash_info():
    try:
        # Get filesystem stats
        stats = os.statvfs("/")

        # Calculate storage info in KB
        block_size = stats[0]  # Block size
        total_blocks = stats[2]  # Total blocks
        free_blocks = stats[3]  # Free blocks 3

        total_space = (block_size * total_blocks) / 1024  # Convert to KB
        free_space = (block_size * free_blocks) / 1024  # Convert to KB
        used_space = total_space - free_space

        # Get RAM info
        gc.collect()
        ram_free = gc.mem_free() / 1024  # Convert to KB
        ram_alloc = gc.mem_alloc() / 1024  # Convert to KB

        print("Flash Storage:")
        print(f"Total: {total_space:.2f}KB")
        print(f"Used: {used_space:.2f}KB")
        print(f"Free: {free_space:.2f}KB")
        print("\nRAM Memory:")
        print(f"Free: {ram_free:.2f}KB")
        print(f"Allocated: {ram_alloc:.2f}KB")

    except Exception as e:
        print("Error getting storage info:", e)


# a = os.statvfs("/")
# total = int(a[0] * a[2] / 1024)
# free = int(a[0] * a[3] / 1024)
# used = total - free
# print(f"Total({total}k)-Used({used}k")

# # Run storage check on boot
get_flash_info()
