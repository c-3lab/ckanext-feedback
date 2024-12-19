from datetime import datetime

from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization


def approve_utilization(utilization_id_list, approval_user_id):
    session.bulk_update_mappings(
        Utilization,
        [
            {
                'id': utilization_id,
                'approval': True,
                'approved': datetime.now(),
                'approval_user_id': approval_user_id,
            }
            for utilization_id in utilization_id_list
        ],
    )


def delete_utilization(utilization_id_list):
    (
        session.query(Utilization)
        .filter(Utilization.id.in_(utilization_id_list))
        .delete(synchronize_session='fetch')
    )
