class Route():
    """Route类是对path, method, callback的封装，每次请求到达时，路由器router函数根据请求的路径，返回对应的Route对象
    """

    def __init__(self, app, method, path, callback):
        #: 这个路由关联的MiniBottle实例
        self.app = app
        #: 静态路由字符串 (例： “/wiki” ).
        self.path = path
        #: HTTP请求method字符串 (e.g. ``GET``).
        self.method = method
        # callback即用户使用框架定义的回调函数，下面例子中的hello函数
        # @route('/hello')
        # def hello():
        #     return "Hello World!"
        self.callback = callback

    def call(self):
        return self.callback()


class AppClass():
    def __init__(self):
        self.routes = []  # routes属性存储当前实例的路由

    def __call__(self, environ, start_response):
        """ 每个MiniBottle类都是一个WSGI application. """
        return self.wsgi(environ, start_response)

    def wsgi(self, environ, start_response):
        """wsgi 接口"""
        path = environ['PATH_INFO']
        target_route = self.router(path)
        out = target_route.call()
        start_response(
            '200 OK', [('Content-Type', 'text/plain; charset=utf-8')])
        return out

    def route(self, path, method="GET"):
        """一个路由装饰器，将用户定义的callback函数封装，
            具体应用如下：

            @app.route('\hello')
            def hello(self):
        """
        def decorator(callback):
            # callback = route(self, path)(callback)
            print(f'添加回调函数{callback}到self.routes')
            # 初始化一个Route实例，然后添加到self的routes属性(list)
            route = Route(self, method, path, callback)
            self.routes.append(route)
            return callback
        return decorator

    def router(self, path, method="GET"):
        """路由器,根据请求的静态路径和方法，返回对应的Route对象"""
        for route in self.routes:
            if route.path == path and route.method == method:
                return route


class WSGIRefServer():

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port

    def run(self, app):
        from wsgiref.simple_server import make_server
        from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
        self.server = make_server(self.host, self.port, app, server_class=WSGIServer,
                                  handler_class=WSGIRequestHandler)
        print(f'{self.host} Serving HTTP on port {self.port}...')
        try:
            self.server.serve_forever()  # 程序将在这里阻塞，不停处理http请求
        except KeyboardInterrupt:  # 如果运行时键盘按ctrl+s将会终止程序
            self.server.server_close()


if __name__ == "__main__":

    app = AppClass()  # 实例化一个应用

    @app.route('/')
    def index():
        return [b'index']
    # @app.route('/')等价于在这一行执行：hello = app.route('/')(index)。具体请查看python装饰器的知识

    @app.route('/hello')
    def hello():
        return [b'hello']

    @app.route('/world')
    def index():
        return [b'world']

    @app.route('/nihao')
    def helloworld():
        out1 = '你好'.encode('utf-8')
        out2 = '世界'.encode('utf-8')
        return [out1, out2]

    wsgiServer = WSGIRefServer()  # 创建一个实例对象
    wsgiServer.run(app)  # 调用对象的run方法。
