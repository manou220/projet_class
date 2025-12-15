/**
 * Polyfills pour compatibilité multi-navigateurs
 * Support: IE11+, Chrome, Firefox, Safari, Edge
 */

// Polyfill pour Promise (IE11)
if (typeof Promise === 'undefined') {
    (function() {
        function Promise(executor) {
            var self = this;
            self.state = 'pending';
            self.value = undefined;
            self.handlers = [];
            
            function resolve(result) {
                if (self.state === 'pending') {
                    self.state = 'fulfilled';
                    self.value = result;
                    self.handlers.forEach(handle);
                    self.handlers = null;
                }
            }
            
            function reject(error) {
                if (self.state === 'pending') {
                    self.state = 'rejected';
                    self.value = error;
                    self.handlers.forEach(handle);
                    self.handlers = null;
                }
            }
            
            function handle(handler) {
                if (self.state === 'pending') {
                    self.handlers.push(handler);
                } else {
                    if (self.state === 'fulfilled' && typeof handler.onFulfilled === 'function') {
                        handler.onFulfilled(self.value);
                    }
                    if (self.state === 'rejected' && typeof handler.onRejected === 'function') {
                        handler.onRejected(self.value);
                    }
                }
            }
            
            self.then = function(onFulfilled, onRejected) {
                return new Promise(function(resolve, reject) {
                    handle({
                        onFulfilled: function(result) {
                            try {
                                resolve(onFulfilled ? onFulfilled(result) : result);
                            } catch (ex) {
                                reject(ex);
                            }
                        },
                        onRejected: function(error) {
                            try {
                                resolve(onRejected ? onRejected(error) : error);
                            } catch (ex) {
                                reject(ex);
                            }
                        }
                    });
                });
            };
            
            try {
                executor(resolve, reject);
            } catch (ex) {
                reject(ex);
            }
        }
        window.Promise = Promise;
    })();
}

// Polyfill pour fetch (IE11, anciens navigateurs)
if (typeof fetch === 'undefined') {
    window.fetch = function(url, options) {
        return new Promise(function(resolve, reject) {
            var xhr = new XMLHttpRequest();
            var method = (options && options.method) || 'GET';
            var headers = (options && options.headers) || {};
            
            xhr.open(method, url);
            
            Object.keys(headers).forEach(function(key) {
                xhr.setRequestHeader(key, headers[key]);
            });
            
            xhr.onload = function() {
                var response = {
                    status: xhr.status,
                    statusText: xhr.statusText,
                    ok: xhr.status >= 200 && xhr.status < 300,
                    json: function() {
                        return Promise.resolve(JSON.parse(xhr.responseText));
                    },
                    text: function() {
                        return Promise.resolve(xhr.responseText);
                    }
                };
                resolve(response);
            };
            
            xhr.onerror = function() {
                reject(new Error('Network error'));
            };
            
            xhr.send(options && options.body);
        });
    };
}

// Polyfill pour Object.assign (IE11)
if (typeof Object.assign !== 'function') {
    Object.assign = function(target) {
        if (target == null) {
            throw new TypeError('Cannot convert undefined or null to object');
        }
        var to = Object(target);
        for (var index = 1; index < arguments.length; index++) {
            var nextSource = arguments[index];
            if (nextSource != null) {
                for (var nextKey in nextSource) {
                    if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                        to[nextKey] = nextSource[nextKey];
                    }
                }
            }
        }
        return to;
    };
}

// Polyfill pour Array.from (IE11)
if (!Array.from) {
    Array.from = function(arrayLike, mapFn, thisArg) {
        var C = this;
        var items = Object(arrayLike);
        if (arrayLike == null) {
            throw new TypeError('Array.from requires an array-like object - not null or undefined');
        }
        var mapFunction = mapFn !== undefined;
        var T;
        if (typeof mapFn !== 'undefined') {
            if (typeof mapFn !== 'function') {
                throw new TypeError('Array.from: when provided, the second argument must be a function');
            }
            if (arguments.length > 2) {
                T = thisArg;
            }
        }
        var len = parseInt(items.length) || 0;
        var A = typeof C === 'function' ? Object(new C(len)) : new Array(len);
        var k = 0;
        var kValue;
        while (k < len) {
            kValue = items[k];
            if (mapFunction) {
                A[k] = typeof T === 'undefined' ? mapFn(kValue, k) : mapFn.call(T, kValue, k);
            } else {
                A[k] = kValue;
            }
            k += 1;
        }
        A.length = len;
        return A;
    };
}

// Polyfill pour String.includes (IE11)
if (!String.prototype.includes) {
    String.prototype.includes = function(search, start) {
        if (typeof start !== 'number') {
            start = 0;
        }
        if (start + search.length > this.length) {
            return false;
        } else {
            return this.indexOf(search, start) !== -1;
        }
    };
}

// Polyfill pour Array.includes (IE11)
if (!Array.prototype.includes) {
    Array.prototype.includes = function(searchElement, fromIndex) {
        if (this == null) {
            throw new TypeError('"this" is null or not defined');
        }
        var o = Object(this);
        var len = parseInt(o.length) || 0;
        if (len === 0) {
            return false;
        }
        var n = parseInt(fromIndex) || 0;
        var k;
        if (n >= 0) {
            k = n;
        } else {
            k = len + n;
            if (k < 0) {
                k = 0;
            }
        }
        function sameValueZero(x, y) {
            return x === y || (typeof x === 'number' && typeof y === 'number' && isNaN(x) && isNaN(y));
        }
        for (; k < len; k++) {
            if (sameValueZero(o[k], searchElement)) {
                return true;
            }
        }
        return false;
    };
}

// Polyfill pour Map (IE11)
if (typeof Map === 'undefined' || typeof Map.prototype.forEach !== 'function') {
    (function() {
        function Map() {
            this._keys = [];
            this._values = [];
        }
        Map.prototype.set = function(key, value) {
            var index = this._keys.indexOf(key);
            if (index === -1) {
                this._keys.push(key);
                this._values.push(value);
            } else {
                this._values[index] = value;
            }
            return this;
        };
        Map.prototype.get = function(key) {
            var index = this._keys.indexOf(key);
            return index === -1 ? undefined : this._values[index];
        };
        Map.prototype.has = function(key) {
            return this._keys.indexOf(key) !== -1;
        };
        Map.prototype.delete = function(key) {
            var index = this._keys.indexOf(key);
            if (index !== -1) {
                this._keys.splice(index, 1);
                this._values.splice(index, 1);
                return true;
            }
            return false;
        };
        Map.prototype.forEach = function(callback) {
            for (var i = 0; i < this._keys.length; i++) {
                callback(this._values[i], this._keys[i], this);
            }
        };
        Object.defineProperty(Map.prototype, 'size', {
            get: function() {
                return this._keys.length;
            }
        });
        window.Map = Map;
    })();
}

// Polyfill pour Set (IE11)
if (typeof Set === 'undefined' || typeof Set.prototype.forEach !== 'function') {
    (function() {
        function Set(values) {
            this._values = [];
            if (values) {
                for (var i = 0; i < values.length; i++) {
                    this.add(values[i]);
                }
            }
        }
        Set.prototype.add = function(value) {
            if (this._values.indexOf(value) === -1) {
                this._values.push(value);
            }
            return this;
        };
        Set.prototype.has = function(value) {
            return this._values.indexOf(value) !== -1;
        };
        Set.prototype.delete = function(value) {
            var index = this._values.indexOf(value);
            if (index !== -1) {
                this._values.splice(index, 1);
                return true;
            }
            return false;
        };
        Set.prototype.forEach = function(callback) {
            for (var i = 0; i < this._values.length; i++) {
                callback(this._values[i], this._values[i], this);
            }
        };
        Object.defineProperty(Set.prototype, 'size', {
            get: function() {
                return this._values.length;
            }
        });
        window.Set = Set;
    })();
}

// Détection de compatibilité et avertissements
(function() {
    var warnings = [];
    
    // Vérifier localStorage
    try {
        localStorage.setItem('_test', '1');
        localStorage.removeItem('_test');
    } catch (e) {
        warnings.push('localStorage non disponible');
    }
    
    // Vérifier geolocation
    if (!navigator.geolocation) {
        warnings.push('Géolocalisation non disponible');
    }
    
    // Afficher les avertissements en mode développement
    if (warnings.length > 0 && window.console && console.warn) {
        console.warn('Compatibilité navigateur:', warnings.join(', '));
    }
})();

