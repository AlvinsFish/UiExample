
def save_to_txt(txt_name='', msg=None):
    """保存一个txt"""
    try:
        txt_file = open(txt_name, 'w+')
        txt_file.write(str(msg).replace('\r\n', '\n'))
        txt_file.flush()
        txt_file.close()
    except Exception as e:
        print("error: tools_result_file: save_to_txt")
        print(e.args)
