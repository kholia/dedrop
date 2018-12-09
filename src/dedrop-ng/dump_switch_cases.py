import idautils
import idaapi
import idc

myfunc=0
jump_table = dict()
switch_map = {}

for func in idautils.Functions():
    if 'PyEval_EvalFrameEx' == idc.GetFunctionName(func):
        print('[+] Found target function!')
        myfunc = func
        break


def is_user_name(ea):
    f = idc.GetFlags(ea)
    return idc.hasUserName(f)

for (startea, endea) in Chunks(myfunc):
    for head in Heads(startea, endea):
        switch_info = idaapi.get_switch_info_ex(head)
        if switch_info != None:
            num_cases = switch_info.get_jtable_size()
            # print(num_cases)
            # print 'good jump table found'
            results = idaapi.calc_switch_cases(head, switch_info)
            for idx in xrange(results.cases.size()):
                cur_case = results.cases[idx]
                ret = is_user_name(results.targets[idx])
                if ret:
                    name = idc.NameEx(BADADDR, results.targets[idx])
                    if "TARGET_" in name or "PRED_" in name:
                        for cidx in xrange(len(cur_case)):
                            number = int(cur_case[cidx])
                            name = name.replace("TARGET_", "").replace("PRED_", "")
                            if name not in jump_table:
                                jump_table[name] = number

print(jump_table)
