from flask import request

def set_like_status_cookie(resp,resource_id,like_status):
    if like_status not in ["True","False"]:
        raise ValueError("like_status must be 'True' or 'False'")
    resp.set_cookie(f'like_status_{resource_id}', f'{like_status}', max_age=2147483647)
    return resp

def set_repeat_post_limit_cookie(resp,resource_id):
    resp.set_cookie(f'repeat_post_limit_{resource_id}', 'alreadyPosted', max_age=2147483647)
    return resp


def get_like_status_cookie(resource_id):
    return request.cookies.get(f'like_status_{resource_id}')


def get_repeat_post_limit_cookie(resource_id):
    return request.cookies.get(f'repeat_post_limit_{resource_id}')
