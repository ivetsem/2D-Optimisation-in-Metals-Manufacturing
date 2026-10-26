from rectpack import newPacker, MaxRectsBssf

# Each tuple is: (part_id, width, height)
# Give each physical part a unique ID.
parts = [
    ("A1", 1200, 600),
    ("A2", 1200, 600),
    ("B1", 800, 500),
    ("B2", 800, 500),
    ("C1", 600, 400),
    ("C2", 600, 400),
    ("D1", 400, 300),
    ("D2", 400, 300),
]

sheet_width = 2500
sheet_height = 1250
available_sheets = 2

# Allow 90-degree rotation.
packer = newPacker(
    pack_algo=MaxRectsBssf,
    rotation=True,
)

for part_id, width, height in parts:
    packer.add_rect(width, height, rid=part_id)

packer.add_bin(
    sheet_width,
    sheet_height,
    count=available_sheets,
)

packer.pack()

# Each result is:
# (bin_index, x, y, placed_width, placed_height, part_id)
placements = packer.rect_list()

print("Part placements:")
for bin_index, x, y, width, height, part_id in placements:
    print(
        f"{part_id}: sheet={bin_index + 1}, "
        f"position=({x}, {y}), size={width} x {height}"
    )

# Detect any parts that were not packed.
packed_ids = {row[5] for row in placements}
unpacked_ids = {
    part_id for part_id, _, _ in parts
} - packed_ids

print(f"\nPacked: {len(placements)} / {len(parts)} parts")
print(f"Unpacked: {sorted(unpacked_ids)}")

# bin_list() contains only sheets actually used.
used_sheets = packer.bin_list()

part_area = sum(
    width * height
    for _, _, _, width, height, _ in placements
)
used_sheet_area = sum(
    width * height
    for width, height in used_sheets
)

utilisation = part_area / used_sheet_area if used_sheet_area else 0

print(f"Sheets used: {len(used_sheets)} / {available_sheets}")
print(f"Material utilisation: {utilisation:.1%}")
print(f"Unused area: {used_sheet_area - part_area:,} mm²")