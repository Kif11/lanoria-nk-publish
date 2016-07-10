from nk_publish import NukePublish
from dependency import NukeDependencies

nuke.scriptOpen("/Users/kif/BoxSync/LaNoria/Shots/lacaja_test/test_seq/test_shot_6/working/comp/nuke/test_shot_6_comp_v057.nk")

np = NukePublish()

np.publish()
