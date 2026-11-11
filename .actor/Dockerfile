FROM apify/actor-python:3.12

WORKDIR /usr/src/app
COPY --chown=myuser:myuser pyproject.toml README.md LICENSE ./
COPY --chown=myuser:myuser getsocialapi_facebook/ ./getsocialapi_facebook/
RUN python -m pip install --no-cache-dir 'apify>=3.4,<4' .
COPY --chown=myuser:myuser .actor/main.py ./actor_main.py

CMD ["python", "actor_main.py"]
