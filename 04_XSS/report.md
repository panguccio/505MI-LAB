# Lab 2: Cross-Site Scripting (XSS)

Second laboratory for the **Cybersecurity Laboratory** course.

**Objective:** exploit and understand XSS vulnerabilities using the [**OWASP Juice Shop**](https://owasp.org/www-project-juice-shop/) web application.

## Introduction

### Lab aim

The objective of this laboratory was to successfully execute and document two distinct types of XSS challenges within the OWASP Juice Shop environment:

* a [DOM XSS](##DOM XSS) attack
* a [Reflected XSS](##Reflected XSS) attack

Specifically, the report focuses on:

* The exploitation attempts for solving the two challenges;
* The difference between the two vulnerabilities, i.e., how the user input is handled in the two cases and why they are labeled as "DOM" and "Reflected”.

### Setup Juice Shop

#### Docker

The OWASP Juice Shop application was deployed using Docker.

1. Pulling the remote **Docker Image**:

   ```bash
   docker pull bkimminich/juice-shop 
   ```

2. Running the **container**:

   ```bash
   docker run -d -p 3000:3000 -e NODE_ENV=unsafe bkimminich/juice-shop
   ```

   Or directly from docker desktop:

<img src="images/Screenshot 2026-06-11 alle 17.12.22.png" alt="docker desktop container setup" style="zoom:30%;" />

> [!NOTE]
>
> The `NODE_ENV` is a environment variable to allow the "unsafe" version to run. This is important to execute some of the XSS challenges that would be otherwise blocked due to application-level security mechanisms.

Once initialized, the web application can be accessed at: `http://localhost:3000`

<img src="images/Screenshot 2026-06-11 alle 17.22.06.png" alt="juice shop home page" style="zoom:20%;" />

#### The Challenges

By analyzing the routing structure of the single-page application, the URL for the hidden score board was inferred, as it was similar to the photo wall page URL (`http://localhost:3000/#/photo-wall`).

So using a similar routing structure, the score board was then found at: `http://localhost:3000/#/score-board`.

This unlocked the tracking dashboard and the target challenges for the lab: **DOM XSS** and **Reflected XSS**. The challenge in both cases involves executing an XSS attack with `<iframe src="javascript:alert(1)">`.

<img src="images/Screenshot 2026-06-11 alle 17.30.58.png" alt=" " style="zoom:48%;" /><img src="images/Screenshot 2026-06-11 alle 17.31.07.png" alt=" " style="zoom:50%;" />

## DOM XSS

### Exploitation attempt

The most obvious entry point was the application **search bar.**  

When a search query is submitted, the application updates the URL using a query parameter dynamically (`http://localhost:3000/#/search?q=QUERY`).

To test for a DOM-based XSS vulnerability, the unsanitized HTML element containing a JavaScript payload (as suggested in the score board challenge description) was appended into the `q` parameter:

```
http://localhost:3000/#/search?q=%3Ciframe%20src%3D%22javascript:alert(%60xss%60)%22%3E
```

The attempt was successful, as the payload was executed, rendering the alert box and confirming the vulnerability.

<img src="images/Screenshot 2026-06-11 alle 17.38.29.png" alt="this image shows the alert box screenshot appearing as a pop up. the background is the search for products page, that appears empty, with no results found" style="zoom:30%;" />

<img src="images/Screenshot 2026-06-22 alle 12.49.59.png" alt="this image shows that in the HTML for the page the box where the search query should appear, there's the iframe that was injected" style="zoom:50%;" />

### Understanding root causes

To understand what was happening "under the hood", the client-side source code was inspected using the browser's **Developer Tools** (Sources tab). The core application logic was found in the `main.js` file and, specifically for this challenge, within the `filterTable()` method.

```js
filterTable() {
            let e = this.route.snapshot.queryParams.q; // get the value of q from the query
            e ? (e = e.trim(),
            this.ngZone.runOutsideAngular( () => {
                this.io.socket().emit("verifyLocalXssChallenge", e)
            }
            ),
            this.dataSource.filter = e.toLowerCase(),
            this.searchValue = this.sanitizer.bypassSecurityTrustHtml(e), // VULNERABILITY: transfers the value of e without sanitization
            this.gridDataSourceSubscription && this.gridDataSourceSubscription.unsubscribe(),
            this.gridDataSourceSubscription = this.gridDataSource.subscribe(i => {
                i.length === 0 ? this.emptyState = !0 : this.emptyState = !1
            }
            )) : (this.dataSource.filter = "", this.searchValue = void 0, this.emptyState = !1)
        }
```

The application extracts the query directly from the URL (`this.route.snapshot.queryParams.q`). This is the **source** of the DOM XSS vulnerability.

At line 9, the code explicitly invokes the method `this.sanitizer.bypassSecurityTrustHtml(e)` and assigns it to `this.searchValue`. This is the **sink**. 

`bypassSecurityTrustHtml` is a built-in Angular method  (as can be found [here](https://angular.dev/api/platform-browser/DomSanitizer)) that bypasses security and trusts the given value to be **safe HTML**. 

The variable is the rendered as "Search Result - [`QUERY`]" at the top of the search results, as can be seen by the resulting HTML template:

```html
<div _ngcontent-ng-c1161564479="">
  <span _ngcontent-ng-c1161564479="">Search Results - </span>
  <span _ngcontent-ng-c1161564479="" id="searchValue">product</span>
</div>
```

When Angular evaluates the page, it takes the value stored in `this.searchValue` and natively handles the DOM injection.

By default, Angular's sanitizer would intercept the query `<iframe src="javascript:alert(1)">` and flag it as dangerous. Using this method, this safety check is skipped and the **iframe** is injected directly in the DOM, that then gets executed by the client.

This satisfies the definition of a DOM XSS attack, since the client-side JavaScript reads from a local source and writes improperly into a local sink.

## Reflected XSS

### Exploitation root causes

The second challenge required identifying an input source that interacts with the backend server. 

The vulnerable component is the Track Order page (to find it,  [this guide](https://clouddocs.f5.com/training/community/waf/html/waf2025/module2/lab3.html) was used as help): the user needs to place a fake order of some product from the website so that the page was available at  `http://localhost:3000/#/track-result/new?id=[ORDER_ID]`. 

Similarly to the DOM XSS attack, the iframe payload was pasted directly into the `id` parameter, generating the following URL:

```
http://localhost:3000/#/track-result/new?id=%3Ciframe%20src%3D%22javascript:alert(%60xss%60)%22%3E%
```

The attempt was successful, as the payload was executed, rendering the alert box and confirming the vulnerability.

<img src="images/Screenshot 2026-06-22 alle 12.36.07.png" alt="this image shows the alert box screenshot appearing at the top. the background is the tracking order page, that appears almost empty, since no order was found" style="zoom:20%;" />

<img src="images/Screenshot 2026-06-22 alle 12.37.37.png" alt=" this image shows that in the HTML for the page the box where the orderId should appear, there's the iframe that was injected" style="zoom:30%;" />

### Understanding root causes

The execution was similar to the first challenge, however what was going on under the hood was very different.



Analyzing the `main.js` file, the logic for getting the tracking informations was expressed by `ngOnInit()`. 

```js
ngOnInit() {
            this.orderId = this.route.snapshot.queryParams.id,
            this.trackOrderService.find(this.orderId).subscribe(e => {
                this.results.orderNo = this.sanitizer.bypassSecurityTrustHtml(`<code>${e.data[0].orderId}</code>`), // VULNERABILITY: transfers the value of orderId without sanitization
                this.results.email = e.data[0].email,
                this.results.totalPrice = e.data[0].totalPrice,
                this.results.products = e.data[0].products,
                this.results.eta = e.data[0].eta !== void 0 ? e.data[0].eta : "?",
                this.results.bonus = e.data[0].bonus,
                this.dataSource.data = this.results.products,
                e.data[0].delivered ? this.status = ua.Delivered : this.route.snapshot.data.type ? this.status = ua.New : this.results.eta > 2 ? this.status = ua.Packing : this.status = ua.Transit
            }
            )
        }
```

The client extracts the malicious `orderId` from the URL parameter and then transmits it to the backend with the service `this.trackOrderService.find(this.orderId)`, as is, without sanitization. 

The method used to bypass security is the same as the DOM challenge. In this case however, the variable used is obtained from an HTTP response to the server. 

To understand better what is going on, the logic for the method `find` needs to be analyzed.

By searching for "track-order" we can find the class definition of `oo`. This is a HTTP Angular service defined as a anonymous class.

```js
var oo = ( () => {
    class t {
        http = m(ue);
        hostServer = J.hostServer;
        host = this.hostServer + "/rest/track-order";
        find(e) {
            return e = encodeURIComponent(e),
            this.http.get(`${this.host}/${e}`).pipe(W(i => i), L(i => {
                throw i
            }
            ))
        }
        static \u0275fac = function(i) {
            return new (i || t)
        }
        ;
        static \u0275prov = U({
            token: t,
            factory: t.\u0275fac,
            providedIn: "root"
        })
    }
    return t
}
```

Since the variables are minified, the entire script was given to an LLM (Claude) to properly understand and derive each of the variables and understand better the logic behind. The output was this much more legible, although simplified, code. 

```js
class TrackOrderService {
  http = HttpClient;
  hostServer = environment.hostServer;
  host = this.hostServer + "/rest/track-order";

  find(orderId) {
    orderId = encodeURIComponent(orderId);
    return this.http.get(`${this.host}/${orderId}`);
  }
}
```

The variable `oo` actually corresponds to `TrackOrderService`. 

Here the method `find` which is called in the vulnerable original code makes a GET request to `/rest/track-order/{id}` to get the details about the order (such as email, product names, quantities and total price).

After a rather unsuccessful trip (given that there's no order corresponding to the iframe), the payload returns to the client, without any validation. 

The vulnerable line is this one, in the `ngOnInt` method:

```js
this.results.orderNo = this.sanitizer.bypassSecurityTrustHtml(`<code>${e.data[0].orderId}</code>`),
```

The resulting `orderId` from the HTTP response is inserted by the frontend inside an HTML tag, bypassing security. This way, what would be treated as text by default by Angular, is not sanitized and is interpreted as inner JS code by the browser.

## Takeaways

### DOM vs Reflected

The main difference between the two exploits is that:

* in the DOM XSS, the payloads never leaves the client, it's injected directly into the DOM by the client-side JavaScript
* in the Reflected XSS, instead, the payload travels to the server, through an HTTP request, then is reflected back in the HTTP response and only then executed by the client