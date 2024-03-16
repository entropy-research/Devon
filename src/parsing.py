def parse_code(code):
    return code.split("<AST>")[1].split("</AST>")[0]

end_json_symbol = "</END_JSON>"
begin_xml = "<root>"