FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN git config --global user.name "git_game"
RUN git config --global user.email "git_game@game.com"
RUN git config --global init.defaultBranch main

COPY ./services/api .

RUN chmod a+rx /app/git_orchestrator/git_editor

ENV INSIDE_DOCKER=1
ENV PATH="/usr/local/bin:${PATH}"

CMD ["bash", "./entrypoint.sh"]