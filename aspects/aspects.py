import sys
import wrapt
from purgatory import AsyncCircuitBreakerFactory
from ratelimit import limits
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

counter = 1
circuitbreaker = AsyncCircuitBreakerFactory(default_threshold=3)

@wrapt.patch_function_wrapper("langchain_core.tools", "StructuredTool.ainvoke")
@circuitbreaker("StructuredTool.ainvoke")
async def structuredtool_ainvoke(wrapped, instance, args, kwargs):
    return await wrapped(*args, **kwargs)

@wrapt.patch_function_wrapper("langchain_core.tools", "StructuredTool.ainvoke")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(3),
    retry=retry_if_exception_type(Exception),
)
@limits(calls=1, period=2)
async def structuredtool_ainvoke(wrapped, instance, args, kwargs):
    global counter
    try:
        print(str(counter) + ". " + args[0].get("name"), file=sys.stderr)
    except:
        print(str(counter) + ". " + "StructuredTool.ainvoke called", file=sys.stderr)
    counter += 1
    return await wrapped(*args, **kwargs)