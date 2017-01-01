To setup the application, you must have Python 3.4, node > 5.0, and git-crypt

```
sudo apt-get install libmysqlclient-dev libffi-dev libssl-dev build-essential libffi-dev python3.4-dev g++
mkvirtualenv taxon --python `which python3.4`
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
npm install
./node_modules/.bin/bower install
./node_modules/.bin/brunch watch
git-crypt unlock
python manage.py init_db -g
celery worker -A taxon.celery_entry -B
python manage.py runserver
```

To expose the IPN to PayPal:

``` 
ssh bl -R 8080:localhost:5000
```

To run the tests

```
py.test taxon
# Or with coverage report
py.test taxon --cov=taxon --cov-report=html
```

To build with Docker

```
./build/build.sh
# To run the new instance. Your config needs the following added:
#TEMPLATE_PATH: "/app/templates"
#STATIC_PATH: "/app/public"
docker run --rm -i -p 0.0.0.0:8000:8000 -v /Users/icook/programming/taxon:/etc/frontend --env TIPPIT_CONFIG="/etc/frontend/config2.yml" taxon /usr/local/bin/gunicorn taxon.wsgi_entry:app -w 4 -b 0.0.0.0:8000 --log-level debug
#          Remove after it's finished
#               Attach the container to my console, show me what's going on
#                  Expose port 8000
#                                      Mount my current directory as volume we can access
#                                                                                        Tell our application where to load the configuration file
```
