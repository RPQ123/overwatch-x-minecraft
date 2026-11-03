"""Pure saved-evidence analyzer fixtures; no native/MC/game access."""
import unittest
from analyze_blink_weapon_state import analyze, BLINK, PISTOLS


class BlinkWeaponAnalysisTests(unittest.TestCase):
    def row(self, wall, finished, tick, frames, generation=1, model=10):
        return dict(wallMs=wall, sampleEndWallMs=wall+5, modelId=model,
                    states=[dict(script=BLINK, node=35, instanceAddress=100, nativeTick=tick, finished=finished)],
                    compositor=dict(pid=4, generation=generation, handMaskTraceEnabled=True, handMaskTrace=frames),
                    mappedBefore=dict(host=dict(generation=generation, frame=2),
                                      mc=dict(hostGeneration=generation, hostFrame=1, mcFrame=90)))

    def test_baseline_is_not_begin_and_exact_frame_join(self):
        frames=[dict(frame=1,wall=100,viewMode=1,preserved=True),dict(frame=2,wall=150,viewMode=1,resumed=1,invalid=True,preserved=False)]
        result=analyze(dict(pid=4,creation=123,rows=[self.row(100,True,1,frames),self.row(150,False,2,frames)]))
        self.assertEqual(result['uniqueFrames'],2)
        self.assertEqual(len(result['events']),1)
        self.assertEqual(result['events'][0]['wallInterval'],[100,155])
        self.assertEqual(result['events'][0]['kind'],'Begin-observed')
        self.assertEqual(len(result['events'][0]['mappedFrameMatches']),2)
        self.assertFalse(result['provenCompositorCause'])

    def test_generation_separation_gaps_and_lost_begin(self):
        a=[dict(frame=1,wall=100,viewMode=1,preserved=True),dict(frame=3,wall=200,viewMode=1,preserved=False)]
        b=[dict(frame=1,wall=300,viewMode=1,preserved=True)]
        result=analyze(dict(pid=4,rows=[self.row(100,True,1,a),self.row(200,True,2,a),self.row(300,True,3,b,generation=2,model=20)]))
        self.assertEqual(result['uniqueFrames'],3)
        self.assertEqual(len(result['frameGaps']),1)
        self.assertEqual(result['frameGaps'][0]['missing'],1)
        self.assertIn('may be lost',result['events'][0]['kind'])
        self.assertEqual(len(result['events']),1) # different model initializes a baseline

    def test_wrong_report_pid_is_never_joined(self):
        row=self.row(100,True,1,[dict(frame=1,wall=100,viewMode=1)])
        row['compositor']['pid']=999
        result=analyze(dict(pid=4,rows=[row]))
        self.assertEqual(result['uniqueFrames'],0)

    def test_complete_blink_and_weapon_scripts_are_kept(self):
        a=self.row(100,True,1,[])
        b=self.row(200,False,2,[])
        a['states'] += [dict(script=BLINK,node=45,instanceAddress=100,nativeTick=1,finished=True),
                        dict(script=PISTOLS,node=3,instanceAddress=200,nativeTick=1,finished=True)]
        b['states'] += [dict(script=BLINK,node=45,instanceAddress=100,nativeTick=2,finished=False),
                        dict(script=PISTOLS,node=3,instanceAddress=200,nativeTick=2,finished=False)]
        result=analyze(dict(pid=4,rows=[a,b]))
        self.assertEqual(result['eventCount'],3)
        self.assertEqual(result['eventScriptCounts'],{BLINK:2,PISTOLS:1})


if __name__=='__main__':
    unittest.main()
