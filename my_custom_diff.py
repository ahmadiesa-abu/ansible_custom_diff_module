#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python default imports
import os
import time
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes

def shell_exec(command):
    '''
    Execute raw shell command and return exit code and output
    '''
    cpt = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = []
    for line in iter(cpt.stdout.readline, ''):
        output.append(line)

    # Wait until process terminates (without using p.wait())
    while cpt.poll() is None:
        # Process hasn't exited yet, let's wait some
        time.sleep(0.5)

    # Get return code from process
    return_code = cpt.returncode

    # return output as string instead of array
    output = '\n'.join(output)

    # Return code and output
    return return_code, output


def diff_module_validation(module):
    '''
    Validate for correct module call/usage in ansible.
    '''
    source = module.params.get('source')
    target = module.params.get('target')
    source_type = module.params.get('source_type')
    target_type = module.params.get('target_type')

    # Validate source
    if source_type == 'file':
        b_source = to_bytes(source, errors='surrogate_or_strict')
        if not os.path.exists(b_source):
            module.fail_json(msg="source %s not found" % (source))
        if not os.access(b_source, os.R_OK):
            module.fail_json(msg="source %s not readable" % (source))
        if os.path.isdir(b_source):
            module.fail_json(msg="diff does not support recursive diff of directory: %s" % (source))

    # Validate target
    if target_type == 'file':
        b_target = to_bytes(target, errors='surrogate_or_strict')
        if not os.path.exists(b_target):
            module.fail_json(msg="target %s not found" % (target))
        if not os.access(b_target, os.R_OK):
            module.fail_json(msg="target %s not readable" % (target))
        if os.path.isdir(b_target):
            module.fail_json(msg="diff does not support recursive diff of directory: %s" % (target))

    return module


def main():
    argument_spec = {
        'source': {'type': 'str', 'required': True},
        'target': {'type': 'str', 'required': True},
        'source_type': { 'type': 'str', 'required': True,
                         'choices': ['string', 'file', 'command']},
        'target_type': { 'type': 'str', 'required': True,
                         'choices': ['string', 'file', 'command']}
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    module = diff_module_validation(module)

    source = module.params.get('source')
    target = module.params.get('target')
    source_type = module.params.get('source_type')
    target_type = module.params.get('target_type')
    if source_type == 'file':
        with open(source, 'rt') as fpt:
            source = fpt.read().decode("UTF-8")
    elif source_type == 'command':
        if module.check_mode:
            result = dict(
                changed=False,
                msg="This module does not support check mode when source_type is 'command'.",
                skipped=True
            )
            module.exit_json(**result)
        else:
            ret, source = shell_exec(source)
            if ret != 0:
                module.fail_json(msg="source command failed: %s" % (source))


    # Targe file to string
    if target_type == 'file':
        with open(target, 'rt') as fpt:
            target = fpt.read().decode("UTF-8")
    # Target command to string
    elif target_type == 'command':
        if module.check_mode:
            result = dict(
                changed=False,
                msg="This module does not support check mode when target_type is 'command'.",
                skipped=True
            )
            module.exit_json(**result)
        else:
            ret, target = shell_exec(target)
            if ret != 0:
                module.fail_json(msg="target command failed: %s" % (target))

    diff = {
        'target': target,
        'source': source,
    }
    changed = (source != target)
    result = dict(
        diff=diff,
        changed=changed
    )

    module.exit_json(**result)

if __name__ == '__main__':
    main()
