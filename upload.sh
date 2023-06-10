#!/usr/bin/bash
rsync -avP --exclude=.venv --exclude=.git --exclude=db.sqlite --exclude=config.toml ./ lighthouse@43.155.62.103:~/cherino/
