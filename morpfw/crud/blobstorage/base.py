import typing
from webob.dec import wsgify
from webob import exc
from webob.response import Response
from webob.static import FileIter
import os
BLOCK_SIZE = 1 << 16


class Blob(object):
    def __init__(self, uuid, filename, mimetype=None, size=None, encoding=None):
        self.uuid = uuid
        self.size = size
        self.filename = filename
        self.mimetype = mimetype
        self.encoding = encoding

    def open(self) -> typing.BinaryIO:
        raise NotImplementedError

    def get_size(self) -> int:
        return self.size

    @wsgify
    def __call__(self, req):
        if req.method not in ('GET', 'HEAD'):
            return exc.HTTPMethodNotAllowed("You cannot %s a file" %
                                            req.method)

        try:
            file = self.open()
        except (IOError, OSError) as e:
            msg = "You are not permitted to view this file (%s)" % e
            return exc.HTTPForbidden(msg)

        if 'wsgi.file_wrapper' in req.environ:
            app_iter = req.environ['wsgi.file_wrapper'](file, BLOCK_SIZE)
        else:
            app_iter = FileIter(file)

        return Response(
            app_iter=app_iter,
            content_length=self.get_size(),
            content_type=self.mimetype,
            content_encoding=self.encoding
            # @@ etag
        ).conditional_response_app


class BlobStorage(object):

    def get(self, uuid: str) -> Blob:
        raise NotImplementedError

    def put(self, fileobj: typing.BinaryIO,
            filename: str, mimetype: typing.Optional[str] = None,
            size: typing.Optional[int] = None,
            encoding: typing.Optional[str] = None) -> Blob:
        raise NotImplementedError

    def delete(self, uuid: str):
        raise NotImplementedError