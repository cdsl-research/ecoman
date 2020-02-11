import re
from collections import defaultdict


nested_dict = lambda: defaultdict(nested_dict)
_params = nested_dict()


def setter(stack, value, before=None):
    # 値渡しにするため
    my_stack = list(stack)
    # print('setter()', 'stack=', stack)

    if len(my_stack) <= 1:
        key = my_stack.pop(0)
        if before is None:
            return
        before[key] = value
    else:
        key = my_stack.pop(0)
        before = _params[key]
        setter(my_stack, value, before)


def parser(content):
    stack2 = []
    for line in content:
        l2 = line.strip()
        # print('cur-stack:', stack2)
        # print('line:', l2)
        
        if re.match(r'\A"\S+",?\Z', l2):
            # print('"xxx",', '\t', l2)
            value = l2.strip(',')[1:-2]
            setter(stack2, value)

        elif re.match(r'\A\S+ = [\'\(\"][\S ]*[\'\)\"],?\Z', l2):
            # print('xxx = "yyy",', '\t', l2)
            key = l2.split(' = ')[0]
            value = l2.split(' = ')[1].strip(',')[1:-1]
            stack2.append(key)
            setter(stack2, value)
            del stack2[-1]

        elif re.match(r'\A\S+ = \d+,?\Z', l2):
            # print('xxx = 123,', '\t', l2)
            key = l2.split(' = ')[0]
            value = l2.split(' = ')[1].strip(',')
            stack2.append(key)
            setter(stack2, int(value))
            del stack2[-1]

        elif re.match(r'\A\S+ = (true|false|\<unset\>)+,?\Z', l2):
            # print('xxx = false,', '\t', l2)
            key = l2.split(' = ')[0]
            value = l2.split(' = ')[1].strip(',').capitalize()
            value2 = None if value == '<unset>' else eval(value)
            stack2.append(key)
            setter(stack2, value2)
            del stack2[-1]

        elif re.match(r'\A\S+ = \(\S+\) null,?\Z', l2):
            # print('xxx = (yyy) null', '\t', l2)
            key = l2.split(' = ')[0]
            stack2.append(key)
            setter(stack2, None)
            del stack2[-1]

        elif re.match(r'\A\(\S+\) \{\Z', l2):
            # print('(xxx) {', '\t', l2)
            key = l2[1:-3]
            stack2.append(key)

        elif re.match(r'\A\S+ = \(\S+\) [\[\{]\Z', l2):
            # print('xxx = (yyy) {', '\t', l2)
            key = l2.split(' = ')[0]
            stack2.append(key)

        elif re.match(r'\A[\]\}],?\Z', l2):
            # print('end', '\t', l2)
            try:
                del stack2[-1]
            except IndexError:
                pass

        else:
            # print(' '*8, '\t', l2)
            print('Fail to parse:', l2)

    return _params       


def main():
    with open('cmd.txt') as f:
        content = f.readlines()

    result = parser(content)
    # debug
    for k,v in result.items():
        for k2,v2 in v.items():
            print(k,k2,'=',v2)


if __name__ == '__main__':
    main()
