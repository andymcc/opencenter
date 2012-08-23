#!/usr/bin/env python
import os
import sys
import resource

from flask import Flask, Response, request, session, jsonify, url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import UnmappedInstanceError

from database import db_session
from models import Nodes, Roles, Clusters

from ConfigParser import ConfigParser
from getopt import getopt, GetoptError
from pprint import pprint

import logging
import backends

app = Flask(__name__)


@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/roles', methods=['GET', 'POST'])
def list_roles():
    if request.method == 'POST':
        if 'name' in request.json:
            name = request.json['name']
            desc = None
            if 'description' in request.json:
                desc = request.json['description']
            role = Roles(name, desc)
            db_session.add(role)
            try:
                db_session.commit()
                msg = {'status': 201, 'message': 'Role Created',
                           'role': dict((c, getattr(role, c))
                                        for c in role.__table__.columns.keys()),
                           'ref': url_for('role_by_id', role_id=role.id)}
                resp = jsonify(msg)
                resp.status_code = 201
            except IntegrityError, e:
                msg = {'status': 500, "message": e.message}
                resp = jsonify(msg)
                resp.status_code = 500
        else:
            msg = {'status': 400, "message": "Attribute 'name' was not provided"}
            resp = jsonify(msg)
            resp.status_code = 400
        return resp
    else:
        role_list = dict(roles=[dict((c, getattr(r, c))
                         for c in r.__table__.columns.keys())
                         for r in Roles.query.all()])
        resp = jsonify(role_list)
        return resp


@app.route('/roles/<role_id>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def role_by_id(role_id):
    if request.method == 'PATCH' or request.method == 'POST':
        message = {
            'status': 501,
            'message': 'Not Implemented'
        }
        resp = jsonify(message)
        resp.status_code = 501
    elif request.method == 'PUT':
        r = Roles.query.filter_by(id=role_id).first()
        if 'name' in request.json:
            r.name = request.json['name']
        if 'description' in request.json:
            r.description = request.json['description']
        #TODO(shep): this is an un-excepted db call
        db_session.commit()
        resp = jsonify(dict((c, getattr(r, c))
                       for c in r.__table__.columns.keys()))
    elif request.method == 'DELETE':
        r = Roles.query.filter_by(id=role_id).first()
        try:
            db_session.delete(r)
            db_session.commit()
            msg = {'status': 200, 'message': 'Role deleted'}
            resp = jsonify(msg)
            resp.status_code = 200
        except UnmappedInstanceError, e:
            msg = {'status': 404, 'message': 'Resource not found',
                   'role': {'id': role_id}}
            resp = jsonify(msg)
            resp.status_code = 404
    else:
        r = Roles.query.filter_by(id=role_id).first()
        if r is None:
            msg = {'status': 404, 'message': 'Resource not found',
                   'role': {'id': role_id}}
            resp = jsonify(msg)
            resp.status_code = 404
        else:
            resp = jsonify(dict((c, getattr(r, c))
                           for c in r.__table__.columns.keys()))
    return resp


@app.route('/clusters', methods=['GET'])
def list_clusters():
    cluster_list = dict(clusters=[dict((c, getattr(r, c))
                        for c in r.__table__.columns.keys())
                        for r in Clusters.query.all()])
    resp = jsonify(cluster_list)
    return resp


@app.route('/nodes', methods=['GET', 'POST'])
def node():
    if request.method == 'POST':
        hostname = request.json['hostname']

        # Grab role_id from payload
        role_id = None
        if 'role_id' in request.json:
            role_id = request.json['role_id']

        # Grab cluster_id from payload
        cluster_id = None
        if 'cluster_id' in request.json:
            cluster_id = request.json['cluster_id']

        node = Nodes(hostname, role_id, cluster_id)
        # TODO(shep): need to break if IntegrityError is thrown
        db_session.add(node)
        db_session.commit()
        message = {
            'status': 201,
            'message': 'Node Created',
            'ref': url_for('node_by_id', node_id=node.id)
        }
        resp = jsonify(message)
        resp.status_code = 201
        return resp
    else:
        node_list = dict(nodes=[dict((c, getattr(r, c))
                         for c in r.__table__.columns.keys())
                         for r in Nodes.query.all()])
        resp = jsonify(node_list)
        return resp


@app.route('/nodes/<node_id>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def node_by_id(node_id):
    if request.method == 'PUT':
        message = {
            'status': 501,
            'message': 'Not Implemented'
        }
        resp = jsonify(message)
        resp.status_code = 501
        return resp
    elif request.method == 'PATCH':
        message = {
            'status': 501,
            'message': 'Not Implemented'
        }
        resp = jsonify(message)
        resp.status_code = 501
        return resp
    elif request.method == 'DELETE':
        r = Nodes.query.filter_by(id=node_id).first()
        db_session.delete(r)
        db_session.commit()
        return 'Deleted node: %s' % (node_id)
    elif request.method == 'GET':
        r = Nodes.query.filter_by(id=node_id).first()
        pprint(r)
        if r is None:
            resp = jsonify(dict())
        else:
            resp = jsonify(dict((c, getattr(r, c))
                           for c in r.__table__.columns.keys()))
        return resp

if __name__ == '__main__':
    debug = False
    configfile = None
    daemonize = False
    config_hash = { "main": {} }
    global backend

    bind_address = '0.0.0.0'
    bind_port = 8080

    def do_daemonize():
        if os.fork():
            sys.exit(0)
        else:
            os.setsid()
            os.chdir('/')
            os.umask(0)
            if os.fork():
                sys.exit(0)

        # Resource usage information.
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = 1024 # ?

        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:
                pass

        # reopen stds to/from /dev/null
        os.open("/dev/null", os.O_RDWR) # this will be 0
        os.dup2(0,1)
        os.dup2(0,2)

    def usage():
        print "%s: [options]\n"
        print "Options:"
        print " -c <configfile>         use exernal config"
        print " -d                      daemonize"
        print " -v                      verbose"

    try:
        opts, args = getopt(sys.argv[1:], "c:dv")
    except GetoptError, e:
        print str(e)
        usage()
        sys.exit(1)

    for o, a in opts:
        if o == '-c':
            configfile = a
        elif o == '-v':
            debug = True
        elif o == '-d':
            daemonize = True
        else:
            usage()
            sys.exit(1)

    # set up logging
    LOG = logging.getLogger()
    LOG.addHandler(logging.FileHandler("/dev/stdout"))

    # read the config file
    if configfile:
        config = ConfigParser()
        config.read(configfile)

        config_hash = dict(
            [(s, dict(config.items(s))) for s in config.sections()])

        bind_address = config_hash['main'].get('bind_address', '0.0.0.0')
        bind_port = int(config_hash['main'].get('bind_port', '8080'))

        backend_module = config_hash['main'].get('backend', 'null')
        backend = backends.load(
            backend_module, config_hash.get('%s_backend' % backend_module, {}))

    app.debug = debug

    if daemonize and not debug:
        do_daemonize()

    # open log handler
    # set up logging
    if 'logfile' in config_hash['main']:
        for handler in LOG.handlers:
            LOG.removeHandler(handler)

        handler = logging.FileHandler(config_hash['main']['logfile'])
        LOG.addHandler(handler)

    if 'loglevel' in config_hash['main']:
        LOG.setLevel(config_hash['main']['loglevel'])


    LOG.debug("Starting app server on %s:%d" % (bind_address, bind_port))
    app.run(host=bind_address, port=bind_port)