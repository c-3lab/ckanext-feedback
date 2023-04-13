import pytest
import six
import uuid
from ckan import model
from ckan.tests import factories
from flask import request,Flask
from datetime import datetime

from ckanext.feedback.command.feedback import (
    create_download_tables,
    create_resource_tables,
    create_utilization_tables,
    get_engine,
)
from ckanext.feedback.controllers.utilization import UtilizationController
from ckanext.feedback.models.session import session
from ckanext.feedback.models.utilization import (
    Utilization,
    UtilizationComment,
    UtilizationCommentCategory,
)

def register_utilization(id,resource_id,title,description,approval):
        utilization = Utilization(
            id=id,
            resource_id=resource_id,
            title=title,
            description=description,
            approval=approval
        )
        session.add(utilization)

def get_registered_utilization(resource_id):
    return (
        session.query(
            Utilization.id,
            Utilization.approval,
            Utilization.approved,
            Utilization.approval_user_id,
        )
        .filter(Utilization.resource_id == resource_id)
        .first()
    )

def register_utilization_comment(id,utilization_id,category,content,created,approval,approved,approval_user_id):
        utilization_comment = UtilizationComment(
            id=id,
            utilization_id=utilization_id,
            category=category,
            content=content,
            created=created,
            approval=approval,
            approved=approved,
            approval_user_id=approval_user_id
        )
        session.add(utilization_comment)

def get_registered_utilization_comment(utilization_id):
    return (
        session.query(
            UtilizationComment.id,
            UtilizationComment.utilization_id,
            UtilizationComment.category,
            UtilizationComment.content,
            UtilizationComment.approval,
            UtilizationComment.approved,
            UtilizationComment.approval_user_id,
        )
        .filter(UtilizationComment.utilization_id == utilization_id)
        .all()
    )

def convert_utilization_comment_to_tuple(utilization_comment):
    return (
        utilization_comment.utilization_id,
        utilization_comment.category,
        utilization_comment.content,
        utilization_comment.approval,
        utilization_comment.approved,
        utilization_comment.approval_user_id,
    )

@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestUtilizationController:

    @classmethod
    def setup_class(cls):
        model.repo.init_db()
        engine = get_engine('db', '5432', 'ckan_test', 'ckan', 'ckan')
        create_utilization_tables(engine)
        create_resource_tables(engine)
        create_download_tables(engine)

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve(self,app):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id,resource['id'],title,description,False)
        utilization_before_approved = get_registered_utilization(resource['id'])

        self.app = Flask(__name__)
        user_env = {'REMOTE_USER': six.ensure_str(user['name'])}
        with self.app.test_request_context():
            response = app.post(
                url='utilization/'+utilization_before_approved.id+'/approve',
                extra_environ=user_env,
                data={
                    'utilization_id':utilization_before_approved.id
                }
            )
        utilization_after_approved = get_registered_utilization(resource['id'])
        fake_utilization = (id,True,datetime.now(),user['id'])

        assert response.status == '200 OK'
        assert utilization_after_approved == fake_utilization

    def test_create_comment(self,app):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(id,resource['id'],title,description,False)
        utilization = get_registered_utilization(resource['id'])

        self.app = Flask(__name__)
        user_env = {'REMOTE_USER': six.ensure_str(user['name'])}
        content = 'test content'
        with self.app.test_request_context():
            response = app.post(
                url='utilization/'+utilization.id+'/comment/new',
                extra_environ=user_env,
                data={
                    'utilization_id':utilization.id,
                    'category':UtilizationCommentCategory.REQUEST.name,
                    'content':content
                }
            )
        utilization_comments = get_registered_utilization_comment(utilization.id)
        assert response.status == '200 OK'
        assert len(utilization_comments) == 1
        
        registered_utilization_comment = convert_utilization_comment_to_tuple(utilization_comments[0])
        fake_utilization_comment = (id,UtilizationCommentCategory.REQUEST,content,False,None,None)
        assert registered_utilization_comment == fake_utilization_comment

    @pytest.mark.freeze_time(datetime(2000, 1, 2, 3, 4))
    def test_approve_comment(self,app):
        dataset = factories.Dataset()
        user = factories.User()
        resource = factories.Resource(package_id=dataset['id'])

        utilization_id = str(uuid.uuid4())
        title = 'test title'
        description = 'test description'
        register_utilization(utilization_id,resource['id'],title,description,False)
        utilization = get_registered_utilization(resource['id'])

        comment_id = str(uuid.uuid4())
        category = UtilizationCommentCategory.REQUEST
        content = 'test content'
        created = datetime.now()
        
        register_utilization_comment(comment_id,utilization.id,category,content,created,False,None,None)
        utilization_comments = get_registered_utilization_comment(utilization.id)
        comment_not_approved = utilization_comments[0]
        assert comment_not_approved.approval == False

        self.app = Flask(__name__)
        user_env = {'REMOTE_USER': six.ensure_str(user['name'])}
        content = 'test content'
        with self.app.test_request_context():
            response = app.post(
                url='utilization/'+utilization.id+'/comment/'+comment_not_approved.id+'/approve',
                extra_environ=user_env,
                data={
                    'utilization_id':utilization.id,
                    'comment_id':comment_not_approved.id,
                }
            )
        utilization_comments = get_registered_utilization_comment(utilization.id)
        comment_approved = utilization_comments[0]
        assert response.status == '200 OK'
        
        tuple_comment_approved = convert_utilization_comment_to_tuple(comment_approved)
        fake_utilization_comment = (utilization.id,category,content,True,datetime.now(),user['id'])
        assert tuple_comment_approved == fake_utilization_comment