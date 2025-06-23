import re
import shutil

input_file = "index.html"
backup_file = "index.html.bak"
output_file = "index.html"

# Read the original file
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# Backup the original file
shutil.copyfile(input_file, backup_file)

# Tags to consider as blocks
block_tags = ["article", "section", "div", "main", "aside", "nav", "header", "footer"]

# Build a regex pattern for each tag
block_patterns = [
    re.compile(
        rf"<{tag}\b[^>]*>.*?</{tag}>",
        re.DOTALL | re.IGNORECASE
    )
    for tag in block_tags
]

def should_remove(block):
    block_lower = block.lower()
    return "article_1" in block_lower or "monitors_map" in block_lower

# Remove matching blocks for each tag
removed_count = 0
for pattern in block_patterns:
    while True:
        match = pattern.search(content)
        if not match:
            break
        block = match.group(0)
        if should_remove(block):
            removed_count += 1
            print(f"Removing block #{removed_count} ({pattern.pattern})")
            content = content[:match.start()] + content[match.end():]
        else:
            # If the first match doesn't contain the keyword, skip it and search for the next
            # This is handled by the while loop
            break

# Write the cleaned file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Cleanup complete! Removed {removed_count} HTML blocks.")
print("Backup saved as index.html.bak")

# Verify cleanup
article_1_count = content.lower().count("article_1")
monitors_map_count = content.lower().count("monitors_map")
print(f"Remaining references - article_1: {article_1_count}, monitors_map: {monitors_map_count}")