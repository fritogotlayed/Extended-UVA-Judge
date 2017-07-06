from flask import Blueprint, jsonify, current_app, request, Response, redirect
from flask import url_for
from extended_uva_judge import errors, enums, utilities, languages, problems
from extended_uva_judge.objects import ProblemWorkerFactory, \
    ProblemResponseBuilder


mod = Blueprint('api', __name__, url_prefix='/api/v1')


@mod.route('/problem/<problem_id>/<lang>/test', methods=['POST'])
def test(problem_id, lang):
    output = _validate_submission_request(problem_id, lang)

    if output is None:
        with ProblemWorkerFactory.create_worker(
                lang, problem_id, request.args.get('debug', False)) as worker:
            output = worker.test(request)

    return Response(output.build_response(),
                    status=200 if output.code != 'SE' else 400,
                    mimetype='application/json')


@mod.route('/available_problems', methods=['GET'])
def available_problems():
    return redirect(url_for('api.problems'))


@mod.route('/available_languages', methods=['GET'])
def available_languages():
    return redirect(url_for('api.languages'))


@mod.route('/problems', methods=['GET'])
def get_problems():
    config = current_app.app_config

    return jsonify({'problems': problems.get_available_problems(config)})


@mod.route('/languages', methods=['GET'])
def get_languages():
    config = current_app.app_config
    lang_configs = config.get('languages')
    configured_keys = list(lang_configs.keys())

    return jsonify({'languages': languages.get_all_languages(configured_keys)})


def _allowed_file(filename, language):
    config = current_app.app_config
    lang = languages.map_language(language)
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
            message = ('Unsupported language. Please GET ' +
                       url_for('api.get_problems'))

    return None if code is None else ProblemResponseBuilder(code, message)
