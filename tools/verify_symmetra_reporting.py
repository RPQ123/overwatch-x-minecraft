"""Symmetra assertion/status reporting; imports perform no game or UI access."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXIT_CODES = {'PASSED': 0, 'FAILED': 1, 'BLOCKED': 2}
SUBMISSIONS = {
    'shield': ('shieldCommits', '01c3:3', False,
               'BLOCKED: no native01c3:3 success; E search must never grant a shield'),
    'turret': ('turretCommits', '017e:47', True,
               'BLOCKED: native017e:47 did not execute after confirmation; no MC-left fallback'),
    'portal': ('portalCommits', '0169:66', True,
               'BLOCKED: native0169:66 did not execute; no MC-left fallback'),
}


class VerificationAssertion(AssertionError):
    def __init__(self, case, assertion, message, *, status='FAILED', expected=None, actual=None):
        super().__init__(message)
        self.failure = dict(case=case, assertion=assertion, message=message, status=status,
                            expected=expected, actual=actual)


class AssertionBundle(AssertionError):
    def __init__(self, failures):
        self.failures = list(failures)
        super().__init__('; '.join(f['message'] for f in self.failures))


def require_submission(case, before, after):
    counter, node, exact, message = SUBMISSIONS[case]
    first, last = before.get(counter), after.get(counter)
    expected = 'delta == 1' if exact else 'delta >= 1'
    actual = dict(counter=counter, before=first, after=last, nativeNode=node)
    assertion = 'native.'+case+'.submission'
    if any(type(v) is not int or v < 0 for v in (first, last)):
        raise VerificationAssertion(case, assertion, 'Invalid native submission counter', expected=expected, actual=actual)
    delta = last-first
    actual['delta'] = delta
    if delta == 0:
        raise VerificationAssertion(case, assertion, message, status='BLOCKED', expected=expected, actual=actual)
    if delta < 0 or (exact and delta != 1):
        raise VerificationAssertion(case, assertion, 'Native submission counter regressed or duplicated', expected=expected, actual=actual)


def failure_details(case, error, assertion='case.assertion'):
    if isinstance(error, AssertionBundle):
        return copy.deepcopy(error.failures)
    if isinstance(error, VerificationAssertion):
        return [copy.deepcopy(error.failure)]
    return [dict(case=case, assertion=assertion, message=str(error) or repr(error),
                 status='FAILED', exception=repr(error))]


def case_failure(case, error):
    failures = failure_details(case, error)
    status = 'FAILED' if any(f['status'] != 'BLOCKED' for f in failures) else 'BLOCKED'
    return dict(passed=False, status=status, error=repr(error), assertionFailures=failures)


def finalize_result(result, extra_failures=()):
    failures = list(copy.deepcopy(extra_failures))
    for name, outcome in (result.get('cases') or {}).items():
        if outcome.get('passed'):
            outcome.update(status='PASSED', assertionFailures=[])
        else:
            if not outcome.get('assertionFailures'):
                outcome.update(case_failure(name, AssertionError(outcome.get('error') or 'Case failed without an assertion message')))
            failures.extend(outcome['assertionFailures'])
    if result.get('cleanupRequired', True) and result.get('cleaned') is not True:
        if not any(f['case'] == 'cleanup' for f in failures):
            failures.extend(failure_details('cleanup', RuntimeError(result.get('cleanupError') or 'Cleanup was not verified'), 'cleanup.verified'))
    if not failures and not result.get('cases') and not result.get('passed'):
        failures.extend(failure_details('setup', RuntimeError(result.get('error') or 'No case completed'), 'setup.completed'))
    status = ('FAILED' if any(f['status'] != 'BLOCKED' for f in failures)
              else 'BLOCKED' if failures else 'PASSED')
    result.update(status=status, exitCode=EXIT_CODES[status], passed=status == 'PASSED', assertionFailures=failures)
    result['error'] = '; '.join(dict.fromkeys(f"{f['case']}: {f['message']}" for f in failures)) or None
    return result['exitCode']


def review_historical(source):
    result = copy.deepcopy(source)
    for case, outcome in result['cases'].items():
        if outcome.get('passed'):
            continue
        # Only these exact historical assertions + recorded zero deltas
        # can become BLOCKED; a BLOCKED prefix alone is never sufficient.
        spec = SUBMISSIONS.get(case)
        step = result.get('steps', {}).get(case, {})
        expected_error = 'ValueError('+repr(spec[3])+')' if spec else None
        if spec and outcome.get('error') == expected_error:
            before = step.get('before', step.get('preview', {}))
            try:
                require_submission(case, before, step.get('after', {}))
            except VerificationAssertion as error:
                outcome.update(case_failure(case, error))
            else:
                outcome.update(case_failure(case, AssertionError('Historical assertion contradicts recorded submission counters')))
    finalize_result(result)
    return result


def annotate_b14():
    """Offline review of the four requested results. Original exits are retained."""
    reviewed = {}
    for key in ['symmetra', 'symmetra-shield', 'symmetra-turret', 'symmetra-portal']:
        path = ROOT/'research/sprint-20261024'/('integration-live-B14-'+key)/'result.json'
        original = path.with_name('result.original-B14.json')
        if not original.exists():
            original.write_bytes(path.read_bytes())
        raw = original.read_bytes()
        result = review_historical(json.loads(raw.decode('utf-8')))
        code = result['exitCode']
        result['classificationReview'] = dict(offlineOnly=True, executedAgain=False, originalProcessExitCode=1,
                                               rerunExitCode=code, originalResultSha256=hashlib.sha256(raw).hexdigest())
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        reviewed[key] = {k: result[k] for k in ['status', 'exitCode', 'error', 'assertionFailures', 'classificationReview']}
    output = ROOT/'research/sprint-20261024/symmetra-B14-reporting-review.json'
    output.write_text(json.dumps(reviewed, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k: dict(status=v['status'], assertions=len(v['assertionFailures']), rerunExitCode=v['exitCode'])
                      for k, v in reviewed.items()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annotate-b14', action='store_true', required=True)
    parser.parse_args()
    annotate_b14()
