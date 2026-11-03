import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from creative_controls import ray_hit,intersects_hero

class CreativeChecks(unittest.TestCase):
    def test_downward_ground_and_surface_normal(self):
        hit=ray_hit((.5,1.2,.5),(0,-1,0),(0,0,0),{(0,-1,0):9})
        self.assertEqual(hit,((0,-1,0),(0,1,0),1.2))
    def test_negative_and_translated_world(self):
        hit=ray_hit((10.5,42,20.5),(-1,0,0),(10,40,20),{(-2,2,0):1})
        self.assertEqual(hit[0],(-2,2,0));self.assertEqual(hit[1],(1,0,0))
    def test_front_cube_occludes_farther_cube(self):
        hit=ray_hit((.5,1.2,.5),(0,0,1),(0,0,0),{(0,1,2):1,(0,1,4):1})
        self.assertEqual(hit[0],(0,1,2))
    def test_reach_and_removed_block(self):
        self.assertIsNone(ray_hit((.5,1,.5),(0,0,1),(0,0,0),{(0,1,9):1}))
        self.assertIsNone(ray_hit((.5,1,.5),(0,0,1),(0,0,0),{}))
    def test_player_placement_and_invalid_aim(self):
        self.assertTrue(intersects_hero((0,0,0),(.5,0,.5),(0,0,0)))
        self.assertFalse(intersects_hero((0,2,0),(.5,0,.5),(0,0,0)))
        with self.assertRaises(ValueError):ray_hit((0,0,0),(float('nan'),0,1),(0,0,0),{})

if __name__=='__main__':unittest.main()
