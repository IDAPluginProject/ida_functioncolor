import ida_hexrays
import ida_idaapi
import ida_idp
import ida_lines
import re

# Colors
FCOL_START = ida_lines.SCOLOR_DEFAULT + ida_lines.SCOLOR_DREF
FCOL_NAME = ida_lines.SCOLOR_REG
FCOL_NAMESPACE_END = ida_lines.SCOLOR_DEFAULT + ida_lines.SCOLOR_CNAME
FCOL_TEMPLATE = ida_lines.SCOLOR_DEFAULT + ida_lines.SCOLOR_SYMBOL
FCOL_BRACKET = ida_lines.SCOLOR_DEFAULT + ida_lines.SCOLOR_VOIDOP
FCOL_ARG = ida_lines.SCOLOR_DEFAULT + ida_lines.SCOLOR_REG

class HexRaysFunctionColHooks(ida_hexrays.Hexrays_Hooks):
    def _insert_color_at(self, string, index, color):
        return string[:index] + ida_lines.SCOLOR_DEFAULT + color + string[index:]

    def func_printed(self, cfunc):
        pseudocode = cfunc.get_pseudocode()
        for sl in pseudocode:
            #print(sl.line) # Print in output for testing purposes...

            # Basically first line...
            begin_bracket = sl.line.find("\x09(")
            if (begin_bracket != -1):
                # Ignores arguments that are "inline" typedefs or __shifted and other crap (maybe should find better way to fix this)
                if (sl.line.find("\x01(") == -1):
                    # Start (data_type call_convetion)
                    sl.line = sl.line.replace("\x01\x17", FCOL_START)
                    sl.line = sl.line.replace("\x01\x21", FCOL_START)

                    last_space_bb = sl.line.rfind(" ", 0, begin_bracket) # Last space before bracket (Function name start)
                    if (last_space_bb != -1):
                        sl.line = self._insert_color_at(sl.line, last_space_bb + 1, FCOL_NAME) # Function color
                        begin_bracket += 2 # Offset due to color insert

                        # Function namespace end
                        template_start = sl.line.rfind("<", last_space_bb, begin_bracket)
                        template_end = sl.line.rfind(">", last_space_bb, begin_bracket)
                        if (template_start != -1): # Has template?
                            sl.line = sl.line[:last_space_bb] + re.sub("([<)([>])", FCOL_TEMPLATE + "\\1" + ida_lines.SCOLOR_DEFAULT + FCOL_NAME, sl.line[last_space_bb:])
                            sl.line = sl.line[:last_space_bb] + re.sub("(:....:..)([^:]+<)", "\\1" + FCOL_NAMESPACE_END + "\\2", sl.line[last_space_bb:])
                        
                        if (template_end == -1 or begin_bracket > template_end + 3):
                            sl.line = sl.line[:last_space_bb] + re.sub("(:....:..)([^:]+\()", "\\1" + FCOL_NAMESPACE_END + "\\2", sl.line[last_space_bb:])

                    # Left bracket
                    sl.line = re.sub("(..)\(", "\\1" + FCOL_BRACKET + "(", sl.line)

                    # Arg/s
                    sl.line = re.sub("\(..", "(" + FCOL_ARG, sl.line)
                    sl.line = re.sub("(\(....)", "\\1" + FCOL_ARG, sl.line)
            else:
                # Arg
                sl.line = sl.line.replace("\x01\x17", FCOL_ARG)
                sl.line = sl.line.replace("\x01\x21", FCOL_ARG)

            # Break out of loop if we reached end
            end_bracket = sl.line.find(')')
            if (end_bracket != -1 and end_bracket > (len(sl.line) - 8)):
                sl.line = re.sub("(..)\\)", "\\1" + FCOL_BRACKET + ")", sl.line)
                break
        return 0

class HexRaysFunctionColPlugin(ida_idaapi.plugin_t):
    flags = ida_idaapi.PLUGIN_HIDE

    comment = "Color function in pseudocode"
    wanted_name = "Hex-rays Function Colors"
    wanted_hotkey = ""
    help = ""

    def init(self):
        self.hexrays_hooks = None
        self.hexrays_hooks = HexRaysFunctionColHooks()
        self.hexrays_hooks.hook()
        return ida_idaapi.PLUGIN_KEEP

    def run(self, arg):
        return

    def term(self):
        if self.hexrays_hooks:
            self.hexrays_hooks.unhook()
        pass

def PLUGIN_ENTRY():
    return HexRaysFunctionColPlugin()
