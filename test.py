from context_logger import *


@log_decorator(lambda args: f"x = {args['x']}")
def prints_args_in_log(x):
    log(f"Should have printed x={x}")


@log_decorator("this is a log decorator")
def some_other_function():
    log("probably important")
    with log("very important"):
        log("asdasd")
        log("very very important")
        prints_args_in_log(11)
    log("finished now :)")


def main():
    logger = Logger("Not global anymore")

    log("still global?")

    with logger:
        log("Something")
        log("This also indents:")
        log("should be indented")
        log(":finished")
        log("Another thing")
        with log("Something else"):
            log("in context manager")
            some_other_function()
            log("Still something else")
        log("Ok finished")

    log("still??")


log("This should be in global logger context.")

if __name__ == "__main__":
    main()
