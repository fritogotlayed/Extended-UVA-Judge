import logging
from flask import Blueprint, jsonify, current_app, request, Response, redirect
from flask import url_for
from extended_uva_judge import errors, enums, utilities, languages as langs,\
    problems as probs
from extended_uva_judge.objects import ProblemWorkerFactory, \
    ProblemResponseBuilder


mod = Blueprint('api', __name__, url_prefix='/api/v1')


@mod.route('/problem/<problem_id>/<lang>/test', methods=['POST'])
def test(problem_id, lang):
    output = _validate_submission_request(problem_id, lang)
    status_code = 400

    try:
        if output is None:
            with ProblemWorkerFactory.create_worker(
                    lang, problem_id) as worker:
                output = worker.test(request)
                status_code = 200
    except NotImplementedError as ex:
        logging.warning('Failure to run problem worker.', exc_info=ex)
        output = ProblemResponseBuilder(
            code=enums.ProblemResponses.SUBMISSION_ERROR,
            description='Problem Worker for language not implemented.'
        )

    output.debug = request.args.get('debug', False)

    return Response(output.build_response(),
                    status=status_code,
                    mimetype='application/json')


@mod.route('/available_problems', methods=['GET'])
def available_problems():
    return redirect(url_for('api.problems'))


@mod.route('/available_languages', methods=['GET'])
def available_languages():
    return redirect(url_for('api.languages'))


@mod.route('/problems', methods=['GET'])
def problems():
    config = current_app.app_config

    return jsonify({'problems': probs.get_available_problems(config)})


@mod.route('/languages', methods=['GET'])
def languages():
    config = current_app.app_config
    lang_configs = config.get('languages')
    configured_keys = list(lang_configs.keys())

    return jsonify({'languages': langs.get_all_languages(configured_keys)})


def _allowed_file(filename, language):
    config = current_app.app_config
    lang = langs.map_language(language)
    lang_configs = config.get('languages')
    allowed_extensions = lang_configs.get(lang, {}).get('file_extensions', [])
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions)


def _validate_submission_request(problem_id, lang):
    code = None
    message = None

    if not request.files:
        code = enums.ProblemResponses.SUBMISSION_ERROR
        message = 'File not found.'
    elif len(request.files) != 1:
        code = enums.ProblemResponses.SUBMISSION_ERROR
        message = 'Too many files.'
    elif utilities.does_problem_config_exist(
            current_app.app_config, problem_id) is False:
        code = enums.ProblemResponses.SUBMISSION_ERROR
        message = 'Could not find problem configuration on this judge.'
    else:
        try:
            for filename in request.files.keys():
                if not _allowed_file(filename, lang):
                    code = enums.ProblemResponses.SUBMISSION_ERROR
                    message = 'Invalid file type.'
        except errors.UnsupportedLanguageError:
            code = enums.ProblemResponses.SUBMISSION_ERROR
            message = 'Unsupported language. Please GET /available_languages'

    return None if code is None else ProblemResponseBuilder(code, message)
