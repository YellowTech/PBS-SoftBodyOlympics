from requests_futures.sessions import FuturesSession
import time
import ujson as json
from codetiming import Timer


session = FuturesSession()


with Timer(text="Request {:.8f}"):
    future_one = session.get('https://input.yellowtech.ch/input')
    print(future_one.done())

    while not future_one.done():
        print("Not done yet")

with Timer(text="JSON {:.8f}"):
    print(json.loads(future_one.result().content))

