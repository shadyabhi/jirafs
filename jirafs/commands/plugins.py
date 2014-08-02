from blessings import Terminal

from jirafs import utils
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Enable/Disable or display information about installed issue plugins """
    MIN_VERSION = '1.0'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, parser, **kwargs):
        enabled_plugins = folder.get_enabled_plugins()
        if args.disabled_only and args.enabled_only:
            parser.error(
                "--disabled-only and --enabled-only are mutually exclusive."
            )
        if args.enable and args.enable not in enabled_plugins:
            parser.error(
                "Plugin '%s' is not installed." % args.enable
            )

        return self.plugins(folder, args)

    def add_arguments(self, parser):
        parser.add_argument('--verbose', action='store_true', default=False)
        parser.add_argument(
            '--enabled-only',
            dest='enabled_only',
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--disabled-only',
            dest='disabled_only',
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--enable',
        )
        parser.add_argument(
            '--disable',
        )
        parser.add_argument(
            '--global',
            dest='set_global',
            default=False,
            action='store_true',
        )

    def build_plugin_dict(self, enabled, available):
        all_plugins = {}
        for plugin_name, cls in available.items():
            all_plugins[plugin_name] = {
                'enabled': False,
                'class': cls,
            }
        for plugin_instance in enabled:
            plugin_name = plugin_instance.plugin_name
            all_plugins[plugin_name]['enabled'] = True
            all_plugins[plugin_name]['instance'] = plugin_instance

        return all_plugins

    def plugins(self, folder, args):
        t = Terminal()

        enabled_plugins = folder.get_enabled_plugins()
        available_plugins = utils.get_installed_plugins()

        if args.enable:
            if args.set_global:
                utils.set_global_config_value(
                    'plugins', args.enable, 'enabled',
                )
            else:
                folder.set_config_value(
                    'plugins', args.enable, 'enabled'
                )
        elif args.disable:
            if args.set_global:
                utils.set_global_config_value(
                    'plugins', args.disable, 'disabled',
                )
            else:
                folder.set_config_value(
                    'plugins', args.disable, 'disabled'
                )
        else:
            all_plugins = self.build_plugin_dict(
                enabled_plugins,
                available_plugins
            )

            for plugin_name, plugin_data in all_plugins.items():
                if plugin_data['enabled'] and args.disabled_only:
                    continue
                if not plugin_data['enabled'] and args.enabled_only:
                    continue
                if plugin_data['enabled']:
                    color = t.bold
                else:
                    color = t.normal

                print(
                    color + plugin_name + t.normal +
                    (
                        ' (Enabled)'
                        if plugin_data['enabled']
                        else (
                            ' (Disabled; enable by running `jirafs '
                            'plugins --enable=%s`)' % plugin_name
                        )
                    )
                )
                if args.verbose:
                    doc_string = (
                        plugin_data['class'].__doc__.strip().split('\n')
                    )
                    for line in doc_string:
                        print('     %s' % line)
