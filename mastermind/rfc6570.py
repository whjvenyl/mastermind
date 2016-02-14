try:
   from urllib.parse import quote
except ImportError:
  from urllib import quote
import uritemplate
import re
from collections import deque

SEQ_TPL = re.compile("{([/+.#]?)([^+#./;?&|!@}]+)}")
PAIRS_TPL = re.compile("{([?;&])([^+#./;?&|!@}]+)}")

##
# This RFC 6570 implementation implements Level 1, 2 and 3. Level 4 is not
# implemented as it is not useful for Mastermind.
#
# Levels 1, 2 and 3 are implemented with specialised functions based on the
# expected input, a list of values or a list of tuples.  The first case applies
# values in strict order, the second by key.

##
# When partial is False and there are no seguments left it follows the RFC
# so the result is empty.  But, when partial is True, the expression is kept
# intact so you can apply multiple times the function with different
# sequences:
#
#   expand_sequence("{var}", []) # => ""
#   expand_sequence("{var}", [], partial=True) # => "{var}"
#   expand_sequence("{foo}/{bar}", ["a"], partial=True) # => "a/{bar}"
#
def expand_sequence(tpl, segments, partial=False):
    queue = deque(segments)
    operators = "/.#"
    reserved = ":/?#[]@!$&'()*+,;="

    def take_varlist(variable_list, limit):
        return (variable_list[0:limit], variable_list[limit:])

    def sub(m):
        if len(queue) == 0 and partial: return m.group(0)
        if len(queue) == 0: return ""

        operator = m.group(1)
        expression = m.group(2)
        variable_list, leftovers = take_varlist(expression.split(","), len(queue))
        prefix = operator if (operator in operators) else ""
        infix = operator if operator == "/" else ","
        safe = reserved if operator else ""

        tokens = map(lambda _: quote(queue.popleft(), safe=safe), variable_list)

        leftovers_tpl = ""
        if len(leftovers) > 0 and partial:
            leftovers_tpl = "{{{}{}}}".format(operator, ",".join(leftovers))

        return "{}{}{}".format(prefix, infix.join(tokens), leftovers_tpl)

    r = SEQ_TPL.sub(sub, tpl)
    print(tpl,r)
    return r


##
# When partial is False and there are no matching pairs it follows the RFC
# so the result is empty.  But, when partial is True, the expression is kept
# intact so you can apply multiple times the function with different
# sequences:
#
#   expand_pair("{?x}", []) # => ""
#   expand_pair("{?x}", [], partial=True) # => "{?x}"
#
def expand_pairs(tpl, pairs, partial=False):
    def join_query_pair(x, y):
        return "=".join([x, y])

    def join_param_pair(x, y):
        return "=".join([x, y]) if y else x

    def take_leftovers(varlist, pairs):
        return filter(lambda v: not any(map(lambda (x, _): v == x, pairs)), varlist)

    def take_tokens(varlist, pairs, operator):
        join_pair = join_param_pair if operator == ";" else join_query_pair
        return [join_pair(x, y) for x, y in pairs
                                if any(map(lambda v: x == v, varlist))]

    def sub(m):
        if len(pairs) == 0 and partial: return m.group(0)
        if len(pairs) == 0: return ""

        operator = m.group(1)
        expression = m.group(2)
        prefix = operator
        infix = operator if operator == ";" else "&"

        variable_list = map(lambda x: x.strip(), expression.split(","))

        tokens = take_tokens(variable_list, pairs, operator)
        leftovers = take_leftovers(variable_list, pairs)

        leftovers_tpl = ""
        if len(leftovers) > 0 and partial:
            leftovers_tpl = "{{{}{}}}".format(operator, ",".join(leftovers))

        return "{}{}{}".format(prefix, infix.join(tokens), leftovers_tpl)

    r = PAIRS_TPL.sub(sub, tpl)
    # print(tpl,r)
    return r
