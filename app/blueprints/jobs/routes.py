from flask import Blueprint, jsonify, send_file
import os
from app import utils

bp = Blueprint('jobs', __name__)


@bp.route('/status/<jobid>')
def job_status(jobid):
    job = utils.read_job(jobid)
    if job is None:
        return jsonify({'status': 'not_found'}), 404
    return jsonify({'status': job.get('status'), 'error': job.get('error')})


@bp.route('/result/<jobid>')
def job_result(jobid):
    job = utils.read_job(jobid)
    if job is None:
        return jsonify({'error': 'not_found'}), 404
    if job.get('status') != 'done':
        return jsonify({'status': job.get('status')}), 202
    return jsonify({'status': 'done', 'result': job.get('result')})
