# Backend App for Secret Voldemort


# How to run:
    $ git clone https://github.com/ExpectoAprobarum/BackendSV.git
    $ cd BackendSV
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ hypercorn src.main:app --reload
By default it will be running on http://127.0.0.1:8000

To see swagger docs just add to the url: /docs

### Endpoints

* /games (get: list all games)
* /games (post: create a new game, returns game id and a message)
* /games/<id> (get a specific game)
* /users (post/get)


### Tests
Run tests using:
    $ pytest -s --capture=no -vv --cov