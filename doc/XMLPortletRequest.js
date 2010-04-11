XMLPortletRequest = function (namespace) {
 	
/*
An attribute that takes an EventListener as value that must be
invoked when readystatechange is dispatched on the object implementing
the XMLHttpRequest interface. Its initial value must be null.
*/
 	this.onreadystatechange = null;
 	
 	/*
 	The state of the object. The attribute must be one of the following values:
 	
 	0 Uninitialized
 	The initial value.
 	1 Open
 	The open() method has been successfully called.
 	2 Sent
 	The user agent successfully acknowledged the request.
 	3 Receiving
 	Immediately before receiving the message body (if any).
 	All HTTP headers have been received.
 	4 Loaded
 	The data transfer has been completed.
 	*/
 	this.readyState = 0;
 	
 	this.responseText = null;
 	this.responseXML = null;
 	this.status = 0;
 	this.statusText = 0;
 	this.title = null;
 	this.requestObject = null;
 	
 	if (window.XMLHttpRequest) {
 		this.requestObject = new XMLHttpRequest();
 	} else if (window.ActiveXObject) {
 		this.requestObject = new ActiveXObject("Microsoft.XMLHTTP");
 	} else {
 		this.requestObject = new XMLHttpRequest();
 	}
 	
 	XMLPortletRequest.prototype.namespace = namespace;
 }
 	
 XMLPortletRequest.prototype = {
 	
 	/*
 	Calling this method must initialize the object by remembering the method,
 	url, async (defaulting to true if omitted), user (defaulting to null
 	if omitted), and password (defaulting to null if omitted) arguments,
 	setting the readyState attribute to 1 (Open), resetting the responseText,
 	responseXML, status, and statusText attributes to their initial values,
 	and resetting the list of request headers.
 	*/
 	open:function(method, url, async, user, password) {
	 	var xpr = this;
	 	this.requestObject.onreadystatechange = function () {
	 		xpr.asyncEventHandler.call(xpr);
	 	};
	 	this.requestObject.open(method,url);
 	},
 	
 	/*
 	Invokes setRequestHeader method on XMLHttpRequest
 	*/
 	setRequestHeader:function(header, value){
 		this.requestObject.setRequestHeader(header, value);
 	},
 	
 	/*
 	Invokes send(data) method of XMLHttpRequest
 	*/
 	send:function (data){
 		this.requestObject.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
 		this.requestObject.send(data);
 	},
 	
 	/*
 	Invokes abort() method of XMLHttpRequest
 	*/
 	abort:function (){
 		return this.requestObject.abort();
 	},
 	
 	
 	/*
 	Invokes getAllResponseHeaders method of XMLHttpRequest
 	*/
 	getAllResponseHeaders:function (){
 		return this.requestObject.getAllResponseHeaders();
 	},
 	
 	/*
 	Invokes getResponseHeader method of XMLHttpRequest
 	*/
 	getResponseHeader:function (header){
 		return this.requestObject.getResponseHeader(header);
 	},
 	
 	/*
 	Invokes setEvent
 	*/
 	setEvent:function (qName, values){
 		var functionName = this.namespace+"EventQueue"+name+".setEvent";
 		var args = [qName, values];
 		eval(functionName).apply(window, args);
 	},
 	
 	/*
 	Callback method for all async requests. This will act as a router for the
 	responses for all requests made using this object
 	*/
 	asyncEventHandler:function(){
	 	this.responseText = this.requestObject.responseText;
	 	this.status = this.requestObject.status;
	 	this.responseXML = this.requestObject.responseXML;
	 	this.statusText = this.requestObject.statusText;
	 	this.title = this.requestObject.title;
	 	this.readyState = this.requestObject.readyState;
	 	if (this.readyState == 4) {
		 	if ((this.status == 200) || (this.status == 0)) {
		 		this.onreadystatechange(this);
		 	}
	 	}
 	
 	}
 	
 	
 }
 	