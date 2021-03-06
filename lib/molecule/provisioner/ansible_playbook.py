#  Copyright (c) 2015-2018 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
"""Ansible-Playbook Provisioner Module."""

from molecule import logger, util

LOG = logger.get_logger(__name__)


class AnsiblePlaybook(object):
    """Privisioner Playbook."""

    def __init__(self, playbook, config, out=LOG.out, err=LOG.error):
        """
        Set up the requirements to execute ``ansible-playbook`` and returns \
        None.

        :param playbook: A string containing the path to the playbook.
        :param config: An instance of a Molecule config.
        :param out: An optional function to process STDOUT for underlying
         :func:``sh`` call.
        :param err: An optional function to process STDERR for underlying
         :func:``sh`` call.
        :returns: None
        """
        self._ansible_command = None
        self._playbook = playbook
        self._config = config
        self._out = out
        self._err = err
        self._cli = {}
        self._env = self._config.provisioner.env

    def bake(self):
        """
        Bake an ``ansible-playbook`` command so it's ready to execute and \
        returns ``None``.

        :return: None
        """
        if not self._playbook:
            return

        # Pass a directory as inventory to let Ansible merge the multiple
        # inventory sources located under
        self.add_cli_arg("inventory", self._config.provisioner.inventory_directory)
        options = util.merge_dicts(self._config.provisioner.options, self._cli)
        verbose_flag = util.verbose_flag(options)
        if self._playbook != self._config.provisioner.playbooks.converge:
            if options.get("become"):
                del options["become"]

        ansible_args = list(self._config.provisioner.ansible_args) + list(
            self._config.ansible_args
        )

        # if ansible_args:
        #     if self._config.action not in ["create", "destroy"]:
        #         # inserts ansible_args at index 1
        #         self._ansible_command.cmd.extend(ansible_args)

        self._ansible_command = util.BakedCommand(
            cmd=[
                "ansible-playbook",
                *util.dict2args(options),
                *util.bool2args(verbose_flag),
                *ansible_args,
                self._playbook,  # must always go last
            ],
            cwd=self._config.scenario.directory,
            env=self._env,
            stdout=self._out,
            stderr=self._err,
        )

    def execute(self):
        """
        Execute ``ansible-playbook`` and returns a string.

        :return: str
        """
        if self._ansible_command is None:
            self.bake()

        if not self._playbook:
            LOG.warning("Skipping, %s action has no playbook." % self._config.action)
            return

        self._config.driver.sanity_checks()
        result = util.run_command(self._ansible_command, debug=self._config.debug)
        if result.returncode != 0:
            util.sysexit_with_message(
                f"Ansible return code was {result.returncode}, command was: {result.args}",
                result.returncode,
            )

        return result.stdout

    def add_cli_arg(self, name, value):
        """
        Add argument to CLI passed to ansible-playbook and returns None.

        :param name: A string containing the name of argument to be added.
        :param value: The value of argument to be added.
        :return: None
        """
        if value:
            self._cli[name] = value

    def add_env_arg(self, name, value):
        """
        Add argument to environment passed to ansible-playbook and returns \
        None.

        :param name: A string containing the name of argument to be added.
        :param value: The value of argument to be added.
        :return: None
        """
        self._env[name] = value
