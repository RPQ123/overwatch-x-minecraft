import unittest
from native_picker_cursor import can_release
class PickerCursorTests(unittest.TestCase):
    def test_actual_smaller_centered_clip(self):self.assertTrue(can_release(2,True,True,False,(0,0,2560,1440),(320,180,2240,1260)))
    def test_gameplay_and_unrelated_surface_refused(self):
        for mode,foreground,cursor,drag in [(1,True,True,False),(2,False,True,False),(2,True,False,False),(2,True,True,True)]:
            self.assertFalse(can_release(mode,foreground,cursor,drag,(0,0,2560,1440),(320,180,2240,1260)))
    def test_full_external_degenerate_and_offcenter_clips_untouched(self):
        for clip in [(0,0,2560,1440),(-1,0,2240,1260),(320,180,320,1260),(0,0,200,200)]:self.assertFalse(can_release(2,True,True,False,(0,0,2560,1440),clip))
if __name__=='__main__':unittest.main()
