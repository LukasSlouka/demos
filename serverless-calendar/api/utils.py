from flask import (
    Flask,
    Request,
)
from werkzeug.datastructures import Headers


def cloud_function_entry_point(flask_app: Flask, api_request: Request):
    """Should be an entry point of all HTTP triggered cloud functions.

    This function takes flask application and ensures valid routing in between
    cloud function routes by creating request context, preprocessing and
    dispatching the request.

    :param flask_app: flask application
    :param api_request: http request
    :return:
    """
    with flask_app.app_context():

        # construct headers
        headers = Headers()
        for key, value in api_request.headers.items():
            headers.add(key, value)

        # prepare content
        content = {}
        if headers.get('content-type') == 'application/json':
            content['json'] = api_request.get_json(silent=True)
        else:
            content['data'] = api_request.form

        with flask_app.test_request_context(
                method=api_request.method,
                base_url=api_request.base_url,
                path=api_request.path,
                query_string=api_request.query_string,
                headers=headers,
                **content
        ):
            try:
                rv = flask_app.preprocess_request()
                if rv is None:
                    rv = flask_app.dispatch_request()
            except Exception as e:
                rv = flask_app.handle_user_exception(e)
            response = flask_app.make_response(rv)
            return flask_app.process_response(response)
