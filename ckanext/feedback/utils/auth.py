from ckan.lib import api_token as api_token_lib
from ckan.plugins import toolkit


def create_auth_context():
    """
    Create standard context for CKAN authorization checks.

    This context is used for checking access permissions to packages,
    resources, and other CKAN objects.

    Returns:
        dict: CKAN context with model, session, and for_view flag
    """
    import ckan.model as model

    return {'model': model, 'session': model.Session, 'for_view': True}


class AuthTokenHandler:
    @staticmethod
    def validate_api_token(api_token):
        """
        Validates the presence of the API token.

        Args:
            api_token (str): The API token to validate.

        Raises:
            toolkit.NotAuthorized: If the API token is missing.
        """
        if not api_token:
            raise toolkit.NotAuthorized("API Token is missing.")

    @staticmethod
    def decode_api_token(api_token):
        """
        Decodes the API token and returns its 'jti' (token id).

        Args:
            api_token (str): The API token to decode.

        Returns:
            str: The 'jti' (token id) extracted from the token.

        Raises:
            toolkit.NotAuthorized: If the API token is invalid.
        """
        try:
            data = api_token_lib.decode(api_token)
            return data.get("jti")
        except Exception:
            raise toolkit.NotAuthorized("Invalid API Token.")

    @staticmethod
    def check_sysadmin(user):
        """
        Checks if the user is a sysadmin.

        Args:
            user (User): The user object to check.

        Raises:
            toolkit.NotAuthorized: If the user is not a sysadmin.
        """
        if not bool(getattr(user, 'sysadmin', False)):
            raise toolkit.NotAuthorized("The user is not a sysadmin.")
