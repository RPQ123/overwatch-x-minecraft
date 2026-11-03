import unittest
from hanzo_q_controls import control_contract,dragon_render_snapshot,dragon_draw_contract


def rows():
    trace=[]
    for phase in ['locked','recovered']:
        for i in range(8):
            controls=dict(nativeBegin=100,startedWall=1000,locked=phase=='locked',lockMillis=2500,nativeCastMillis=2500,
                          nativeEndWall=3500 if phase=='recovered' else 0,releasedWall=3500 if phase=='recovered' else 0)
            trace.append(dict(phase=phase,wall=1+i*.1 if phase=='locked' else 3.55+i*.1,
                              position=[0,64,0] if phase=='locked' else [i*.3,64,0],velocity=[0,0,0],driving=True,
                              nativeYaw=179 if phase=='locked' else 179+i*2,mcYaw=179 if phase=='locked' else 179+i*2,
                              nativePitch=0 if phase=='locked' else i,mcPitch=0 if phase=='locked' else i,
                              controls=controls,dragonDrawEvidence=dict(passed=phase=='recovered'),
                              nativeInput=dict(hanzoControlProtocol=2,hanzoMotionLocked=phase=='locked',hanzoMotionFrames=1+i)))
    return trace


class QControlAssertions(unittest.TestCase):
    def test_frozen_then_restored_passes(self):self.assertTrue(control_contract(rows(),True)['passed'])
    def test_input_without_native_cast_fails(self):self.assertFalse(control_contract(rows(),False)['passed'])
    def test_motion_during_lock_fails(self):
        trace=rows();trace[2]['position'][1]+=.1;self.assertFalse(control_contract(trace,True)['passed'])
    def test_pitch_escape_during_lock_fails(self):
        trace=rows();trace[2]['mcPitch']=1;self.assertFalse(control_contract(trace,True)['passed'])
    def test_native_mouse_motion_fails_even_if_mc_frozen(self):
        trace=rows();trace[2]['nativeYaw']=170;self.assertFalse(control_contract(trace,True)['passed'])
    def test_no_recovery_fails(self):
        trace=rows()
        for r in trace:r['position']=[0,64,0]
        self.assertFalse(control_contract(trace,True)['passed'])
    def test_missing_or_future_release_cannot_unlock(self):
        for value in [0,9999]:
            trace=rows()
            for r in trace:
                if r['phase']=='recovered':r['controls']['releasedWall']=value
            self.assertFalse(control_contract(trace,True)['passed'])
    def test_wrong_cast_or_false_release_diagnostic_fails(self):
        trace=rows();trace[-1]['controls']['nativeBegin']=99;self.assertFalse(control_contract(trace,True)['passed'])
    def test_no_actual_dragon_draw_fails(self):
        trace=rows()
        for r in trace:r['dragonDrawEvidence']['passed']=False
        self.assertFalse(control_contract(trace,True)['passed'])
    def test_mc_lock_alone_without_native_filter_receipt_fails(self):
        trace=rows()
        for r in trace:r['nativeInput']={}
        self.assertFalse(control_contract(trace,True)['passed'])
    def test_waiting_indefinitely_after_both_completed_fails(self):
        trace=rows()
        for r in trace:
            if r['phase']=='recovered':r['wall']+=.4
        self.assertFalse(control_contract(trace,True)['passed'])


class DragonDrawDiagnostics(unittest.TestCase):
    def test_existing_exported_skin_counters_prove_body_without_optional_key(self):
        before=dragon_render_snapshot(dict(hanzoDragonSkinDraws=10,hanzoDragonSkinFallbackDraws=2,hanzoDragonRendererErrors=0))
        after=dragon_render_snapshot(dict(hanzoDragonSkinDraws=12,hanzoDragonSkinFallbackDraws=2,hanzoDragonRendererErrors=0))
        self.assertEqual(before['bodyDraws'],12);self.assertEqual(after['bodyDraws'],14)
        self.assertIn('hanzoDragonDraws',after['missing']);self.assertTrue(dragon_draw_contract(before,after,1)['passed'])

    def test_missing_all_counters_is_blocked_not_zero(self):
        unknown=dragon_render_snapshot({});self.assertIsNone(unknown['bodyDraws'])
        self.assertEqual(dragon_draw_contract(unknown,unknown,1)['status'],'BLOCKED')

    def test_starting_arrow_frames_never_count_as_twin_body(self):
        before=dragon_render_snapshot(dict(hanzoDragonSkinDraws=0,hanzoDragonSkinFallbackDraws=0,hanzoDragonRendererFrames=0))
        after=dragon_render_snapshot(dict(hanzoDragonSkinDraws=0,hanzoDragonSkinFallbackDraws=0,hanzoDragonRendererFrames=100,hanzoDragonArrowFrames=100))
        self.assertEqual(dragon_draw_contract(before,after,1)['status'],'WAIT')

    def test_old_body_submissions_need_a_fresh_delta(self):
        snapshot=dragon_render_snapshot(dict(hanzoDragonSkinDraws=20,hanzoDragonSkinFallbackDraws=4))
        self.assertFalse(dragon_draw_contract(snapshot,snapshot,1)['passed'])

    def test_new_render_error_and_counter_source_change_fail(self):
        before=dragon_render_snapshot(dict(hanzoDragonDraws=0,hanzoDragonRendererErrors=0))
        after=dragon_render_snapshot(dict(hanzoDragonDraws=2,hanzoDragonRendererErrors=1,hanzoDragonRendererError='missing pack'))
        self.assertEqual(dragon_draw_contract(before,after,1)['status'],'FAIL')
        other=dragon_render_snapshot(dict(hanzoDragonSkinDraws=2,hanzoDragonSkinFallbackDraws=0))
        self.assertEqual(dragon_draw_contract(before,other,1)['status'],'FAIL')

    def test_new_body_submissions_need_a_live_dragon(self):
        before=dragon_render_snapshot(dict(hanzoDragonDraws=0));after=dragon_render_snapshot(dict(hanzoDragonDraws=2))
        self.assertFalse(dragon_draw_contract(before,after,0)['passed'])


if __name__=='__main__':unittest.main()
