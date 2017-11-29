def snap_name(perf_vm_domain, baseline_branch, target_branch=''):
    if perf_vm_domain == 'CP':
        return 'readyfortestsnap'
    if perf_vm_domain == 'candlepin-perf-mysql':
        version = baseline_branch.split('.')
        return 'testsnap_%s.%s' % (version[0], version[1])
    return ""

def baseline_file(baseline_branch):
    version = baseline_branch.split('.')
    return 'baseline/%s.%s-baseline.json' % (version[0], version[1])

def expected_file(baseline_branch):
    version = baseline_branch.split('.')
    return 'expected/%s.%s-expected.json' % (version[0], version[1])

class FilterModule(object):
  def filters(self):
      return {'snap_name': snap_name,
              'baseline_file': baseline_file,
              'expected_file': expected_file}
