# Lab 3: SQL Injection (SQLi)

Third laboratory for the **Cybersecurity Laboratory** course.

**Objective:** To exploit and understand SQLi vulnerabilities using the [**OWASP Juice Shop**](https://owasp.org/www-project-juice-shop/) web application.

## Introduction

### Lab aim

The objective of this laboratory was to execute and document at least two **SQL injection** challenges within the OWASP Juice Shop environment, in the categories:

* attack to [bypass authentication](#bypass-authentication)
* attack to [extract data](#extract-data)

Specifically, the report focuses on: 

* The exploitation attempts for solving the challenges;
* Discussion on root causes and takeaways

### Set up Juice Shop

Refer to the [first lab]() for the setup of the Juice Shop container.

#### The Challenges

The challenges this report focuses on are:

* **Login Admin**: Log in with the administrator's user account
* **User Credentials**: Retrieve a list of all user credentials via SQL Injection

<img src="images/Screenshot 2026-06-18 alle 17.39.19.png" alt=" " style="zoom:42%;" /><img src="images/Screenshot 2026-06-18 alle 17.39.30.png" alt=" " style="zoom:50%;" />

## Bypass Authentication

For authentication, the most obvious entry point was the **login page**.

### Is it vulnerable to an SQLi?

To understand if there's a SQL vulnerability in the login page, the first attempt was to use the character `'` as an email. If the system doesn't sanitise user input, this character could be interpreted as part of the code. The password could be anything.

An unexpected `[object Object]` appeared. If the website worked correctly, that shouldn't be shown, so this confirms the suspicion.

<img src="images/Screenshot 2026-06-24 alle 18.04.16.png" alt="the login page with ' as email is shown, with object object printed on top'" style="zoom:50%;" />

To ensure it was an SQL vulnerability, the Network tab in the Browser's Developer Tools was analysed to review the server's response. The response confirmed the vulnerability and allows for a **in-band SQLi**.

<img src="images/Screenshot 2026-06-24 alle 18.11.18.png" alt=" " style="zoom:50%;" />

### Exploit structure

By analysing the source code, inferences can be made on how to execute the injection.

```sql
SELECT * FROM Users WHERE email = '<email>' AND password = '<password>' AND [...]
```

The first step is searching for the admin email (or other interesting users). By looking at the products' comments, it can be found quite easily: `admin@juice-sh.op`.

<img src="images/Screenshot 2026-06-23 alle 12.14.39.png" style="zoom:26%;" />

Then, the email can be structured like: `admin@juice-sh.op' --`

The attempt was successful, as accessing with this "mail" and any password results in a successful login.

<img src="images/Screenshot 2026-06-24 alle 18.32.31.png" alt="Screenshot 2026-06-24 alle 18.32.31" style="zoom:50%;" />

### Understanding root causes

The original code appears in the "coding challenges" section of the Scoreboard page. Here, the vulnerability is detected at line 15: the SQL query is built with string interpolation.

```typescript
export function login () {
  function afterLogin (user: { data: User, bid: number }, res: Response, next: NextFunction) {
    BasketModel.findOrCreate({ where: { UserId: user.data.id } })
      .then(([basket]: [BasketModel, boolean]) => {
        const token = security.authorize(user)
        user.bid = basket.id // keep track of original basket
        security.authenticatedUsers.put(token, user)
        res.json({ authentication: { token, bid: basket.id, umail: user.data.email } })
      }).catch((error: Error) => {
        next(error)
      })
  }

  return (req: Request, res: Response, next: NextFunction) => {
    models.sequelize.query(`SELECT * FROM Users WHERE email = '${req.body.email || ''}' AND password = '${security.hash(req.body.password || '')}' AND deletedAt IS NULL`, { model: UserModel, plain: true })
      .then((authenticatedUser) => {
        const user = utils.queryResultToJson(authenticatedUser)
        if (user.data?.id && user.data.totpSecret !== '') {
          res.status(401).json({
            status: 'totp_token_required',
            data: {
              tmpToken: security.authorize({
                userId: user.data.id,
                type: 'password_valid_needs_second_factor_token'
              })
            }
          })
        } else if (user.data?.id) {
          afterLogin(user, res, next)
        } else {
          res.status(401).send(res.__('Invalid email or password.'))
        }
      }).catch((error: Error) => {
        next(error)
      })
  }
}
```

To fix this vulnerability, the `sequelize` **binding** mechanism can be used to create a prepared statement. This way, the user input cannot be interpreted as SQL code.

```typescript
models.sequelize.query(
  `SELECT * FROM Users WHERE email = $1 AND password = $2 AND deletedAt IS NULL`,
  {
    bind: {
      email: req.body.email || '',
      password: security.hash(req.body.password || '')
    }
    model: UserModel,
    plain: true,
  }
)
```

## Extract Data

The objective for this challenge is to retrieve a list of usernames and credentials from the `Users` table.

### Entry point

To extract sensible data, finding the entry point is less direct. The idea is to search for an HTTP request that explicitly returns database data as `JSON` and see if it's vulnerable to SQLi.

On the homepage, all the products are available at first access. By disabling cache and analysing the HTTP history with Burp, a request to `/rest/products/search?q=` can be found, it returns a `JSON` document.

<img src="images/Screenshot 2026-06-18 alle 15.44.06.png" alt=" " style="zoom:40%;" />

### Is it vulnerable to an SQLi?

By accessing the corresponding page and modifying the query parameter, data can be obtained directly.

<img src="images/Screenshot 2026-06-18 alle 15.44.59.png" alt=" " style="zoom:30%;" />

In order to understand if an SQL vulnerability is present, different values for `q` are tried, similarly to the first challenge. In particular, with `q = ' or '1'='1' --` all the products were returned without errors: so the query is interpreted as SQL code. This allows for an **in-band SQLi**.

### User table structure

At this point, the idea is to execute a union select with the Users table. However, in order to do that, the structure of that table needs to be known.

As seen from the error message of the first challenge, the SQL DBMS is implemented with the library **SQLite**. After [a quick Google search](https://stackoverflow.com/questions/6460671/sqlite-schema-information-metadata), it can be found that the structures of the tables in SQLite are kept in the `sqlite_master` table.

Therefore, to obtain info about the Users table, this syntax can be used: `q=' UNION SELECT sql, "", "", null, null, null, null, null, null FROM sqlite_master WHERE name = 'Users' --`. 

The resulting URL will be:

```
http://localhost:3000/rest/products/search?q=%20%27))union%20SELECT%20sql,%27%27,%27%27,null,null,null,null,null,null%20FROM%20sqlite_master%20where%20name%20=%20%27Users%27--
```

* The columns are 9, corresponding to the ones returned in the `JSON`. 
* The information about the tables (`sql`) will be returned in the first field of the response (`id`). 
* The other columns are set to `null` to allow for the union select, since they have to be the same number of columns. 
* However, setting the `name` and `description` to null returned an error, likely due to some internal non-null check. That's why, for them, the empty string is used instead.

This operation was successful, and the structure of the Users table is obtained. 

<img src="images/Screenshot 2026-06-18 alle 17.06.59.png" alt=" " style="zoom:30%;" />

Now that the names of the columns are known, the actual malevolent union select can be executed. The attacker can choose which information to obtain, but the most interesting ones could be the *password* and the *TOTP secret*. 

A possible query could be: `q=' UNION SELECT id, username, email, password, role, deluxeToken, lastLoginIp, totpSecret, profileImage FROM Users --`.

The resulting URL will be:

```
http://localhost:3000/rest/products/search?q=%27))%20UNION%20SELECT%20id,%20username,%20email,%20password,%20role,%20deluxeToken,%20lastLoginIp,%20totpSecret,%20profileImage%20from%20Users--
```

<img src="images/Screenshot 2026-06-25 alle 12.52.08.png" alt="Screenshot 2026-06-25 alle 12.52.08" style="zoom:30%;" />

### Understanding root causes

Similarly to the first challenge, the source code can be obtained from the "coding challenges". Here, the vulnerability is at line 5: the variable `criteria` is inserted in the SQL query with string interpolation. 

```typescript
export function searchProducts () {
  return (req: Request, res: Response, next: NextFunction) => {
    let criteria: any = req.query.q === 'undefined' ? '' : req.query.q ?? ''
    criteria = (criteria.length <= 200) ? criteria : criteria.substring(0, 200)
    models.sequelize.query(`SELECT * FROM Products WHERE ((name LIKE '%${criteria}%' OR description LIKE '%${criteria}%') AND deletedAt IS NULL) ORDER BY name`)
      .then(([products]: any) => {
        const dataString = JSON.stringify(products)
        for (let i = 0; i < products.length; i++) {
          products[i].name = req.__(products[i].name)
          products[i].description = req.__(products[i].description)
        }
        res.json(utils.queryResultToJson(products))
      }).catch((error: ErrorWithParent) => {
        next(error.parent)
      })
  }
}
```

To fix this vulnerability, the `sequelize` **replacement** mechanism can be used to create a prepared statement. This way the user input cannot be interpreted as SQL code.

```typescript
models.sequelize.query(`SELECT * FROM Products WHERE ((name LIKE '%:criteria%' OR description LIKE '%:criteria%') AND deletedAt IS NULL) ORDER BY name`, {replacements: { criteria }})
```

## Takeaways

### SQLi classification

In this report 2 challenges were described: one for authentication and one for data extraction.

* In the first case, the query involved the use of comments to ignore the rest of the SQL query and the verbose error from the server was observed to properly structure the exploit.
* The second case was a union-based attack, to obtain sensible data extraction: it involved finding an access point, understanding the structure of the table and finally constructing a union select to exploit the vulnerability.

The important takeaway is this:

* SQL vulnerabilities are common and exploiting them may have a big impact on confidentiality and authentication, as shown by this report. 
* One possible defense is using **prepared statement**. 
