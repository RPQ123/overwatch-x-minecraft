"""Regression for bright rectangular sprites under actual ONE/ONE blending."""
import unittest
import numpy as np
from PIL import Image
from pack_pharah_rocket import additive_rgba

class AdditiveMaterialTests(unittest.TestCase):
    def test_zero_light_edges_even_when_blend_ignores_alpha(self):
        # Original opaque-black sprite edge and transparent-white export edge
        # must both contribute zero RGB under ONE/ONE, not a glowing rectangle.
        image=Image.fromarray(np.array([[[0,0,0,255],[255,255,255,0],[255,255,255,255]]],dtype=np.uint8))
        result=np.array(additive_rgba(image))
        self.assertEqual(result[0,0].tolist(),[0,0,0,0])
        self.assertEqual(result[0,1].tolist(),[0,0,0,0])
        self.assertEqual(result[0,2].tolist(),[255,255,255,255])
    def test_soft_intensity_and_existing_texture_tint_survive(self):
        image=Image.fromarray(np.array([[[128,128,128,255],[255,255,255,128]]],dtype=np.uint8))
        result=np.array(additive_rgba(image,(255,190,72)))
        self.assertEqual(result[0,0].tolist(),[128,95,36,128])
        self.assertEqual(result[0,1].tolist(),[128,95,36,128])

if __name__=='__main__':unittest.main()
