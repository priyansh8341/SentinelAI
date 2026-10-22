import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock,patch
import requests
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'SentinelAI'))
import server
from agent import ModelUnavailable,reason_over_changes
from storage import SnapshotStore

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'history.db'
        self.patch=patch.object(server,'store',SnapshotStore(self.path));self.patch.start()
        self.lock=patch.object(server,'update_lock',threading.Lock());self.lock.start()
        self.client=TestClient(server.app)
    def tearDown(self):
        self.client.close();self.lock.stop();self.patch.stop();self.temp.cleanup()
    def update(self,text):return self.client.post('/update',json={'snapshot':text})
    def test_baseline_needs_no_model(self):
        with patch.object(server,'reason_over_changes') as model:result=self.update('Errors: 1').json();model.assert_not_called()
        self.assertEqual(result['mode'],'baseline');self.assertFalse(result['changed']);self.assertEqual(len(result['history']),1)
    def test_identical_submission_skips_model_and_new_revision(self):
        original=self.update('Errors: 1').json()
        with patch.object(server,'reason_over_changes') as model:result=self.update('Errors: 1').json();model.assert_not_called()
        self.assertEqual(result['mode'],'unchanged');self.assertEqual(result['revision'],original['revision']);self.assertEqual(len(result['history']),1)
    def test_changed_snapshot_has_exact_diff_and_persistent_report(self):
        self.update('Errors: 1\nOwner: ops')
        with patch.object(server,'reason_over_changes',return_value='Errors increased from 1 to 2.') as model:
            result=self.update('Errors: 2\nOwner: ops').json()
        model.assert_called_once_with('Errors: 1\nOwner: ops','Errors: 2\nOwner: ops')
        self.assertTrue(result['changed']);self.assertIn('-Errors: 1',result['diff']);self.assertIn('+Errors: 2',result['diff'])
        reopened=SnapshotStore(self.path);self.assertEqual(reopened.latest()['insight'],result['insight'])
        self.assertEqual(self.client.get('/state').json()['revision'],result['revision'])
        self.assertEqual(self.client.get('/export').json()['snapshot'],'Errors: 2\nOwner: ops')
    def test_model_failure_preserves_previous_revision(self):
        baseline=self.update('Errors: 1').json()
        with patch.object(server,'reason_over_changes',side_effect=ModelUnavailable('Local model unavailable.')):response=self.update('Errors: 2')
        self.assertEqual(response.status_code,503)
        current=self.client.get('/state').json();self.assertEqual(current['snapshot'],'Errors: 1');self.assertEqual(current['revision'],baseline['revision'])
    def test_concurrent_revision_change_cannot_overwrite_newer_snapshot(self):
        original=self.update('Errors: 1').json()
        def concurrent_change(*args):
            SnapshotStore(self.path).save(original['revision'],'Errors: 9','Other update','','model','test-model')
            return 'Stale comparison'
        with patch.object(server,'reason_over_changes',side_effect=concurrent_change):response=self.update('Errors: 2')
        self.assertEqual(response.status_code,409);self.assertEqual(server.store.latest()['snapshot'],'Errors: 9')
        self.assertEqual(len(server.store.history()),2)
    def test_busy_request_rejected_without_advancing_baseline(self):
        self.update('Errors: 1');server.update_lock.acquire()
        try:self.assertEqual(self.update('Errors: 2').status_code,409)
        finally:server.update_lock.release()
        self.assertEqual(server.store.latest()['snapshot'],'Errors: 1')
    def test_blank_oversized_and_unknown_fields_rejected(self):
        for text in ['','   ','x'*6001]:self.assertEqual(self.update(text).status_code,422)
        self.assertEqual(self.client.post('/update',json={'snapshot':'hello','action':'delete'}).status_code,422)
        self.assertIsNone(server.store.latest())
    def test_export_without_a_baseline_is_not_found(self):
        self.assertEqual(self.client.get('/export').status_code,404)
    def test_history_retains_latest_ten_and_reopens(self):
        revision=None
        for i in range(12):revision=server.store.save(revision,f'Snapshot {i}','Brief','','model','test-model')
        history=SnapshotStore(self.path).history();self.assertEqual(len(history),10);self.assertEqual(history[0]['note'],'Snapshot 11')
    def test_timeout_and_invalid_model_output_are_sanitized(self):
        with patch('agent.requests.post',side_effect=requests.Timeout()):
            with self.assertRaises(ModelUnavailable):reason_over_changes('before','after')
        response=Mock();response.json.return_value={'response':None}
        with patch('agent.requests.post',return_value=response):
            with self.assertRaises(ModelUnavailable):reason_over_changes('before','after')
    def test_model_configuration_and_bounded_http_request(self):
        response=Mock();response.json.return_value={'response':'A model-written brief.'}
        with patch.dict(os.environ,OLLAMA_MODEL='test-model',OLLAMA_URL='http://127.0.0.1:11434/'),patch('agent.requests.post',return_value=response) as post:
            self.assertEqual(reason_over_changes('before','after'),'A model-written brief.')
        self.assertEqual(post.call_args.kwargs['json']['model'],'test-model');self.assertEqual(post.call_args.kwargs['timeout'],(3,45))

if __name__=='__main__':unittest.main()
