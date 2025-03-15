"""
修复 six.moves 导入问题的补丁文件

这个文件应该在项目启动前导入，它会修改 sys.modules 来添加 six.moves 模块，
使得 'from six.moves import _thread' 这样的导入语句能够正常工作。
"""

import sys
import six

# 确保 six.moves 可以被直接导入
if 'six.moves' not in sys.modules:
    sys.modules['six.moves'] = six.moves

# 确保 six.moves 的子模块也可以被直接导入
for attr_name in dir(six.moves):
    if not attr_name.startswith('_') or attr_name == '_thread':
        module_name = f'six.moves.{attr_name}'
        if module_name not in sys.modules:
            try:
                attr = getattr(six.moves, attr_name)
                sys.modules[module_name] = attr
            except (ImportError, AttributeError):
                pass 