# These 3 lines are here since we are using files in the same repo, not from a package.
import sys
import pxbuild

my = sys.path[0].replace("\\demo", "\\")
sys.path.insert(1, my)

print("paths", sys.path[0], sys.path[1])

model = pxbuild.build_px_file("03024", "example_data/pxbuildconfig/ssb_config.json")
print("Written files:", model.statistics.output_files)
print("Title:", model.title)
print("Row count:", model.statistics.row_count)
print("Valid:", model.is_valid)
