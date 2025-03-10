def concat_with_for_loop_simple():
    result = ""
    for i in range(10):
        result += str(i)
    return result


def show_details():
    details = "This is a sentence."
    print(details.upper().lower().upper().capitalize().upper().replace("|", "-"))
