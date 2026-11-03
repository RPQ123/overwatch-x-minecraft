"""Counter samples must distinguish new images, repeated presents and report cadence."""
import unittest
from unittest.mock import Mock,patch
from measure_passthrough_perf import summarize,read_report

class PerformanceTests(unittest.TestCase):
    def test_short_writer_lock_retries_same_report_and_records_retries(self):
        path=Mock();path.read_text.side_effect=[PermissionError(),'{','{"frames":123}']
        with patch('measure_passthrough_perf.time.sleep'):self.assertEqual(read_report(path),({'frames':123},2))
        path.read_text.side_effect=PermissionError()
        with patch('measure_passthrough_perf.time.sleep'),self.assertRaises(PermissionError):read_report(path)
    def rows(self):
        a={'pid':42,'generation':10,'probeVersion':21,'sampleWallMs':1000,'frames':100,'colorUploads':90,'heldFrames':2,'unmaskedFrames':0,'drawObserveCpuNs':1000000,'drawObservations':1000}
        b={**a,'sampleWallMs':3000,'frames':500,'colorUploads':390,'heldFrames':102,'drawObserveCpuNs':401000000,'drawObservations':5000}
        return [{'elapsed':0,'health':{'published':0},'native':a},{'elapsed':2.2,'health':{'published':330},'native':b}]
    def test_report_time_and_unique_frames(self):
        s=summarize(self.rows())
        self.assertEqual(s['hostFps'],200)
        self.assertEqual(s['distinctComposedFps'],150)
        self.assertEqual(s['heldFrames'],100)
        self.assertAlmostEqual(s['mcFps'],150)
        self.assertEqual(s['cpuMsPerNativeFrame']['drawObserveCpu'],1)
    def test_stopped_frames_cannot_pass(self):
        rows=self.rows();rows[-1]['native']['frames']=100
        with self.assertRaisesRegex(ValueError,'advancing'):summarize(rows)
    def test_restarted_session_cannot_mix_counters(self):
        rows=self.rows();rows[-1]['native']['generation']=11
        with self.assertRaisesRegex(ValueError,'identity'):summarize(rows)
    def test_legacy_sample_has_explicit_fallback_span(self):
        rows=self.rows()
        for r in rows:del r['native']['sampleWallMs']
        s=summarize(rows)
        self.assertEqual(s['nativeSampleSeconds'],2.2)
        self.assertAlmostEqual(s['hostFps'],400/2.2)
    def test_average_cannot_hide_slow_report_window_or_duplicate_report(self):
        rows=self.rows();middle={**rows[0]['native'],'sampleWallMs':2000,'colorUploads':190,'frames':300}
        rows[1:1]=[{'elapsed':1,'health':{'published':150},'native':middle},
                   {'elapsed':1.1,'health':{'published':160},'native':middle.copy()}]
        s=summarize(rows)
        self.assertEqual(s['distinctComposedFps'],150)
        self.assertEqual(s['distinctReportWindows'],{'samples':2,'minSeconds':1,'maxSeconds':1,'minimumFps':100,'below150':1})
    def test_middle_session_change_is_rejected(self):
        rows=self.rows();middle={**rows[0]['native'],'generation':999,'sampleWallMs':2000}
        rows.insert(1,{'elapsed':1,'health':{'published':150},'native':middle})
        with self.assertRaisesRegex(ValueError,'identity'):summarize(rows)

if __name__=='__main__':unittest.main()
