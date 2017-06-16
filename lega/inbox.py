#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Service creating the inboxes
#
####################################

It picks a message from a local queue, containing information about a user.

It inserts it in the database and creates the necessary location in the inbox server.
'''

import sys
import os
import logging
import subprocess
from pathlib import Path

from .conf import CONF
from . import exceptions
from . import amqp as broker
from . import db
from .utils import catch_user_error, generate_password
from .crypto import generate_key

LOG = logging.getLogger('inbox')


@catch_user_error
def work(data):
    '''Creates a user account, given the details from `data`.
    '''

    user_id = data['user_id']
    elixir_id = data['elixir_id']

    LOG.info(f'Handling account creation for user {elixir_id}')

    user_home = Path( CONF.get('inbox','user_home',raw=True) % { 'user_id': user_id } )

    # Create user (might raise exception)
    cmd = CONF.get('inbox','create_account',raw=True) # should we sanitize first?
    subprocess.run(cmd.format(home=user_home,comment=elixir_id,user_id=user_id),
                   shell=True,
                   check=True,
                   stderr = subprocess.DEVNULL)

    # Generate pub/priv key
    pubkey, seckey = generate_key(2048)

    with open(f'{user_home}/.ssh/authorized_keys', 'a') as ssh_keys:
        ssh_keys.write(pubkey)
        ssh_keys.write('\n')

    # Generate password
    password = generate_password(10)
    os.system(f'echo "{user_id}:{password}" | chpasswd -e')

    # Update database
    db.update_user(user_id, password, pubkey, seckey)

    LOG.info(f'Account created for user {elixir_id}')
    return {
        'user_id': user_id,
        'elixir_id': elixir_id,
        'pubkey' : pubkey,
        'seckey': seckey,
        'password': password,
    }

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    LOG.info('Starting a connection to the local broker')

    connection = broker.get_connection('local.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume(channel,
                       work,
                       from_queue  = CONF.get('local.broker','users_queue'),
                       to_channel  = channel,
                       to_exchange = CONF.get('local.broker','exchange'),
                       to_routing  = CONF.get('local.broker','routing_account'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()