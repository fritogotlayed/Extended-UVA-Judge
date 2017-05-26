from extended_uva_judge import errors, enums, utilities
from subprocess import TimeoutExpired, PIPE, Popen
from random import choice
from string import ascii_letters
from concurrent.futures import ThreadPoolExecutor

import os
import shutil
import logging
import json
import time
import abc


class ProblemResponseBuilder:
    def __init__(self, code, description=None):
        self.code = code
        self.description = description

    def build_response(self):
        response_body = {
            'code': self.code,
            'message': self.MESSAGE_MAP.get(self.code)
        }
        if self.description is not None:
            response_body['description'] = self.description

        return json.dumps(response_body)

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


class Languages:
    PYTHON2 = 'python2'
    PYTHON3 = 'python3'
    C_SHARP = 'c_sharp'
    JAVA = 'java'

    _lang_map = {
        PYTHON2: PYTHON2,
        'python': PYTHON2,
        'py2': PYTHON2,
        PYTHON3: PYTHON3,
        'py3': PYTHON3,
        C_SHARP: C_SHARP,
        'csharp': C_SHARP,
        'cs': C_SHARP,
        JAVA: JAVA
    }

    def __init__(self):
        raise NotImplementedError

    @staticmethod
    def map_language(language):
        val = Languages._lang_map.get(language)
        if val is None:
            raise errors.UnsupportedLanguageError(language)
        return val

    @staticmethod
    def get_all_languages(lang_filter=None):
        languages = {}
        for key in Languages._lang_map.keys():
            normalized_key = Languages.map_language(key)
            if lang_filter is None or normalized_key in lang_filter:
                if languages.get(normalized_key) is None:
                    languages[normalized_key] = []
                languages[normalized_key].append(key)

        return languages


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

        if lang == Languages.PYTHON2 or lang == Languages.PYTHON3:
            worker = PythonProblemWorker(*args)
        elif lang == Languages.C_SHARP:
            worker = CSharpProblemWorker(*args)
        else:
            raise NotImplementedError()

        logging.debug('Mapped {lang} to {worker}.'.format(
            lang=lang, worker=worker.__class__.__name__))
        return worker

    @staticmethod
    def _normalize_language(language):
        mapped_lang = Languages.map_language(language)
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
        self._child_threads = []
        self._run_command = None
        self._test_result = None

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
            self._compile(user_file_path)
            self._run_command = self._build_run_command(user_file_path)
            self._execute_test_runs()
            self._aggregate_run_results()
        except RuntimeError:
            self._test_result = ProblemResponseBuilder(
                enums.ProblemResponses.RUNTIME_ERROR)

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

    def _execute_test_runs(self):
        """Executes the various test runs based on the specified problem id.
        """
        available_runs = self._get_problem_config()['runs']
        max_workers = int(self._config['max_submission_workers'])
        pool = ThreadPoolExecutor(max_workers=max_workers)

        for run in available_runs:
            self._child_threads.append(
                pool.submit(self._execute_run_and_verify_output,
                            run))

    def _aggregate_run_results(self):
        """Aggregates the various test runs and sets the test result
        """
        accepted_results = [
            enums.ProblemResponses.ACCEPTED,
            enums.ProblemResponses.ACCEPTED_PRESENTATION_ERROR
        ]

        try:
            result_code = enums.ProblemResponses.ACCEPTED
            for child in self._child_threads:
                code = child.result()
                if code == enums.ProblemResponses.ACCEPTED_PRESENTATION_ERROR:
                    result_code = code
                elif code not in accepted_results:
                    result_code = code
                    break
        except TimeoutExpired:
            result_code = enums.ProblemResponses.TIME_LIMIT_EXCEEDED

        self._test_result = ProblemResponseBuilder(result_code)

    def _execute_run_and_verify_output(self, run):
        """

        :param run: the run to acquire arguments from
        :return: The response code for the output verification
        :rtype: str
        """
        output = self._execute_run(run)
        code = self._verify_output(run, output)
        return code

    def _execute_run(self, run):
        """Executes the users application with the run arguments.

        :param run: the run to acquire arguments from
        :return: The output from the users program
        :rtype: str
        """
        program_input = run['input'].encode()
        timeout = float(self._get_problem_config()['time_limit'])

        return_code, stdout, stderr = self._execute_command(
            self._run_command, cmd_input=program_input, timeout=timeout)

        if return_code != 0:
            self._log.debug(
                'Problem with test...\nStandard Output: {out}\n'
                'Standard Error: {err}\nReturn Code:{code}'.format(
                    out=stdout, err=stderr, code=return_code))
            raise RuntimeError(stderr)

        return stdout

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

    def _verify_output(self, run, output):
        """Verifies the provided output against the expected output in the run

        :param run: The run to verify against
        :param output: the output to verify
        :return: The response code for the output verification
        :rtype: str
        """
        # Translate the line endings for os compatibility
        line_sep = os.linesep.encode()
        expected = run['output'].encode().replace(line_sep, b'\n')
        output = output.replace(line_sep, b'\n')
        run['user_output'] = output

        verdict = enums.ProblemResponses.ACCEPTED
        if output != expected:
            template = ('Output Mismatch! output="{output}", '
                        'expected="{expected}"')
            self._log.debug(template.format(output=output, expected=expected))
            verdict = enums.ProblemResponses.WRONG_ANSWER

        run['verdict'] = verdict
        return verdict

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
            # Make sure all of the child threads are done before we clean up
            # the temp folder.
            for child in self._child_threads:
                while not child.done():
                    time.sleep(0.25)

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
        args = [compiler,
                ''.join(['/out:', exe_file_path]),
                *args,
                user_file_path]
        self._execute_command(args)
