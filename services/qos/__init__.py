# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import QoSHandler

def get_service(config):
    return QoSHandler(config.qos.pickle_dir, config.qos.config_dir)

