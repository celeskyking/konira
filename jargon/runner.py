import inspect
import sys
from jargon.util            import StopWatch
from jargon.collector       import globals_from_execed_file
from jargon.output          import (out_red, out_green, out_spec, 
                                    ExcFormatter, out_footer)



class Runner(object):

    def __init__(self, paths):
        self.paths          = paths
        self.failures       = []
        self.errors         = []
        self.total_cases    = 0
        self.total_failures = 0
        self.total_errors   = 0


    def run(self):
        self.timer = StopWatch()
        for f in self.paths:
            try:
                classes = [i for i in self._collect_classes(f)]
            except Exception, e:
                self.total_errors += 1
                self.errors.append(e)
                continue
            for case in classes:
                self.run_suite(case)
        self.elapsed = self.timer.elapsed()


    def run_suite(self, case):
        sys.stdout.write('\n')
        # Initialize the test class
        suite = case()

        # check test environment setup
        environ = TestEnviron(suite)

        # Name the class
        out_spec(suite.__class__.__name__)

        methods = self._collect_methods(suite)

        # Set before all if any
        environ.set_before_all()

        for test in methods:
            self.total_cases += 1

            # Set before each if any
            environ.set_before_each()

            try:
                getattr(suite, test)()
                out_green(test)
                
                # Set after each if any
                environ.set_after_each()
            except BaseException, e:
                trace = inspect.trace()
                self.total_failures += 1
                out_red(test)
                self.failures.append(
                    dict(
                        failure   = sys.exc_info(),
                        exc_name  = e.__class__.__name__
                       ) 
                    )

        # Set after all if any
        environ.set_after_all()


    # This is probably the wrong spot for this guy
    def report(self):
        sys.stdout.write('\n')
        if self.failures:
            format_exc = ExcFormatter(self.failures)
            format_exc.output_failures()
        if self.errors:
            format_exc = ExcFormatter(self.errors)
            format_exc.output_errors()
        out_footer(self.total_cases, self.total_failures, self.elapsed)


    def _collect_classes(self, path):
            global_modules = map(globals_from_execed_file, [path])
            return [i for i in global_modules[0].values() if callable(i) and i.__name__.startswith('Case_')]


    def _collect_methods(self, module):
        invalid = ['_before_each', '_before_all', '_after_each', '_after_all']
        return [i for i in dir(module) if not i.startswith('_') and i not in invalid] 




class TestEnviron(object):
    """
    Checks for all test setup calls and sets a boolean
    flag for each.
    This approach avoids the runner to be checking getattr
    for every time since we alredy did at the beginning.
    """


    def __init__(self, suite):
        self.suite           = suite
        self.has_before_all  = self._before_all
        self.has_before_each = self._before_each
        self.has_after_all   = self._after_all
        self.has_after_each  = self._after_each


    @property
    def _before_all(self):
        if hasattr(self.suite, '_before_all'):
            return True
        return False


    @property
    def _before_each(self):
        if hasattr(self.suite, '_before_each'):
            return True
        return False


    @property
    def _after_all(self):
        if hasattr(self.suite, '_after_all'):
            return True
        return False


    @property
    def _after_each(self):
        if hasattr(self.suite, '_after_each'):
            return True
        return False
    

    def set_before_all(self):
        if self.has_before_all:
            getattr(self.suite, '_before_all')()


    def set_before_each(self):
        if self.has_before_each:
            return getattr(self.suite, '_before_each')()


    def set_after_all(self):
        if self.has_after_all:
            return getattr(self.suite, '_after_all')()


    def set_after_each(self):
        if self.has_after_each:
            return getattr(self.suite, '_after_each')()
                

