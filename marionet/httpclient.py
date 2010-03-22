"""
#  Copyright 2008-2009 The University of Manchester, UK.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  A copy of the licence is in LICENSE.txt
#
#
# This library was originally developed for use by the NanoCMOS project,
# EPSRC-funded under grant EP/E001947/1 <http://www.nanocmos.ac.uk/>.
#
#
# This httpclient library aims to address shortcomings of urllib2, included in
# the core Python (2.4/2.5) distribution, mainly:
#   - its handling of proxy servers (especially HTTPS),
#   - its handling of SSL/TLS certificate (lack of verification),
#   - other methods (PUT, ...).
#
# 
# Authors:     Bruno Harbulot (University of Manchester)
# Contributor: Dave Reid (University of Glasgow)
#
"""

import httplib
import urlparse
import base64
import socket

try:
    import ssl
    USE_OPENSSL = False
except ImportError:
    import OpenSSL
    USE_OPENSSL = True


VERSION = "0.3"

class Configuration():
    """This classes holds various configuration settings. It is a singleton.
    """
    __shared_state = {}
    __user_agent = 'NanoCMOS-Python-HttpClient/' + str(VERSION)
    __max_follow_redirects = 10
    __debug_level = 0
    __http_proxy = None
    __client_cert = None
    __client_key = None
    __trust_store = None
    def __init__(self):
        self.__dict__ = self.__shared_state

    def set_user_agent(self, user_agent):
        """Sets the User-Agent header to use.
        @param user_agent: the User-Agent to header to use.
        """
        self.__user_agent = user_agent
    def get_user_agent(self):
        """Gets the User-Agent header to be used.
        @return: the User-Agent header to be used.
        """
        return self.__user_agent
        
    def set_max_follow_redirects(self, max_redirects):
        """Sets the maximum of redirections to follow (for example, with 
        HTTP 302).
        @param max_redirects: maximum number of redirects (integer).
        """
        self.__max_follow_redirects = max_redirects
    def get_max_follow_redirects(self):
        """Returns the maximum of redirections to follow (for example, with 
        HTTP 302).
        @return: maximum number of redirects (integer).
        """
        return self.__max_follow_redirects
        
    def set_debug_level(self, debug_level):
        """Sets the debug level. See code for checking what these levels do.
        @param debug_levell: debug level.
        """
        self.__debug_level = debug_level
    def get_debug_level(self):
        """Gets the debug level. See code for checking what these levels do.
        @return: debug level.
        """
        return self.__debug_level
    
    def set_http_proxy(self, http_proxy):
        """Sets the HTTP proxy.
        @param http_proxy: proxy-hostname:proxy-port
        """
        self.__http_proxy = http_proxy
    def get_http_proxy(self):
        """Gets the HTTP proxy settings.
        @return: proxy-hostname:proxy-port
        """
        return self.__http_proxy
    
    def set_client_cert(self, path):
        """Sets the path of the client certificate to use (PEM format).
        @param path: path of the client certificate to use
        """
        self.__client_cert = path
    def get_client_cert(self):
        """Gets the path of the client certificate to use.
        @return: path of the client certificate to use
        """
        return self.__client_cert
    def set_client_key(self, path):
        """Sets the path of the private key for the client certificate
        (PEM format).
        @param path: path of the key
        """
        self.__client_key = path
    def get_client_key(self):
        """Gets the path of the private key for the client certificate
        (PEM format).
        @return: path of the client certificate to use
        """
        return self.__client_key
    
    def set_trust_store(self, path):
        """Sets the path of the trust anchors with which to verify the 
        remote certificates (a concatenation of PEM certificates).
        @param path: path of the trust store
        """
        self.__trust_store = path
    def get_trust_store(self):
        """Gets the path of the trust anchors with which to verify the 
        remote certificates (a concatenation of PEM certificates).
        @return: path of the trust store
        """
        return self.__trust_store
    
    def load_dictionary(self, config_dictionary={}, prefix="http."):
        """Loads the configuration from a dictionary.
        The key names are http.max_follow_redirects, http.debug_level, http.proxy,
        http.client_cert, http.client_key and http.trust_store.
        @param config_dictionary: dictionary from which to load the settings.
        @param prefix: prefix of the key names in that dictionary (defaults to 'http.').
        """

        keyname = prefix + "max_follow_redirects"
        if config_dictionary.has_key(keyname) and config_dictionary[keyname]:
            self.__max_follow_redirects = config_dictionary[keyname]
        keyname = prefix + "debug_level"
        if config_dictionary.has_key(keyname) and config_dictionary[keyname]:
            self.__debug_level = config_dictionary[keyname]
        keyname = prefix + "proxy"    
        if config_dictionary.has_key(keyname) and config_dictionary[keyname]:
            self.__http_proxy = config_dictionary[keyname]
        keyname = prefix + "client_cert"    
        if config_dictionary.has_key(keyname) and config_dictionary[keyname]:
            self.__client_cert = config_dictionary[keyname]
        keyname = prefix + "client_key"    
        if config_dictionary.has_key(keyname) and config_dictionary[keyname]:
            self.__client_key = config_dictionary[keyname]
        keyname = prefix + "trust_store"    
        if config_dictionary.has_key(keyname) and config_dictionary[keyname]:
            self.__trust_store = config_dictionary[keyname]


class OpensslHTTPSConnection(httplib.HTTPConnection):
    """This class is an extension of httplib.HTTPConnection that adds the
    ability to verify the certificate of the server and the ability to use 
    a client certificate.
    """
    __key_file = None
    __cert_file = None
    __trust_store = None

    def __init__(self, host, port=None, trust_store=None, key_file=None,
                 cert_file=None, strict=None):
        self.default_port = httplib.HTTPS_PORT
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.__key_file = key_file
        self.__cert_file = cert_file
        self.__trust_store = trust_store

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = self.convert_ssl_sock(sock)

        
    def convert_ssl_sock(self, sock):
        """Converts the default socket into an OpenSSL or ssl socket, with the
        required options.
        """
        if USE_OPENSSL:
            ctx = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv3_METHOD)
            ctx.load_verify_locations(self.__trust_store)
            ctx.set_verify(OpenSSL.SSL.VERIFY_PEER or OpenSSL.SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.__verify__callback)
            if self.__key_file and self.__cert_file:
                ctx.use_certificate_chain_file(self.__cert_file)
                ctx.use_privatekey_file(self.__key_file)
                ctx.check_privatekey()
            ssl_sock = OpenSSL.SSL.Connection(ctx, sock)
            status = ssl_sock.connect_ex((self.host, self.port))
            peer_cert = ssl_sock.get_peer_certificate()
            return httplib.FakeSocket(sock, ssl_sock)
        
        else:
            ssl_sock = ssl.wrap_socket(sock,
                                        keyfile=self.__key_file,
                                        certfile=self.__cert_file,
                                        ca_certs=self.__trust_store,
                                        cert_reqs=ssl.CERT_REQUIRED)
            ssl_sock.connect((self.host, self.port))
            peer_cert = ssl_sock.getpeercert()

            # Extract the host names from the CommonName field of the subject DN.
            cert_host_names = set([val for subject_entry in peer_cert['subject'] for key,val in subject_entry if key == 'commonName' ])
            # Extract the host names from the subjectAltName.
            cert_host_names = cert_host_names.union(set([name for key, name in peer_cert['subjectAltName'] if key == 'DNS' ]))
            # Verify that the host name is in the list of names for this certificate.
            if not self.host in cert_host_names:
                raise ssl.SSLError("The certificate does not match the host name.")
            
            return ssl_sock
        
    def __verify__callback(self, connection, x509cert, errno, depth, ret):
        """This is the callback that verifies the certificate (once the chain
        has been established).
        """
        if depth == 0:
            if self.host == x509cert.get_subject().commonName:
                return ret
            else:
                return 0
        return ret



class HttpAuthenticationHandler:
    """This class is an empty authentication handler.
    """
    def __init__(self):
        pass
    def can_handle(self, http_method, preempt=False):
        """Checks whether-or-not this handler should be used
        to attempt to provide authentication with that request.
        @param http_method: instance of HttpMethodBase.
        @param preempt: true if preemptive authentication should be used.
        @return: true if this authentication method should be used.
        """
        return preempt
    def execute(self, http_method):
        """Executes the method, including authentication mechanism if appropriate.
        @param http_method: instance of HttpMethodBase.
        """
        http_connection = http_method.create_http_connection()
        http_method.init_headers(http_connection)
        http_method.make_request(http_connection)



class HttpBasicAuthenticationHandler(HttpAuthenticationHandler):
    """HttpAuthenticationHandler that handles HTTP Basic authentication.
    """
    __realm = None
    __username = ''
    __password = ''
    def __init__(self, realm, username, password):
        """Creates a new HttpBasicAuthenticationHandler
        @param realm: realm for the basic authentication.
        @param username: user name.
        @param password: password.
        @bug: Checking the realm name could be substantially improved.
        """
        HttpAuthenticationHandler.__init__(self)
        self.__realm = realm
        self.__username = username
        self.__password = password
    def can_handle(self, http_method, preempt=False):
        """Checks whether-or-not this handler should be used
        to attempt to provide authentication with that request.
        @param http_method: instance of HttpMethodBase.
        @param preempt: true if preemptive authentication should be used.
        @return: true if this authentication method should be used.
        """
        response = http_method.get_response()
        if response:
            wwwauthenticate = response.getheader('WWW-Authenticate')
            if wwwauthenticate:
                wwwauthenticate = wwwauthenticate.split(' ', 1)
                if len(wwwauthenticate) == 2:
                    authkind = wwwauthenticate[0]
                    if authkind != 'Basic':
                        return False
                    if self.__realm:
                        realminfo = wwwauthenticate[1].split('=', 1)
                        if len(realminfo) == 2:
                            realm = realminfo[1]
                            realm = realm.strip('"')
                            # TODO: better realm matching...
                            if realm == self.__realm:
                                return True
                            else:
                                return False
                    else:
                        return True
            return True
        else:
            return preempt
    def add_authentication_header(self, http_connection):
        """Adds the authentication header to the request.
        @param http_connection: httpConnetion obtained from the httpMethod.
        """
        if Configuration().get_debug_level() > 0:
            print "Adding auth header: " + self.__username + ":" + self.__password
        http_connection.putheader('Authorization', "Basic " + base64.b64encode(self.__username + ":" + self.__password))
    def execute(self, http_method):
        """Executes the method, including authentication mechanism if appropriate.
        @param http_method: instance of HttpMethodBase.
        """
        http_connection = http_method.create_http_connection()
        http_method.init_headers(http_connection)
        self.add_authentication_header(http_connection)
        http_method.make_request(http_connection)

        

class HttpMethodBase:
    """This class is an abstraction for an HTTP method.
    """
    __uri = None
    __headers = {}
    __hasBeenUsed = False
    __response = None
    __follow_redirects = 0
    __user_agent = None
    __visited_redirections = set()
    __do_authentication = True
    __proxy = None
    def __init__(self, uri=None):
        """Constructs an HTTP method.
        @param uri: URI of the method
        """
        self.__uri = uri
        self.__user_agent = Configuration().get_user_agent()
        self.__proxy = Configuration().get_http_proxy()

    def add_request_header(self, name, value):
        """Adds a header to the request.
        @param name: header name.
        @param value: header value.
        """
        if not(self.__headers.has_key(name)):
            self.__headers[name] = value
    def set_request_header(self, name, value):
        """Sets a request header.
        @param name: header name.
        @param value: header value.
        """
        self.__headers[name] = value
    def remove_request_header(self, name):
        """Removes a request header.
        @param name: header name.
        """
        del self.__headers[name]
    def get_request_header(self, name):
        """Gets a request header.
        @param name: header name.
        @return: header value.
        """
        return self.__headers[name]
    
    def get_user_agent(self):
        """Gets the User-Agent name.
        @return: User-Agent name.
        """
        return self.__user_agent
    def set_user_agent(self, user_agent):
        """Sets the User-Agent name.
        @param user_agent: User-Agent name.
        """
        self.__user_agent = user_agent
      
    def get_name(self):
        """Returns the name of the request; to be overridden for actual HTTP methods.
        @return: HTTP verb used by the request, for example GET.
        """
        return 'GET'
    
    def get_uri(self):
        """Returns the URI of the target resource.
        @return: URI of the target resource.
        """
        return self.__uri
    def set_uri(self, uri):
        """Sets the URI of the target resource.
        @param uri: URI of the target resource.
        """
        self.__uri = uri
    
    
    # The proxy code in this was inspired by
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456195
    # by Alessandro Budai.
    def create_http_connection(self):
        """Creates an HttpConnection for this method.
        """
        parsed_url = urlparse.urlsplit(self.get_uri())
        if parsed_url.scheme == "https":
            port = 443
        else:
            port = 80
            
        if self.__proxy:
            http_connection = httplib.HTTPConnection(self.__proxy)
            #httpConnection.debuglevel=1
            http_connection.connect()
            if parsed_url.port:
                port = parsed_url.port
            http_connection.send("CONNECT %s:%d HTTP/1.0\r\n\r\n" % (parsed_url.hostname, port))
            
            response = http_connection.response_class(http_connection.sock, strict=http_connection.strict, method=self.get_name())
            (version, code, message) = response._read_status()
            if code != 200:
                http_connection.close()
                raise socket.error, "Proxy connection failed: %d %s" % (code, message.strip())
            while True:
                line = response.fp.readline()
                if line == '\r\n': 
                    break
            if parsed_url.scheme == "https":
                if Configuration().get_client_key() and Configuration().get_client_cert():
                    fake_http_connection = OpensslHTTPSConnection(parsed_url.netloc, trust_store=Configuration().get_trust_store(), key_file=Configuration().get_client_key(), cert_file=Configuration().get_client_cert())
                else:
                    fake_http_connection = OpensslHTTPSConnection(parsed_url.netloc, trust_store=Configuration().get_trust_store())
                ssl = fake_http_connection.convert_ssl_sock(http_connection.sock)
                http_connection.sock = httplib.FakeSocket(http_connection.sock, ssl)
                
        else:
            if parsed_url.scheme == "https":
                if Configuration().get_client_key() and Configuration().get_client_cert():
                    http_connection = OpensslHTTPSConnection(parsed_url.netloc, trust_store=Configuration().get_trust_store(), key_file=Configuration().get_client_key(), cert_file=Configuration().get_client_cert())
                else:
                    http_connection = OpensslHTTPSConnection(parsed_url.netloc, trust_store=Configuration().get_trust_store())
                #httpConnection.debuglevel=1
            else:
                http_connection = httplib.HTTPConnection(parsed_url.netloc)
                #httpConnection.debuglevel=1
        #httpConnection.debuglevel=1
        return http_connection
    
    def init_headers(self, http_connection):
        """Initializes the connection with the usual headers.
        @param http_connection: HttpConnection on which to put the headers.
        """
        parsed_url = urlparse.urlsplit(self.get_uri())
        if parsed_url.query:
            fullpath = parsed_url.path + "?" + parsed_url.query
        else:
            fullpath = parsed_url.path
        if self.__proxy:
            http_connection.putrequest(self.get_name(), self.get_uri())
        else:
            http_connection.putrequest(self.get_name(), fullpath)
            
        if self.get_user_agent():
            http_connection.putheader("User-Agent", self.get_user_agent())
        for name, value in self.__headers.iteritems():
            http_connection.putheader(name, value)
            
    def make_request(self, http_connection):
        """Performs the request. To be used internally.
        @param http_connection: HttpConnection on which to put the headers.
        """
        http_connection.endheaders()
        self.set_response(http_connection.getresponse())
        
    def execute(self, preemptive_auth_handler_list=[], challenged_auth_handler_list=[]):
        """Executes the request, and perhaps follows the redirections.
        @param preemptive_auth_handler_list: list of preemptive authentication handlers.
        @param challenged_auth_handler_list: list of handlers to be used as a response to a challenge.
        """
        preemptive_auth_handler_list.append(HttpAuthenticationHandler())
        for preemptive_auth_handler in preemptive_auth_handler_list:
            if Configuration().get_debug_level() > 0:
                print "Trying preemptive handler: " + str(preemptive_auth_handler.can_handle(self, True))
            if preemptive_auth_handler.can_handle(self, True):
                preemptive_auth_handler.execute(self)
                if Configuration().get_debug_level() > 0:
                    print "Tried. Unauthorized? " + str(self.is_response_unauthorized())
                if self.is_response_unauthorized():
                    for challenged_auth_handler in challenged_auth_handler_list:
                        if Configuration().get_debug_level() > 0:
                            print "Trying challenged handler: " + str(challenged_auth_handler.can_handle(self))
                        if challenged_auth_handler.can_handle(self):
                            challenged_auth_handler.execute(self)
                        if (self.__response and not(self.is_response_unauthorized() or self.is_response_forbidden())):
                            break
                if (self.__response and not(self.is_response_unauthorized() or self.is_response_forbidden())):
                    break
        if self.is_response_redirection():
            if (self.get_follow_redirects() > 0):
                self.__visited_redirections.add(self.get_uri())
                location = self.__response.getheader('Location', None)
                if Configuration().get_debug_level() > 0:
                    print "Redirecting to location: " + location
                if location:
                    if not(location in self.__visited_redirections):
                        self.set_uri(location)
                        self.set_follow_redirects(self.get_follow_redirects() - 1)
                        self.execute(preemptive_auth_handler_list, challenged_auth_handler_list)
                    else:
                        pass # Exception? Loop in the redirections?
                else:
                    pass # Exception? No location header?
    
    def set_response(self, response):
        """Sets the response.
        @param response: response.
        """
        self.__response = response
    def get_response(self):
        """Gets the response.
        @return: response.
        """
        return self.__response
    
    def get_response_header(self, name):
        if self.__response:
            return self.__response.getheader(name, None)
        else:
            return None
    
    def get_follow_redirects(self):
        """Gets the number of maximum redirections allowed.
        @return: max number of redirections to follow.
        """
        return self.__follow_redirects
    def set_follow_redirects(self, follow_redirects):
        """Sets the number of maximum redirections allowed.
        @param follow_redirects: max number of redirections to follow.
        """
        self.__follow_redirects = follow_redirects
        
    def is_response_meta(self):
        if self.__response:
            return (self.__response.status < 200)
        else:
            return False
    def is_response_success(self):
        if self.__response:
            return ((self.__response.status >= 200) and (self.__response.status < 300))
        else:
            return False
    def is_response_redirection(self):
        if self.__response:
            return ((self.__response.status >= 300) and (self.__response.status < 400))
        else:
            return False
    def is_response_client_error(self):
        if self.__response:
            return ((self.__response.status >= 400) and (self.__response.status < 500))
        else:
            return False
    def is_response_server_error(self):
        if self.__response:
            return (self.__response.status >= 500)
        else:
            return False
    def is_response_unauthorized(self):
        if self.__response:
            return (self.__response.status == 401)
        else:
            return False
    def is_response_forbidden(self):
        if self.__response:
            return (self.__response.status == 403)
        else:
            return False
    
    def get_path(self):
        parsed_url = urlparse.urlsplit(self.get_uri())
        return parsed_url.path
    def get_query_string(self):
        parsed_url = urlparse.urlsplit(self.get_uri())
        return parsed_url.query

    def set_do_authentication(self, do_authentication):
        self.__do_authentication = do_authentication
    def get_do_authentication(self):
        return self.__do_authentication




class HttpMethodWithBody(HttpMethodBase):
    """This class is an abstraction for an HTTP method with a body
    (e.g. POST, PUT).
    """
    __body = None
    __content_type = None
    def __init__(self, uri):
        HttpMethodBase.__init__(self, uri)
        
    def set_body(self, body):
        self.__body = body
    def get_body(self):
        return self.__body
    
    def set_request_content_type(self, content_type):
        self.__content_type = content_type
    def get_request_content_type(self):
        return self.__content_type
    
    def make_request(self, http_connection):
        if self.get_request_content_type():
            http_connection.putheader("Content-type", self.get_request_content_type())
        if self.get_body():
            http_connection.putheader("Content-length", "%d" % len(self.get_body()))
        http_connection.endheaders()
        if self.get_body():
            http_connection.send(self.get_body())
        self.set_response(http_connection.getresponse())




class GetMethod(HttpMethodBase):
    def __init__(self, uri):
        HttpMethodBase.__init__(self, uri)
        self.set_follow_redirects(Configuration().get_max_follow_redirects())
    def get_name(self):
        return 'GET'


class DeleteMethod(HttpMethodBase):
    def __init__(self, uri):
        HttpMethodBase.__init__(self, uri)
        self.set_follow_redirects(0)
    def get_name(self):
        return 'DELETE'
    

class PostMethod(HttpMethodWithBody):
    def __init__(self, uri):
        HttpMethodWithBody.__init__(self, uri)
        self.set_follow_redirects(0)
    def get_name(self):
        return 'POST'


class PutMethod(HttpMethodWithBody):
    def __init__(self, uri):
        HttpMethodWithBody.__init__(self, uri)
        self.set_follow_redirects(0)
    def get_name(self):
        return 'PUT'


