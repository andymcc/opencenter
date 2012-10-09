import json
import os

from sqlalchemy import *
from migrate import *

from migrate.changeset import schema

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, object_mapper

from db.models import Adventures, Nodes, Tasks, Clusters
from db import api as api


# Base = declarative_base()
meta = MetaData()


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    adventures = [
        {'name': 'install chef',
         'dsl': 'install_chef.json',
         'criteria': 'install_chef.criteria'},
        {'name': 'run chef',
         'dsl': 'run_chef.json',
         'criteria': 'run_chef.criteria'},
        {'name': 'install chef server',
         'dsl':  'install_chef_server.json',
         'criteria': 'install_chef_server.criteria'}]

    for adventure in adventures:
        json_path = os.path.join(
            os.path.dirname(__file__), adventure['dsl'])
        criteria_path = os.path.join(
            os.path.dirname(__file__), adventure['criteria'])
        adventure['dsl'] = json.loads(open(json_path).read())
        adventure['criteria'] = open(criteria_path).read()
        adv = api.adventure_create(adventure)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    types = Table('types', meta, autoload=True)
    types.delete().where(types.c.name == 'Unprovisioned').execute()
