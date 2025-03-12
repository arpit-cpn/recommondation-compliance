Get started
---

copy `.env` file which acts like a template to `development.env` or `production.env`
And fill this environment variables list

'''python
  $ python -m venv venv
  $ source venv/bin/activate
'''

Deployment
---

* development mode (default)

'''bash
  $ python src/main.py
'''

* production mode
'''bash
  $ APP_ENV=production python src/main.py
'''

The difference is that development mode would load environment variables from `development.env`, whereas the production mode would load them from `production.env`. these mode specific .env files are git ignored. So the settings would not kept in git log. **Do not fill the .env file which only acts as a ENV template**

Deployment with Docker
---

```bash
  $ docker create --name t-{REPO} -v /var/vertex/appdata/t-{REPO}:/root/usr cpnet/{REPO}:develop
  $ docker cp production.env t-{REPO}:/root/app
  $ docker start t-{REPO}
```

Reference
---

* https://blog.authlib.org/2020/fastapi-google-login
* https://medium.com/@chandanp20k/leveraging-custom-middleware-in-python-fastapi-for-enhanced-web-development-09ba72b5ddc6
* https://fastapi.tiangolo.com/reference/exceptions/#fastapi.HTTPException--example
* https://docs.authlib.org/en/latest/jose/jwt.html#jwt-payload-claims-validation
* https://www.uvicorn.org/settings/#production
