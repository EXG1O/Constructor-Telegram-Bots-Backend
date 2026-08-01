from rest_framework.routers import DynamicRoute, Route, SimpleRouter


class DetailRouter(SimpleRouter):
    routes = [
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={'get': 'list', 'post': 'create'},
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'},
        ),
        DynamicRoute(
            url=r'^{prefix}/{url_path}{trailing_slash}$',
            name='{basename}-{url_name}',
            detail=False,
            initkwargs={},
        ),
        Route(
            url=r'^{prefix}/me{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy',
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'},
        ),
        DynamicRoute(
            url=r'^{prefix}/me/{url_path}{trailing_slash}$',
            name='{basename}-{url_name}',
            detail=True,
            initkwargs={},
        ),
    ]
