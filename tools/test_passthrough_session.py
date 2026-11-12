"""Startup recovery tests: synthetic module/report fixtures, no injection."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
import launch_passthrough_session as session

class StartupHotkeyTests(unittest.TestCase):
    def test_legacy_conflict_refused_before_any_startup_side_effect(self):
        for key in ('F7','F8','F9','F10','F11'):
            with self.subTest(key=key), patch.object(session,'selected_map') as selected, patch.object(session,'launch_guest') as launch:
                with self.assertRaises(ValueError):
                    session.run({'flightKey':key})
                selected.assert_not_called();launch.assert_not_called()

class HeroRefreshTests(unittest.TestCase):
    def test_generic_primary_precedes_slow_field_and_movement_once(self):
        order=[];hero=0x02e000000000006e;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_armory',side_effect=lambda *a:order.append('primary')) as primary,patch.object(session,'prepare_biotic',side_effect=lambda *a:order.append('field')),patch.object(session,'prepare_locomotion',side_effect=lambda *a:order.append('movement') or dict(hero=hero,modelId=9)):
            session.HeroBindingRefresh().refresh(42,body)
            self.assertEqual(order,['primary','field','movement']);primary.assert_called_once()
    def test_failed_generic_primary_does_not_publish_new_locomotion_identity(self):
        hero=0x02e0000000000003;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9);refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_armory',side_effect=ValueError('current model settling')),patch.object(session,'prepare_locomotion') as movement:
            with self.assertRaisesRegex(ValueError,'settling'):refresh.refresh(42,body)
            movement.assert_not_called();self.assertIsNone(refresh.identity)
    def test_tracer_pulse_precedes_new_movement_owner_and_failure_retries(self):
        hero=0x02e0000000000003;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        order=[];refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_pulse',side_effect=[ValueError('pulse settling'),{}]) as pulse,patch.object(session,'prepare_recall'),patch.object(session,'prepare_blink'),patch.object(session,'prepare_locomotion',side_effect=lambda *args:order.append('movement') or dict(hero=hero,modelId=9)):
            with self.assertRaises(ValueError):refresh.refresh(42,body)
            self.assertEqual(order,[]);self.assertIsNone(refresh.identity)
            self.assertTrue(refresh.refresh(42,body));self.assertEqual(pulse.call_count,2);self.assertEqual(order,['movement'])
    def test_soldier_field_precedes_publishing_new_locomotion_identity(self):
        hero=0x02e000000000006e;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9,worldId=1)
        order=[];refresh=session.HeroBindingRefresh()
        def locomotion(*args):order.append('movement');return dict(hero=hero,modelId=9)
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_biotic',side_effect=lambda *args:order.append('field')),patch.object(session,'prepare_locomotion',side_effect=locomotion):
            self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
            body['worldId']=2;self.assertTrue(refresh.refresh(42,body))
        self.assertEqual(order,['field','movement','field','movement'])
    def test_soldier_field_failure_cannot_cache_a_ready_new_model(self):
        hero=0x02e000000000006e;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_biotic',side_effect=[ValueError('field settling'),{}]),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)) as movement:
            with self.assertRaises(ValueError):refresh.refresh(42,body)
            self.assertIsNone(refresh.identity);movement.assert_not_called()
            self.assertTrue(refresh.refresh(42,body));movement.assert_called_once()
    def test_forced_same_model_repair_does_not_refill_health(self):
        refresh=session.HeroBindingRefresh({'fillNativeHealth':True})
        hero=0x02e0000000000042
        body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)),patch.object(session,'prepare_emission') as emission,patch.object(session,'prepare_roll'),patch.object(session,'fill') as fill:
            refresh.refresh(42,body);refresh.refresh(42,body,force=True)
            self.assertEqual(fill.call_count,1);self.assertEqual(emission.call_count,2)
    def test_partial_skill_failure_does_not_refill_the_same_live_hero_on_retry(self):
        hero=0x02e0000000000042;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        refresh=session.HeroBindingRefresh({'fillNativeHealth':True})
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)),patch.object(session,'prepare_emission'),patch.object(session,'prepare_roll',side_effect=[ValueError('settling'),{}]),patch.object(session,'fill') as fill:
            with self.assertRaises(ValueError):refresh.refresh(42,body)
            self.assertTrue(refresh.refresh(42,body));fill.assert_called_once()
    def test_primary_and_first_shift_binding_precede_optional_melee(self):
        for hero,skill in ((0x02e0000000000029,'prepare_ultimate'),(0x02e0000000000042,'prepare_roll')):
            order=[];body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
            with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)),patch.object(session,'prepare_emission',side_effect=lambda *a,**kw:order.append('primary')),patch.object(session,skill,side_effect=lambda *a:order.append('shift')),patch.object(session,'prepare_melee',side_effect=lambda *a:order.append('melee')):
                session.HeroBindingRefresh().refresh(42,body)
                self.assertEqual(order,['primary','shift','melee'])
    def test_meter_failure_is_retryable_instead_of_caching_incomplete_skill_binding(self):
        hero=0x02e0000000000042;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)),patch.object(session,'prepare_emission'),patch.object(session,'prepare_roll'),patch.object(session,'prepare_meter',side_effect=[ValueError('graph settling'),{}]):
            with self.assertRaises(ValueError):refresh.refresh(42,body)
            self.assertIsNone(refresh.identity);self.assertTrue(refresh.refresh(42,body))
    def setUp(self):
        # These fixtures mock native readers individually. Auto-discovered voice
        # plugins have their own reader fixtures and must not inspect this Mock.
        heroes_patch=patch.object(session,'HERO_PREPARES',{});heroes_patch.start();self.addCleanup(heroes_patch.stop)
        mei_patch=patch.object(session,'prepare_mei');mei_patch.start();self.addCleanup(mei_patch.stop)
        mccree_patch=patch.object(session,'apply_mccree_profile');self.mccree=mccree_patch.start();self.addCleanup(mccree_patch.stop)
        armory_patch=patch.object(session,'prepare_armory');self.armory=armory_patch.start();self.addCleanup(armory_patch.stop)
        hover_patch=patch.object(session,'apply_hover_response');self.hover=hover_patch.start();self.addCleanup(hover_patch.stop)
        skill_patch=patch.object(session,'prepare_skills');self.skills=skill_patch.start();self.addCleanup(skill_patch.stop)
        meter_patch=patch.object(session,'prepare_meter');self.meter=meter_patch.start();self.addCleanup(meter_patch.stop)
        melee_patch=patch.object(session,'prepare_melee');self.melee=melee_patch.start();self.addCleanup(melee_patch.stop)
        sustain_patch=patch.object(session,'prepare_sustain');self.sustain=sustain_patch.start();self.addCleanup(sustain_patch.stop)
        health_patch=patch.object(session,'prepare_health');self.health=health_patch.start();self.addCleanup(health_patch.stop)
    def test_health_binding_failure_cannot_cache_current_pawn(self):
        hero=0x02e000000000006e;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9)
        refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_biotic'),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)),patch.object(session,'prepare_health',side_effect=[ValueError('health settling'),{}]) as health:
            with self.assertRaisesRegex(ValueError,'health settling'):refresh.refresh(42,body)
            self.assertIsNone(refresh.identity);self.assertTrue(refresh.refresh(42,body));self.assertEqual(health.call_count,2)
    def test_mei_and_bastion_rebind_sustain_after_model_and_dimension_change(self):
        body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':0x02e0000000000015,'modelId':9,'worldId':1}
        refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',side_effect=lambda p,pid:{'hero':body['hero'],'modelId':body['modelId']}),patch.object(session,'prepare_armory'):
            self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body));body.update(hero=0x02e00000000000dd,modelId=10)
            self.assertTrue(refresh.refresh(42,body));body['worldId']=2;self.assertTrue(refresh.refresh(42,body));self.assertEqual(self.sustain.call_count,3)
    def test_pharah_rebinds_native_flight_barrage_states_meter_and_factories(self):
        refresh=session.HeroBindingRefresh();body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':0x02e0000000000008,'modelId':9}
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value={'hero':body['hero'],'modelId':9}),patch.object(session,'prepare_emission') as emission,patch.object(session,'prepare_armory') as armory:
            self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
            self.skills.assert_called_once();self.meter.assert_called_once();emission.assert_called_once();armory.assert_called_once()
            self.hover.assert_called_once()
    def test_pharah_unsupported_extensions_keep_verified_primary_and_do_not_retry_each_tick(self):
        hero=0x02e0000000000008;body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':hero,'modelId':9}
        refresh=session.HeroBindingRefresh();problem=session.UnsupportedArmory(hero,9,[{'error':'Projectile motion requires separate calibration'}])
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',side_effect=lambda p,pid:{'hero':body['hero'],'modelId':body['modelId']}),patch.object(session,'prepare_emission') as emission,patch.object(session,'prepare_armory',side_effect=problem) as armory:
            self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
            emission.assert_called_once();armory.assert_called_once();self.assertEqual(refresh.warnings[0]['modelId'],9)
            body['modelId']=10;armory.side_effect=None
            self.assertTrue(refresh.refresh(42,body));self.assertEqual(refresh.warnings,[])
    def test_optional_fallback_never_hides_primary_failure_or_wrong_owner(self):
        hero=0x02e0000000000008;body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':hero,'modelId':9}
        refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value={'hero':hero,'modelId':9}),patch.object(session,'prepare_emission',side_effect=ValueError('primary unavailable')),patch.object(session,'prepare_armory') as armory:
            with self.assertRaisesRegex(ValueError,'primary unavailable'):refresh.refresh(42,body)
            armory.assert_not_called();self.assertIsNone(refresh.identity)
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value={'hero':hero,'modelId':9}),patch.object(session,'prepare_emission'),patch.object(session,'prepare_armory',side_effect=session.UnsupportedArmory(hero,10,[])):
            with self.assertRaises(session.UnsupportedArmory):refresh.refresh(42,body)
            self.assertIsNone(refresh.identity)
    def test_other_heroes_and_unexpected_errors_remain_retryable_failures(self):
        for hero,error in ((0x02e0000000000002,session.UnsupportedArmory(0x02e0000000000002,9,[])),(0x02e0000000000008,ValueError('owner/read failure'))):
            body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':hero,'modelId':9};refresh=session.HeroBindingRefresh()
            with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value={'hero':hero,'modelId':9}),patch.object(session,'prepare_emission'),patch.object(session,'prepare_armory',side_effect=error):
                with self.assertRaises(ValueError):refresh.refresh(42,body)
                self.assertIsNone(refresh.identity)
    def test_pharah_optional_fallback_rechecks_current_model(self):
        hero=0x02e0000000000008;body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':hero,'modelId':9};refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',side_effect=[{'hero':hero,'modelId':9},{'hero':hero,'modelId':10}]),patch.object(session,'prepare_emission'),patch.object(session,'prepare_armory',side_effect=session.UnsupportedArmory(hero,9,[])):
            with self.assertRaisesRegex(ValueError,'changed during optional armory'):refresh.refresh(42,body)
            self.assertIsNone(refresh.identity);self.assertEqual(refresh.warnings,[])
    def test_new_model_rebinds_once_even_when_hero_name_matches(self):
        refresh=session.HeroBindingRefresh();body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':0x02e0000000000029,'modelId':9}
        with patch.object(session,'ResearchProcess') as process,patch.object(session,'prepare_ultimate') as ultimate,patch.object(session,'prepare_emission') as emission,patch.object(session,'prepare_locomotion',side_effect=lambda p,pid:{'hero':body['hero'],'modelId':body['modelId']}) as prepare:
            self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
            body['modelId']=10;self.assertTrue(refresh.refresh(42,body));self.assertEqual(prepare.call_count,2)
            self.assertEqual(process.return_value.close.call_count,2)
            self.assertEqual(ultimate.call_count,2);self.assertEqual(emission.call_count,2)
            self.assertEqual(self.skills.call_count,2)
            self.assertTrue(emission.call_args.kwargs['refresh'])
    def test_mccree_binds_and_failed_genji_return_can_retry(self):
        refresh=session.HeroBindingRefresh();body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':0x02e0000000000042,'modelId':9}
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',side_effect=lambda p,pid:{'hero':body['hero'],'modelId':body['modelId']}),patch.object(session,'prepare_ultimate') as ultimate,patch.object(session,'prepare_emission') as emission,patch.object(session,'prepare_roll') as roll:
            refresh.refresh(42,body);ultimate.assert_not_called();emission.assert_called_once()
            roll.assert_called_once()
            body.update(hero=0x02e0000000000029,modelId=10);emission.side_effect=ValueError('transitional binding')
            with self.assertRaises(ValueError):refresh.refresh(42,body)
            emission.side_effect=None;self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
    def test_dimension_transition_waits_and_rebinds_even_when_model_is_unchanged(self):
        refresh=session.HeroBindingRefresh({'fillNativeHealth':True})
        body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':0x02e0000000000042,
              'modelId':9,'worldId':100,'worldStable':True}
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',side_effect=lambda p,pid:{'hero':body['hero'],'modelId':body['modelId']}),patch.object(session,'prepare_emission'),patch.object(session,'prepare_roll'),patch.object(session,'fill') as fill:
            self.assertTrue(refresh.refresh(42,body))
            body['worldId']=200;body['worldStable']=False
            with self.assertRaisesRegex(ValueError,'stable guest dimension'):refresh.refresh(42,body)
            fill.assert_called_once()
            body['worldStable']=True
            self.assertTrue(refresh.refresh(42,body))
            self.assertEqual(fill.call_count,1)
    def test_wrong_process_cannot_rebind(self):
        with self.assertRaisesRegex(ValueError,'healthy'):session.HeroBindingRefresh().refresh(42,{'pid':43})
    def test_injured_pawn_dimension_change_skips_fill_but_guest_restart_initializes(self):
        hero=0x02e0000000000042;body=dict(pid=42,probeVersion=session.BODY_VERSION,enabled=True,failures=0,hero=hero,modelId=9,worldId=1,sourcePid=7,guestGeneration=8,hostGeneration=10)
        refresh=session.HeroBindingRefresh({'fillNativeHealth':True})
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value=dict(hero=hero,modelId=9)) as movement,patch.object(session,'prepare_emission'),patch.object(session,'prepare_roll'),patch.object(session,'fill') as fill:
            self.assertTrue(refresh.refresh(42,body));fill.side_effect=ValueError('MC health is2; new pawn fill not allowed')
            body['worldId']=2;self.assertTrue(refresh.refresh(42,body));self.assertEqual(fill.call_count,1);self.assertEqual(movement.call_count,2)
            body.update(sourcePid=11,guestGeneration=12)
            with self.assertRaisesRegex(ValueError,'MC health is2'):refresh.refresh(42,body)
            fill.side_effect=None;self.assertTrue(refresh.refresh(42,body));self.assertEqual(fill.call_count,3)
    def test_guest_restart_same_hero_and_world_rebinds_once(self):
        hero=0x02e0000000000042;body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'hero':hero,'modelId':9,'worldId':100,'sourcePid':7,'guestGeneration':8,'hostGeneration':10}
        refresh=session.HeroBindingRefresh()
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',return_value={'hero':hero,'modelId':9}) as locomotion,patch.object(session,'prepare_emission'),patch.object(session,'prepare_roll'):
            self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
            body.update(sourcePid=11,guestGeneration=12,worldStable=False)
            with self.assertRaisesRegex(ValueError,'stable guest dimension'):refresh.refresh(42,body)
            body['worldStable']=True;self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body));self.assertEqual(locomotion.call_count,2)
    def test_health_tracks_all_three_native_models_and_retries_failure(self):
        refresh=session.HeroBindingRefresh({'fillNativeHealth':True});body={'pid':42,'probeVersion':session.BODY_VERSION,'enabled':True,'failures':0,'modelId':9}
        with patch.object(session,'ResearchProcess'),patch.object(session,'prepare_locomotion',side_effect=lambda p,pid:{'hero':body['hero'],'modelId':body['modelId']}),patch.object(session,'prepare_ultimate'),patch.object(session,'prepare_emission'),patch.object(session,'prepare_roll'),patch.object(session,'fill') as fill:
            for hero in (0x02e0000000000029,0x02e0000000000042,0x02e0000000000009):
                body.update(hero=hero,modelId=body['modelId']+1)
                self.assertTrue(refresh.refresh(42,body));self.assertFalse(refresh.refresh(42,body))
            self.assertEqual(fill.call_count,3)
            body['modelId']+=1;fill.side_effect=ValueError('health owner changed')
            with self.assertRaises(ValueError):refresh.refresh(42,body)
            fill.side_effect=None;self.assertTrue(refresh.refresh(42,body))

class RecoveryTests(unittest.TestCase):
    def test_status_reader_sharing_race_cannot_kill_supervisor(self):
        with tempfile.TemporaryDirectory() as d,patch.object(session,'STATUS',Path(d)/'status.json'),patch.object(Path,'replace',side_effect=[PermissionError('reader'),None]) as replace,patch.object(session.time,'sleep'):
            self.assertTrue(session.write_status({'ready':False}));self.assertEqual(replace.call_count,2)
        with tempfile.TemporaryDirectory() as d,patch.object(session,'STATUS',Path(d)/'status.json'),patch.object(Path,'replace',side_effect=PermissionError('reader')),patch.object(session.time,'sleep'):
            self.assertFalse(session.write_status({'ready':False}))
    def test_module_snapshot_retries_only_bad_length(self):
        invalid=session.ctypes.c_void_p(-1).value
        create=Mock(side_effect=[invalid,invalid,123])
        with patch('attach_host_probe.bind',return_value=create),patch.object(session.ctypes,'get_last_error',return_value=24),patch.object(session.time,'sleep') as sleep:
            self.assertEqual(session.module_snapshot(Mock(),42),123)
            self.assertEqual(sleep.call_count,2)
        create=Mock(return_value=invalid)
        with patch('attach_host_probe.bind',return_value=create),patch.object(session.ctypes,'get_last_error',return_value=5),patch.object(session.time,'sleep') as sleep:
            with self.assertRaises(OSError):session.module_snapshot(Mock(),42)
            create.assert_called_once();sleep.assert_not_called()
    def test_module_snapshot_retry_has_bound(self):
        create=Mock(return_value=session.ctypes.c_void_p(-1).value)
        with patch('attach_host_probe.bind',return_value=create),patch.object(session.ctypes,'get_last_error',return_value=24),patch.object(session.time,'sleep') as sleep:
            with self.assertRaises(OSError):session.module_snapshot(Mock(),42)
            self.assertEqual(create.call_count,10);self.assertEqual(sleep.call_count,9)
    def test_reused_pid_does_not_adopt_stale_bootstrap_file(self):
        with patch.object(session,'installed_modules',return_value={}),patch.object(session,'attach') as attach:
            session.ensure_bootstrap(42);attach.assert_called_once_with(42,bootstrap=True,bootstrap_map=session.MAPS['hollywood'])
    def test_kyoto_request_is_passed_without_changing_default_map(self):
        with patch.object(session,'installed_modules',return_value={}),patch.object(session,'attach') as attach:
            session.ensure_bootstrap(42,session.MAPS['kyoto-login']);attach.assert_called_once_with(42,bootstrap=True,bootstrap_map=0x0800000000000664)
    def test_loaded_old_bootstrap_is_not_overlaid(self):
        with patch.object(session,'installed_modules',return_value={'owmc-session-bootstrap-v3.dll':session.BUILD/'owmc-session-bootstrap-v3.dll'}),patch.object(session,'attach') as attach:
            with self.assertRaisesRegex(RuntimeError,'different native bootstrap'):session.ensure_bootstrap(42)
            attach.assert_not_called()
    def exercise(self,loaded,healthy=True):
        native=Mock();native.create_time.return_value=123
        with patch.object(session.psutil,'Process',return_value=native),patch.object(session,'installed_modules',side_effect=lambda pid:dict(loaded)),patch.object(session,'stage_ready',return_value=healthy),patch.object(session,'wait',side_effect=lambda label,fn,seconds:fn()),patch.object(session,'attach') as attach:
            def install(pid,**mode):
                prefix=next(k for k,v in session.MODES.items() if mode.get(v));name=session.NATIVE_FILES[prefix];loaded[name]=(session.BUILD/name).resolve()
            attach.side_effect=install
            session.connect_stages(42)
            return attach.call_args_list
    def test_resume_after_emission_preflight_failure_preserves_three_live_hooks(self):
        loaded={name:(session.BUILD/name).resolve() for key,name in session.NATIVE_FILES.items() if key!='native-emissions'}
        calls=self.exercise(loaded)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0].kwargs,{'emissions':True})
    def test_healthy_adoption_never_reloads_any_hook(self):
        self.assertEqual(self.exercise({name:(session.BUILD/name).resolve() for name in session.NATIVE_FILES.values()}),[])
    def test_failed_loaded_hook_requires_restart(self):
        with self.assertRaisesRegex(RuntimeError,'do not reload'):self.exercise({session.COMPOSITOR_DLL:(session.BUILD/session.COMPOSITOR_DLL).resolve()},False)
    def test_old_native_version_requires_restart(self):
        with self.assertRaisesRegex(RuntimeError,'earlier native build'):self.exercise({'owmc-live-passthrough-v12.dll':(session.BUILD/'owmc-live-passthrough-v12.dll').resolve()})

    def test_weapon_preflight_transitional_flags_retry_before_loading(self):
        loaded={name:(session.BUILD/name).resolve() for key,name in session.NATIVE_FILES.items() if key!='weapon-gate'}
        native=Mock();native.create_time.return_value=123
        with patch.object(session.psutil,'Process',return_value=native),patch.object(session,'installed_modules',side_effect=lambda pid:dict(loaded)),patch.object(session,'stage_ready',return_value=True),patch.object(session,'wait',side_effect=lambda label,fn,seconds:fn()),patch.object(session,'attach',side_effect=[ValueError('Unexpected native hero flags/Volley nodes'),ValueError('Unexpected native hero flags/Volley nodes'),None]) as attach:
            session.connect_stages(42)
            self.assertEqual(attach.call_count,3)
    def test_same_named_dll_from_unrelated_folder_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'unhealthy'):self.exercise({session.COMPOSITOR_DLL:session.ROOT/'other'/session.COMPOSITOR_DLL})

    def test_mapped_optional_observer_without_report_does_not_block_or_reload(self):
        loaded={session.COMPOSITOR_DLL:(session.BUILD/session.COMPOSITOR_DLL).resolve()}
        ready={'world-live'}
        attempted=set()
        native=Mock(create_time=Mock(return_value=123))
        def attach(pid,**mode):
            self.assertIs(mode['wait_for_report'],False)
            prefix=next(k for k,v in session.MODES.items() if mode.get(v))
            name=session.NATIVE_FILES[prefix]
            loaded[name]=(session.BUILD/name).resolve()
            if prefix!='body-sync':ready.add(prefix)
        def wait(label,condition,seconds):
            self.assertLess(seconds,1)
            if not condition():raise TimeoutError(label)
        with patch.object(session.psutil,'Process',return_value=native), \
             patch.object(session,'installed_modules',side_effect=lambda pid:dict(loaded)), \
             patch.object(session,'stage_ready',side_effect=lambda pid,prefix,created:prefix in ready), \
             patch.object(session,'wait',side_effect=wait),patch.object(session,'attach',side_effect=attach) as launch:
            self.assertEqual(session.connect_stages(42,session.OBSERVERS,observer_attempts=attempted),'body-sync')
            self.assertEqual(session.connect_stages(42,session.OBSERVERS,observer_attempts=attempted),'body-sync')
            launch.assert_called_once_with(42,body_sync=True,wait_for_report=False)
            ready.add('body-sync')
            self.assertIsNone(session.connect_stages(42,session.OBSERVERS,observer_attempts=attempted))
            self.assertEqual(launch.call_count,3)

    def test_pending_loader_is_never_repeated_even_before_dll_is_mapped(self):
        loaded={session.COMPOSITOR_DLL:(session.BUILD/session.COMPOSITOR_DLL).resolve()}
        attempted=set()
        with patch.object(session.psutil,'Process',return_value=Mock(create_time=Mock(return_value=123))), \
             patch.object(session,'installed_modules',return_value=loaded),patch.object(session,'stage_ready',return_value=True), \
             patch.object(session,'attach',side_effect=session.NativeLoaderPending()) as launch:
            for _ in range(2):
                self.assertEqual(session.connect_stages(42,session.OBSERVERS,observer_attempts=attempted),'body-sync')
            launch.assert_called_once_with(42,body_sync=True,wait_for_report=False)
            loaded[session.BODY_DLL]=session.ROOT/'other'/session.BODY_DLL
            with self.assertRaisesRegex(RuntimeError,'do not reload'):
                session.connect_stages(42,session.OBSERVERS,observer_attempts=attempted)

class GuestRecoveryTests(unittest.TestCase):
    def setUp(self):
        cursor_patch=patch.object(session,'PickerCursorRepair')
        self.cursor=cursor_patch.start();self.addCleanup(cursor_patch.stop)
        self.cursor.return_value.released=0
    def record(self):
        return {'settings':{'showMinecraft':True,'worldName':'Old'},'loadedFiles':{},'ready':False}
    def test_live_guest_is_not_restarted(self):
        guest=Mock();guest.is_running.return_value=True
        with patch.object(session.psutil,'Process',return_value=guest),patch.object(session,'launch_guest') as launch:
            recovery=session.GuestRecovery({'sourcePid':7,'worldName':'Old'})
            self.assertFalse(recovery.recover(self.record()));launch.assert_not_called()
    def test_replacement_even_with_reused_pid_refreshes_identity_world_and_loaded_jar(self):
        old=Mock();old.is_running.return_value=False;new=Mock();new.is_running.return_value=True
        with tempfile.TemporaryDirectory() as folder:
            profile=Path(folder);(profile/'mods').mkdir();(profile/'mods/owmc-guest-0.1.0.jar').write_bytes(b'new guest')
            record=self.record()
            with patch.object(session,'PROFILE',profile),patch.object(session.psutil,'Process',side_effect=[old,new]),patch.object(session,'launch_guest',return_value={'sourcePid':7,'worldName':'New'}) as launch:
                recovery=session.GuestRecovery({'sourcePid':7,'worldName':'Old'})
                self.assertTrue(recovery.recover(record));self.assertIs(recovery.identity,new)
                self.assertEqual(record['settings']['worldName'],'New')
                self.assertEqual(record['loadedFiles']['guest\\build\\libs\\owmc-guest-0.1.0.jar'],hashlib.sha256(b'new guest').hexdigest())
                self.assertEqual(record['guestRecovery'],{'restarts':1,'sourcePid':7})
                self.assertFalse(recovery.recover(record));launch.assert_called_once_with(True)
    def test_recovery_bound_is_retained_across_phase_change(self):
        dead=Mock();dead.is_running.return_value=False
        with tempfile.TemporaryDirectory() as folder:
            profile=Path(folder);(profile/'mods').mkdir();(profile/'mods/owmc-guest-0.1.0.jar').write_bytes(b'jar')
            record=self.record()
            with patch.object(session,'PROFILE',profile),patch.object(session.psutil,'Process',return_value=dead),patch.object(session,'launch_guest',return_value={'sourcePid':8,'worldName':'Old'}) as launch:
                recovery=session.GuestRecovery({'sourcePid':7,'worldName':'Old'})
                recovery.recover(record);record['phase']='gameplay';recovery.recover(record);recovery.recover(record)
                with self.assertRaisesRegex(RuntimeError,'stopped repeatedly'):recovery.recover(record)
                self.assertEqual(launch.call_count,3)
    def test_initial_picker_recovers_before_first_confirmation_and_keeps_manifest(self):
        old=Mock();old.is_running.return_value=False;new=Mock();new.is_running.return_value=True
        native=Mock();native.is_running.return_value=True
        with tempfile.TemporaryDirectory() as folder:
            profile=Path(folder);(profile/'mods').mkdir();(profile/'mods/owmc-guest-0.1.0.jar').write_bytes(b'jar')
            record=self.record();snapshots=[]
            with patch.object(session,'PROFILE',profile),patch.object(session.psutil,'Process',side_effect=[old,native,new]),patch.object(session,'launch_guest',return_value={'sourcePid':8,'worldName':'New'}) as launch,patch.object(session,'first_person_ready',side_effect=[False,True]),patch.object(session,'write_status',side_effect=lambda r:snapshots.append(copy.deepcopy(r))),patch.object(session.time,'sleep'):
                recovery=session.GuestRecovery({'sourcePid':7,'worldName':'Old'})
                session.wait_for_selection(42,record['settings'],recovery,record)
                launch.assert_called_once_with(True)
                self.assertFalse(snapshots[-1]['ready']);self.assertEqual(snapshots[-1]['phase'],'hero-selection')
                self.assertEqual(snapshots[-1]['settings']['worldName'],'New')
                self.assertIn('guest\\build\\libs\\owmc-guest-0.1.0.jar',snapshots[-1]['loadedFiles'])
                self.assertNotIn('error',snapshots[-1]);self.assertEqual(recovery.retries,1)
    def test_picker_does_not_follow_a_reused_native_pid(self):
        native=Mock();native.is_running.return_value=False
        with patch.object(session.psutil,'Process',return_value=native),patch.object(session,'first_person_ready') as ready:
            with self.assertRaisesRegex(RuntimeError,'exited during hero selection'):
                session.wait_for_selection(42,{},Mock(),self.record())
            ready.assert_not_called()
    def test_confirmation_during_guest_recovery_does_not_keep_the_stop_error(self):
        native=Mock();native.is_running.return_value=True
        recovery=Mock();recovery.alive.return_value=False;record=self.record()
        with patch.object(session.psutil,'Process',return_value=native),patch.object(session,'first_person_ready',return_value=True),patch.object(session,'write_status'):
            session.wait_for_selection(42,record['settings'],recovery,record)
            recovery.recover.assert_called_once_with(record);self.assertNotIn('error',record)

class ReadinessTests(unittest.TestCase):
    def test_present_without_new_images_is_not_ready(self):
        tracker=session.CompositionProgress();state={'generation':123,'lastMcFrame':99,'blended':100,'unmaskedFrames':0}
        self.assertEqual(tracker.observe(1,state,0),[])
        self.assertTrue(tracker.observe(1,state,4))
        self.assertEqual(tracker.observe(1,{**state,'lastMcFrame':100},5),[])
        self.assertEqual(tracker.observe(2,state,10),[])
    def test_continuous_missing_foreground_is_not_ready(self):
        tracker=session.CompositionProgress();state={'generation':123,'lastMcFrame':99,'blended':100,'unmaskedFrames':0}
        tracker.observe(1,state,0)
        self.assertTrue(tracker.observe(1,{**state,'lastMcFrame':150,'blended':200,'unmaskedFrames':100},2))
        self.assertEqual(tracker.observe(1,{**state,'lastMcFrame':250,'blended':300,'unmaskedFrames':100},4),[])
    def setUp(self):
        self.guest={'failed':False,'published':500,'player':{'alive':True},
                    'hostPoseConnected':True,'hostPoseFlags':1,'hostGeneration':123}
        self.combat={'feedError':'','dashError':'','ultimate':{'error':''},'locomotion':{'ready':True,'error':''}}
        self.presentation={'generation':123,'blended':100,'colorUploads':50,
                           'lastMcFrame':500,'lastMcGeneration':456,'heldFrames':1,'viewMode':1}

    def problems(self):
        return session.runtime_problems(self.guest,self.combat,self.presentation)

    def test_connected_hooks_and_camera_do_not_prove_composition(self):
        self.presentation.update(blended=0,colorUploads=0,lastMcFrame=0,lastMcGeneration=0,heldFrames=7561)
        self.assertTrue(any('No Minecraft image' in reason for reason in self.problems()))

    def test_composited_selection_is_not_playable_readiness(self):
        self.presentation['viewMode']=2
        self.assertIn('Original hero selection has not entered first person',self.problems())

    def test_native_neutral_frame_is_not_a_minecraft_image(self):
        self.presentation.update(lastMcFrame=0,lastMcGeneration=0)
        self.assertTrue(self.problems())

    def test_old_camera_generation_is_rejected(self):
        self.guest['hostGeneration']=122
        self.assertIn('Minecraft camera belongs to a different native session',self.problems())

    def test_synthetic_pose_is_not_native_readiness(self):
        self.guest['hostPoseFlags']=2
        self.assertTrue(self.problems())

    def test_failures_report_rendering_and_ability_reasons_together(self):
        self.presentation['blended']=0
        self.combat['dashError']='native camera unavailable'
        problems=self.problems()
        self.assertEqual(len(problems),2)
        self.assertIn('dash: native camera unavailable',problems)

    def test_dead_guest_is_not_ready(self):
        self.guest['player']['alive']=False
        self.assertTrue(self.problems())

    def test_composed_image_and_native_channels_are_ready_without_fake_attacks(self):
        # Readiness does not require manufacturing a projectile/attack for the player.
        self.assertEqual(self.problems(),[])

    def test_mccree_does_not_require_genji_dash_or_ultimate_readers(self):
        self.combat['dashError']='native hero/ability changed'
        self.combat['ultimate']={'error':'native hero/ability changed'}
        self.assertEqual(session.runtime_problems(self.guest,self.combat,self.presentation,0x02e0000000000042),[])

if __name__=='__main__':unittest.main()
