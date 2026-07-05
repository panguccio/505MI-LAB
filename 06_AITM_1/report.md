# Lab 4: AITM 1

Fourth laboratory for the **Cybersecurity Laboratory** course.

**Objective:** execute **SSLStrip** on [**BURP**](https://portswigger.net/burp) Proxy on two different websites.

## Introduction

### Lab aim

The objective of this laboratory was to successfully execute and document an **SSLStrip attack** using the BURP Proxy on:

* [a website that doesn't use Strict Transport Security](#case-a-website-without-hsts)
* [a website that uses Strict Transport Security](#case-b-website-with-hsts)

Specifically, the report focuses on:

* Configuration of BURP for SSLStrip
* Application of changes to requests/responses
* Discussion of the outcomes of the attacks

### Set up Burp

After creating a new project with Burp and turning on **Intercept**, the Proxy listener will be active on `127.0.0.1:8080`.

Then, Burp has to be configured for SSLStrip.

* On Proxy settings, the **Response Modification Rules** was edited by turning on "Convert HTTPS links to HTTP" and "Remove secure flag from cookies". This way Burp will change the protocol from `https://` to `http://`.
  <img src="images/Screenshot 2025-11-06 alle 15.50.26.png" alt="Screenshot 2025-11-06 alle 15.50.26" style="zoom:50%;" />
* Then, in the section **Proxy Listeners**, the line `127.0.0.1:8080` was edited. In Request handling, for "Redirect to port", `443` was inserted. The option "Force use of TLS" was turned on. This way, Burp will communicate with the server with HTTPS.
  <img src="images/Screenshot 2025-11-06 alle 15.29.34.png" alt="Screenshot 2025-11-06 alle 15.29.34" style="zoom:30%;" />
* Finally, the interception of responses was turned on in the **Response Interception Rules** with as match type "Content type header" and as condition "text".
  <img src="images/Screenshot 2025-11-06 alle 15.29.25.png" alt="Screenshot 2025-11-06 alle 15.29.25" style="zoom:40%;" />

Then, by opening the Burp embedded browser **Chromium**, everything is ready for the lab execution.

## Case A: Website without HSTS

The first website analysed was `www.deeplearningbook.org`: it's a website dedicated to the online version of a book on Deep Learning.

### Checking suitability

As it can be seen by  `curl` return, by accessing the website with `http`, the response is a `301 Moved Permanently`. However, neither the HTTP or the HTTPS responses contain the header `Strict-Transport-Security`, therefore it doesn't use HSTS. This makes this website vulnerable to SSLStrip and suitable for case A.

* Result of `curl -I http://www.deeplearningbook.org/`

  ```http
  HTTP/1.1 301 Moved Permanently
  Connection: keep-alive
  Content-Length: 162
  Server: GitHub.com
  Content-Type: text/html
  Location: https://www.deeplearningbook.org/
  X-GitHub-Request-Id: 9416:2D4B67:1F34F0C:1F7FD34:6A4A380C
  Accept-Ranges: bytes
  Age: 0
  Date: Sun, 05 Jul 2026 10:55:08 GMT
  Via: 1.1 varnish
  X-Served-By: cache-lin1730071-LIN
  X-Cache: MISS
  X-Cache-Hits: 0
  X-Timer: S1783248909.516029,VS0,VE142
  Vary: Accept-Encoding
  X-Fastly-Request-ID: e8e504cdf99807c401f79f7cd7d9ca34d17d52ff
  ```

* Result of `curl -I https://www.deeplearningbook.org/`

  ```http
  HTTP/2 200 
  server: GitHub.com
  content-type: text/html; charset=utf-8
  last-modified: Sat, 07 Sep 2024 23:17:44 GMT
  access-control-allow-origin: *
  etag: "66dcdf18-1737"
  expires: Sun, 05 Jul 2026 11:05:16 GMT
  cache-control: max-age=600
  x-proxy-cache: MISS
  x-github-request-id: 5F2C:2E93B1:1FA07F0:1FEB7DD:6A4A3813
  accept-ranges: bytes
  age: 0
  date: Sun, 05 Jul 2026 10:55:16 GMT
  via: 1.1 varnish
  x-served-by: cache-lin1730056-LIN
  x-cache: MISS
  x-cache-hits: 0
  x-timer: S1783248917.812917,VS0,VE117
  vary: Accept-Encoding
  x-fastly-request-id: a69a7275c22283726b0e91913173317d7f774233
  content-length: 5943
  ```

Now, by placing on http://deeplearningbook.org, the page remains on HTTP. 

<img src="images/Screenshot 2026-07-04 alle 21.30.03.png" alt="Screenshot 2026-07-04 alle 21.30.03" style="zoom:50%;" />

From BURP, it can be seen the Request made with HTTP and the response obtained with HTTPS.

<img src="images/Screenshot 2026-07-04 alle 21.37.43.png" alt="Screenshot 2026-07-04 alle 21.37.43" style="zoom:40%;" />

### SSLStrip Attempts

#### Match and Replace in the Response

With the menu option `match/replace`, some words from the response can be changed automatically.

<img src="images/Screenshot 2026-07-04 alle 21.53.54.png" alt=" " style="zoom:30%;" /><img src="images/Screenshot 2026-07-04 alle 21.56.37.png" alt=" " style="zoom:40%;" />

#### Changing URLs

Another rule can be added to change any url with whatever website of interest, for example a cloned version of Amazon to steal credentials or a link to download a malicious file.

<img src="images/Screenshot 2026-07-04 alle 22.38.45.png" alt="Screenshot 2026-07-04 alle 22.38.45" style="zoom:30%;" /><img src="images/Screenshot 2026-07-04 alle 22.39.47.png" alt="Screenshot 2026-07-04 alle 22.39.47" style="zoom:40%;" />

#### Adding a login form

Another possible idea could be adding an HTML form to the response, to then intercept username and password from Burp.

```html
<form action="/" method="post">
  <div class="imgcontainer">
    <img src="img_avatar2.png" alt="Avatar" class="avatar">
  </div>

  <div class="container">
    <label for="uname"><b>Username</b></label>
    <input type="text" placeholder="Enter Username" name="uname" required>

    <label for="psw"><b>Password</b></label>
    <input type="password" placeholder="Enter Password" name="psw" required>

    <button type="submit">Login</button>
  </div>
</form>
```

## Case B: Website with HSTS

The second website analysed was `github.com`, the famous code hosting platform.

### Checking suitability

As it can be seen by  `curl` return, by accessing the website with `http`, the response is a `301 Moved Permanently`. The HTTPS response contains the header `Strict-Transport-Security`, which implies that the website uses the HSTS protocol. This makes this website suitable for case B.

* Result of `curl -I http://github.com`

  ```http
  HTTP/1.1 301 Moved Permanently
  Content-Length: 0
  Location: https://github.com/
  ```

* Result of `curl -I https://github.com`

  ```http
  HTTP/2 200 
  date: Sun, 05 Jul 2026 10:44:14 GMT
  content-type: text/html; charset=utf-8
  vary: X-PJAX, X-PJAX-Container, Turbo-Visit, Turbo-Frame, X-Requested-With, Accept-Language, Sec-Fetch-Site,Accept-Encoding, Accept, X-Requested-With
  content-language: en-US
  etag: W/"0fdb45ddd7b0c4b2e8452bf28ff744ca"
  cache-control: max-age=0, private, must-revalidate
  strict-transport-security: max-age=31536000; includeSubdomains; preload
  x-frame-options: deny
  x-content-type-options: nosniff
  x-xss-protection: 0
  referrer-policy: origin-when-cross-origin, strict-origin-when-cross-origin
  content-security-policy: default-src 'none'; base-uri 'self'; [...]
  server: github.com
  accept-ranges: bytes
  set-cookie: [...] TYo6L6nAIlQ%3D%3D; path=/; HttpOnly; secure; SameSite=Lax
  set-cookie: _octo=GH1.1.1900857025.1783248255; expires=Mon, 05 Jul 2027 10:44:15 GMT; domain=.github.com; path=/; secure; SameSite=Lax
  set-cookie: logged_in=no; expires=Mon, 05 Jul 2027 10:44:15 GMT; domain=.github.com; path=/; HttpOnly; secure; SameSite=Lax
  x-github-request-id: F6C6:3030A1:AE01447:86FBD52:6A4A357F
  ```

As suggested by `preload`, the domain is already present in the HSTS set of the browser Chromium.

<img src="images/Screenshot 2026-07-05 alle 14.37.48.png" alt="Screenshot 2026-07-05 alle 14.37.48" style="zoom:30%;" />

### SSLStrip Attempts

Now, from Burp embedded browser Chromium, by placing on http://github.com, the page is moved to https://github.com due to HSTS.  The browser trusts the Proxy, so the traffic is not interrupted all together.

<img src="images/Screenshot 2026-07-05 alle 14.56.01.png" alt=" " style="zoom:50%;" />

By opening it on Firefox instead, using Burp as Proxy, the browser blocks entirely the HTTP packet and shows this error page, explaining it's due to HSTS. 

<img src="images/Screenshot 2026-07-05 alle 13.02.44.png" alt=" " style="zoom:50%;" />

The difference in behaviour can be explained by the fact that Firefox doesn't automatically trust Burp certificate like Chromium does. 

#### Removing HSTS domain

After removing the website from the HSTS set of the browser Chromium, the SSLStrip is again possible, as accessing to http://github.com will not redirect.

<img src="images/Screenshot 2026-07-05 alle 15.24.46.png" alt=" " style="zoom:50%;" />

This simulates the **vulnerability window**, i.e. the browser has never visited the site on `https` and so has never acquired the HSTS policy (**Trust On First Use**) or the policy has expired.

## Takeaways

### SSLStrip and HSTS

* SSLStrip attacks can have a strong impact on confidentiality, as the attacker can record and modify all traffic between client and server.
* One possible simple defence is for users to avoid exploring websites without TLS all together. However, this is difficult to enforce, since it relies on user action. 
* HSTS is a mechanism that forces the browser to always use HTTPS, but it's subject to a vulnerability window.
* With HSTS Preloading, the HSTS policies are hardcoded into the browser for certain set of domains, eliminating the vulnerability window.
