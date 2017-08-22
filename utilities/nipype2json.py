""" nipype2json.py

Makes a Porcupine-compatible dictionary of nodes.
Created by Tomas Knapen (Free University, Amsterdam) &
Lukas Snoek (University of Amsterdam)
"""
import inspect
import importlib
import os.path as op


def node2json(node, module=None, custom_node=False, category="Custom", module_path=None):
    """ Converts nipype nodes to Porcupine-compatible json-files.

    This function takes a Nipype node from a Python module and
    creates a Porcupine json-file.

    Parameters
    ----------
    node : Nipype Node object
        Nipype node to create a json-dict for.
    module : str
        Name of module in which node is contained.
    custom_node : bool
        Whether the node is a custom node or a node within
        the Nipype package.
    category : str
        Category of node (default: "Custom")
    module_path : str
        Path to module (only relevant for custom modules)
    """

    if module is None:
        module = "custom"

    if custom_node:
        category = "Custom"

    all_inputs, mandatory_inputs = _get_inputs(node, custom_node)
    all_outputs = _get_outputs(node, custom_node)
    descr = _get_descr(node, custom_node)

    this_category = [category]
    if module.split('.')[0] == 'algorithms':
        this_category.append('algorithms')

    if custom_node:
        this_category.append(module)
    else:
        this_category.append(module.split('.')[1])

    if not custom_node:
        sub_modules = _get_submodule(node)[1:]
        if sub_modules and sub_modules[0] != this_category[-1]:
            this_category.extend(sub_modules)

    web_url = _get_web_url(node, module, custom_node)
    node_name = _get_node_name(node, custom_node)
    import_statement = _get_import_statement(node, module, module_path)

    titleBlock = {

        'name': '%s.%s' % (this_category[-1], node_name),
        'web_url': web_url,
        'code': [{
            'language': category,
            'comment': descr,
            'argument': {
                "name": this_category[-1] + '.%s()' % node_name,
                "import": import_statement
            }
        }]
    }

    dockerCode = _docker_block(this_category[-1])
    if dockerCode is not None:
        
        titleBlock['code'].append({
            'language': 'Docker',
            'argument': {
                "name": dockerCode
            }
        })

    ports = []

    for inp in all_inputs:
        codeBlock = {
            'language': category,
            'argument': {
                "name": inp
            }
        }

        is_mandatory = inp in mandatory_inputs

        port = {
            'input': True,
            'output': False,
            'visible': True if is_mandatory else False,
            'editable': True,
            'name': inp,
            'code': [codeBlock]
        }

        ports.append(port)

    ports = sorted(ports, reverse=True, key=lambda p: p['visible'])

    for outp in all_outputs:

        codeBlock = {
            'language': category,
            'argument': {
                "name": outp
            }
        }

        port = {
            'input': False,
            'output': True,
            'visible': True,
            'editable': False,
            'name': outp,
            'code': [codeBlock]
        }
        ports.append(port)

    node_to_return = {
        'category': this_category,
        'title': titleBlock,
        'ports': ports
    }
    return node_to_return


def _get_inputs(node, custom_node=True):

    all_inputs, mandatory_inputs = [], []
    if custom_node:
        TO_SKIP = ['function_str', 'trait_added', 'trait_modified',
                   'ignore_exception']
        all_inputs.extend([inp for inp in node.inputs.traits().keys()
                           if not inp in TO_SKIP])
        mandatory_inputs.extend(all_inputs)
    else:
        all_inputs.extend([inp for inp in node.input_spec().traits().keys()
                           if not inp.startswith('trait')])
        mandatory_inputs.extend(node.input_spec().traits(mandatory=True).keys())

    return all_inputs, mandatory_inputs


def _get_outputs(node, custom_node=True):

    if custom_node:
        TO_SKIP = ['trait_added', 'trait_modified']
        outputs = list(node.aggregate_outputs().traits().keys())
        all_outputs = [outp for outp in outputs
                       if not outp in TO_SKIP]
    else:
        if hasattr(node, 'output_spec'):
            if node.output_spec is not None:
                all_outputs = [outp for outp in node.output_spec().traits().keys()
                               if not outp.startswith('trait')]
            else:
                all_outputs = []
        else:
            all_outputs = []

    return all_outputs


def _get_descr(node, custom_node=True):

    if custom_node:
        name = _get_node_name(node, custom_node=True)
        descr = 'Custom interface wrapping function %s' % name
    else:
        if hasattr(node, 'help'):
            descr = node.help(returnhelp=True).splitlines()[0]
        else:
            descr = node.__name__

    return descr


def _get_web_url(node, module, custom_node):

    if custom_node:
        return ''

    is_algo = module.split('.')[0] == 'algorithms'

    web_url = 'https://nipype.readthedocs.io/en/latest/interfaces/generated/'

    all_sub_modules = _get_submodule(node)

    if is_algo or len(all_sub_modules) < 2:
        module = 'nipype.' + module

    web_url += module

    if len(all_sub_modules) > 1:

        if not is_algo:
            web_url += '/%s.html' % all_sub_modules[1]
        else:
            web_url += '.html'

        web_url += '#%s' % node.__name__.lower()
    else:
        web_url += '.html#%s' % node.__name__.lower()

    return web_url


def _get_node_name(node, custom_node):

    if custom_node:
        function_code = node.inputs.function_str
        name = function_code.split(':')[0].split('(')[0].split(' ')[-1]
        return name
    else:
        return node.__name__


def _get_import_statement(node, module, module_path):

    try:
        importlib.import_module('nipype.' + module)
        import_statement = "import nipype.%s as %s" % (module, module.split('.')[-1])
    except ImportError:
        import_statement = "sys.path.append('%s')\nimport %s"
        import_statement = import_statement % (op.abspath(op.dirname(module_path)), module)

    return import_statement



def _get_submodule(node):

    module_tree = inspect.getmodule(node).__name__
    all_sub_modules = [n for n in module_tree.split('.')
                       if n not in ('interfaces', 'nipype')]
    return all_sub_modules


DOCKER_DICTIONARY = {'afni': '--afni version=latest',
                     'ants': '--ants version=2.2.0',
                     'freesurfer': '--freesurfer version=6.0.0 min=true',
                     'fsl': '--fsl version=5.0.10',
                     'mrtrix': '--mrtrix3'}


def _docker_block(module):
    try:
        return DOCKER_DICTIONARY[module]
    except KeyError:
        return None


def pyfunc2json():
    """ Experimental function to convert Python functions
    directly to Porcupine's JSON format (by converting it)
    first to a Nipype node. """
    pass
