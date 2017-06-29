import os
import shutil
import logging
import json
import abc
import mmap

from subprocess import TimeoutExpired, PIPE, Popen
from random import choice
from string import ascii_letters
from extended_uva_judge import errors, enums, utilities, languages


class ProblemResponseBuilder:
    def __init__(self, code, description=None, trace=None, debug=False,
                 stdout=None, stderr=None):
        self._code = code
        self._description = description
        self._trace = trace
        self._debug = debug
        self._stdout = None
        self._stderr = None

        # Convert some things that sometimes come in as bytes
        self.stdout = stdout
        self.stderr = stderr

    def build_response(self):
        response_body = {
            'code': self._code,
            'message': self.MESSAGE_MAP.get(self._code)
        }

        if self._description is not None:
            response_body['description'] = self._description

        if self._trace is not None:
            response_body['trace'] = (
                self._trace.replace('\\r', '\r')
                    .replace('\\n', '\n')
                    .replace('\\\\', '\\'))

        if self._debug:
            response_body['stdout'] = self.stdout
            response_body['stderr'] = self.stderr

        return json.dumps(response_body)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    @property
    def stdout(self):
        return self._stdout

    @stdout.setter
    def stdout(self, value):
        if isinstance(value, bytes):
            value = value.decode()
        self._stdout = value

    @property
    def stderr(self):
        return self._stderr

    @stderr.setter
    def stderr(self, value):
        if isinstance(value, bytes):
            value = value.decode()
        self._stderr = value

    @property
    def code(self):
        return self._code

    MESSAGE_MAP = {
        enums.ProblemResponses.ACCEPTED: 'Accepted',
        enums.ProblemResponses.ACCEPTED_PRESENTATION_ERROR:
            'Accepted with Presentation Error',
        enums.ProblemResponses.PRESENTATION_ERROR: 'Presentation Error',
        enums.ProblemResponses.WRONG_ANSWER: 'Wrong Answer',
        enums.ProblemResponses.COMPILE_ERROR: 'Compile Error',
        enums.ProblemResponses.RUNTIME_ERROR: 'Runtime Error',
        enums.ProblemResponses.TIME_LIMIT_EXCEEDED: 'Time Limit Exceeded',
        enums.ProblemResponses.MEMORY_LIMIT_EXCEEDED: 'Memory Limit Exceeded',
        enums.ProblemResponses.OUTPUT_LIMIT_EXCEEDED: 'Output Limit Exceeded',
        enums.ProblemResponses.RESTRICTED_FUNCTION: 'Restricted Function',
        enums.ProblemResponses.SUBMISSION_ERROR: 'Submission Error'
    }


class ProblemWorkerFactory:
    _config = None

    def __init__(self):
        raise NotImplementedError()

    @staticmethod
    def initialize(app_config):
        global _config
        _config = app_config

    @staticmethod
    def create_worker(language, problem_id):
        global _config

        lang = ProblemWorkerFactory._normalize_language(language)
        args = lang, problem_id, _config

        if lang == languages.PYTHON2 or lang == languages.PYTHON3:
            worker = PythonProblemWorker(*args)
        elif lang == languages.C_SHARP:
            worker = CSharpProblemWorker(*args)
        else:
            logging.warning('Failure to run problem worker. '
                            'Language not implemented.')
            worker = NotImplementedProblemWorker(*args)

        logging.debug('Mapped {lang} to {worker}.'.format(
            lang=lang, worker=worker.__class__.__name__))
        return worker

    @staticmethod
    def _normalize_language(language):
        mapped_lang = languages.map_language(language)
        logging.getLogger().debug(
            'Mapped language {input} to {output}.'.format(
                input=language, output=mapped_lang))
        return mapped_lang


class ProblemWorker:
    def __init__(self, language, problem_id, config):
        self._mapped_lang = language
        self._problem_id = problem_id
        self._config = config  # type: dict
        self._log = logging.getLogger()
        self._temp_work_dir = None
        self._run_command = None
        self._test_result = None
        self._failure_trace = None
        self._user_output = None
        self._user_error = None
        self._user_result_code = None
        self._safe_to_run = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._remove_temp_work_dir()

    def __del__(self):
        self._remove_temp_work_dir()

    def test(self, request):
        """Runs the users submission against all test cases

        :param request: The http request containing the users submission
        :return: A ProblemResponseBuilder for the verdict
        :rtype: ProblemResponseBuilder
        """
        try:
            self._create_temp_work_dir()
            user_file_path = self._save_user_file(request)
            self._scan_for_disallowed_constructs(user_file_path)
            if self._safe_to_run:
                self._compile(user_file_path)
                self._run_command = self._build_run_command(user_file_path)
                self._execute_run()
                self._verify_output()
                self._analyze_result_code()
        except RuntimeError:
            self._log.debug('Runtime error.')
            self._test_result = ProblemResponseBuilder(
                enums.ProblemResponses.RUNTIME_ERROR,
                trace=self._failure_trace)
        except TimeoutExpired:
            self._log.debug('Time limit exceeded.')
            self._test_result = ProblemResponseBuilder(
                enums.ProblemResponses.TIME_LIMIT_EXCEEDED,
            )

        return self.test_result

    @abc.abstractmethod
    def _compile(self, user_file_path):
        """Compiles the submission for the users language.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _build_run_command(self, user_file_path):
        """Builds the command to run the users app

        :param user_file_path: The path to the users compiled application
        """
        raise NotImplementedError

    @property
    def language(self):
        """Gets the normalized programming language.

        :return: The normalized programming language.
        :rtype: str
        """
        return self._mapped_lang

    @property
    def test_result(self):
        """Returns the test results if available, None otherwise

        :return: The test results
        :rtype: ProblemResponseBuilder
        """
        return self._test_result

    @property
    def output(self):
        return self._user_output

    def _scan_for_disallowed_constructs(self, user_file_path):
        lang_details = self._config.get('languages', {}).get(self.language, {})
        restricted = lang_details.get('restricted')
        if restricted is None:
            return

        restricted_item = False
        with open(user_file_path, 'rb', 0) as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as s:
                for item in restricted:
                    if s.find(item.encode()) != -1:
                        restricted_item = item

        if restricted_item:
            self._test_result = ProblemResponseBuilder(
                enums.ProblemResponses.RESTRICTED_FUNCTION,
                description=('Restricted Function: %s' % restricted_item)
            )
        else:
            self._safe_to_run = True

    def _analyze_result_code(self):
        """Analyzes the test result code and sets the test result
        """
        self._test_result = ProblemResponseBuilder(
            self._user_result_code,
            stdout=self._user_output,
            stderr=self._user_error
        )

    def _execute_run(self):
        """Executes the users application with the run arguments.

        :return: The output from the users program
        :rtype: str
        """
        problem_config = self._get_problem_config()
        program_input = problem_config['input'].replace(
            '\r\n', '\n').rstrip('\n').encode()
        timeout = float(problem_config['time_limit'])

        return_code, stdout, stderr = self._execute_command(
            self._run_command, cmd_input=program_input, timeout=timeout)

        self._user_output = stdout
        self._user_error = stderr

        if return_code != 0:
            message = (
                'Problem with test...\nStandard Output: {out}\n'
                'Standard Error: {err}\nReturn Code:{code}'.format(
                    out=stdout, err=stderr, code=return_code))
            self._log.debug(message)
            self._failure_trace = str(stderr)
            raise RuntimeError(stderr)

    @staticmethod
    def _execute_command(command, cmd_input=None, timeout=None):
        """Executes the specified command

        :param command: the command to execute
        :param cmd_input: standard in inputs to provide to the running command
        :param timeout: Time limit in which to kill the app in seconds.
        :return: return code, standard output, standard error
        :rtype: tuple
        """
        p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(input=cmd_input, timeout=timeout)

        return p.returncode, stdout, stderr

    def _verify_output(self):
        """Verifies the provided output against the expected output in the run

        :return: The response code for the output verification
        :rtype: str
        """
        # Translate the line endings for os compatibility
        line_sep = os.linesep.encode()
        expected_list = self._get_problem_config()['output']
        self._user_output = self._user_output.replace(line_sep, b'\n')

        self._log.debug('Checking output against %s solutions' %
                        len(expected_list))

        accepted = False
        expected = None
        for expected in expected_list:
            expected = expected.encode().replace(line_sep, b'\n')
            message = 'output="{output}", expected="{expected}"'.format(
                output=self._user_output, expected=expected
            )
            self._log.debug(message)
            if self._user_output == expected:
                self._log.debug('Answer accepted.')
                accepted = True
                break
            self._log.debug('Answer not accepted.')

        if accepted is False:
            message = ('Output Mismatch! output="{output}", '
                       'expected="{expected}"').format(
                output=self._user_output, expected=expected
            )
            self._log.debug(message)
            verdict = enums.ProblemResponses.WRONG_ANSWER
        else:
            verdict = enums.ProblemResponses.ACCEPTED

        self._user_result_code = verdict

    def _save_user_file(self, request):
        """Persists users uploaded file to the temp working directory.
        """
        user_file = request.files[list(request.files.keys())[0]]
        new_path = os.path.join(self._temp_work_dir, user_file.filename)
        user_file.save(new_path)
        return new_path

    def _create_temp_work_dir(self):
        """Creates the temporary work directory.
        """
        base = self._config.get('work_directory')
        if not base:
            raise errors.MissingConfigEntryError('work_directory')

        working = True
        path = ''
        while working:
            path = base + os.sep + self._gen_random_string()

            if not os.path.exists(path):
                os.makedirs(path)
                working = False

        self._temp_work_dir = path

    @staticmethod
    def _gen_random_string(length=20):
        """Generates a random string of ascii letters.

        :return: A random string of the specified length of upper and lower
                 case letters
        :rtype: str
        """
        return ''.join(choice(ascii_letters) for _ in range(length))

    def _remove_temp_work_dir(self):
        """Removes the temporary working directory
        """
        if self._temp_work_dir:
            shutil.rmtree(self._temp_work_dir)
            self._temp_work_dir = None

    def _get_compiler(self):
        """Gets the path to the compiler / interpreter.

        :return: The path to the users selected compiler / interpreter and
                 the configured args array.
        :rtype: tuple
        """
        lang_details = self._config.get('languages', {}).get(self.language, {})
        compiler = lang_details.get('compiler')
        args = lang_details.get('compiler_args')

        self._log.debug('Mapped {lang} to {compiler}.'.format(
            lang=self.language, compiler=compiler
        ))
        return compiler, args

    def _get_problem_config(self):
        """Gets the configuration for this objects corresponding problem.

        :return: The configuration for the users selected problem
        :rtype: dict
        """
        return utilities.get_problem_config(self._config, self._problem_id)


class PythonProblemWorker(ProblemWorker):

    def _build_run_command(self, user_file_path):
        compiler, _ = self._get_compiler()
        return [compiler, user_file_path]

    def _compile(self, user_file_path):
        """Compiles the submission for the users language.

        NO-OP: Python is interpreted
        """
        pass


class CSharpProblemWorker(ProblemWorker):

    def _build_run_command(self, user_file_path):
        exe_file_path = ''.join([user_file_path.rsplit('.', 1)[0], '.exe'])
        args = [exe_file_path]
        return args

    def _compile(self, user_file_path):
        """Compiles the submission for the users language.
        """
        exe_file_path = ''.join([user_file_path.rsplit('.', 1)[0], '.exe'])
        compiler, args = self._get_compiler()
        cmd_args = [compiler, ''.join(['/out:', exe_file_path])]
        cmd_args.extend(args)
        cmd_args.append(user_file_path)
        self._execute_command(cmd_args)


class NotImplementedProblemWorker(ProblemWorker):
    def _build_run_command(self, user_file_path):
        pass

    def _compile(self, user_file_path):
        pass

    def test(self, request):
        """Runs the users submission against all test cases

        :param request: The http request containing the users submission
        :return: A ProblemResponseBuilder for the verdict
        :rtype: ProblemResponseBuilder
        """
        return ProblemResponseBuilder(
            code=enums.ProblemResponses.SUBMISSION_ERROR,
            description='Problem Worker for language not implemented.'
        )
