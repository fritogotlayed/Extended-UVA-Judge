from extended_uva_judge import errors, enums
from subprocess import STDOUT, check_output
from random import choice
from string import ascii_letters
from concurrent.futures import ThreadPoolExecutor

import os
import shutil
import yaml
import logging
import json
import time

_lang_map = {
    'python': 'python2',
    'python2': 'python2',
    'py2': 'python2',
    'python3': 'python3',
    'py3': 'python3'
}


class ProblemResponseBuilder:
    def __init__(self, code):
        self.code = code

    def build_response(self):
        return json.dumps({
            'code': self.code,
            'message': self.MESSAGE_MAP.get(self.code)
        })

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


class ProblemWorker:
    def __init__(self, lang, problem_id, config):
        self._lang = lang
        self._problem_id = problem_id
        self._config = config  # type: dict
        self._log = logging.getLogger()
        self._temp_work_dir = None
        self._child_threads = []

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
        self._create_temp_work_dir()
        new_path = self._save_user_file(request)
        problem_config = self._get_problem_config()
        base_cmd_and_args = [self._get_compiler(), new_path]

        available_runs = problem_config['runs']
        pool = ThreadPoolExecutor(max_workers=len(available_runs))
        for run in available_runs:
            self._child_threads.append(
                pool.submit(self._execute_run_and_verify_output,
                            base_cmd_and_args,
                            run))

        accepted_results = [
            enums.ProblemResponses.ACCEPTED,
            enums.ProblemResponses.ACCEPTED_PRESENTATION_ERROR
        ]
        result_code = enums.ProblemResponses.ACCEPTED
        for child in self._child_threads:
            code = child.result()
            if code == enums.ProblemResponses.ACCEPTED_PRESENTATION_ERROR:
                result_code = code
            elif code not in accepted_results:
                result_code = code
                break

        return ProblemResponseBuilder(result_code)

    def _execute_run_and_verify_output(self, base_cmd_and_args, run):
        """
        
        :param base_cmd_and_args: The command to run the users application
        :param run: the run to acquire arguments from
        :return: The response code for the output verification
        :rtype: str
        """
        output = self._execute_run(base_cmd_and_args, run)
        code = self._verify_output(run, output)
        return code

    def _execute_run(self, base_cmd_and_args, run):
        """Executes the users application with the run arguments.

        :param base_cmd_and_args: The command to run the users application
        :param run: the run to acquire arguments from
        :return: The output from the users program
        :rtype: str
        """
        program_input = run['input']

        cmd_and_args = list(base_cmd_and_args)
        cmd_and_args.extend(program_input.split(' '))

        self._log.debug(cmd_and_args)
        output = check_output(
            cmd_and_args, cwd=self._temp_work_dir,
            stderr=STDOUT, timeout=3)

        return output

    def _verify_output(self, run, output):
        """Verifies the provided output against the expected output in the run

        :param run: The run to verify against
        :param output: the output to verify
        :return: The response code for the output verification
        :rtype: str
        """
        expected = run['output'].encode()

        # If running PyCharm debugger, remove extra prepended lines
        line_sep = os.linesep.encode()
        if output.startswith(b'pydev debugger: '):
            first_line_index = output.index(line_sep)
            output = output[first_line_index + len(line_sep) * 2:]

        # Translate the expected output line endings for os compatibility
        output = output.replace(line_sep, b'\n')

        if output != expected:
            template = ('Output Mismatch! output="{output}", '
                        'expected="{expected}"')
            self._log.debug(template.format(output=output, expected=expected))
            return enums.ProblemResponses.WRONG_ANSWER

        return enums.ProblemResponses.ACCEPTED

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

    def _get_lang(self):
        """Gets the normalized programming language.

        :return: The normalized programming language.
        :rtype: str
        """
        lang = self._lang
        mapped_lang = _lang_map.get(lang)
        self._log.debug('Mapped language {input} to {output}.'.format(
            input=lang, output=mapped_lang))
        return mapped_lang

    def _get_compiler(self):
        """Gets the path to the compiler / interpreter.

        :return: The path to the users selected compiler / interpreter.
        :rtype: str
        """
        lang = self._get_lang()
        lang_details = self._config.get('languages', {}).get(lang, {})
        compiler = lang_details.get('compiler')

        self._log.debug('Mapped {lang} to {compiler}.'.format(
            lang=lang, compiler=compiler
        ))
        return compiler

    def _get_problem_directory(self):
        """Gets the directory containing the problem configs.

        :return: The path to the problem configs.
        :rtype: str
        """
        problem_directory = self._config['problem_directory']

        if not problem_directory:
            raise errors.MissingConfigEntryError('problem_directory')

        # Check for full windows or *nix directory path
        if not (problem_directory.startswith('/') or ':' in problem_directory):
            # assume it's relative to the current working directory
            problem_directory = os.path.join(os.getcwd(), problem_directory)
        return problem_directory

    def _get_problem_config(self):
        """Gets the configuration for this objects corresponding problem.

        :return: The configuration for the users selected problem
        :rtype: dict
        """
        problem_directory = self._get_problem_directory()

        problem_config_path = os.path.join(
            problem_directory, '%s.yaml' % self._problem_id)
        problem_config = yaml.load(open(problem_config_path))
        return problem_config
