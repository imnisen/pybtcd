# UsageFlag define flags that specify additional properties about the
# circumstances under which a command can be used.
class UsageFlag(int):
    pass


# UFWalletOnly indicates that the command can only be used with an RPC
# server that supports wallet commands.
UFWalletOnly = UsageFlag(1 << 0)

# UFWebsocketOnly indicates that the command can only be used when
# communicating with an RPC server over websockets.  This typically
# applies to notifications and notification registration functions
# since neiher makes since when using a single-shot HTTP-POST request.
UFWebsocketOnly = UsageFlag(1 << 1)

# UFNotification indicates that the command is actually a notification.
# This means when it is marshalled, the ID must be nil.
UFNotification = UsageFlag(1 << 2)

# highestUsageFlagBit is the maximum usage flag bit and is used in the
# stringer and tests to ensure all of the above constants have been
# tested.
highestUsageFlagBit = UsageFlag(1 << 3)



#########################
# Not same register
########################
register_cmds = {}
def register_cmd_name(cmd_name, cmd):
    register_cmds[cmd_name] = cmd

def find_cmd(cmd_name):
    if cmd_name not in register_cmds:
        raise Exception("command name %s is not found" % cmd_name)

    return register_cmds[cmd_name]

# # TODO let's add this latter
# def new_cmd(cmd_name, *args):  # args only pass as list
#     cmd = find_cmd(cmd_name)
#     return cmd.unmarshal_json(args)
