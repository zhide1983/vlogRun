import re

f = open('python_test.v', 'r')
line_num = 0
b = []

while True:
    line = f.readline()
    if not line:
        break
    b.append(line)


# the code below is the same as in the vim script

class Module:

    # members introduction
    # vlog_style : type(int), 0: v95, 1: v2001

    def __init__(self):
        self.name = ''
        self.ports = []
        self.parameters = []
        self.local_parameters = []
        self.instances = []
        self.reg_signals = []
        self.wire_signals = []
        self.is_ansi_header = True
        pass


class Port:
    # [member] name: string type
    name = ''
    # [member] 'input' | 'output' | 'inout'
    direction = 'inout'
    # [member] 'wire' | 'bit' | 'logic' | 'reg'
    net_type = 'wire'
    # [member] 'signed' | 'unsigned' | ''
    signing = ''
    # [member] upper range
    up_range = 0
    # [member] lower range
    lo_range = 0
    # [member] about macro
    macro_idx = 0
    # [member] comment: string type, one line
    comment = ''

    def __init__(self):
        pass


class Parameter:

    def __init__(self):
        self.name = ''
        self.value = 0
        pass


class LocalParameter:

    def __init__(self):
        self.name = ''
        self.value = 0
        pass


class Instance:

    def __init__(self):
        self.m_name = ''
        self.i_name = ''
        self.auto_inst = False
        self.parameters = []  # parameter name & instantiated value
        self.port_match = []
        pass


class MacroCell:

    def __init__(self, name, logic):
        self.name = name
        self.logic = logic
        self.next_pt = None
        pass

    def link_cell(self, next_cell):
        self.next_pt = next_cell


def proc_para_list(proc_str=''):
    """
    :param
    proc_str: type=string, the string to be processed
    is_in_module_def: type=bool,
        True    : inside the module declaration
        False   : outside the module declaration
    :return type=string, the string left
    :parsing the input string recursively to get the parameter name and value
    """
    global point_to_identifier
    global is_in_para_port_list
    global proc_type
    if proc_str == '':
        return ''
    elif re.match(r'\)', proc_str) and is_in_para_port_list is True:
        # process ')' to stop when inside module declaration
        is_in_para_port_list = False
        return re.sub(r'^\)', '', proc_str)
    elif re.match(r';', proc_str) and is_in_para_port_list is False:
        # process ';' to stop when outside module declaration
        is_in_para_port_list = False
        return proc_str
    elif re.match(r'=', proc_str) is not None:
        # ptr points to value
        point_to_identifier = False
        return proc_para_list(re.sub(r'^=', '', proc_str))
    elif re.match(r',', proc_str) is not None:
        point_to_identifier = True
        return proc_para_list(re.sub(r'^,', '', proc_str))
    elif proc_str == 'parameter':
        proc_type = 'parameter'
        return ''
    elif proc_str == 'localparam':
        proc_type = 'localparam'
        return ''
    elif (re.match(r"'", proc_str) is not None) and (point_to_identifier is False):
        if proc_type == 'parameter':
            parameter_list[-1].value += "'"
        elif proc_type == 'localparam':
            localparam_list[-1].value += "'"
        return proc_para_list(re.sub("^'", '', proc_str))
    elif re.match(r'\w+', proc_str) is not None:
        str2 = re.match(r'\w+', proc_str).group()
        if (str2 == 'logic') or (str2 == 'wire') or (str2 == 'reg') or (str2 == 'integer') or (str2 == 'bit'):
            # pass the type keyword
            return proc_para_list(re.sub(r'^\w+', '', proc_str))
        elif point_to_identifier is True:
            if proc_type == 'parameter':
                p = Parameter()
                p.name = re.match(r'\w+', proc_str).group()
                p.value = ''
                parameter_list.append(p)
            else:
                p = LocalParameter()
                p.name = re.match(r'\w+', proc_str).group()
                p.value = ''
                localparam_list.append(p)
            return proc_para_list(re.sub(r'^\w+', '', proc_str))
        else:
            if proc_type == 'parameter':
                parameter_list[-1].value += re.match(r'\w+', proc_str).group()
                return proc_para_list(re.sub(r'^\w+', '', proc_str))
            else:
                localparam_list[-1].value += re.match(r'\w+', proc_str).group()
                return proc_para_list(re.sub(r'^\w+', '', proc_str))

    else:
        print('Debug: see what is left')
        print(proc_str)
        return ''


def proc_port_list(proc_str):
    """
    :param proc_str: type=string, the string to be processed
    :return type=string, the string left
    :parsing the input string recursively to get the port info
    """
    global is_ansi_header
    global point_to_identifier
    global is_in_port_list
    global is_in_one_port_declare
    global is_in_up_range
    global is_in_lo_range
    if proc_str == '':
        return ''
    elif re.match(r'\)', proc_str) is not None and is_in_port_list is True:
        is_in_port_list = False
        return re.sub(r'^\)', '', proc_str)
    elif re.match(r';', proc_str) is not None and is_in_port_list is False:
        if is_in_port_list is False:
            del port_list[-1]
        return proc_str
    elif re.match(r',', proc_str) is not None:
        is_in_one_port_declare = False
        return proc_port_list(re.sub(r'^,', '', proc_str))
    elif re.match(r'output|input|inout', proc_str) is not None:
        # dealing with direction
        if is_in_port_list is True and is_ansi_header is False:
            is_ansi_header = True
        str2 = re.search(r'^output|input|inout', proc_str).group()
        is_in_one_port_declare = True
        port = Port()
        port.direction = str2
        port_list.append(port)
        return proc_port_list(re.sub(r'^output|input|inout', '', proc_str))
    elif re.match(r'wire|bit|logic|reg', proc_str) is not None:
        # dealing with net_type
        str2 = re.search(r'^wire|bit|logic|reg', proc_str).group()
        if is_in_one_port_declare is True:
            port_list[-1].net_type = str2
        else:
            # missing direction, inout by default
            is_in_one_port_declare = True
            port = Port()
            port.direction = 'inout'
            port.net_type = str2
            port_list.append(port)
        return proc_port_list(re.sub(r'^wire|bit|logic|reg', '', proc_str))
    elif re.match(r'signed|unsigend', proc_str) is not None:
        # dealing with signing
        str2 = re.search(r'^signed|unsigend', proc_str).group()
        if is_in_one_port_declare is True:
            port_list[-1].signing = str2
        else:
            # missing direction, inout/wire by default
            is_in_one_port_declare = True
            port = Port()
            port.direction = 'inout'
            port.net_type = 'wire'
            port.signing = str2
            port_list.append(port)
        return proc_port_list(re.sub(r'^signed|unsigend', '', proc_str))
    elif re.match(r'\[', proc_str) is not None:
        # dealing with range splitter
        is_in_up_range = True
        return proc_port_list(re.sub(r'^\[', '', proc_str))
    elif re.match(r'\]', proc_str) is not None:
        # dealing with range splitter
        is_in_lo_range = False
        return proc_port_list(re.sub(r'^\]', '', proc_str))
    elif re.match(r':', proc_str) is not None:
        # dealing with range splitter
        is_in_up_range = False
        is_in_lo_range = True
        return proc_port_list(re.sub(r'^:', '', proc_str))
    elif re.match(r'\d+', proc_str) is not None:
        # dealing with range
        str2 = re.search(r'^\d+', proc_str).group()
        if is_in_up_range is True:
            port_list[-1].up_range = int(str2)
        elif is_in_lo_range is True:
            port_list[-1].lo_range = int(str2)
        else:
            print('[Error]A digital number should not be here!')
        return proc_port_list(re.sub(r'^\d+', '', proc_str))
    elif re.match(r'\w+', proc_str) is not None:
        # dealing with identifier
        str2 = re.search(r'^\w+', proc_str).group()
        if is_in_port_list is True:
            # inside module port declaration
            if is_ansi_header is False:
                # only the name in the module port list for non-ANSI header
                port = Port()
                port.name = str2
                port_list.append(port)
            elif is_in_one_port_declare is True:
                port_list[-1].name = str2
            else:
                # share the same attributes with the previous one
                port = Port()
                port.net_type = port_list[-1].net_type
                port.up_range = port_list[-1].up_range
                port.lo_range = port_list[-1].lo_range
                port.signing = port_list[-1].signing
                port.direction = port_list[-1].direction
                port.name = str2
                port_list.append(port)
        else:
            # outside module port declaration
            if is_in_one_port_declare is True:
                is_in_list = False
                for each_port in port_list:
                    if each_port.name == str2:
                        each_port.net_type = port_list[-1].net_type
                        each_port.up_range = port_list[-1].up_range
                        each_port.lo_range = port_list[-1].lo_range
                        each_port.signing = port_list[-1].signing
                        each_port.direction = port_list[-1].direction
                        is_in_list = True
                        break
                if is_in_list is False:
                    print('Error: Port ' + str2 + ' not defined in module port list')
                    exit(1)
            else:
                # share the same attributes with the previous one
                is_in_list = False
                for each_port in port_list:
                    if each_port.name == str2:
                        each_port.net_type = port_list[-1].net_type
                        each_port.up_range = port_list[-1].up_range
                        each_port.lo_range = port_list[-1].lo_range
                        each_port.signing = port_list[-1].signing
                        each_port.direction = port_list[-1].direction
                        is_in_list = True
                        break
                if is_in_list is False:
                    print('Error: Port ' + str2 + ' not defined in module port list')
                    exit(1)

        return proc_port_list(re.sub(r'^\w+', '', proc_str))


# is_in_comment: show that whether current line is in a block comment region
is_in_comment = False
# processing the line number
line_num = 0
is_in_module = False
is_in_block = False
is_in_para_port_list = False
is_in_port_list = False
is_in_one_port_declare = False
is_in_up_range = False
is_in_lo_range = False
is_ansi_header = False
proc_type = 'None'

content_list = []
parameter_list = []
localparam_list = []
point_to_identifier = True
port_list = []

while line_num < len(b):
    valid_content = b[line_num]
    while True:
        if is_in_comment is True:
            # to check whether there is a '*/'
            m1 = re.search('\*\/.*$', valid_content)
            if m1 is not None:
                valid_content = re.sub('^.*\*\/', '', valid_content)
                is_in_comment = False
                continue
            else:
                valid_content = ''
                break
        else:  # is_in_comment is False
            # search '/*'
            m1 = re.search('\/\*.*$', valid_content)
            # search '//'
            m2 = re.search('\/\/.*$', valid_content)

            if (m1 is not None) and (m2 is not None):
                if m1.span()[0] < m2.span()[0]:
                    # '/*' ahead, '//' will be omitted
                    if re.search('\/\*.*?\*\/', valid_content) is not None:
                        # '/*...*/' found in the same line, remove it and continue
                        # [NOTE] use the .*? pattern to avoid greedy
                        # .../*aaa*/.../*bbb*/ will match /*aaa*/ only while not /*aaa*/.../*bbb*/
                        valid_content = re.sub('\/\*.*?\*\/', '', valid_content)
                        continue
                    else:
                        # remove /*... and set is_in_comment true
                        valid_content = re.sub('\/\*.*$', '', valid_content)
                        is_in_comment = True
                        # break to finish this line
                        break
                else:
                    # '//' ahead, '/*' will be omitted
                    valid_content = re.sub('\/\/.*$', '', valid_content)
                    break
            elif m1 is not None:
                # '/*' ahead, '//' will be omitted
                if re.search('\/\*.*?\*\/', valid_content) is not None:
                    # '/*...*/' found in the same line, remove it and continue
                    # [NOTE] use the .*? pattern to avoid greedy
                    # .../*aaa*/.../*bbb*/ will match /*aaa*/ only while not /*aaa*/.../*bbb*/
                    valid_content = re.sub('\/\*.*?\*\/', '', valid_content)
                    # continue to check the string left
                    continue
                else:
                    # remove /*... and set is_in_comment true
                    valid_content = re.sub('\/\*.*$', '', valid_content)
                    is_in_comment = True
                    # break to finish this line
                    break
            elif m2 is not None:
                valid_content = re.sub('\/\/.*$', '', valid_content)
                # break to finish this line
                break
            else:
                # neither '/*' nor '//' exists, keep valid_content and
                # break to finish this line
                break
    print(line_num, valid_content)
    line_num += 1
    temp = valid_content.split()
    if temp != []:
        content_list += temp

print content_list

# now the valid_content is the comment-removed content
# begin to process

m = Module();

idx_module = content_list.index('module')

# (a) dealing with module name and module port list
# Feature supported:
# (*) parameter_port_declaration (only subset)
# -----------------------------------------------------
# module a #(A = 0) (port declaration...);
# module a #(parameter A=0, parameter B=0) (port declaration...);
# (*)

# (a.1) get the module name
proc_idx = idx_module + 1
temp = content_list[proc_idx]
m.name = re.match(r'\w*', temp).group()
temp = re.sub(r'^\w*', '', temp)
# case 1: only module name
# case 2: pattern like: 'test()', or 'my_gate(o,a,b);'
#         may contain '(', or port names, or ')', even ';'

# (a.2) processing the parameter in module port declaration
if '#' in temp:
    # parameter_port_declaration exists
    if ('(' in temp) and (')' in temp):
        # all parameter_port_declaration declaration in this string
        # the only case: module_name#(A=1,B=2,C=3)...
        # no 'parameter' keyword exists, no spaces
        temp_para_port_list = re.search(r'#\((.*?\))').group(1)
        str_left = proc_para_list(temp_para_port_list)
    elif '(' in temp:
        is_in_para_port_list = True
        str_left = proc_para_list(re.sub(r'^#\(', '', temp))
    else:
        pass
proc_idx += 1
temp = content_list[proc_idx]

if temp == '#':
    proc_idx += 1
    temp = content_list[proc_idx]
    if re.match(r'\(', temp) is None:
        print ('[Error] missing "(" after "#" in parameter declaration in module port!')
    else:
        is_in_para_port_list = True
        str_left = proc_para_list(re.sub(r'^\(', '', temp))
elif re.match(r'#\(', temp) is not None:
    is_in_para_port_list = True
    str_left = proc_para_list(re.sub(r'^#\(', '', temp))

while is_in_para_port_list is True:
    proc_idx += 1
    str_left = proc_para_list(content_list[proc_idx])

# (a.3) processing the port list
point_to_identifier = True
if str_left == '':
    proc_idx += 1
    str1 = content_list[proc_idx]
else:
    str1 = str_left

if re.match(r'\(', str1) is not None:
    str1 = re.sub(r'^\(', '', str1)
    is_in_port_list = True
    str_left = proc_port_list(str1)
    while is_in_port_list is True:
        proc_idx += 1
        str_left = proc_port_list(content_list[proc_idx])
else:
    print("No port list found in module " + m.name)

# (b) processing parameter/localparameter/port outside module declaration
point_to_identifier = True
if str_left == '':
    proc_idx += 1
    str1 = content_list[proc_idx]
else:
    str1 = str_left

while str1 != 'endmodule':
    if str1 == '':
        proc_idx += 1
        str1 = content_list[proc_idx]
        continue
    elif re.match(r';', str1) is not None:
        point_to_identifier = True
        proc_type = 'None'
        str1 = re.sub(r'^;', '', str1)
        continue
    elif proc_type == 'port':
        str1 = proc_port_list(str1)
        continue
    elif proc_type == 'parameter':
        str1 = proc_para_list(str1)
        continue
    elif proc_type == 'localparam':
        str1 = proc_para_list(str1)
        continue
    elif re.match(r'output\b|input\b|inout\b', str1) is not None:
        proc_type = 'port'
        if is_ansi_header is True:
            print('Error: Do not define port outside module while in ANSI header mode!')
            exit(1)
        str1 = proc_port_list(str1)
        continue
    elif re.match(r'parameter\b', str1) is not None:
        proc_type = 'parameter'
        str1 = proc_para_list(str1)
        continue
    elif re.match(r'localparam\b', str1) is not None:
        proc_type = 'localparam'
        str1 = proc_para_list(str1)
        continue
    elif re.match(r'always\b|asisgn\b|initial\b', str1) is not None:
        # process block begins
        break
    elif re.match(r'\w+', str1) is not None and proc_type == 'None':
        # maybe instantiation
        break
    else:
        print('Error: The string is -- ', str1)
        break

# (c) processing block

for cell in port_list:
#    cell = Port()
    print(cell.name, cell.direction, cell.signing, cell.net_type, cell.up_range, cell.lo_range)

for cell in parameter_list:
#    cell = Port()
    print(cell.name, cell.value)

for cell in localparam_list:
#    cell = Port()
    print(cell.name, cell.value)

# to match the
idx_endmodule = content_list.index('endmodule')

# m.name = content_list[idx_module+1]
#
#    if valid_content is None:
#        break
#    elif re.match('\s*$', valid_content) is None:
#        break
#
#    if is_in_module is False:
#        # todo: processing outside the module
#        if re.search(r'\bmodule\b', valid_content) is None:
#            # wait till 'module' keyword comes
#            break
#        else:
#            # found keyword {module}
#            for word in valid_content.split():
#                if word == 'module':
#                    if
#
#
#
#    else:
#        # todo: processing the module
#
#
#
#
#    root = MacroCell('name', True)
#    a = MacroCell('name', False)
#    root.link_cell(a)
#    a.link_cell(b)
#

print m.name
