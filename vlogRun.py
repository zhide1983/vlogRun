import re


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
        self.file_name = ''
        self.content = []  # instantiation text
        self.auto_inst = True
        self.parameters = []  # parameter name & instantiated value
        self.port_list = []  # port list info got from module
        self.mapping = []  # port mapping info got from instantiation
        pass


class MacroCell:

    def __init__(self, name, logic):
        self.name = name
        self.logic = logic
        self.next_pt = None
        pass

    def link_cell(self, next_cell):
        self.next_pt = next_cell


class ModuleContList:

    def __init__(self):
        self.m_name = ''
        self.is_ansi_header = True
        self.header_param_content = []
        self.header_port_content = []
        self.param_content = []
        self.port_content = []
        self.type_content = []
        self.localparam_content = []
        self.block_content = []
        pass


def proc_param_list(text_list=None, is_header_param=False, is_local_param=False, param_list=None):
    """
    :param
        text_list: type=string list
        is_header_param: type=bool
            True    : inside the module declaration
            False   : outside the module declaration
        is_local_param: type=bool
            True    : local parameter declaration
            False   : parameter declaration
        param_list: parameter cell list
    """
    idx1 = 0
    str1 = ''
    state = 0
    while idx1 < len(text_list):
        while str1 == '':
            str1 = text_list[idx1]
            idx1 += 1

        if state == 0:
            # idle state, waiting 'parameter' or 'localparam'
            if str1 == 'parameter' or str1 == 'localparam':
                str1 = ''
                state = 1
            elif is_header_param is True and str1 == ',':
                str1 = ''
            elif is_header_param is False and str1 == ';':
                str1 = ''
            else:
                print('Error: got unknown string in parameter declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 1:
            # waiting for identifier
            # maybe exists something like
            #   parameter logic [2:0] A = 3'd2
            if str1 == 'logic' or str1 == 'reg' or str1 == 'wire' or str1 == 'integer' or str1 == 'bit':
                str1 = ''
            elif re.match(r'\w+', str1):
                p = Parameter()
                p.name = re.match(r'\w+', str1).group()
                p.value = ''
                str1 = re.sub(r'^\w+', '', str1)
                state = 2
            else:
                # pass all other things
                str1 = ''
        elif state == 2:
            # waiting for '='
            if re.match('=', str1):
                state = 3
                str1 = re.sub(r'^=', '', str1)
            else:
                print('Error: got unknown string in parameter declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 3:
            # waiting for value
            if re.match(',', str1) and is_header_param is True:
                # [case]
                # ( ...
                # parameter A = 1,
                #           B = 2
                # [OR]
                # parameter A = 1,
                # parameter B = 2
                # ) ...
                state = 4
                param_list.append(p)
                str1 = re.sub(r'^,', '', str1)
            elif re.match(';', str1) and is_header_param is False:
                # [case]
                # parameter A = 1
                #           B = 2
                # [OR]
                # parameter A = 1;
                # parameter B = 2;
                state = 0
                param_list.append(p)
                str1 = re.sub(r'^;', '', str1)
            elif re.match(',', str1) and is_header_param is False:
                # [case]
                # parameter A = 1,
                #           B = 2;
                state = 1
                param_list.append(p)
            elif idx1 == len(text_list):
                # [case]
                # ( ...
                # parameter A = 1)
                # no ',' in the last parameter in ANSI header
                state = 0
                param_list.append(p)
            else:
                p.value += str1
                str1 = ''
        elif state == 4:
            # only for header
            if str1 == 'parameter':
                state = 1
                str1 = ''
            else:
                state = 2
                # do not clean str1 here
    if state != 0:
        print('Error: maybe parameter declaration not completed, check your code!')
        print('State = %d, text = %s' % (state, str1))
        exit(1)


def proc_port_list(text_list=None, is_header_port=False, port_list=None, module=None):
    """
    :param
        text_list: type=string list
        is_header_port: type=bool
            True    : inside the module declaration
            False   : outside the module declaration
        port_list: port cell list
    """
    idx1 = 0
    str1 = ''
    state = 0
    while idx1 < len(text_list):
        if str1 == '':
            str1 = text_list[idx1]
            idx1 += 1

        if state == 0:
            # idle state, waiting for direction 'output/input/inout'
            if str1 == re.match(r'output|input|inout', str1):
                if is_header_port is True:
                    module.is_ansi_header = True
                p = Port()
                p.direction = re.match(r'output|input|inout', str1).group()
                state = 1
                str1 = re.sub(r'^output|input|inout', '', str1)
            elif str1 == re.match('wire|bit|logic|reg', str1):
                # missing direction, use inout by default
                p = Port()
                p.direction = 'inout'
                p.net_type = re.match('wire|bit|logic|reg', str1).group()
                str1 = re.sub(r'^wire|bit|logic|reg', '', str1)
                state = 2
            elif str1 == re.match('signed|unsigned', str1):
                # missing direction, use inout by default
                p = Port()
                p.direction = 'inout'
                p.net_type = 'wire'
                p.signing = re.match('signed|unsigned', str1).group()
                str1 = re.sub(r'^signed|unsigned', '', str1)
                state = 3
            elif re.match(r'\w+', str1):
                if is_header_port:
                    # [case]
                    # (out1, in1, in2)
                    p = Port()
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 7
                else:
                    print('Error: got unknown string in port declaration!')
                    print('State = %d, text = %s' % (state, str1))
                    exit(1)
            elif is_header_port is True and str1 == ',':
                str1 = ''
            elif is_header_port is False and str1 == ';':
                str1 = ''
            else:
                print('Error: got unknown string in port declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 1:
            # waiting for net_type or signing or identifier
            if re.match(r'wire|bit|logic|reg', str1):
                p.net_type = re.match('wire|bit|logic|reg').group()
                str1 = re.sub(r'^wire|bit|logic|reg', '', str1)
                state = 2
            elif re.match(r'signed|unsigend', str1):
                # 'wire' by default
                p.net_type = 'wire'
                p.signing = re.match('signed|unsigned').group()
                str1 = re.sub(r'^signed|unsigned', '', str1)
                state = 3
            elif re.match(r'\[', str1):
                # 'wire'/'unsigned' by default
                p.net_type = 'wire'
                p.signing = 'unsigned'
                str1 = re.sub(r'^\[', '', str1)
                state = 4
            elif re.match(r'\w+', str1):
                if is_header_port:
                    # [case]
                    # (output out1)
                    # 'wire'/'unsigned' by default
                    p.net_type = 'wire'
                    p.signing = 'unsigned'
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                elif module.is_ansi_header and not is_header_port:
                    print('Error: port defined in both inside and outside module header')
                    print('State = %d, text = %s' % (state, str1))
                    exit(1)
                elif not module.is_ansi_header and not is_header_port:
                    # port already generated when parsing header
                    for each_port in m.ports:
                        if each_port.name == p.name:
                            each_port.net_type = 'wire'
                            each_port.signing = 'unsigned'
                            each_port.direction = p.direction
                        else:
                            print('Error: port declared outside the header is not declared inside the header!')
                            print('State = %d, port = %s' % (state, p.name))
                            exit(1)
                    str1 = re.sub(r'^\w+', '', str1)
                state = 7
            else:
                print('Error: got unknown string in port declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 2:
            # waiting for signing or [..:..] or identifier
            if re.match(r'signed|unsigend', str1):
                p.signing = re.match('signed|unsigned').group()
                str1 = re.sub(r'^signed|unsigned', '', str1)
                state = 3
            elif re.match(r'\[', str1):
                # 'unsigned' by default
                p.signing = 'unsigned'
                str1 = re.sub(r'^\[', '', str1)
                state = 4
            elif re.match(r'\w+', str1):
                if is_header_port:
                    # [case]
                    # (output wire out1)
                    # 'unsigned' by default
                    p.signing = 'unsigned'
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                elif module.is_ansi_header and not is_header_port:
                    print('Error: port defined in both inside and outside module header')
                    print('State = %d, text = %s' % (state, str1))
                    exit(1)
                elif not module.is_ansi_header and not is_header_port:
                    # port already generated when parsing header
                    for each_port in m.ports:
                        if each_port.name == p.name:
                            each_port.signing = 'unsigned'
                            each_port.direction = p.direction
                            each_port.net_type = p.net_type
                        else:
                            print('Error: port declared outside the header is not declared inside the header!')
                            print('State = %d, port = %s' % (state, p.name))
                            exit(1)
                    str1 = re.sub(r'^\w+', '', str1)
                state = 7
            else:
                print('Error: got unknown string in port declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 3:
            # waiting for [..:..] or identifier
            if re.match(r'\[', str1):
                # 'wire'/'unsigned' by default
                str1 = re.sub(r'^\[', '', str1)
                state = 4
            elif re.match(r'\w+', str1):
                if is_header_port:
                    # [case]
                    # (output wire unsigned out1)
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                elif module.is_ansi_header and not is_header_port:
                    print('Error: port defined in both inside and outside module header')
                    print('State = %d, text = %s' % (state, str1))
                    exit(1)
                elif not module.is_ansi_header and not is_header_port:
                    # port already generated when parsing header
                    for each_port in m.ports:
                        if each_port.name == p.name:
                            each_port.direction = p.direction
                            each_port.net_type = p.net_type
                            each_port.signing = p.signing
                        else:
                            print('Error: port declared outside the header is not declared inside the header!')
                            print('State = %d, port = %s' % (state, re.match(r'\w+', str1).group()))
                            exit(1)
                    str1 = re.sub(r'^\w+', '', str1)
                state = 7
            else:
                print('Error: got unknown string in port declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 4:
            # waiting for upper range
            if re.search(r':', str1):
                p.up_range += re.match(r'(.*?):', str1).group(1)
                str1 = re.sub(r'(.*?):', '', str1)
                state = 5
            else:
                p.up_range += str1
                str1 = ''
        elif state == 5:
            # waiting for lower range
            if re.search(r']', str1):
                p.lo_range += re.match(r'(.*?)]', str1).group(1)
                str1 = re.sub(r'(.*?)]', '', str1)
                state = 6
            else:
                p.lo_range += str1
                str1 = ''
        elif state == 6:
            if re.match(r'\w+', str1):
                if is_header_port:
                    # [case]
                    # (output wire unsigned [5:0] out1)
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                elif module.is_ansi_header and not is_header_port:
                    print('Error: port defined in both inside and outside module header')
                    print('State = %d, text = %s' % (state, str1))
                    exit(1)
                elif not module.is_ansi_header and not is_header_port:
                    # port already generated when parsing header
                    for each_port in m.ports:
                        if each_port.name == p.name:
                            each_port.direction = p.direction
                            each_port.net_type = p.net_type
                            each_port.signing = p.signing
                            each_port.up_range = p.up_range
                            each_port.lo_range = p.lo_range
                        else:
                            print('Error: port declared outside the header is not declared inside the header!')
                            print('State = %d, port = %s' % (state, p.name))
                            exit(1)
                    str1 = re.sub(r'^\w+', '', str1)
                state = 7
            else:
                print('Error: got unknown string in port declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 7:
            port_list.append(p)
            if str1 == ';':
                state = 0
                str1 = ''
            elif str1 == ',':
                state = 8
                str1 = ''
            elif idx1 == len(content_list) and str1 == '':
                state = 0
            else:
                print('Error: port declaration may be not completed!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        elif state == 8:
            if re.match(r'output|input|inout', str1) and is_header_port:
                state = 0
                # keep str1
            elif re.match(r'wire|bit|logic|reg', str1) and is_header_port:
                state = 0
                # keep str1
            elif re.match(r'signed|unsigned', str1) and is_header_port:
                state = 0
                # keep str1
            elif re.match(r'\w+', str1):
                # [case]
                # output wire [3:0] A,B,C,D;
                if is_header_port:
                    # [case]
                    # (output wire unsigned [5:0] out1,out2,out3)
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                elif module.is_ansi_header and not is_header_port:
                    print('Error: port defined in both inside and outside module header')
                    print('State = %d, text = %s' % (state, str1))
                    exit(1)
                elif not module.is_ansi_header and not is_header_port:
                    # port already generated when parsing header
                    for each_port in m.ports:
                        if each_port.name == p.name:
                            each_port.direction = p.direction
                            each_port.net_type = p.net_type
                            each_port.signing = p.signing
                            each_port.up_range = p.up_range
                            each_port.lo_range = p.lo_range
                        else:
                            print('Error: port declared outside the header is not declared inside the header!')
                            print('State = %d, port = %s' % (state, p.name))
                            exit(1)
                    str1 = re.sub(r'^\w+', '', str1)
                state = 7
            else:
                print('Error: got unknown string in port declaration!')
                print('State = %d, text = %s' % (state, str1))
                exit(1)
        else:
            print('Error: got unknown string in port declaration!')
            print('State = %d, text = %s' % (state, str1))
            exit(1)
    if state != 0:
        print('Error: maybe parameter declaration not completed, check your code!')
        print('State = %d, text = %s' % (state, str1))


def parse_comment(line_list):
    """
    The function parse_comment(line_list) is used to filter out the comment in the verilog file.
    :param line_list: string list with the input text from file
    :return content_list: string list without comment
    """
    line_num = 0
    content_list = []
    inside_comment = False
    str_list1 = []
    while line_num < len(line_list):
        valid_content = line_list[line_num]
        if re.match(r'//\s+\[VlogAutoInst]', valid_content):
            content_list.append(re.match(r'//\s+\[VlogAutoInst].*$', valid_content).group())
            line_num += 1
            continue
        while True:
            if inside_comment is True:
                # to check whether there is a '*/'
                m1 = re.search(r'\*/.*$', valid_content)
                if m1 is not None:
                    valid_content = re.sub(r'^.*\*/', '', valid_content)
                    inside_comment = False
                    continue
                else:
                    valid_content = ''
                    break
            else:  # inside_comment is False
                # search '/*'
                m1 = re.search(r'/\*.*$', valid_content)
                # search '//'
                m2 = re.search(r'//.*$', valid_content)

                if (m1 is not None) and (m2 is not None):
                    if m1.span()[0] < m2.span()[0]:
                        # '/*' ahead, '//' will be omitted
                        if re.search(r'/\*.*?\*/', valid_content) is not None:
                            # '/*...*/' found in the same line, remove it and continue
                            # [NOTE] use the .*? pattern to avoid greedy
                            # .../*aaa*/.../*bbb*/ will match /*aaa*/ only while not /*aaa*/.../*bbb*/
                            valid_content = re.sub(r'/\*.*?\*/', '', valid_content)
                            continue
                        else:
                            # remove /*... and set is_in_comment true
                            valid_content = re.sub(r'/\*.*$', '', valid_content)
                            inside_comment = True
                            # break to finish this line
                            break
                    else:
                        # '//' ahead, '/*' will be omitted
                        valid_content = re.sub(r'//.*$', '', valid_content)
                        break
                elif m1 is not None:
                    # '/*' ahead, '//' will be omitted
                    if re.search(r'/\*.*?\*/', valid_content) is not None:
                        # '/*...*/' found in the same line, remove it and continue
                        # [NOTE] use the .*? pattern to avoid greedy
                        # .../*aaa*/.../*bbb*/ will match /*aaa*/ only while not /*aaa*/.../*bbb*/
                        valid_content = re.sub(r'/\*.*?\*/', '', valid_content)
                        # continue to check the string left
                        continue
                    else:
                        # remove /*... and set is_in_comment true
                        valid_content = re.sub(r'/\*.*$', '', valid_content)
                        inside_comment = True
                        # break to finish this line
                        break
                elif m2 is not None:
                    valid_content = re.sub(r'//.*$', '', valid_content)
                    # break to finish this line
                    break
                else:
                    # neither '/*' nor '//' exists, keep valid_content and
                    # break to finish this line
                    break
        print(line_num, valid_content)
        line_num += 1
        str_list1 = valid_content.split()
        if str_list1:
            for each_str in str_list1:
                content_list += re.split(r'([;,])', each_str)
    print(content_list)
    return content_list


def parse_module(content_list, parse_all_module, module_name, parse_port_only):
    """
    :param content_list: input content without comment
    :param parse_all_module: type = bool, TRUE: parse all modules; FALSE: parse only one module
    :param module_name: when parse_all_module is FALSE, parse only the module specified by module_name,
                        otherwise, this parameter will be ignored
    :param parse_port_only: type = bool, TRUE: parsing stop till port analysis finished, FALSE: parsing all
    :return split_cont_list
    """
    idx = 0
    pstate = 0
    str2 = ''
    m_list = []
    while idx < len(content_list):
        if str2 == '':
            str2 = content_list[idx]
            idx += 1
        if pstate == 0:
            if str2 == 'module':
                if parse_all_module is False and module_name != content_list[idx]:
                    # bypass the not matching module
                    pstate = 10
                else:
                    pstate = 1
                    m1 = ModuleContList()
                    m1.m_name = content_list[idx]
                idx += 1
            str2 = ''
        elif pstate == 1:
            # pstate = 1, already get 'module' and module name
            if re.match(r'#', str2):
                pstate = 2
                m1.is_ansi_header = True
                str2 = re.sub(r'^#', '', str2)
                continue
            elif re.match(r'\(', str2):
                pstate = 3
                str2 = re.sub(r'^\(', '', str2)
                continue
            elif str2 == ';':
                # no port in module declaration
                pstate = 4
                m1.port_content = []
            else:
                print('Error: Syntax error in module definition.')
        elif pstate == 2:
            # parameter in module port declaration, only exists in ANSI header
            if re.match(r'\)', str2):
                # start with '(' and end with ')'
                str2 = re.sub(r'^\)', '', str2)
                pstate = 3
                continue
            elif re.match(r'\(', str2):
                # start with '(' and end with ')'
                str2 = re.sub(r'^\(', '', str2)
                continue
            else:
                m1.header_param_content.append(str2)
                str2 = ''
                continue
        elif pstate == 3:
            # state 3, port declaration in module port
            if str2 == ';':
                m1.header_port_content.append(str2)
                pstate = 4
                str2 = ''
            else:
                m1.header_port_content.append(str2)
                str2 = ''
        elif pstate == 4:
            # pstate 4, module declaration done
            if re.match(r'wire\b|reg\b|logic\b|bit\b', str2):
                pstate = 5
                if parse_port_only is False:
                    m1.type_content.append(str2)
                str2 = ''
            elif re.match(r'parameter\b', str2):
                pstate = 6
                m1.param_content.append(str2)
                str2 = ''
            elif re.match(r'localparam\b', str2):
                pstate = 7
                if parse_port_only is False:
                    m1.localparam_content.append(str2)
                str2 = ''
            elif str2 == 'endmodule':
                m_list.append(m1)
                if parse_all_module:
                    pstate = 0
                    str2 = ''
                else:
                    return m_list
            else:
                pstate = 4
                if parse_port_only is False:
                    m1.block_content.append(str2)
                str2 = ''
        elif pstate == 5:
            if str2 == ';':
                pstate = 4
            m1.type_content.append(str2)
            str2 = ''
            pstate = 4
        elif pstate == 6:
            if str2 == ';':
                pstate = 4
            m1.param_content.append(str2)
            str2 = ''
        elif pstate == 7:
            if str2 == ';':
                pstate = 4
            m1.localparam_content.append(str2)
            str2 = ''
        elif pstate == 10:
            if str2 == 'endmodule':
                pstate = 0
            str2 = ''
        else:
            pass
    return m_list


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
module_list = []

f = open('python_test.v', 'r')
line_num = 0
b = []

while True:
    line = f.readline()
    if not line:
        break
    b.append(line)

# now the valid_content is the comment-removed content
# begin to process
content_list = parse_comment(b)

module_content_list = parse_module(content_list, True, '', False)

for module_content in module_content_list:
    m = Module()
    if module_content.header_param_content:
        proc_param_list(module_content.header_param_content, True, False, m.parameters)
    if module_content.header_port_content:
        proc_port_list(module_content.header_port_content, True, m.ports, m)
    if module_content.param_content:
        proc_param_list(module_content.header_param_content, False, False, m.parameters)
    if module_content.localparam_content:
        proc_param_list(module_content.header_param_content, False, True, m.local_parameters)
    if module_content.port_content:
        proc_port_list(module_content.port_content, False, m.ports, m)






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
    elif re.match(r'always\b|assign\b|initial\b', str1) is not None:
        # process block begins
        break
    elif re.match(r'\/\/ \[VlogAutoInst\]', str1) is not None:
        # maybe instantiation
        break
    elif re.match(r'\w+', str1) is not None and proc_type == 'None':
        # maybe instantiation
        break
    else:
        print('Error: The string is -- ', str1)
        break

# for cell in port_list:
##    cell = Port()
#    print(cell.name, cell.direction, cell.signing, cell.net_type, cell.up_range, cell.lo_range)
#
# for cell in parameter_list:
##    cell = Port()
#    print(cell.name, cell.value)
#
# for cell in localparam_list:
##    cell = Port()
#    print(cell.name, cell.value)


block_list = []


class Block:

    def __init__(self):
        self.type = ''
        self.content = []
        self.signal = []
        pass


is_inside_a_block = False
is_inside_omitted = False
num_begin = 0
num_end = 0

# (c) processing block
while str1 != 'endmodule':
    if is_inside_a_block is False:
        if re.match(r'always\b|assign\b|initial\b', str1) is not None:
            b = Block()
            if re.match(r'always\b', str1) is not None:
                b.type = 'always'
            elif re.match(r'assign\b', str1) is not None:
                b.type = 'assign'
            else:
                b.type = 'initial'
            b.content.append(str1)
            block_list.append(b)
            is_inside_a_block = True
        elif re.match(r'wire\b|reg\b|parameter\b|localpara\b', str1) is not None:
            # other wire/reg/parameter declaration, omitted
            is_inside_omitted = True
            is_inside_a_block = True
        else:
            # maybe instantiation
            block_list.append(Block())
            block_list[-1].type = 'instance'
            block_list[-1].content.append(str1)
            is_inside_a_block = True
    else:
        if is_inside_omitted is True:
            if re.search(r';', str1) is not None:
                block_list[-1].content.append(re.match(r'.*?;', str1))
                str1 = re.sub(r'.*?;', '', str1)
                is_inside_a_block = False
                is_inside_omitted = False
                if str1 != '':
                    continue
            else:
                block_list[-1].content.append(str1)
        elif block_list[-1].type == 'assign' or block_list[-1].type == 'instance':
            if re.search(r';', str1) is not None:
                block_list[-1].content.append(re.match(r'.*?;', str1).group())
                str1 = re.sub(r'.*?;', '', str1)
                is_inside_a_block = False
                if str1 != '':
                    continue
            else:
                block_list[-1].content.append(str1)
        elif block_list[-1].type == 'always' or block_list[-1].type == 'initial':
            if num_begin == 0 and re.search(r';', str1) is not None:
                # never found 'begin' but found ';', end the always block
                block_list[-1].content.append(re.match(r'.*?;', str1).group())
                str1 = re.sub(r'.*?;', '', str1)
                is_inside_a_block = False
                if str1 != '':
                    continue
            elif (num_begin - num_end) == 1 and re.search(r'\bend\b', str1) is not None:
                # found the final 'end' for the always block, end
                block_list[-1].content.append(re.match(r'.*?\bend\b', str1).group())
                str1 = re.sub(r'.*?\bend\b', '', str1)
                is_inside_a_block = False
                num_begin = 0
                num_end = 0
                if str1 != '':
                    continue
            elif re.search(r'\bbegin\b', str1) is not None:
                block_list[-1].content.append(re.match(r'.*?\bbegin\b', str1).group())
                str1 = re.sub(r'.*?\bbegin\b', '', str1)
                num_begin += 1
                if str1 != '':
                    continue
            elif re.search(r'\bend\b', str1) is not None:
                block_list[-1].content.append(re.match(r'.*?\bend\b', str1).group())
                str1 = re.sub(r'.*?\bend\b', '', str1)
                num_end += 1
                if str1 != '':
                    continue
            else:
                block_list[-1].content.append(str1)
        else:
            print("Error: see the block type: " + block_list[-1].type)
            exit(1)
    proc_idx += 1
    str1 = content_list[proc_idx]

# (d) do the instance analysis

inst_list = []

for block_cell in block_list:
    if block_cell.type != 'instance':
        continue
    else:
        # processing instantiation
        inst_list.append(Instance())
        if re.match(r'//\s+\[VlogAutoInst\]', block_cell.content[0]):
            idx2 = 2
            inst_list[-1].m_name = block_cell.content[1]
            str1 = re.sub(r'//\s+\[VlogAutoInst\]\s+', '', block_cell.content[0])
            info = str1.split()
            if not info:
                try:
                    f = open('./' + inst_list[-1].m_name + '.v', 'r')
                    f.close()
                    inst_list[-1].file_name = './' + inst_list[-1].m_name + '.v'
                except IOError:
                    try:
                        f = open('./' + inst_list[-1].m_name + '.sv', 'r')
                        f.close()
                        inst_list[-1].file_name = './' + inst_list[-1].m_name + '.sv'
                    except IOError:
                        print("Warning: Module file cannot be opened for reading")
                    pass
            elif re.search(r'\.v$|.sv$|.vh$|.svh$', info[0]):
                try:
                    f = open(info[0], 'r')
                    f.close()
                    inst_list[-1].file_name = info[0]
                except IOError:
                    print("Warning: Module file cannot be opened for reading")
            elif re.search(r'\\$', info[0]):
                try:
                    f = open(info[0] + inst_list[-1].m_name + '.v', 'r')
                    f.close()
                    inst_list[-1].file_name = info[0]
                except IOError:
                    print("Warning: Module file cannot be opened for reading")
            else:
                try:
                    f = open(info[0] + '\\' + inst_list[-1].m_name + '.v', 'r')
                    f.close()
                    inst_list[-1].file_name = info[0]
                except IOError:
                    print("Warning: Module file cannot be opened for reading")
        else:
            inst_list[-1].m_name = block_cell.content[0]
            idx2 = 1

        if re.match(r'#', block_cell.content[idx2]):
            # parameter
            str1 = re.sub(r'^#', '', block_cell.content[idx2])
            idx2 += 1
            # parsing parameter FSM
            # state 0:  first '('
            # state 1:  '.'
            # state 2:  parameter name
            # state 3:  '('
            # state 4:  parameter value
            # state 5:  ')'
            # state 6:  ',' or end ')'
            state = 0
            while idx2 < len(block_cell.content):
                if str1 == '':
                    str1 = block_cell.content[idx2]
                    idx2 += 1
                if state == 0 and re.match(r'\(', str1):
                    state = 1
                    str1 = re.sub(r'^\(', '', str1)
                    if str1:
                        continue
                elif state == 1 and re.match(r'\.', str1):
                    state = 2
                    str1 = re.sub(r'^\.', '', str1)
                    if str1:
                        continue
                elif state == 2 and re.match(r'\w+', str1):
                    state = 3
                    p = Parameter()
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                    if str1:
                        continue
                elif state == 3 and re.match(r'\(', str1):
                    state = 4
                    str1 = re.sub(r'^\(', '', str1)
                    if str1:
                        continue
                elif state == 4 and re.match(r'\w+', str1):
                    state = 5
                    p.value = re.match(r'\w+', str1).group()
                    inst_list[-1].parameters.append(p)
                    str1 = re.sub(r'^\w+', '', str1)
                    if str1:
                        continue
                elif state == 5 and re.match(r'\)', str1):
                    state = 6
                    str1 = re.sub(r'^\)', '', str1)
                    if str1:
                        continue
                elif state == 6 and re.match(r',', str1):
                    state = 1
                    str1 = re.sub(r'^,', '', str1)
                    if str1:
                        continue
                elif state == 6 and re.match(r'\)', str1):
                    state = 0
                    str1 = re.sub(r'^\)', '', str1)
                    break
                else:
                    print("Error: state = ")
                    print(state)
                    print(" string = " + str1)
                    exit(1)
        if not str1:
            str1 = inst_list[-1].content[idx2]
            idx2 += 1
        inst_list[-1].i_name = re.match(r'\w+', str1).group()
        str1 = re.sub(r'^\w+', '', str1)

        if str1 == '':
            str1 = block_cell.content[idx2]
            idx2 += 1
        # parsing port FSM
        # state 0:  first '('
        # state 1:  '.'
        # state 2:  parameter name
        # state 3:  '('
        # state 4:  parameter value
        # state 5:  ')'
        # state 6:  ',' or end ')'
        state = 0

        while (idx2 < len(block_cell.content)) or (idx2 == len(block_cell.content) and not str1):
            if str1 == '':
                str1 = block_cell.content[idx2]
                idx2 += 1
            if state == 0 and re.match(r'\(', str1):
                state = 1
                str1 = re.sub(r'^\(', '', str1)
                if str1:
                    continue
            elif state == 1 and re.match(r'\.', str1):
                state = 2
                str1 = re.sub(r'^\.', '', str1)
                if str1:
                    continue
            elif state == 2 and re.match(r'\w+', str1):
                state = 3
                p = Parameter()
                p.name = re.match(r'\w+', str1).group()
                str1 = re.sub(r'^\w+', '', str1)
                if str1:
                    continue
            elif state == 3 and re.match(r'\(', str1):
                state = 4
                str1 = re.sub(r'^\(', '', str1)
                if str1:
                    continue
            elif state == 4 and re.match(r'\w+', str1):
                state = 5
                p.value = re.match(r'\w+', str1).group()
                inst_list[-1].mapping.append(p)
                str1 = re.sub(r'^\w+', '', str1)
                if str1:
                    continue
            elif state == 5 and re.match(r'\)', str1):
                state = 6
                str1 = re.sub(r'^\)', '', str1)
                if str1:
                    continue
            elif state == 6 and re.match(r',', str1):
                state = 1
                str1 = re.sub(r'^,', '', str1)
                if str1:
                    continue
            elif state == 6 and re.match(r'\)', str1):
                state = 7
                str1 = re.sub(r'^\)', '', str1)
                if str1:
                    continue
            elif state == 7 and re.match(r';', str1):
                state = 0
                str1 = re.sub(r'^;', '', str1)
                if str1:
                    continue
            else:
                print("Error: state = ")
                print(state)
                print(" string = " + str1)
                exit(1)

print(inst_list)


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
