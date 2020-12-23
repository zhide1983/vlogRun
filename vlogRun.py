# =========================================================
# -               Verilog Code Generator                  -
# ---------------------------------------------------------
# Author    : Chen Zhide (Derek Chen)
# Emain     : chen_zhide@sina.cn
# Project   : https://github.com/zhide1983/vlogRun
#
# ---------------------------------------------------------



import re
import sys

# the code below is the same as in the vim script

class Module:

    # members introduction
    # vlog_style : type(int), 0: v95, 1: v2001

    def __init__(self):
        self.name = ''
        self.ports = []
        self.nets = []
        self.parameters = []
        self.local_parameters = []
        self.instances = []
        self.reg_signals = []
        self.wire_signals = []
        self.is_ansi_header = True
        self.block_list = []
        self.instance_list = []
        pass


class Net:
    # [member] name: string type
    name = ''
    # [member] 'wire' | 'bit' | 'logic' | 'reg'
    net_type = 'wire'
    # [member] 'signed' | 'unsigned' | ''
    signing = ''
    # [member] upper range
    up_range = ''
    # [member] lower range
    lo_range = ''
    # [member] about macro
    macro_idx = 0
    # [member] comment: string type, one line
    comment = ''

    def __init__(self):
        pass


class Port(Net):
    # [member] 'input' | 'output' | 'inout'
    direction = 'inout'

    def __init__(self):
        pass


# class Port:
#    # [member] name: string type
#    name = ''
#    # [member] 'input' | 'output' | 'inout'
#    direction = 'inout'
#    # [member] 'wire' | 'bit' | 'logic' | 'reg'
#    net_type = 'wire'
#    # [member] 'signed' | 'unsigned' | ''
#    signing = ''
#    # [member] upper range
#    up_range = ''
#    # [member] lower range
#    lo_range = ''
#    # [member] about macro
#    macro_idx = 0
#    # [member] comment: string type, one line
#    comment = ''
#
#    def __init__(self):
#        pass


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
        self.m_param = []  # parameter name & value in the module
        self.i_param = []  # parameter name & value when instantiation
        self.m_port = []  # port list info got from module
        self.i_port = {}  # port mapping info got from instantiation
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
        self.block_list = []
        pass


class Block:

    def __init__(self):
        self.type = ''
        self.content = []
        self.signal = []
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
    while idx1 < len(text_list) or str1 != '':
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
                p.value += str1
                param_list.append(p)
                str1 = ''
                state = 0
            else:
                p.value += str1
                str1 = ''
        elif state == 4:
            # only for header
            if str1 == 'parameter':
                state = 1
                str1 = ''
            else:
                state = 1
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
        while str1 == '' and idx1 < len(text_list):
            str1 = text_list[idx1]
            idx1 += 1

        if state == 0:
            # idle state, waiting for direction 'output/input/inout'
            if re.match(r'output\b|input\b|inout\b', str1):
                if is_header_port is True:
                    module.is_ansi_header = True
                p = Port()
                p.direction = re.match(r'output\b|input\b|inout\b', str1).group()
                state = 1
                str1 = re.sub(r'^output\b|input\b|inout\b', '', str1)
            elif re.match(r'wire\b|bit\b|logic\b|reg\b', str1):
                # missing direction, use inout by default
                p = Port()
                p.direction = 'inout'
                p.net_type = re.match(r'wire\b|bit\b|logic\b|reg\b', str1).group()
                str1 = re.sub(r'^wire\b|bit\b|logic\b|reg\b', '', str1)
                state = 2
            elif re.match(r'signed\b|unsigned\b', str1):
                # missing direction, use inout by default
                p = Port()
                p.direction = 'inout'
                p.net_type = 'wire'
                p.signing = re.match(r'signed\b|unsigned\b', str1).group()
                str1 = re.sub(r'^signed\b|unsigned\b', '', str1)
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
            if re.match(r'wire\b|bit\b|logic\b|reg\b', str1):
                p.net_type = re.match(r'wire\b|bit\b|logic\b|reg\b', str1).group()
                str1 = re.sub(r'^wire\b|bit\b|logic\b|reg\b', '', str1)
                state = 2
            elif re.match(r'signed\b|unsigend\b', str1):
                # 'wire' by default
                p.net_type = 'wire'
                p.signing = re.match(r'signed\b|unsigned\b').group()
                str1 = re.sub(r'^signed\b|unsigned\b', '', str1)
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
                p.signing = re.match('signed|unsigned', str1).group()
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
            elif idx1 == len(text_list) and str1 == '':
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
                    p = Port()
                    p.name = re.match(r'\w+', str1).group()
                    p.direction = port_list[-1].direction
                    p.net_type = port_list[-1].net_type
                    p.signing = port_list[-1].signing
                    p.up_range = port_list[-1].up_range
                    p.lo_range = port_list[-1].lo_range
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


def proc_block_list(text_list=None, block_list=None, inst_list=None):
    """
    :param text_list, type = string list, all the block content
    :param block_list, type = list of Block, used to return
    :param inst_list, type = instance list
    """
    idx1 = 0
    str1 = ''
    is_inside_a_block = False
    is_inside_omitted = False
    num_begin = 0
    num_end = 0
    state = 0
    while idx1 < len(text_list):
        while str1 == '' and idx1 < len(text_list):
            str1 = text_list[idx1]
            idx1 += 1
        if state == 0:
            if re.match(r'always\b|assign\b|initial\b', str1):
                b = Block()
                if re.match(r'always\b', str1) is not None:
                    b.type = 'always'
                    state = 1
                elif re.match(r'assign\b', str1) is not None:
                    b.type = 'assign'
                    state = 2
                else:
                    b.type = 'initial'
                    state = 1
                b.content.append(str1)
                block_list.append(b)
            else:
                # instance
                i = Instance()
                i.content.append(str1)
                inst_list.append(i)
                state = 3
            str1 = ''
        elif state == 1:
            if num_begin == 0 and str1 == ';':
                # never found 'begin' but found ';', end the always block
                block_list[-1].content.append(str1)
                str1 = ''
                state = 0
            elif (num_begin - num_end) == 1 and str1 == 'end':
                # found the final 'end' for the always block, end
                block_list[-1].content.append(str1)
                str1 = ''
                num_begin = 0
                num_end = 0
                state = 0
            elif re.search(r'\bbegin\b', str1):
                block_list[-1].content.append(re.match(r'.*?\bbegin\b', str1).group())
                str1 = re.sub(r'.*?\bbegin\b', '', str1)
                num_begin += 1
            elif re.search(r'\bend\b', str1):
                block_list[-1].content.append(re.match(r'.*?\bend\b', str1).group())
                str1 = re.sub(r'.*?\bend\b', '', str1)
                num_end += 1
            else:
                block_list[-1].content.append(str1)
                str1 = ''
        elif state == 2:
            if str1 == ';':
                state = 0
            block_list[-1].content.append(str1)
            str1 = ''
        elif state == 3:
            if str1 == ';':
                state = 0
            inst_list[-1].content.append(str1)
            str1 = ''
    if state != 0:
        print('Error: maybe block declaration not completed, check your code!')
        print('State = %d, text = %s' % (state, str1))


def proc_inst_list(inst_list=None):
    for inst in inst_list:
        idx1 = 0
        str1 = ''
        state = 0
        while idx1 < len(inst.content):
            while str1 == '' and idx1 < len(inst.content):
                str1 = inst.content[idx1]
                idx1 += 1
            if state == 0:
                if re.match(r'//\s+\[VlogAutoInst]', str1):
                    # process the INFO line
                    inst.auto_inst = True
                    inst.m_name = inst.content[idx1]
                    idx1 += 1
                    str1 = re.sub(r'//\s+\[VlogAutoInst]\s+', '', str1)
                    info = str1.split()
                    if not info:
                        try:
                            file_name = './' + inst.m_name + '.v'
                            f1 = open(file_name, 'r')
                            inst.file_name = file_name
                            state = 1
                        except IOError:
                            try:
                                file_name = './' + inst.m_name + '.sv'
                                f1 = open(file_name, 'r')
                                inst.file_name = file_name
                                state = 1
                            except IOError:
                                print("Warning: Module file cannot be opened for reading")
                                inst.auto_inst = False
                                state = 20
                                pass
                    elif re.search(r'\.v$|.sv$|.vh$|.svh$', info[0]):
                        try:
                            f1 = open(info[0], 'r')
                            inst.file_name = info[0]
                            state = 1
                        except IOError:
                            print("Warning: Module file cannot be opened for reading")
                            inst.auto_inst = False
                            state = 20
                    elif re.search(r'/$', info[0]):
                        try:
                            file_name = info[0] + inst.m_name + '.v'
                            f1 = open(file_name, 'r')
                            inst.file_name = file_name
                            state = 1
                        except IOError:
                            print("Warning: Module file cannot be opened for reading")
                            inst.auto_inst = False
                            state = 20
                    else:
                        try:
                            file_name = info[0] + '/' + inst.m_name + '.v'
                            f1 = open(file_name, 'r')
                            inst.file_name = file_name
                            state = 1
                        except IOError:
                            print("Warning: Module file cannot be opened for reading")
                            inst.auto_inst = False
                            state = 20
                else:
                    inst.auto_inst = False
                    inst.m_name = str1
                    str1 = ''
                    state = 20
            elif state == 1:
                # open file and process it
                line_list1 = []
                while True:
                    line1 = f1.readline()
                    if not line1:
                        break
                    line_list1.append(line1)
                content_list1 = parse_comment(line_list1)
                m_content_list = parse_module(content_list1, False, inst.m_name, True)
                if m_content_list:
                    mi = Module()
                    if m_content_list[0].header_param_content:
                        proc_param_list(m_content_list[0].header_param_content, True, False, mi.parameters)
                    if m_content_list[0].header_port_content:
                        proc_port_list(m_content_list[0].header_port_content, True, mi.ports, mi)
                    if m_content_list[0].param_content:
                        proc_param_list(m_content_list[0].param_content, False, False, mi.parameters)
                    if m_content_list[0].port_content:
                        proc_port_list(m_content_list[0].port_content, False, mi.ports, mi)
                    inst.m_param = mi.parameters
                    inst.m_port = mi.ports
                    state = 2
                else:
                    print('Warning: cannot find module in the file' + inst.file_name)
                    inst.auto_inst = False
                    state = 20
                str1 = ''
            elif state == 2:
                # Auto instance
                if re.match(r'#', str1):
                    # parameter
                    str1 = re.sub(r'^#', '', str1)
                    state = 3
                elif re.match(r'\w+', str1):
                    # instance name
                    inst.i_name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 11
                elif re.match(r'\(', str1):
                    # missing instance name
                    str1 = re.sub(r'^\(', '', str1)
                    state = 12
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 3:
                if re.match(r'\(', str1):
                    str1 = re.sub(r'^\(', '', str1)
                    state = 4
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 4:
                if re.match(r'\.', str1):
                    str1 = re.sub(r'^\.', '', str1)
                    state = 5
                elif re.match(r'\)', str1):
                    str1 = re.sub(r'^\)', '', str1)
                    state = 10
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 5:
                if re.match(r'\w+', str1):
                    p = Parameter()
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 6
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 6:
                if re.match(r'\(', str1):
                    str1 = re.sub(r'^\(', '', str1)
                    state = 7
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 7:
                if re.match(r'\w+', str1):
                    p.value = re.match(r'\w+', str1).group()
                    inst.i_param.append(p)
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 8
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 8:
                if re.match(r'\)', str1):
                    str1 = re.sub(r'^\)', '', str1)
                    state = 9
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 9:
                if re.match(r',', str1):
                    str1 = re.sub(r'^,', '', str1)
                    state = 4
                elif re.match(r'\)', str1):
                    str1 = re.sub(r'^\)', '', str1)
                    state = 10
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 10:
                if re.match(r'\w+', str1):
                    inst.i_name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 11
                elif re.match(r'\(', str1):
                    str1 = re.sub(r'^\(', '', str1)
                    state = 12
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 11:
                if re.match(r'\(', str1):
                    str1 = re.sub(r'^\(', '', str1)
                    state = 12
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 12:
                if re.match(r'\.', str1):
                    str1 = re.sub(r'^\.', '', str1)
                    state = 13
                elif re.match(r'\)', str1):
                    str1 = re.sub(r'\)', '', str1)
                    state = 18
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 13:
                if re.match(r'\w+', str1):
                    p = Parameter()
                    p.name = re.match(r'\w+', str1).group()
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 14
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 14:
                if re.match(r'\(', str1):
                    str1 = re.sub(r'^\(', '', str1)
                    state = 15
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 15:
                if re.match(r'\w+', str1):
                    p.value = re.match(r'\w+', str1).group()
                    inst.i_port[p.name] = p.value
                    str1 = re.sub(r'^\w+', '', str1)
                    state = 16
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 16:
                if re.match(r'\)', str1):
                    str1 = re.sub(r'^\)', '', str1)
                    state = 17
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 17:
                if re.match(r',', str1):
                    state = 12
                    str1 = re.sub(r'^,', '', str1)
                elif re.match(r'\)', str1):
                    state = 18
                    str1 = re.sub(r'^\)', '', str1)
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 18:
                if str1 == ';':
                    state = 0
                    str1 = ''
                else:
                    print('Error: In instance processing, wrong string input!')
                    print(' state = %s, string = %s' % (state, str1))
                    exit(1)
            elif state == 20:
                break
            else:
                print('Error: In instance processing, wrong string input!')
                print(' state = %s, string = %s' % (state, str1))
                exit(1)
        if state == 20:
            state = 0
            continue


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
        while str2 == '':
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
                pstate = 4
                str2 = ''
            elif re.match(r'\(', str2):
                str2 = re.sub(r'^\(', '', str2)
            elif re.search(r'\)', str2):
                m1.header_port_content.append(re.match(r'(.*?)\)', str2).group(1))
                str2 = re.sub(r'.*?\)', '', str2)
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


def main():
    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print('Error: Cannot open file: ' + sys.argv[1])
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
            proc_param_list(module_content.param_content, False, False, m.parameters)
        if module_content.localparam_content:
            proc_param_list(module_content.localparam_content, False, True, m.local_parameters)
        if module_content.port_content:
            proc_port_list(module_content.port_content, False, m.ports, m)
        # separate block content into 'always'/'initial'/'assign'/'instance' sub-blocks
        if module_content.block_content:
            proc_block_list(module_content.block_content, module_content.block_list, m.instance_list)

        proc_inst_list(m.instance_list)

        print('output auto instantiation')
        print('-------------------------')

        for inst in m.instance_list:
            if inst.i_param:
                print(inst.m_name + ' #(')
                for each_param in inst.i_param:
                    last = each_param == inst.i_param[-1]
                    if last:
                        print('    .' + each_param.name + ' '*(23-len(each_param.name))
                              + '(' + each_param.value + ' '*(23-len(each_param.value)) + ')')
                    else:
                        print('    .' + each_param.name + ' ' * (23 - len(each_param.name))
                          + '(' + each_param.value + ' ' * (23 - len(each_param.value)) + '),')
                print(') ' + inst.i_name + ' (')
            else:
                print(inst.m_name + ' ' + inst.i_name + ' (')
            for each_port in inst.m_port:
                last = each_port == inst.m_port[-1]
                if each_port.direction == 'output' or each_port.direction == 'inout':
                    w = Net()
                    w.net_type = 'wire'
                    if inst.i_port.has_key(each_port.name):
                        w.name = inst.i_port[each_port.name]
                    else:
                        w.name = each_port.name
                    w.up_range = each_port.up_range
                    w.lo_range = each_port.lo_range
                    m.nets.append(w)
                    if last:
                        print('    .' + each_port.name + ' '*(23-len(each_port.name))
                              + '(' + w.name + ' '*(23-len(w.name)) + ')')
                    else:
                        print('    .' + each_port.name + ' ' * (23 - len(each_port.name))
                              + '(' + w.name + ' ' * (23 - len(w.name)) + '),')
                else:
                    w = Net()
                    w.net_type = 'wire'
                    if inst.i_port.has_key(each_port.name):
                        w.name = inst.i_port[each_port.name]
                    else:
                        w.name = each_port.name
                    w.up_range = each_port.up_range
                    w.lo_range = each_port.lo_range
                    m.nets.append(w)
                    if last:
                        print('    .' + each_port.name + ' ' * (23 - len(each_port.name))
                              + '(' + w.name + ' ' * (23 - len(w.name)) + ')')
                    else:
                        print('    .' + each_port.name + ' ' * (23 - len(each_port.name))
                              + '(' + w.name + ' ' * (23 - len(w.name)) + '),')
            print(');')

            print('output signal width inferrer')
            print('----------------------------')

            # todo: the case that up_range/lo_range are parameter or define
            for net in m.nets:
                if net.lo_range:
                    ts = net.net_type + ' [' + net.up_range + ':' + net.lo_range + ']'
                    ts += ' ' * (24 - len(ts))
                    ts += net.name + ';'
                else:
                    ts = net.net_type
                    ts += ' ' * (24 - len(ts))
                    ts += net.name + ';'
                print(ts)

        pass


if __name__ == '__main__':
    main()

