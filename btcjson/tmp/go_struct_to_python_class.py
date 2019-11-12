####################################
# This is a tool to make life easier
# A program to write program
# with some adition help;)
####################################

import re


# input list of fields and class name
# output python class
# don't go into ast now
def generate_python_class(struct_name, field_lst):
    field_lst = [field_transfer(field) for field in field_lst]

    result = "class %s:\n" % struct_name
    result += "    def __init__(self,"

    for field in field_lst:
        result += "%s," % field

    result = result.rstrip(",")

    result += "):\n"

    for field in field_lst:
        result += "        self.%s = %s\n" % (field, field)
    return result


# Input HelloWorld
# Output hello_world
def field_transfer(field):
    new_field = ""
    index = -1

    for c in field:
        index += 1
        if c.isupper():
            if index == 0:
                new_field += c.lower()
            else:
                new_field += "_%s" % c.lower()

        else:
            new_field += c
    return new_field


# Input
example_s = """
type GetMempoolInfoResult struct {
	Size  int64 `json:"size"`
	Bytes int64 `json:"bytes"`
}
"""


# output: GetMempoolInfoResult, [Size, Bytes]
# Note: a very strict version
def read_go_struct(s):
    "s is a string"

    line = 0
    cache = ''
    add_to_cache = False

    struct_name = re.findall(r'type (.+) struct', s)[0]
    fields = re.findall(r'\t(.+?) .+\n', s)

    return struct_name, fields


def main(s):
    struct_name, fields = read_go_struct(s)
    result = generate_python_class(struct_name, fields)
    print(result)
