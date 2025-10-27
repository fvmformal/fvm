"""This module defines the steps class, which is used to manage the steps
and post_steps of the verification process."""
class Steps:
    """This class defines a data structure in which to store the steps and
    provides functions to manage it (such as adding steps and post_steps)"""

    def __init__(self):
        """Class constructor"""
        # Dictionaries are ordered since python 3.7, so we can just insert the
        # steps in the order in which we want it them run. For earlier python
        # versions we could use OrderedDict, but FVM doesn't work with python <
        # 3.8, so there's no need to support that
        self.steps = {}
        self.post_steps = {}

    def add_step(self, framework, step, setup, run):
        """Adds a step to the steps dictionary. Fails if the step already exists"""
        if step in self.steps:
            framework.logger.error(f'{step=} already exists in {self.steps=}')
        self.steps[step] = {}
        self.steps[step]["setup"] = setup
        self.steps[step]["run"] = run

    # Cannot reuse add_step for post_steps because post_steps are never run if
    # the relevant step fails, whereas steps may be run even if the previous
    # step fails (when using the --continue flag)
    def add_post_step(self, framework, step, post_step, setup, run):
        """Adds a post_step to the post_steps dictionary. Fails if the step does not exist"""
        if step not in self.steps:
            framework.logger.error(f'{step=} does not exist in {self.steps=}')
        if post_step in self.post_steps:
            framework.logger.error(f'{post_step=} already exists in {self.steps[step]=}')
        # Initialize the post_steps struct if it doesn't exist
        if step not in self.post_steps:
            self.post_steps[step] = {}
        # Add the specific post_step
        self.post_steps[step][post_step] = {}
        self.post_steps[step][post_step]["setup"] = setup
        self.post_steps[step][post_step]["run"] = run

    def append_step(self, framework, target, step, setup, run):
        """Appends a step after the target step."""
        # Fail if target not in dict
        if target not in self.steps:
            framework.logger.error(f'{target=} not in {self.steps=}, cannot insert step after it')
        # Get position of target in the dict
        pos = list(self.steps).index(target)
        # Convert dict to list
        l = list(self.steps.items())
        # Add step after target
        l.insert(pos+1, (step, {"setup": setup, "run": run}))
        # Convert list to dict
        self.steps = dict(l)

    def prepend_step(self, framework, target, step, setup, run):
        """Prepends a step before the target step."""
        # Fail if target not in dict
        if target not in self.steps:
            framework.logger.error(f'{target=} not in {self.steps=}, cannot insert step before it')
        # Get position of target in the dict
        pos = list(self.steps).index(target)
        # Convert dict to list
        l = list(self.steps.items())
        # Add step before target
        l.insert(pos, (step, {"setup": setup, "run": run}))
        # Convert list to dict
        self.steps = dict(l)
