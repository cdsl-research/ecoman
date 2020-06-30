import re
from collections import defaultdict


_params = {}

def setter(stack, value, before=None):
    # 値渡しにするため
    my_stack = list(stack)

    # print('setter()', 'stack=', my_stack)

    # スタックが空
    if len(my_stack) <= 1:
        key = my_stack.pop(0)
        before[key] = value
        # import json
        # print('before:', json.dumps(before, indent=4))

    else:
        key = my_stack.pop(0)
        if before.get(key) is None:
            before[key] = dict()
        setter(my_stack, value, before[key])


def parser(content):
    stack2 = []
    value_tmp = ''
    is_annotation = False
    _params2 = {}

    for line in content:
        l2 = line.strip()
        # print('cur-stack:', stack2)
        # print('line:', l2)

        # Header
        if re.match(r'\Aannotation = "', l2):
            is_annotation = True
            key = 'annotation'
            value_tmp += l2.strip('annotation = "')
            stack2.append(key)
            continue

        # Footer
        elif is_annotation and re.match(r'\Aproduct = ', l2):
            is_annotation = False
            # ",を取り除く
            setter(stack2, value_tmp[:-2], _params2)
            del stack2[-1]
            value_tmp = ''
            # continueは不要

        # Body
        elif is_annotation:
            value_tmp += l2
            continue

        if re.match(r'\A"\S+",?\Z', l2):
            # print('"xxx",', '\t', l2)
            value = l2.strip(',')[1:-2]
            setter(stack2, value, _params2)

        elif re.match(r'\A\S+ = [\'\(\"][\S ]*[\'\)\"],?\Z', l2):
            # print('xxx = "yyy",', '\t', l2)
            key = l2.split(' = ')[0]
            value = l2.split(' = ')[1].strip(',')[1:-1]
            stack2.append(key)
            setter(stack2, value, _params2)
            del stack2[-1]

        elif re.match(r'\A\S+ = \d+,?\Z', l2):
            # print('xxx = 123,', '\t', l2)
            key = l2.split(' = ')[0]
            value = l2.split(' = ')[1].strip(',')
            stack2.append(key)
            setter(stack2, int(value), _params2)
            del stack2[-1]

        elif re.match(r'\A\S+ = (true|false|\<unset\>)+,?\Z', l2):
            # print('xxx = false,', '\t', l2)
            key = l2.split(' = ')[0]
            value = l2.split(' = ')[1].strip(',').capitalize()
            value2 = None if value == '<unset>' else eval(value)
            stack2.append(key)
            setter(stack2, value2, _params2)
            del stack2[-1]

        elif re.match(r'\A\S+ = \(\S+\) null,?\Z', l2):
            # print('xxx = (yyy) null', '\t', l2)
            key = l2.split(' = ')[0]
            stack2.append(key)
            setter(stack2, None, _params2)
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
            # print('Fail to parse:', l2)
            pass

    return _params2


def main():
    with open('cmd.txt') as f:
        content = f.readlines()

    result = parser(content)
    import json
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
