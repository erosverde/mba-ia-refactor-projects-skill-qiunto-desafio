from flask import Blueprint
from controllers import report_controller as controller


report_bp = Blueprint('reports', __name__)
report_bp.add_url_rule('/reports/summary', 'summary_report', controller.summary_report, methods=['GET'])
report_bp.add_url_rule('/reports/user/<int:user_id>', 'user_report', controller.user_report, methods=['GET'])
report_bp.add_url_rule('/categories', 'get_categories', controller.get_categories, methods=['GET'])
report_bp.add_url_rule('/categories', 'create_category', controller.create_category, methods=['POST'])
report_bp.add_url_rule('/categories/<int:cat_id>', 'update_category', controller.update_category, methods=['PUT'])
report_bp.add_url_rule('/categories/<int:cat_id>', 'delete_category', controller.delete_category, methods=['DELETE'])
