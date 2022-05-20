from context_logger import *


@log_decorator(lambda args: f"x = {args['x']}; {args['y']=}")
def prints_args_in_log(x, y=2):
    log(f"Should have printed x={x}")


@log_decorator("Hi from a log_decorator.")
def some_other_function():
    log("This is from inside the function.")
    with Logger("diff. prefix"):
        log("We now entered a logger with a different prefix")
        log("Although we ")
        log(":can deindent")
        log(":too far,")

    log("After the context manager ends, it is back to normal.")


def main():
    logger = Logger("Not global")

    log("This should still be global.")

    with logger:
        log("Entered non-global logger.")

        log("The following should be indented.:")

        log("The following should be back to normal.")

        log(":Normal.")

        log("Indenting again::")

        log("Indented.")

        log(":This should be normal and following should be indented.:")

        log("Test.")

        log(":The following tests function calls.:")

        with log("Function 1"):
            some_other_function()

        with log("Function 2"):
            prints_args_in_log(11)


log("This should be in global logger context.")

if __name__ == "__main__":
    main()
