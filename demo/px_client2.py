# These 3 lines are here since we are using files in the same repo, not from a package.
import sys
import pxbuild

my = sys.path[0].replace("\\demo", "\\")
sys.path.insert(1, my)

print("paths", sys.path[0], sys.path[1])

model, written_files = pxbuild.build_px_file("2", "testdata/test_cube_2/test_config.json")
print("Written files:", written_files)
# model, written_files = pxbuild.build_px_file('12576', 'example_data/pxbuildconfig/ssb_config.json')
# model, written_files = pxbuild.build_px_file('07459', 'example_data/pxbuildconfig/ssb_config.json')
# model, written_files = pxbuild.build_px_file('03024', 'example_data/pxbuildconfig/ssb_config.json')
# model, written_files = pxbuild.build_px_file('03024', API)
