from context_logger import *


@log_decorator(lambda args: f"x = {args['x']}")
def prints_args_in_log(x):
    log(f"Should have printed x={x}")


@log_decorator("some other function")
def some_other_function():
    log("Probably important")
    with log("Yea vewy impoatant"):
        log("A SDASD")
        log("Vewy Vewy impoatant")
        prints_args_in_log(11)
    log("finished now :)")


def main():
    logger = Logger("Not global anymore")
    with logger:
        log("Something")
        log("This also indents:")
        log("should be indented")
        log(":finished")
        log("Another thing")
        with log("SOmething elese"):
            some_other_function()
            log("Still something else")
        log("Ok finished important")


log("This should be in global logger context.")

if __name__ == "__main__":
    main()
