from flask import Blueprint, jsonify, current_app, request
from extended_uva_judge import errors
from extended_uva_judge.utility import ProblemWorker


mod = Blueprint('api', __name__, url_prefix='/api/v1')

ALLOWED_EXTENSIONS = {'py'}


@mod.route('/problem/<problem_id>/<lang>/test', methods=['POST'])
def test(problem_id, lang):
    if not request.files:
        return jsonify({'message': 'File not found'}), 400

    if len(request.files) != 1:
        raise errors.TooManyFilesError()

    for filename in request.files.keys():
        if not allowed_file(filename):
            return jsonify({'error': 'Invalid File Type'})

    worker = ProblemWorker(lang, problem_id, current_app.app_config)
    output = worker.test(request)

    return jsonify({'output': output}), 200


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
