import time
import uuid

class BehaviorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        print(
            f"[SES] request_id={request_id} "
            f"path={request.path} "
            f"method={request.method} "
            f"duration={duration:.4f}s"
        )

        return response
