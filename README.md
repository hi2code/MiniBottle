# MiniBottle

参考[Bottle框架](https://github.com/bottlepy/bottle)，从0到1实现简单的wsgi应用框架MiniBottle。

阅读本教程前，需要了解基础的python语法和HTTP协议。

每节的代码都可以直接运行的，下一节代码是在上节基础上进行修改，建议参考代码注释动手输入，不要直接复制粘贴

##  WSGI简介

### 简介

**什么是接口？**

生活中的插座就是一种接口，供电端和用电端通过插座连接。使用时把电器的插头插入插座就可以，而不是直接把它连接到导线上。

出现插座是为了将供电端和用电端分离，使得两端可以更加专注，使用更加容易：

- 供电端：负责将电提供到插座上，无需关心是哪个电器在用电
- 用电端：使用时把电器的插头插入插座就可以，就无需关心供电端是如何供电的

**什么是WSGI接口？**

Python Web服务器网关接口（Python Web Server Gateway Interface）是为Web服务器和Web应用程序或框架之间的定义的一种简单而通用的接口，具体可参考[PEP3333_Python Web Server Gateway Interface v1.0.1](https://www.python.org/dev/peps/pep-3333/)

WSGI接口将HTTP网络请求分为两边，服务器端调用应用程序端。

```
wsgi server <-----wsgi接口------> wsgi application
```

- 一边是服务器server（又名网关gateway端）：服务端负责处理http请求和返回。

- 另一边是应用端application（又名框架framework端）：应用端只需要调用服务端的wsgi的接口，负责生成返回内容就可以了。

### **应用端**

应用端（application objects）是一个接受两个参数（environ, start_response）的可调用对象（callable object）。

下面用函数实现hello world应用端：

```python
def demo_app(environ, start_response):
    # environ是包含http请求的所有参数的字典dict
    # start_response是一个用来返回http响应头部的函数
    start_response("200 OK", [('Content-Type', 'text/plain; charset=utf-8')]) 
    return [b'<h1>Hello, world!</h1>'] # 返回一个可迭代iterable对象，这个对象会作为http响应的消息体body
```

函数接受了两个参数：

- environ：http请求的所有参数
- start_response：一个用来返回http响应的函数

> 注：应用端对象（application objects）不只有函数function,这一种， 还可以是：实现`__iter__`方法的类，或有`__call__`方法的实例。每次http请求，服务端都会调用应用端对象。

### **服务端**

服务端针对每次http请求，都会调用一次应用端（application object）

```python
demo_app(environ, start_response):
```

传给demo_app函数两个参数：

- environ：http请求的所有参数
- start_response：一个用来返回http响应的函数

**python内置的服务端wsgiref**

python内置了一个的wsgi服务端wsigref，我们把我们的demo_app在wsgi服务器上启动，浏览器访问http://localhost:8080可以看到hello world。

```PYTHON
from wsgiref.simple_server import make_server

def demo_app(environ, start_response):
    start_response("200 OK", [('Content-Type', 'text/plain; charset=utf-8')])
    return [b'<h1>Hello, world!</h1>'] # 返回一个可迭代iterable对象

if __name__ == '__main__':
    with make_server('', 8080, demo_app) as httpd:
        httpd.serve_forever() # 一直处理请求
```

**[wsgiref.simple_server官方文档](https://docs.python.org/3/library/wsgiref.html#module-wsgiref.simple_server)**

**可以暂时跳过**，后面需要用到wsgiref再回头来看

`wsgiref.simple_server.make_server(host, port, app, server_class=WSGIServer, handler_class=WSGIRequestHandler)`  - > instance of server_class

Create a new WSGI server listening on *host* and *port*, accepting connections for *app*. The return value is an instance of the supplied *server_class*, and will process requests using the specified *handler_class*. *app* must be a WSGI application object, as defined by [**PEP 3333**](https://www.python.org/dev/peps/pep-3333).

`start_response(status:str, headers:[('key1', 'value1'),('key2','value2')])`

**实现一个简单的wsgi服务端的示例**

我们很少会自己实现wsgi服务器，这里给出示例。是为了学习服务端是如何调用application这个对象的。

下面是[PEP3333_Python Web Server Gateway Interface v1.0.1](https://www.python.org/dev/peps/pep-3333/)中给的服务端实现示例

```python
import os, sys

enc, esc = sys.getfilesystemencoding(), 'surrogateescape'

def unicode_to_wsgi(u):
    # Convert an environment variable to a WSGI "bytes-as-unicode" string
    return u.encode(enc, esc).decode('iso-8859-1')

def wsgi_to_bytes(s):
    return s.encode('iso-8859-1')

def run_with_cgi(application):
    environ = {k: unicode_to_wsgi(v) for k,v in os.environ.items()}
    environ['wsgi.input']        = sys.stdin.buffer
    environ['wsgi.errors']       = sys.stderr
    environ['wsgi.version']      = (1, 0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']     = True

    if environ.get('HTTPS', 'off') in ('on', '1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'

    headers_set = []
    headers_sent = []

    def write(data):
        out = sys.stdout.buffer

        if not headers_set:
             raise AssertionError("write() before start_response()")

        elif not headers_sent:
             # Before the first output, send the stored headers
             status, response_headers = headers_sent[:] = headers_set
             out.write(wsgi_to_bytes('Status: %s\r\n' % status))
             for header in response_headers:
                 out.write(wsgi_to_bytes('%s: %s\r\n' % header))
             out.write(wsgi_to_bytes('\r\n'))

        out.write(data)
        out.flush()
	
    #######start_response函数将传给应用端对象########
    def start_response(status, response_headers, exc_info=None):
        if exc_info:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                exc_info = None     # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]

        # Note: error checking on the headers should happen here,
        # *after* the headers are set.  That way, if an error
        # occurs, start_response can only be re-called with
        # exc_info set.

        return write

    #######调用应用端对象application#######
    result = application(environ, start_response)
    try:
        for data in result: #result是应用端返回的可迭代对象，迭代该对象，循环写入标准输出stdout
            if data:    # don't send headers until body appears
                write(data)
        if not headers_sent:
            write('')   # send headers now if body was empty
    finally:
        if hasattr(result, 'close'):
            result.close()
```

##  第一步：用wsgiref服务器启动一个wsgi应用

我们先实现一个最简单的wsgi应用端，并且用wsgiref启动该应用

本节实现功能：浏览器访问localhost:8080，可以看到hello world

下面是具体代码：

```python
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler


def app(environ, start_response):
    """应用端对象application object"""
    # start_response返回http响应头部，使用方法start_response(status:str, headers:[('key1', 'value1'),('key2','value2')])
    start_response(
        '200 OK', [('Content-Type', 'application/json; charset=utf-8')])
    # 返回http响应主体，wsgi接口要求，返回内容必须是一个可迭代的字节对象
    return [b'hello world']


def start_server(app):
    httpd = make_server('', 8080, app, server_class=WSGIServer,
                        handler_class=WSGIRequestHandler)
    httpd.serve_forever()


print('Serving HTTP on port 8080...')
start_server(app)
```

## 第二步：把启动服务器函数封装为类对象

启动服务器时，用户想要修改启动的端口port和主机域名host。并且还可能想要启动多个wsgi服务器监听不同的端口。所以我们把启动服务器这个过程抽象为类WSGIRefServer。

下面是具体代码：

```python
def app(environ, start_response):
    """应用端对象application object"""
    # start_response返回http响应头部，使用方法start_response(status:str, headers:[('key1', 'value1'),('key2','value2')])
    start_response(
        '200 OK', [('Content-Type', 'application/json; charset=utf-8')])
    return [b'hello world']


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
            self.server.serve_forever() # 程序将在这里阻塞，不停处理http请求
        except KeyboardInterrupt: # 如果运行时键盘按ctrl+s将会终止程序
            self.server.server_close()


if __name__ == "__main__":
    wsgiServer = WSGIRefServer()  # 创建一个WSGIRefServer实例对象
    wsgiServer.run(app)  # 调用对象的run方法。启动wsgiref服务器
```

## 第三步：用类对象实现应用端

上节中：我们定义了一个app(environ, start_response)函数，作为应用端对象，函数不方便拓展功能

本节中：我们用类对象实现应用端，类可以更好的实现拓展。

wsgi服务端内部将如下面的方式调用application对象

```python
result = application(environ, start_response) #先调用application对象，下一行开始迭代调用返回的对象
for data in result: #result是应用端返回的可迭代对象，迭代该对象，循环写入标准输出stdout
	if data:    # don't send headers until body appears
  	   write(data)
```

所以如果要用类的实例作为application，需要实现`__call__`方法。

假如我们的实例对象叫`app`，当执行`app()`时，本质上是调用的这个`app.__call__()`

下面是具体代码：

```PYTHON
class AppClass():
    def __init__(self):
        pass

    def __call__(self, environ, start_response):
        """调用AppClass的实例时，将调用该方法"""
        start_response(
            '200 OK', [('Content-Type', 'text/plain; charset=utf-8')])
        return [b'hello world']


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
    app = AppClass() # 实例化一个App类
    WSGIserver = WSGIRefServer()  
    WSGIserver.run(app)  # 传入app应用实例，启动wsgiref服务器

```

## 第四步：实现静态路由处理

**目前为止**：我们的应用端对所有的请求，返回的都是hello world字符串。

**本节将实现**：根据用户不同请求路径，调用不同函数处理请求。本节实现访问`/hello`或`/world`时，返回不同的内容

- http://localhost:8080/hello请求，发给hello函数处理，返回hello
- http://localhost:8080/world 请求，发给world函数处理，返回world

**背景知识**

服务端调用应用端时传入environ变量，键名'PATH_INFO'对应的值就是请求的路径

```python
# environ变量是一个字典，键名'PATH_INFO'对应的值就是请求的路由
# 例如请求路径localhost:8080/hello，则对应的路径为/hello
environ['PATH_INFO'] # 返回值'/hello'
```

 **具体实现**

```python
class AppClass():
    def __init__(self):
        pass

    def __call__(self, environ, start_response):
        # wsgi服务器把http请求封装为字典，通过environ参数传给wsgi应用端
        path = environ['PATH_INFO'].lstrip('/')
        handle_function = self.router(path)  # 调用路由器查找处理函数
        start_response(
            '200 OK', [('Content-Type', 'text/plain; charset=utf-8')])
        return handle_function()

    def router(self, path):
        """路由器，根据请求路径path找出对应的处理函数"""
        return getattr(self, path)

    def hello(self):
        """处理/hello路径的函数"""
        return [b'hello ']

    def world(self):
        """处理/world路径的函数"""
        return [b'world']


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
    app = AppClass()
    wsgiServer = WSGIRefServer()  # 创建一个实例对象
    wsgiServer.run(app)  # 调用对象的run方法。

```

上面的代码实现的功能：

```
浏览器访问：http://localhost:8080/hello
返回：hello
```

```
浏览器访问：http://localhost:8080/world
返回：world
```

## 第五步：用户自定义静态路由

本节以前实现新的功能都是直接修改原来的代码，不方便拓展功能，本节开始用户可以导入框架模块，使用模块中预先定义的对象或者类。

上一节实现了对`/hello`和`/world`的路由处理，但是我们的应用只有访问指定的路由时才可以响应，不能够随意的自定路由。也不能随意的定义处理的函数。

**本节将实现**：框架的用户只需要给定义的函数用一个装饰器，就会变为可以处理这个路由的处理函数

> 注：在Bottle中，有一个默认的app实例，为了方便理解，我们这里不实现默认app，使用前手动实例化MiniBottle实例

```python
# 使用如下的代码，添加一个可以处理'/abc'请求路径的回调函数
app = MiniBottle()
@app.route('/abc')
def hello():
	pass
```

**本节涉及到的知识点**：装饰器（将函数作为一个对象传入函数），参考资料如下

- [装饰器——廖雪峰的python教程](https://www.liaoxuefeng.com/wiki/1016959663602400/1017451662295584)
- [理解 Python 装饰器看这一篇就够了——python之禅](https://foofish.net/python-decorator.html)

**具体实现如下**：

本节代码新增了如下部分

- 新增Route类：
  - 把route函数抽象为Route类，封装了对应的应用端对象，请求路径、请求方法、回调函数

- MiniBottle中 
  - 定义router方法：表示一个路由器，它的作用是根据请求路径，查找对应的路由route对象	

  - 定义wsgi方法：把原来`__call__`方法中的wsgi接口逻辑抽离出来放在wsgi方法中

  - 定义route方法：用户用该装饰器，可以将一个回调处理函数绑定到MIniBottle实例中

  ```python
  # 用户用如下的装饰器@，可以实现将路由'/abc'和回调处理函数hello封装为一个Route对象,并绑定到应用段框架上
  app = MiniBottle()
  @app.route('/abc')
  def hello():
  	pass
  ```

下面的是具体代码，可以在`if __name__ == "__main__":`内代码块中新增任意的静态路由

```python
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

```
