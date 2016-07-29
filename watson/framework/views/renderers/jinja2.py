# -*- coding: utf-8 -*-
import importlib
import os
import types
import jinja2
from watson.common import datastructures
from watson.framework.views.renderers import abc


def template_to_posix_path(template, sep=None):
    if not sep:
        sep = os.path.sep
    return template.replace(sep, '/')


class Renderer(abc.Renderer):
    _env = None
    _debug_mode = False

    @property
    def env(self):
        return self._env

    def __init__(self, config=None, application=None):
        super(Renderer, self).__init__(config)
        self._debug_mode = application.config['debug']['enabled']
        self.register_loaders()
        _types = ('filters', 'globals')
        for _type in _types:
            for module in config[_type]:
                mod = importlib.import_module(module)
                dic = datastructures.module_to_dict(
                    mod, ignore_starts_with='__')
                for name, definition in dic.items():
                    obj = '{0}.{1}'.format(module, name)
                    env_type = getattr(self.env, _type)
                    if isinstance(definition, types.FunctionType):
                        env_type[name] = definition
                    else:
                        env_type[name] = application.container.get(obj)

    def register_loaders(self):
        user_loaders = [jinja2.FileSystemLoader(path)
                        for path in self.config.get('paths')]
        system_loaders = [jinja2.PackageLoader(*package)
                          for package in self.config.get('packages')]
        if self._debug_mode:
            loaders = system_loaders + user_loaders
        else:
            loaders = user_loaders + system_loaders
        kwargs = self.config.get('environment', {})
        kwargs['loader'] = jinja2.ChoiceLoader(loaders)
        self._env = jinja2.Environment(**kwargs)

    def __call__(self, view_model, context=None):
        template = self._env.get_template(
            '{0}.{1}'.format(template_to_posix_path(view_model.template),
                             self.config['extension']))
        return template.render(context=context or {}, **view_model.data)
