from flask import Blueprint, jsonify, current_app, request, Response
from extended_uva_judge import errors
from extended_uva_judge.objects import ProblemWorkerFactory


mod = Blueprint('api', __name__, url_prefix='/api/v1')


@mod.route('/problem/<problem_id>/<lang>/test', methods=['POST'])
def test(problem_id, lang):
    if not request.files:
        return jsonify({'message': 'File not found'}), 400

    if len(request.files) != 1:
        raise errors.TooManyFilesError()

    for filename in request.files.keys():
        if not allowed_file(filename):
            return jsonify({'error': 'Invalid File Type'})

    with ProblemWorkerFactory.create_worker(
            lang, problem_id, current_app.app_config) as worker:
        output = worker.test(request)

    return Response(output.build_response(),
                    status=200,
                    mimetype='application/json')


def allowed_file(filename):
    allowed_extensions = current_app.app_config.get('allowed_extensions', {})
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions)
