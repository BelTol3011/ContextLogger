from context_logger import *

import asyncio


@async_safe
@log_decorator(lambda args: f"running test {args['j']}")
async def test(j):
    with Logger(f"LOGGER{j}", indent=STD_SPACE_INDENT):
        log("test")
        log("test")

        for i in range(4):
            with log("wait 1s"):
                log("start waiting")
                await asyncio.sleep(1)
            log(f"log{i}")


async def main():
    with Logger("MAIN", indent=STD_NUMBERED_INDENT):
        await asyncio.gather(*[test(j) for j in range(5)])


if __name__ == "__main__":
    asyncio.run(main())
