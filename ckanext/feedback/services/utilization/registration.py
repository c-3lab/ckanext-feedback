from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import Utilization


# Create new utilization
def create_utilization(resource_id, title, url, description):
    utilization = Utilization(
        resource_id=resource_id,
        title=title,
        url=url,
        description=description,
    )
    session.add(utilization)
    return utilization
