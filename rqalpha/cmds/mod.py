# -*- coding: utf-8 -*-
# 版权所有 2020 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：
#         http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

import os
from importlib import import_module

import six
import click

from rqalpha.utils.config import dump_config
from .entry import cli


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.help_option('-h', '--help')
@click.argument('cmd', nargs=1, type=click.Choice(['list', 'enable', 'disable']))
@click.argument('params', nargs=-1)
def mod(cmd, params):
    """
    Mod management command

    rqalpha mod list \n
    rqalpha mod enable xxx \n
    rqalpha mod disable xxx \n

    """
    def list(params):
        """
        List all mod configuration
        """
        from tabulate import tabulate
        from rqalpha.utils.config import get_mod_conf

        mod_config = get_mod_conf()
        table = []

        for mod_name, mod in mod_config['mod'].items():
            table.append([
                mod_name,
                ("enabled" if mod['enabled'] else "disabled")
            ])

        headers = [
            "name",
            "status"
        ]

        six.print_(tabulate(table, headers=headers, tablefmt="psql"))
        six.print_("You can use `rqalpha mod list/install/uninstall/enable/disable` to manage your mods")

    def change_mod_status(mod_list, enabled):
        for mod_name in mod_list:
            if "rqalpha_mod_" in mod_name:
                mod_name = mod_name.replace("rqalpha_mod_", "")

            # check whether is installed
            module_name = "rqalpha_mod_" + mod_name
            if module_name.startswith("rqalpha_mod_sys_"):
                module_name = "rqalpha.mod." + module_name

            try:
                import_module(module_name)
            except ModuleNotFoundError:
                print("can not find mod [{}] !, ignore".format(mod_name))
                continue

            from rqalpha.utils.config import user_mod_conf_path, load_yaml
            user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}
            user_conf['mod'].setdefault(mod_name, {'enabled': enabled})['enabled'] = enabled
            dump_config(user_mod_conf_path(), user_conf)

    def enable(params):
        """
        enable mod
        """
        mod_list = params
        change_mod_status(mod_list, True)

    def disable(params):
        """
        disable mod
        """
        mod_list = params
        change_mod_status(mod_list, False)

    def install(params):
        """
        Install third-party Mod
        """
        from pip import main as pip_main
        from pip.commands.install import InstallCommand

        params = [param for param in params]

        options, mod_list = InstallCommand().parse_args(params)

        params = ["install"] + params

        for mod_name in mod_list:
            mod_name_index = params.index(mod_name)
            if mod_name.startswith("rqalpha_mod_sys_"):
                six.print_('System Mod can not be installed or uninstalled')
                return
            if "rqalpha_mod_" in mod_name:
                lib_name = mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            params[mod_name_index] = lib_name

        # Install Mod
        installed_result = pip_main(params)

        # Export config
        from rqalpha.utils.config import load_yaml, user_mod_conf_path
        user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}

        if installed_result == 0:
            # 如果为0，则说明安装成功
            if len(mod_list) == 0:
                """
                主要是方便 `pip install -e .` 这种方式 本地调试 Mod 使用，需要满足以下条件:
                1.  `rqalpha mod install -e .` 命令是在对应 自定义 Mod 的根目录下
                2.  该 Mod 必须包含 `setup.py` 文件（否则也不能正常的 `pip install -e .` 来安装）
                3.  该 Mod 包名必须按照 RQAlpha 的规范来命名，具体规则如下
                    *   必须以 `rqalpha-mod-` 来开头，比如 `rqalpha-mod-xxx-yyy`
                    *   对应import的库名必须要 `rqalpha_mod_` 来开头，并且需要和包名后半部分一致，但是 `-` 需要替换为 `_`, 比如 `rqalpha_mod_xxx_yyy`
                """
                mod_name = _detect_package_name_from_dir()
                mod_name = mod_name.replace("-", "_").replace("rqalpha_mod_", "")
                mod_list.append(mod_name)

            for mod_name in mod_list:
                if "rqalpha_mod_" in mod_name:
                    mod_name = mod_name.replace("rqalpha_mod_", "")
                if "==" in mod_name:
                    mod_name = mod_name.split('==')[0]
                user_conf['mod'][mod_name] = {}
                user_conf['mod'][mod_name]['enabled'] = False

            dump_config(user_mod_conf_path(), user_conf)

        return installed_result

    def uninstall(params):
        """
        Uninstall third-party Mod
        """

        from pip import main as pip_main
        from pip.commands.uninstall import UninstallCommand

        params = [param for param in params]

        options, mod_list = UninstallCommand().parse_args(params)

        params = ["uninstall"] + params

        for mod_name in mod_list:
            mod_name_index = params.index(mod_name)
            if mod_name.startswith("rqalpha_mod_sys_"):
                six.print_('System Mod can not be installed or uninstalled')
                return
            if "rqalpha_mod_" in mod_name:
                lib_name = mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            params[mod_name_index] = lib_name

        # Uninstall Mod
        uninstalled_result = pip_main(params)
        # Remove Mod Config
        from rqalpha.utils.config import user_mod_conf_path, load_yaml
        user_conf = load_yaml(user_mod_conf_path()) if os.path.exists(user_mod_conf_path()) else {'mod': {}}

        for mod_name in mod_list:
            if "rqalpha_mod_" in mod_name:
                mod_name = mod_name.replace("rqalpha_mod_", "")

            del user_conf['mod'][mod_name]

        dump_config(user_mod_conf_path(), user_conf)
        return uninstalled_result

    locals()[cmd](params)


def _detect_package_name_from_dir(params):
    setup_path = os.path.join(os.path.abspath(params[-1]), 'setup.py')
    if not os.path.exists(setup_path):
        return None
    return os.path.split(os.path.dirname(setup_path))[1]
