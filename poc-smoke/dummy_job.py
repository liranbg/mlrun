# ML-12736 POC dummy job — trivial handler to exercise the v2-api run-submission path.
def handler(context, p: int = 21):
    context.logger.info("pydantic-v2 POC dummy job running", p=p)
    context.log_result("answer", p * 2)
    return p * 2
